import os
from celery import shared_task
from time import sleep

import scap.processing as processing

from scap.models import ForestCoverCollection, AGBCollection, AOICollection

@shared_task(bind=True)
def process_updated_collection(self, collection, collection_type):
    match collection_type:
        case 'fc':
            collection = ForestCoverCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            processing.generate_forest_cover_files(collection)
            processing.generate_stocks_and_emissions_files(collection, collection_type)
        case 'agb':
            collection = AGBCollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            processing.generate_agb_files(collection)
            processing.generate_stocks_and_emissions_files(collection, collection_type)
        case 'aoi':
            collection = AOICollection.objects.get(id=collection)
            processing.assign_task(collection, self.request.id)
            processing.generate_aoi_features(collection)
        case _:
            # TODO Raise error
            pass
    processing.generate_zonal_statistics(collection, collection_type)