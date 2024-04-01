import os
from celery import shared_task
from time import sleep

from scap.models import ForestCoverCollection, AGBCollection, AOICollection, ForestCoverFile
import scap.processing as processing

@shared_task
def process_fc_collection(fc_collection_name):
    print("About to process " + fc_collection_name)
    fc_obj = ForestCoverCollection.objects.get(name=fc_collection_name)
    owner = fc_obj.owner

    yearly_files = fc_obj.yearly_files.all().order_by('year')
    for current_file in yearly_files:
        collection_type = 'fc'
        input_path = processing.temp_load(current_file.file.path, fc_collection_name, collection_type, owner)

    print("Done Processing FC")
    fc_obj.processing_status = 'Processed'
    fc_obj.save()


@shared_task
def process_agb_collection(agb_collection_name):
    print("About to process " + agb_collection_name)
    agb_obj = AGBCollection.objects.get(name=agb_collection_name)
    owner = agb_obj.username
    collection_type = 'agb'
    input_path = processing.temp_load(agb_obj.file.path)

    print("Done Processing AGB")
    agb_obj.processing_status = 'Processed'
    agb_obj.save()


@shared_task
def process_aoi_collection(aoi_collection_name):
    print("About to process " + aoi_collection_name)
    aoi_obj = AOICollection.objects.get(name=aoi_collection_name)
    ext = os.path.splitext(aoi_obj.file.path)[1]

    match ext:
        case '.zip':
            pass
        case '.json':
            pass

    print("Done Processing AOI")
    aoi_obj.processing_status = 'Processed'
    aoi_obj.save()