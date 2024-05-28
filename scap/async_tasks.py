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
def process_updated_collection(self, collection, collection_type):
    logger.info('Reached ASYNC function')
    tracemalloc.start()
    stage = 1
    total_stages = 1
    log_memory_snapshot()
    match collection_type:
        case 'fc':
            logger.info('Reached FC')
            collection = ForestCoverCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 3
            processing.set_stage(collection, stage, total_stages)

            processing.generate_forest_cover_files(collection)

            log_memory_snapshot()
            stage += 1
            processing.set_stage(collection, stage, total_stages)

            processing.generate_stocks_and_emissions_files(collection, collection_type)
            log_memory_snapshot()
            stage += 1
        case 'agb':
            logger.info('Reached AGB')
            collection = AGBCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 3
            processing.set_stage(collection, stage, total_stages)

            processing.generate_agb_files(collection)

            log_memory_snapshot()
            stage += 1
            processing.set_stage(collection, stage, total_stages)

            processing.generate_stocks_and_emissions_files(collection, collection_type)
            log_memory_snapshot()
            stage += 1
        case 'aoi':
            logger.info('Reached AOI')
            collection = AOICollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 2
            processing.set_stage(collection, stage, total_stages)

            processing.generate_aoi_features(collection)

            log_memory_snapshot()
            stage += 1
        case _:
            # TODO Raise error
            logger.info('Error processing updated collection')
            pass

    processing.mark_available(collection)
    processing.set_stage(collection, stage, total_stages)
    processing.generate_zonal_statistics(collection, collection_type)
    processing.mark_complete(collection)
    logger.info('Done processing dataset')
    log_memory_snapshot()