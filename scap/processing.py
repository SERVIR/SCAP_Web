import scap.api as api
import xarray as xr
import pandas as pd
import numpy as np
import datetime
import zipfile
import shutil
import math
import json
import time
import os

from celery.utils.log import get_task_logger
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.utils import LayerMapping
from celery.utils.log import get_task_logger
from collections import OrderedDict
from django.conf import settings
from itertools import product
from pathlib import Path

from scap.models import (ForestCoverCollection, ForestCoverFile, AGBCollection, AOICollection, AOIFeature,
                         ForestCoverStatistic, CarbonStatistic, CurrentTask)

from scap.gis_tools import (calculate_change_file, generate_carbon_gtiff, rasterize_aoi, add_collection_name_field,
                            sum_overlapping_pixels, count_overlapping_pixels, copy_mollweide, copy_latlon, mask_water,
                            stitch_geotiffs)


BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

logger = get_task_logger('ScapTestProject.async_tasks')


def assign_task(collection, task_id):
    task = CurrentTask.objects.create(id=task_id)
    collection.processing_task = task
    collection.processing_status = 'In Progress'
    collection.save()


def set_stage(collection, current_stage, total_stages):
    task = collection.processing_task
    task.stage_progress = "Stage {} of {}".format(current_stage, total_stages)
    task.save()


def mark_available(collection):
    collection.processing_status = "Available"
    collection.save()


def mark_complete(collection):
    task = collection.processing_task
    task.subprocess_progress = 100.0
    task.stage_progress = 'All Stages Complete'
    task.description = 'Done Processing Collection'
    task.save() # TODO Delete Task? Keep for records?

    collection.processing_status = "Processed"
    collection.save()


def get_upload_path(file):
    upload_path = os.path.join(settings.MEDIA_ROOT, file.name)
    return upload_path


def get_dataset_item_relative_filepath(dataset_type, user_id, dataset_name, unique_identifier=None):
    user_id = str(user_id)
    if unique_identifier:
        filename = '.'.join((dataset_type, user_id, dataset_name, unique_identifier)) + '.tif'
    else:
        filename = '.'.join((dataset_type, user_id, dataset_name)) + '.tif'

    filepath = os.sep.join((dataset_type, user_id, dataset_name))
    return os.path.join(filepath, filename)


def get_filesystem_dataset_name(original_collection_name, paired_collection_name=None):
    dataset_name = original_collection_name.lower().replace(' ', '-').replace(':', '')

    if paired_collection_name:
        dataset_name += '_' + paired_collection_name.lower().replace(' ', '-')

    return dataset_name


def get_full_filepath(dataset_type, user_id, dataset_name, unique_identifier=None):
    user_id = str(user_id)
    final_dir = os.path.join(config['DATA_DIR'])
    relative_path = get_dataset_item_relative_filepath(dataset_type, user_id, dataset_name, unique_identifier)
    full_filepath = os.path.join(final_dir, relative_path)

    return full_filepath


def load_temp(source_file, dataset_type, user_id, dataset_name, unique_identifier=None):
    user_id = str(user_id)
    temp_dir = os.path.join(config['DATA_DIR'], 'temp')
    relative_path = get_dataset_item_relative_filepath(dataset_type, user_id, dataset_name, unique_identifier)
    temp_filepath = os.path.join(temp_dir, relative_path)

    file_dir = os.path.dirname(temp_filepath)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    shutil.copyfile(source_file, temp_filepath)

    return temp_filepath


def delete_temp(filepath):
    os.remove(filepath)


def update_task_progress(task, progress, progress_change):
    progress = progress + progress_change
    task.subprocess_progress = progress
    task.save()

    return progress


def unzip(zip_filepath, target_directory):
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(target_directory)


def get_shp_file(dir):
    for file in os.listdir(dir):
        if '.shp' in file:
            return os.path.join(dir, file)

    # TODO Error
    return None


