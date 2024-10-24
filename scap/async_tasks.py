import os
import logging
import linecache
import tracemalloc
from celery.utils.log import get_task_logger
from celery import shared_task
from time import sleep

import scap.processing as processing

from scap.models import ForestCoverCollection, AGBCollection, AOICollection,ForestCoverFile
from celery.utils.log import get_task_logger
from scap.utils import validate_file,upload_tiff_to_geoserver
logger = get_task_logger('ScapTestProject.async_tasks')

def log_memory_snapshot():
    snapshot=tracemalloc.take_snapshot()
    key_type='lineno'
    limit=25
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    logger.info("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        logger.info("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        logger.info("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    logger.info("Total allocated size: %.1f KiB" % (total / 1024))

@shared_task(bind=True)
def process_updated_collection(self, collection_id, collection_type):
    collection = processing.get_collection_by_type(collection_id, collection_type)
    processing.assign_task(collection, self.request.id)
    match collection_type:
        case 'fc':
            processing.generate_forest_cover_files(collection_id)
        case 'agb':
            processing.generate_agb_files(collection_id)
        case 'aoi':
            processing.generate_aoi_features(collection_id)
        case _:
            # TODO Raise error
            logger.info('Error processing updated collection')
            pass

@shared_task(bind=True)
def validate_uploaded_dataset(self, dataset_id, dataset_type,coll_name,username):
    print('received a task')
    if dataset_type == 'fc':
        existing_coll = ForestCoverCollection.objects.get(name=coll_name,
                                                          owner__username=username)
        fc_files = ForestCoverFile.objects.filter(collection=existing_coll)
        result = True
        if fc_files.count() == 0:
            existing_coll.approval_status = 'Not Submitted'
            existing_coll.save()
        for file in fc_files:
            if not validate_file(bytes(file.file.read()),'fc'):
                result = False
                break
        if result:
            existing_coll.approval_status = 'Submitted'
            existing_coll.processing_status = 'Not Processed'
            existing_coll.save()
    else: #agb
        existing_coll = AGBCollection.objects.get(name=coll_name,
                                                  owner__username=username)
        if validate_file(bytes(existing_coll.source_file.file.read()),'agb'):
            name = 'preview.agb.' + username + '.' + coll_name + '.' + str(
                existing_coll.year)
            print(existing_coll.source_file.name)
            path = existing_coll.source_file.path
            existing_coll.approval_status = 'Submitted'
            existing_coll.processing_status = 'Not Processed'
            existing_coll.save()
