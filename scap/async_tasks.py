import os
import logging
from celery.utils.log import get_task_logger
from celery import shared_task
from time import sleep

import scap.processing as processing

from scap.models import ForestCoverCollection, AGBCollection, AOICollection
from celery.utils.log import get_task_logger

logger = get_task_logger('ScapTestProject.async_tasks')

logger = get_task_logger('ScapTestProject.async_tasks')


@shared_task(bind=True)
def process_updated_collection(self, collection, collection_type):
    logger.info('Reached ASYNC function')
    stage = 1
    total_stages = 1
    match collection_type:
        case 'fc':
            logger.info('Reached FC')
            collection = ForestCoverCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 3
            processing.set_stage(collection, stage, total_stages)

            processing.generate_forest_cover_files(collection)

            stage += 1
            processing.set_stage(collection, stage, total_stages)

            processing.generate_stocks_and_emissions_files(collection, collection_type)
            stage += 1
        case 'agb':
            logger.info('Reached AGB')
            collection = AGBCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 3
            processing.set_stage(collection, stage, total_stages)

            processing.generate_agb_files(collection)

            stage += 1
            processing.set_stage(collection, stage, total_stages)

            processing.generate_stocks_and_emissions_files(collection, collection_type)
            stage += 1
        case 'aoi':
            logger.info('Reached AOI')
            collection = AOICollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            total_stages = 2
            processing.set_stage(collection, stage, total_stages)

            processing.generate_aoi_features(collection)

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
