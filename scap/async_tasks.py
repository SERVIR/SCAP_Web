import os
import logging
import linecache
import tracemalloc
from celery.utils.log import get_task_logger
from celery import shared_task
from time import sleep

import scap.processing as processing

from scap.models import ForestCoverCollection, AGBCollection, AOICollection
from celery.utils.log import get_task_logger

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