def load_to_VEDA(raster_path):
    pass


def load_for_visualization(raster_path, task_obj, current_progress, step_progress, variable_name, year):
    def progress_callback(complete, unknown, message):
        update_task_progress(task_obj, current_progress, round(step_progress * complete * 0.75, 2))

    final_load_path = raster_path.replace('temp/', '').replace('data/', 'public/').replace('.tif', '.nc4')

    logger.info('Loading {} for visualization'.format(final_load_path))

    final_dir = os.path.dirname(final_load_path)
    if not os.path.exists(final_dir):
        os.makedirs(final_dir)

    split_path = os.path.split(raster_path)
    reprojection_load_path = os.path.join(split_path[0], 'latlon_' + split_path[1])

    copy_latlon(str(raster_path), str(reprojection_load_path), progress_callback)

    try:
        with xr.open_dataset(reprojection_load_path, engine="rasterio", chunks=dict(band=1,x=256, y=256), mask_and_scale=False) as file:
            ds = file.isel(band=0).rename({'band_data': variable_name})

        # Set default timestamps
        start_time = datetime.datetime.strptime('{}{}{}'.format(year, 1, 1), '%Y%m%d')
        end_time = datetime.datetime.strptime('{}{}{}'.format(year, 12, 31), '%Y%m%d')
        ds_time_index = datetime.datetime.strptime('{}{}{}'.format(year, 12, 31), '%Y%m%d')

        # Add the time dimension as a new coordinate.
        ds = ds.assign_coords(time=ds_time_index).expand_dims(dim='time', axis=0)
        ds['time_bnds'] = xr.DataArray([[start_time, end_time]], dims=['time', 'nbnds'])
        # 3) Rename and add attributes to this dataset.
        ds = ds.rename({'y': 'latitude', 'x': 'longitude'})
        ds = ds.assign_coords(latitude=np.around(ds.latitude.values, decimals=6),
                              longitude=np.around(ds.longitude.values, decimals=6))

        # 4) Reorder latitude dimension into ascending order
        if ds.latitude.values[1] - ds.latitude.values[0] < 0:
            ds = ds.reindex(latitude=ds.latitude[::-1])

        lat_attr = OrderedDict([('long_name', 'latitude'), ('units', 'degrees_north'), ('axis', 'Y')])
        lon_attr = OrderedDict([('long_name', 'longitude'), ('units', 'degrees_east'), ('axis', 'X')])

        time_attr = OrderedDict([('long_name', 'time'), ('axis', 'T'), ('bounds', 'time_bnds')])
        time_bounds_attr = OrderedDict([('long_name', 'time_bounds')])

        metadata_dict = {'description': 'Filler', 'contact': 'Contact Filler', 'version': '1', 'reference': 'Reference',
                         'temporal_resolution': 'Resolution', 'spatial_resolution': 'Spatial Resolution', 'source': 'None',
                         'south': np.min(ds.latitude.values), 'north': np.max(ds.latitude.values),
                         'east': np.max(ds.longitude.values), 'west': np.min(ds.longitude.values)}

        file_attr = OrderedDict([('Description', metadata_dict['description']),
                                 ('DateCreated', pd.Timestamp.now().strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('Contact', metadata_dict['contact']),
                                 ('Source', metadata_dict['source']),
                                 ('Version', metadata_dict['version']),
                                 ('Reference', metadata_dict['reference']),
                                 ('RangeStartTime', datetime.date(year=year, month=1, day=1).strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('RangeEndTime', datetime.date(year=year, month=12, day=31).strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('SouthernmostLatitude', metadata_dict['south']),
                                 ('NorthernmostLatitude', metadata_dict['north']),
                                 ('WesternmostLongitude', metadata_dict['west']),
                                 ('EasternmostLongitude', metadata_dict['east']),
                                 ('TemporalResolution', metadata_dict['temporal_resolution']),
                                 ('SpatialResolution', metadata_dict['spatial_resolution'])])


        time_encoding = {'units': 'seconds since 1970-01-01T00:00:00Z', 'dtype': np.dtype('int32')}
        time_bounds_encoding = {'units': 'seconds since 1970-01-01T00:00:00Z', 'dtype': np.dtype('int32')}

        # Set the Attributes
        ds.latitude.attrs = lat_attr
        ds.longitude.attrs = lon_attr
        ds.time.attrs = time_attr
        ds.time_bnds.attrs = time_bounds_attr
        ds.time.encoding = time_encoding
        ds.time_bnds.encoding = time_bounds_encoding

        ds.attrs = file_attr

        ds[variable_name].attrs = OrderedDict([('long_name', variable_name),
                                               ('units', 'None'),
                                               ('accumulation_interval', 'yearly'),
                                               ('comment', 'SCAP Dataset')])# TODO

        ds_dtype = ds[variable_name].dtype
        logger.info(ds_dtype)
        ds[variable_name].encoding = OrderedDict([('dtype', ds_dtype),
                                                  ('_FillValue', np.zeros(1,ds_dtype)[0]),
                                                  ('chunksizes', (1, 256, 256)),
                                                  ('missing_value', np.zeros(1,ds_dtype)[0])])# TODO
                                                  #('zlib', True),
                                                  #('complevel', 5)


        dask_future = ds.to_netcdf(final_load_path, unlimited_dims='time', compute=False)
        dask_future.compute()

        del ds
    except Exception as error:
        logger.info(error)
    update_task_progress(task_obj, current_progress, step_progress)

    delete_temp(reprojection_load_path)


def load_for_statistics(raster_path, task_obj, current_progress, step_progress):
    def progress_callback(complete, unknown, message):
        update_task_progress(task_obj, current_progress, round(step_progress * complete, 2))

    # Assumes raster is loaded to temp directory
    final_load_path = raster_path.replace('temp/', '')
    logger.info('Loading {} for statistics'.format(final_load_path))

    final_dir = os.path.dirname(final_load_path)
    if not os.path.exists(final_dir):
        os.makedirs(final_dir)

    mollweide_file = copy_mollweide(raster_path, final_load_path, progress_callback)

    mask_water(mollweide_file)


def generate_forest_cover_change_file(fc_file, user_id, dataset_name, task_obj, current_progress, step_progress):
    # Assumes fc_file and its respective baseline file to be loaded to stats directory
    # Assumes fc_file is not the collection's baseline file
    logger.info('Generating forest cover change file: {} - {}'.format(dataset_name, fc_file.year))

    def progress_callback(complete):
        update_task_progress(task_obj, current_progress, round(step_progress * complete, 2))

    baseline_fc_file = list(ForestCoverFile.objects.filter(collection=fc_file.collection,
                                                           year__lt=fc_file.year).order_by('year'))[-1]

    target_path = get_full_filepath('fcc', user_id, dataset_name, str(fc_file.year))
    baseline_filepath = get_full_filepath('fc', user_id, dataset_name, str(baseline_fc_file.year))
    current_filepath = get_full_filepath('fc', user_id, dataset_name, str(fc_file.year))

    file_dir = os.path.dirname(target_path)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    calculate_change_file(baseline_filepath, current_filepath, target_path, progress_callback)


def generate_scap_source_files(task, current_progress, progress_total, dataset_info, file, is_public,
                               variable_name=None, year=None, filepath=None):
    NUM_STEPS = (is_public + 1)
    step_progress = progress_total / NUM_STEPS

    if not filepath:
        upload_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
        filepath = load_temp(upload_path, *dataset_info)

    load_for_statistics(filepath, task, current_progress, step_progress)
    progress = current_progress + step_progress

    # TODO Add publicly approved check
    if is_public:
        load_for_visualization(filepath, task, progress, step_progress, variable_name, year)
        progress = progress + step_progress

    delete_temp(filepath)

    return progress


def generate_forest_cover_files(fc_collection):
    fc_collection.source_file_status = 'Unavailable'
    fc_collection.save()

    task = fc_collection.processing_task
    task.description = "Generating Forest Cover Files"

    progress = update_task_progress(task, 0.0, 0.0)

    is_public = fc_collection.access_level == 'Public'
    user_id = fc_collection.owner.id
    dataset_name = get_filesystem_dataset_name(fc_collection.name)
    logger.info('Generating forest cover files: {}'.format(dataset_name))

    # TODO Update to only modified files
    yearly_files = fc_collection.yearly_files.all().order_by('year')
    baseline_file = fc_collection.yearly_files.all().order_by('year')[0]

    single_file_progress = 100.0 / len(yearly_files)
    for yearly_file in yearly_files:
        progress_scale = 2.0/3 if yearly_file != baseline_file else 1.0
        dataset_type = 'fc'
        dataset_info = (dataset_type, user_id, dataset_name, str(yearly_file.year))

        target_filepath = None
        yearly_filename = yearly_file.file.name

        if os.path.splitext(yearly_filename)[1] == '.zip':
            upload_path = os.path.join(settings.MEDIA_ROOT, yearly_filename)

            temp_dir = os.path.join(config['DATA_DIR'], 'temp')
            relative_path = get_dataset_item_relative_filepath(dataset_type, user_id, dataset_name, str(yearly_file.year))
            target_filepath = os.path.join(temp_dir, relative_path)

            target_dir = os.path.dirname(target_filepath)
            target_dir = os.path.join(target_dir, str(yearly_file.year))
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            else:
                for file in os.listdir(target_dir):
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)

            unzip(upload_path, target_dir)
            stitch_geotiffs(target_dir, target_filepath)

        progress = generate_scap_source_files(task, progress, progress_scale * single_file_progress,
                                              dataset_info, yearly_file, is_public, 'forest_cover',
                                              yearly_file.year, target_filepath)

        if yearly_file != baseline_file:
            generate_forest_cover_change_file(yearly_file, user_id, dataset_name,
                                              task, progress, (1.0 - progress_scale) * single_file_progress)


    task.description = "Done Generating Forest Cover Files"
    update_task_progress(task, 100.0, 0.0)

    fc_collection.source_file_status = 'Available'
    fc_collection.save()


def generate_agb_files(agb_collection):
    agb_collection.source_file_status = 'Unavailable'
    agb_collection.save()

    task = agb_collection.processing_task
    task.description = "Generating AGB File"

    update_task_progress(task, 0.0, 0.0)

    is_public = agb_collection.access_level == 'Public'
    user_id = agb_collection.owner.id
    dataset_name = get_filesystem_dataset_name(agb_collection.name)
    file = agb_collection.source_file

    dataset_info = ('agb', user_id, dataset_name)

    generate_scap_source_files(task, 0.0, 100.0, dataset_info, file, is_public,
                               'agb', agb_collection.year)

    task.description = "Done Generating AGB File"
    update_task_progress(task, 100.0, 0.0)

    agb_collection.source_file_status = 'Available'
    agb_collection.save()


def generate_aoi_file(aoi_feature, collection, task, current_progress, single_feature_progress):
    user_id = collection.owner.id
    dataset_name = get_filesystem_dataset_name(collection.name)
    feature_name = get_filesystem_dataset_name(aoi_feature.name)
    is_public = False
    file = None
    dataset_info = None

    temp_dir = os.path.join(config['DATA_DIR'], 'temp')
    relative_path = get_dataset_item_relative_filepath('aoi', user_id, dataset_name, feature_name)
    temp_filepath = os.path.join(temp_dir, relative_path)

    file_dir = os.path.dirname(temp_filepath)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    rasterize_aoi(aoi_feature, temp_filepath)

    if os.path.isfile(temp_filepath):
        generate_scap_source_files(task, current_progress, single_feature_progress,
                                   dataset_info, file, is_public, None, None, temp_filepath)


def generate_aoi_features(aoi_collection):
    task = aoi_collection.processing_task
    task.description = "Generating AOI Features"

    update_task_progress(task, 0.0, 0.0)

    user_id = aoi_collection.owner.id
    dataset_name = get_filesystem_dataset_name(aoi_collection.name)

    temp_dir = os.path.join(config['DATA_DIR'], 'temp')
    relative_path = get_dataset_item_relative_filepath('aoi', user_id, dataset_name).replace('.tif', os.sep)
    target_dir = os.path.join(temp_dir, relative_path)

    upload_path = get_upload_path(aoi_collection.source_file)

    unzip(upload_path, target_dir)
    update_task_progress(task, 12.5, 0.0)
    shp_file = get_shp_file(target_dir)
    add_collection_name_field(shp_file, aoi_collection.name)
    update_task_progress(task, 30.0, 0.0)

    field_map = {
        'collection': {'name': 'SCAPName'},
        'wdpa_pid': 'WDPA_PID',
        'name': 'NAME',
        'orig_name': 'ORIG_NAME',
        'desig_eng': 'DESIG_ENG',
        'desig_type': 'DESIG_TYPE',
        'rep_area': 'REP_AREA',
        'gis_area': 'GIS_AREA',
        'iso3': 'ISO3',
        'geom': 'MULTIPOLYGON',
    }

    lm = LayerMapping(AOIFeature, shp_file, field_map, transform=False)
    lm.save(strict=True)

    progress = update_task_progress(task, 50.0, 0.0)


    aoi_features = AOIFeature.objects.filter(collection=aoi_collection)
    single_feature_progress = 50.0 / len(aoi_features)
    for feature in aoi_features:
        generate_aoi_file(feature, aoi_collection, task, progress, single_feature_progress)

    update_task_progress(task, 100.0, 0.0)
    task.description = "Done Generating AOI Features"


def generate_carbon_files(fc_collection, agb_collection, user_id, carbon_type, task, current_progress, step_progress):
    # Assumptions: All FC Files and the AGB file have been loaded for stats
    # TODO Ensure mutual availability and lack of modification to both collections

    fc_dataset_name = get_filesystem_dataset_name(fc_collection.name)
    agb_dataset_name = get_filesystem_dataset_name(agb_collection.name)
    carbon_dataset_name = get_filesystem_dataset_name(fc_collection.name, agb_collection.name)

    agb_filepath = get_full_filepath('agb', user_id, agb_dataset_name)

    forest_cover_type = 'fcc' if carbon_type == 'emissions' else 'fc'

    publish = fc_collection.access_level == 'Public' and  agb_collection.access_level == 'Public'

    NUM_STEPS = (publish + 1)
    step_progress = step_progress / NUM_STEPS

    yearly_fc_files = fc_collection.yearly_files.all()
    for yearly_fc_file in yearly_fc_files:
        def progress_callback(complete):
            update_task_progress(task, current_progress, round(step_progress * complete, 2))

        fc_filepath = get_full_filepath(forest_cover_type, user_id, fc_dataset_name, str(yearly_fc_file.year))
        if not os.path.isfile(fc_filepath):
            continue
        target_filepath = get_full_filepath(carbon_type, user_id, carbon_dataset_name, str(yearly_fc_file.year))

        file_dir = os.path.dirname(target_filepath)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        output = generate_carbon_gtiff(fc_filepath, agb_filepath, yearly_fc_file.year, agb_collection.year,
                                       target_filepath, carbon_type, progress_callback)

        current_progress += step_progress

        if publish:
            if output:
                load_for_visualization(target_filepath, task, current_progress,
                                       step_progress, carbon_type, yearly_fc_file.year)
            current_progress += step_progress


def generate_stocks_and_emissions_files(collection, collection_type):
    task = collection.processing_task
    progress = update_task_progress(task, 0.0, 0.0)
    carbon_pairs = None
    task.description = "Generating Stock and Emissions Files"
    task.save()

    match collection_type:
        case 'fc':
            carbon_pairs = list(product([ collection ],
                                        api.get_available_agbs(collection, generating_carbon_files=True)))
        case 'agb':
            carbon_pairs = list(product(api.get_available_fcs(collection, generating_carbon_files=True),
                                        [ collection ]))
        case _:
            print("Error generating stocks and emissions files")
            # TODO Raise error
            pass
    print('Carbon Dataset Generation Pairs: {}'.format(carbon_pairs))
    for fc, agb in carbon_pairs:
        generate_carbon_files(fc, agb, agb.owner.id, 'emissions',
                              task, progress, 50.0 / len(carbon_pairs))
        generate_carbon_files(fc, agb, agb.owner.id, 'carbon-stock',
                              task, progress, 50.0 / len(carbon_pairs))


    task.description = "Done Generating Stock and Emissions Files"
    task.save()


def calculate_forest_cover_statistics(fc_filepath, fcc_filepath, aoi_filepath):
    start = time.time()

    fc_area = count_overlapping_pixels(fc_filepath, aoi_filepath, 'forest')
    if os.path.isfile(fcc_filepath):
        fc_loss_area = count_overlapping_pixels(fcc_filepath, aoi_filepath, 'loss')
        fc_gain_area = count_overlapping_pixels(fcc_filepath, aoi_filepath, 'gain')
    else:
        fc_loss_area = 0
        fc_gain_area = 0

    end = time.time()

    processing_time = end - start

    return fc_area, fc_loss_area, fc_gain_area, processing_time


def calculate_carbon_statistics(carbon_filepath, emissions_filepath, agb_filepath, aoi_filepath):
    start = time.time()

    final_carbon_stock = sum_overlapping_pixels(carbon_filepath, aoi_filepath)
    if os.path.isfile(emissions_filepath):
        emissions = sum_overlapping_pixels(emissions_filepath, aoi_filepath)
    else:
        emissions = 0
    agb_value = sum_overlapping_pixels(agb_filepath, aoi_filepath)

    end = time.time()

    processing_time = end - start

    return final_carbon_stock, emissions, agb_value, processing_time


def calculate_zonal_statistics(fc_collection, agb_collection, aoi_collection, generate_fc=False):
    # Assumptions: All FC Files, the AGB file, and all AOI Features have been loaded for stats
    # TODO Ensure mutual availability and lack of modification to all collections
    # TODO Add filters for aoi feature, specific fc years for user drawn aois (api.py) 

    fc_dataset_name = get_filesystem_dataset_name(fc_collection.name)
    agb_dataset_name = get_filesystem_dataset_name(agb_collection.name)
    aoi_dataset_name = get_filesystem_dataset_name(aoi_collection.name)
    carbon_dataset_name = get_filesystem_dataset_name(fc_collection.name, agb_collection.name)

    agb_filepath = get_full_filepath('agb', agb_collection.owner.id, agb_dataset_name)
    agb_calibration_year = agb_collection.year

    if generate_fc:
        yearly_fc_files = fc_collection.yearly_files.all()
    else:
        yearly_fc_files = fc_collection.yearly_files.filter(year__gte=agb_calibration_year)

    aoi_features = aoi_collection.features.all()

    possible_combinations = list(product(yearly_fc_files, aoi_features))
    for yearly_fc_file, aoi_feature in possible_combinations:
        feature_name = get_filesystem_dataset_name(aoi_feature.name)

        fc_filepath = get_full_filepath('fc', fc_collection.owner.id,
                                        fc_dataset_name, str(yearly_fc_file.year))
        fcc_filepath = get_full_filepath('fcc', fc_collection.owner.id,
                                         fc_dataset_name, str(yearly_fc_file.year))
        carbon_filepath = get_full_filepath('carbon-stock', agb_collection.owner.id,
                                            carbon_dataset_name, str(yearly_fc_file.year))
        emissions_filepath = get_full_filepath('emissions', agb_collection.owner.id,
                                               carbon_dataset_name, str(yearly_fc_file.year))
        aoi_filepath = get_full_filepath('aoi', aoi_collection.owner.id,
                                         aoi_dataset_name, feature_name)

        if generate_fc:
            try:
               (fc_area,
                fc_gain_area,
                fc_loss_area,
                processing_time) = calculate_forest_cover_statistics(fc_filepath, fcc_filepath, aoi_filepath)
            except:
                logger.info('Error generating FC statistics for files: {} {}'.format(aoi_filepath, fc_filepath))
                continue

            statistic = ForestCoverStatistic()

            statistic.fc_index = fc_collection
            statistic.aoi_index = aoi_feature
            statistic.year_index = yearly_fc_file.year
            statistic.final_forest_area = fc_area
            statistic.forest_gain = fc_gain_area
            statistic.forest_loss = fc_loss_area
            statistic.processing_time = processing_time

            statistic.save()

        if not generate_fc or agb_calibration_year <= yearly_fc_file.year:
            try:
                (final_carbon_stock,
                 emissions,
                 agb_value,
                 processing_time) = calculate_carbon_statistics(carbon_filepath, emissions_filepath, agb_filepath, aoi_filepath)
            except:
                logger.info("Error generating carbon statistics for files: \n{} \n{} \n{}".format(carbon_filepath, emissions_filepath, aoi_filepath))
                continue


            statistic = CarbonStatistic()

            statistic.fc_index = fc_collection
            statistic.aoi_index = aoi_feature
            statistic.agb_index = agb_collection
            statistic.year_index = yearly_fc_file.year
            statistic.final_carbon_stock = final_carbon_stock
            statistic.emissions = emissions
            statistic.agb_value = agb_value
            statistic.processing_time = processing_time

            statistic.save()
        else:
            if not agb_calibration_year <= yearly_fc_file.year and not generate_fc:
                logger.info("Error, forest cover files are improperly filtered")
            logger.info("Skipping invalid year {}, \nFC: {}, \nAGB: {}".format(yearly_fc_file.year, fc_collection.name, agb_collection.name))



def generate_zonal_statistics(collection, collection_type):
    fc_collections = None
    agb_collections = None
    aoi_collections = None
    task = collection.processing_task
    generate_fc = None
    always_generate = False

    match collection_type:
        case 'fc':
            fc_collections = [ collection ]
            agb_collections = api.get_available_agbs(collection)
            aoi_collections = api.get_available_aois(collection)
            generate_fc = True
        case 'agb':
            fc_collections = api.get_available_fcs(collection)
            agb_collections = [ collection ]
            aoi_collections = api.get_available_aois(collection)
            generate_fc = False
        case 'aoi':
            fc_collections = api.get_available_fcs(collection)
            agb_collections = api.get_available_agbs(collection)
            aoi_collections = [ collection ]
            always_generate = True
            generate_fc = True
        case _:
            # TODO Raise error
            pass

    available_sets = list(product(fc_collections, agb_collections, aoi_collections))
    print('Zonal Stats Sets: {}'.format(available_sets))


    progress = 0.0
    for fc, agb, aoi in available_sets:
        task.description = "Calculating Zonal Statistics {} x {} x {}".format(fc.name,
                                                                              agb.name,
                                                                              aoi.name)
        task.save()

        calculate_zonal_statistics(fc, agb, aoi, generate_fc)
        progress = update_task_progress(task, progress, 100.0 / len(available_sets))
    
        if generate_fc and not always_generate:
            generate_fc = False


    task.description = "Done Calculating Zonal Statistics"
    task.save()
