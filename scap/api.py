import json as json_lib
import os
import shutil
import tempfile
import time
from pathlib import Path
import numpy
import logging

import doi
import requests
import pandas as pd
from osgeo import ogr
from itertools import product
from datetime import datetime
from django.http import JsonResponse
from pandas_highcharts.core import serialize
from shapely.geometry import shape
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import GEOSGeometry
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group

from ScapTestProject import settings
from scap.models import (AOIFeature, ForestCoverFile, CarbonStatistic, ForestCoverStatistic, CarbonStockFile,
                         EmissionFile, AGBFile,
                         AOICollection, ForestCoverCollection, AGBCollection, CurrentTask, PilotCountry, UserMessage)

from scap.processing import calculate_zonal_statistics, generate_aoi_file
from scap.utils import validate_file, upload_tiff_to_geoserver
from scap.async_tasks import process_updated_collection, validate_uploaded_dataset
import geopandas as gpd
from django.core.mail import send_mail

from django.db.models import Count, Max, Min, Avg

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json_lib.load(f)

logger = logging.getLogger("django")


# This method is used to generate geodjango objects for AOI or Boundary Data Source
# Uses LayerMapping technique to update the object from shape file
# def generate_geodjango_objects_boundary(verbose=True):
#     boundaryfiles_mapping = {
#         'feature_id': 'feature_id',
#         'name_es': 'name_es',
#         'nomedep': 'nomedep',
#         'nomemun': 'nomemun',
#         'pais': 'pais',
#         'fid': 'FID',
#         'geom': 'MULTIPOLYGON',
#     }
#     boundary = os.path.abspath(
#         os.path.join(os.path.dirname(__file__), 'data',
#                      r"C:\Users\gtondapu\Desktop\SCAP\Boundary\mapbiomas\mapbiomas_merged.shp"),
#     )
#     lm = LayerMapping(BoundaryFiles, boundary, boundaryfiles_mapping, transform=False)
#     lm.save(strict=True, verbose=verbose)

def test(request):
    generate_geodjango_objects_aoi()
    return HttpResponse("sucess")


@csrf_exempt
def upload_drawn_aoi(request, country):
    user = request.user.username
    if not user:
        return JsonResponse({'error': 'login'})
    lcs = request.POST.getlist('lcs[]')
    agbs = request.POST.getlist('agbs[]')
    feature = request.POST.get('geometry')

    feat = json_lib.loads(feature)
    geom = feat['features'][0]['geometry']

    current_time = datetime.now()

    coll_name = 'user-drawn-' + user + '.' + current_time.strftime("%Y%m%dT%H%M%S")

    coll = AOICollection()
    coll.name = coll_name
    coll.description = 'User Drawn AOI'
    coll.access_level = 'Private'
    coll.owner = request.user
    coll.save()

    if geom['type'] == 'Polygon':
        geom['type'] = 'MultiPolygon'
        geom['coordinates'] = [geom['coordinates']]

    poly = ogr.CreateGeometryFromJson(str(geom))
    area = poly.GetArea()

    uploaded_feature = AOIFeature(geom=GEOSGeometry(json_lib.dumps(geom)), collection=coll)
    uploaded_feature.name = coll_name
    uploaded_feature.iso3 = ''
    uploaded_feature.desig_eng = 'DRAWN'
    uploaded_feature.rep_area = area
    uploaded_feature.save()

    stats_task, vis_task, delete_task = generate_aoi_file(uploaded_feature, coll)

    stats_task.apply()
    delete_task.apply()

    aoi_collections = [coll]
    agb_collections = list(AGBCollection.objects.filter(id__in=agbs))
    fc_collections = list(ForestCoverCollection.objects.filter(id__in=lcs))

    available_sets = list(product(fc_collections, agb_collections, aoi_collections))
    for fc, agb, aoi in available_sets:
        calculate_zonal_statistics.apply_async(args=[fc.id, agb.id, aoi.id], kwargs={}, queue='stats')
        calculate_zonal_statistics.apply_async(args=[fc.id, None, aoi.id], kwargs={}, queue='stats')

    return JsonResponse({"aoi_id": uploaded_feature.id})


def generate_geodjango_objects_aoi(verbose=True):
    aoi_mapping = {
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
    aoi = os.path.abspath(
        os.path.join(r'C:\Users\gtondapu\Downloads\ProtectedAreas_AllPilotCountries\PilotCountries.shp'),
    )

    lm = LayerMapping(AOIFeature, aoi, aoi_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


@csrf_exempt
def save_forest_cover_file(request):
    try:
        coll = ForestCoverCollection.objects.get(name=request.POST['coll_name'])
        new_tiff = ForestCoverFile()
        new_tiff.year = request.POST['year']
        new_tiff.file = request.FILES['FC_tiff']
        new_tiff.metadata_link = request.POST['metadata']
        try:
            new_tiff.doi_link = doi.validate_doi(request.POST['doi'])

        except Exception as e:
            new_tiff.doi_link = ""

        new_tiff.collection = coll
        new_tiff.save()

        return JsonResponse({"result": "success", "error_message": ""})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})


@csrf_exempt
def get_tiff_data(request, pk):
    return_obj = {'data': []}

    try:
        coll_name = request.POST['coll_name']
        if coll_name:
            coll = ForestCoverCollection.objects.get(name=coll_name, owner__username=request.user.username)
            results_arr = []
            tiffs = ForestCoverFile.objects.filter(collection=coll).values('year', 'file', 'metadata_link', 'doi_link')
            for tiff in tiffs:
                try:
                    doi_full = doi.validate_doi(tiff.get('doi_link'))
                except Exception as e:
                    doi_full = ""
                results_arr.append(
                    {'userId': str(request.user), 'year': tiff.get('year'), 'filename': tiff.get('file').split('/')[-1],
                     'metadata': tiff.get('metadata_link'),
                     'doi': tiff.get('doi_link'), 'doi_full_link': doi_full})
            return_obj['data'] = results_arr
        return JsonResponse(return_obj)
    except Exception as e:
        return JsonResponse(return_obj)


@csrf_exempt
def get_tiff_id(request, pk):
    tiff = ForestCoverFile.objects.get(year=request.POST.get('year'), collection__name=request.POST.get('coll_name'))
    return JsonResponse({"id": tiff.id, "doi": tiff.doi_link})


@csrf_exempt
def add_tiff_record(request, pk):
    existing_coll = ForestCoverCollection.objects.get(name=request.POST.get('coll_name'),
                                                      owner__username=request.user.username)
    try:
        new_tiff = ForestCoverFile()
        new_tiff.collection = existing_coll
        new_tiff.year = request.POST.get('year')
        # new_tiff.file = request.FILES['file']
        new_tiff.metadata_link = request.POST.get('metadata_link')
        new_tiff.doi_link = request.POST.get('doi_link')

        validated_file = validate_file(request.FILES['file'], 'fc')
        if validated_file:
            new_tiff.validation_status = 'Validated'
            new_tiff.file = request.FILES['file']
        else:
            raise Exception('Please check the CRS and values. The file will not be saved')
        new_tiff.save()
        name = 'preview.fc.' + request.user.username + '.' + request.POST.get('coll_name') + '.' + str(
            request.POST.get('year'))
        path = new_tiff.file.path
        upload_tiff_to_geoserver(name, path)
    except Exception as e:
        return JsonResponse({"error": str(e)})
    return JsonResponse({"added": "success", "error": ""})


@csrf_exempt
def get_forestcoverfile_stats(request):
    coll_name = request.POST.get('coll_name')
    year = request.POST.get('year')
    import json
    if request.POST.get('type') == 'fc':
        coll = ForestCoverCollection.objects.get(name=coll_name)
        file = ForestCoverFile.objects.get(collection=coll.id, year=year)
        name = file.file.path
    elif request.POST.get('type') == 'agb':
        coll = AGBCollection.objects.get(name=coll_name)
        name = coll.source_file.path
    else:
        coll = AOICollection.objects.get(name=coll_name)
        name = coll.source_file.path
    actual_json = json.loads(os.popen('gdalinfo -stats -json ' + name).read())
    crs = actual_json['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[1]
    return JsonResponse({'shape': json.dumps(actual_json['size']), 'min': actual_json['bands'][0]['minimum'],
                         'max': actual_json['bands'][0]['maximum'], 'crs': crs,
                         'extent': json.dumps(actual_json['wgs84Extent']),
                         'filename': Path(actual_json['description']).name})


@csrf_exempt
def send_for_admin_review(request, pk=0):
    if request.POST.get('type') == 'fc':
        try:
            existing_coll = ForestCoverCollection.objects.get(name=request.POST.get('coll_name'),
                                                              owner__username=request.user.username)
            validate_uploaded_dataset.delay(existing_coll.id, 'fc', request.POST.get('coll_name'),
                                            request.user.username)
            existing_coll.approval_status = 'Validating Data'
            existing_coll.processing_status = 'Not Processed'
            existing_coll.save()
            return JsonResponse({'success': 'success'})
        except:
            return JsonResponse({'error': 'error'})
        # validate sibling files before changing the status to 'Submitted'
        # fc_files = ForestCoverFile.objects.filter(collection=existing_coll)
        # result = True
        # print(fc_files)
        # if fc_files.count() == 0:
        #     existing_coll.approval_status = 'Not Submitted'
        #     existing_coll.save()
        #     return JsonResponse({'error': 'No files to validate'})
        # for file in fc_files:
        #     if not validate_file(bytes(file.file.read())):
        #         result = False
        #         break
        # if result:
        #     existing_coll.approval_status = 'Submitted'
        #     existing_coll.save()

    elif request.POST.get('type') == 'agb':
        try:
            existing_coll = AGBCollection.objects.get(name=request.POST.get('coll_name'),
                                                      owner__username=request.user.username)
            validate_uploaded_dataset.delay(existing_coll.id, 'agb', request.POST.get('coll_name'),
                                            request.user.username)
            existing_coll.approval_status = 'Validating Data'
            existing_coll.processing_status = 'Not Processed'
            existing_coll.save()
            return JsonResponse({'success': 'success'})
        except:
            return JsonResponse({'error': 'error'})
        # existing_coll.approval_status = 'Validating Data'
        # if not validate_file(bytes(existing_coll.source_file.file.read())):
        #     return JsonResponse({'error': 'error'})
        # else:
        #     name = 'preview.agb.' + request.user.username + '.' + request.POST.get('coll_name') + '.' + str(
        #         existing_coll.year)
        #     print(existing_coll.source_file.name)
        #     path = existing_coll.source_file.path
        #     upload_tiff_to_geoserver(name, path)
        #     existing_coll.approval_status = 'Submitted'
        #     existing_coll.save()
        # return JsonResponse({'success': 'success'})
    else:
        return JsonResponse({'error': 'error'})


@csrf_exempt
def update_tiff_record(request, pk):
    return_obj = {}
    existing_tiff = ForestCoverFile.objects.get(id=request.POST.get('id'))
    existing_tiff.year = request.POST.get('year')
    existing_tiff.metadata_link = request.POST.get('metadata_link')
    if request.FILES:
        existing_tiff.file = request.FILES['file']
    existing_tiff.doi_link = request.POST.get('doi_link')
    existing_tiff.save()
    return JsonResponse(return_obj)


@csrf_exempt
def delete_tiff_record(request, pk):
    tiff = ForestCoverFile.objects.get(year=request.POST.get('year'), collection__name=request.POST.get('coll_name'))
    tiff.delete()
    return JsonResponse({"deleted": "success"})


@csrf_exempt
def updatetomodel(request):
    try:

        coll_name = request.POST['coll_name']
        existing_collection = ForestCoverCollection.objects.filter(name=coll_name).first()
        uploaded_tiffs = request.FILES.getlist('FC_tiffs_New[]')
        original_names = request.POST.getlist('FC_tiffs_New_OriginalNames[]')
        uploaded_tiffs_names = request.POST.getlist('FC_tiffs_New_Name[]')

        for i in range(len(uploaded_tiffs)):
            with open(os.path.join(existing_collection.path_to_tif_file, uploaded_tiffs_names[i]),
                      "wb") as file1:
                file1.write(uploaded_tiffs[i].read())
        tiffs = uploaded_tiffs_names

        for tiff in tiffs:
            new_collection = ForestCoverCollection()
            new_collection.name = coll_name
            new_collection.collection_description = existing_collection.collection_description
            new_collection.boundary_file = existing_collection.boundary_file
            new_collection.tiff_file = tiff
            new_collection.access_level = existing_collection.access_level
            new_collection.username = request.user.username
            if 'Mollweide' in proj:
                new_collection.save()
            else:
                return JsonResponse({"result": "error", "error_message": "Invalid file " + original_names[i]})
            return JsonResponse({"result": "success"})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})


@csrf_exempt
def is_forest_cover_collection_valid(request):
    collections = list(ForestCoverCollection.objects.values('name').distinct())
    arr = []
    # print(collections)
    for c in collections:
        arr.append(c['name'])
    print(arr)
    if request.POST['coll_name'] not in arr:
        return JsonResponse({"result": "success"})
    else:
        return JsonResponse({"result": "error", "error_message": "Please choose a different name for collection"})


@csrf_exempt
def get_forest_cover_collections(request):
    arr = []
    collections = list(
        ForestCoverCollection.objects.filter(username=request.user.username).values('name').distinct())

    # print(collections)
    for c in collections:
        arr.append(c['name'])

    return JsonResponse({"coll": arr})


@csrf_exempt
def get_yearly_forest_cover_files(request):
    coll_name = request.POST['coll_name']
    files = list(ForestCoverCollection.objects.filter(name=coll_name))
    arr = []
    print(files)
    for c in files:
        arr.append(c.tiff_file)
    return JsonResponse({"tiffs": arr})


@csrf_exempt
def get_aoi_list(request):
    try:
        aois = AOICollection.objects.filter(username=request.user.username).values()
        print(request.user.username)
        print(aois)
        names = []
        last_accessed_on = []
        for i in range(len(aois)):
            names.append(aois[i]['aoi_name'])
            last_accessed_on.append(aois[i]['last_accessed_on'])
        return JsonResponse({"result": "success", "names": names, "last_accessed_on": last_accessed_on})
    except Exception as e:
        print(e, __line_no__)
        return JsonResponse({"result": "error", "message": str(e)})


@csrf_exempt
def get_aoi_id(request, country=0):
    if request.POST['desig_eng'] == 'COUNTRY':
        pc = PilotCountry.objects.filter(country_name=request.POST['aoi'], country_code=request.POST['iso3']).first()
        return JsonResponse({"id": pc.id, "country_or_aoi": "country"})
    else:
        aoi = AOIFeature.objects.filter(name=request.POST['aoi'], iso3=request.POST['iso3'],
                                        desig_eng=request.POST['desig_eng']).first()
        return JsonResponse({"id": aoi.id, "country_or_aoi": "aoi"})


@csrf_exempt
def get_AOI(request, country=1):
    json_obj = {}
    try:
        vec = gpd.read_file(os.path.join(config['DATA_DIR'], 'aois/peru/peru_pa.shp'))

        json_obj["data_pa"] = json_lib.loads(vec.to_json())
    except:
        return JsonResponse({})
    return JsonResponse(json_obj)


def fetch_carbon_charts(pa_name, owner, container):
    # TODO Add charts for carbon stock and AGB in addition to emissions
    chart = None
    lcs = []
    agbs = []
    try:
        lc_ids = []
        agb_ids = []
        df = pd.DataFrame(list(CarbonStatistic.objects.filter(aoi_index__name=pa_name).values('emissions', 'aoi_index',
                                                                                              'year_index',
                                                                                              'fc_index_id',
                                                                                              'agb_index_id').distinct()))
        print(df)
        if not df.empty:
            lc_ids = numpy.array(df['fc_index_id'].unique()).tolist()
            agb_ids = numpy.array(df['agb_index_id'].unique()).tolist()
            lc_ids.sort()
            agb_ids.sort()
        if owner.is_authenticated:
            df_lc_owner = ForestCoverCollection.objects.filter(owner=owner, id__in=lc_ids).values()
            df_lc_public = ForestCoverCollection.objects.filter(access_level='Public', id__in=lc_ids).values()
            df_lc = pd.DataFrame((df_lc_owner.union(df_lc_public).values()))

            lcs = df_lc.to_dict('records')
            df_agb_owner = AGBCollection.objects.filter(owner=owner, id__in=agb_ids).values()
            df_agb_public = AGBCollection.objects.filter(access_level='Public', id__in=agb_ids).values()
            df_agb = pd.DataFrame(df_agb_owner.union(df_agb_public).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        else:
            df_lc = pd.DataFrame(ForestCoverCollection.objects.filter(access_level='Public', id__in=lc_ids).values())
            lcs = df_lc.to_dict('records')
            df_agb = pd.DataFrame(AGBCollection.objects.filter(access_level='Public',
                                                               id__in=agb_ids).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        if df.empty:
            if pa_name == 'Ivory Coast':
                pa_name = "Côte d'Ivoire"
            chart = serialize(pd.DataFrame([]), render_to=container, output_type='json', type='spline',
                              title='CarbonStatistics: ' + pa_name)
            return chart, lcs, agbs
        df["fc_index_id"] = "LC" + df["fc_index_id"].apply(str)
        df["agb_index_id"] = "AGB" + df["agb_index_id"].apply(str)  # Add the prefix AGB to the AGB id column
        grouped_data = df.groupby(['year_index', 'fc_index_id', 'agb_index_id'])['emissions'].sum().reset_index()
        pivot_table = pd.pivot_table(grouped_data, values='emissions', columns=['fc_index_id', 'agb_index_id'],
                                     index='year_index',
                                     fill_value=None)
        if pa_name == 'Ivory Coast':
            pa_name = "Côte d'Ivoire"
        chart = serialize(pivot_table, render_to=container, output_type='json', type='spline',
                          title='Emission Statistics: ' + pa_name)
        return chart, lcs, agbs
    except Exception as e:
        error_msg = "Could not generate chart data for emissions"
        print(str(e))

    return chart, lcs, agbs


def fetch_carbon_stock_charts(pa_name, owner, container):
    # TODO Add charts for carbon stock and AGB in addition to emissions
    chart_cs = None
    lcs = []
    agbs = []
    try:
        lc_ids = []
        agb_ids = []
        df = pd.DataFrame(
            list(CarbonStatistic.objects.filter(aoi_index__name=pa_name).values('final_carbon_stock', 'aoi_index',
                                                                                'year_index',
                                                                                'fc_index_id',
                                                                                'agb_index_id').distinct()))
        if not df.empty:
            lc_ids = numpy.array(df['fc_index_id'].unique()).tolist()
            agb_ids = numpy.array(df['agb_index_id'].unique()).tolist()
            lc_ids.sort()
            agb_ids.sort()
        if owner.is_authenticated:
            df_lc_owner = ForestCoverCollection.objects.filter(owner=owner, id__in=lc_ids).values()
            df_lc_public = ForestCoverCollection.objects.filter(access_level='Public', id__in=lc_ids).values()
            df_lc = pd.DataFrame((df_lc_owner.union(df_lc_public).values()))

            lcs = df_lc.to_dict('records')
            df_agb_owner = AGBCollection.objects.filter(owner=owner, id__in=agb_ids).values()
            df_agb_public = AGBCollection.objects.filter(access_level='Public', id__in=agb_ids).values()
            df_agb = pd.DataFrame(df_agb_owner.union(df_agb_public).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        else:
            df_lc = pd.DataFrame(ForestCoverCollection.objects.filter(access_level='Public', id__in=lc_ids).values())
            lcs = df_lc.to_dict('records')
            df_agb = pd.DataFrame(AGBCollection.objects.filter(access_level='Public',
                                                               id__in=agb_ids).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        if df.empty:
            chart = serialize(pd.DataFrame([]), render_to=container, output_type='json', type='spline',
                              title='Carbon Stock: ' + pa_name)
            return chart, lcs, agbs
        df["fc_index_id"] = "LC" + df["fc_index_id"].apply(str)
        df["agb_index_id"] = "AGB" + df["agb_index_id"].apply(str)  # Add the prefix AGB to the AGB id column
        grouped_data_cs = df.groupby(['year_index', 'fc_index_id', 'agb_index_id'])[
            'final_carbon_stock'].sum().reset_index()
        pivot_table_cs = pd.pivot_table(grouped_data_cs, values='final_carbon_stock',
                                        columns=['fc_index_id', 'agb_index_id'],
                                        index='year_index',
                                        fill_value=None)
        if pa_name == 'Ivory Coast':
            pa_name = "Côte d'Ivoire"
        chart_cs = serialize(pivot_table_cs, render_to=container, output_type='json', type='spline',
                             title='Carbon Stock: ' + pa_name)
        return chart_cs, lcs, agbs
    except Exception as e:
        error_msg = "Could not generate chart data for carbon stock"
        print(str(e))

    return chart_cs, lcs, agbs


def fetch_forest_change_charts(pa_name, owner, container):
    df_defor = pd.DataFrame(list(ForestCoverStatistic.objects.filter(aoi_index__name=pa_name).values()))
    lc_names = []
    if not df_defor.empty:
        lc_names = numpy.array(df_defor['fc_index'].unique()).tolist()
    if owner.is_authenticated:
        df_lc_defor_owner = ForestCoverCollection.objects.filter(owner=owner, name__in=lc_names).values()
        df_lc_defor_public = ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values()
        df_lc_defor = pd.DataFrame((df_lc_defor_owner.union(df_lc_defor_public).values()))
    else:
        df_lc_defor = pd.DataFrame(
            ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values())
    lcs_defor = df_lc_defor.to_dict('records')
    if df_defor.empty:
        if pa_name == 'Ivory Coast':
            pa_name = "Côte d'Ivoire"
        chart_fc = serialize(pd.DataFrame([]), render_to=container, output_type='json', type='spline',
                             xticks=[],
                             title='Net Forest Change: ' + pa_name, )

        return chart_fc, lcs_defor

    df_defor = df_defor.assign(fc_index_id=[1 + i for i in range(len(df_defor))])[
        ['fc_index_id'] + df_defor.columns.tolist()]
    df_defor["fc_index_id"] = "LC" + df_defor["fc_index"].apply(str)

    df_defor["nfc"] = df_defor['forest_gain'] - df_defor['forest_loss']
    years_defor = list(df_defor['year_index'].unique())
    pivot_table_defor = pd.pivot_table(df_defor, values='nfc', columns=['fc_index'],
                                       index='year_index', fill_value=None)
    if pa_name == 'Ivory Coast':
        pa_name = "Côte d'Ivoire"
    chart_fc = serialize(pivot_table_defor, render_to=container, output_type='json', type='spline',

                         xticks=years_defor,
                         title='Net Forest Change: ' + pa_name, )

    return chart_fc, lcs_defor


def fetch_deforestation_charts(pa_name, owner, container):
    df_defor = pd.DataFrame(list(ForestCoverStatistic.objects.filter(aoi_index__name=pa_name).values()))
    lc_names = []
    if not df_defor.empty:
        lc_names = numpy.array(df_defor['fc_index'].unique()).tolist()
    if owner.is_authenticated:
        df_lc_defor_owner = ForestCoverCollection.objects.filter(owner=owner, name__in=lc_names).values()
        df_lc_defor_public = ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values()
        df_lc_defor = pd.DataFrame((df_lc_defor_owner.union(df_lc_defor_public).values()))
    else:
        df_lc_defor = pd.DataFrame(
            ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values())
    lcs_defor = df_lc_defor.to_dict('records')
    if df_defor.empty:
        if pa_name == 'Ivory Coast':
            pa_name = "Côte d'Ivoire"
        chart_fc = serialize(pd.DataFrame([]), render_to=container, output_type='json', type='spline',
                             xticks=[],
                             title='Deforestation: ' + pa_name, )

        return chart_fc, lcs_defor

    df_defor = df_defor.assign(fc_index_id=[1 + i for i in range(len(df_defor))])[
        ['fc_index_id'] + df_defor.columns.tolist()]
    df_defor["fc_index_id"] = "LC" + df_defor["fc_index"].apply(str)

    # df_defor["nfc"] = df_defor['forest_gain'] - df_defor['forest_loss']
    years_defor = list(df_defor['year_index'].unique())
    pivot_table_defor = pd.pivot_table(df_defor, values='forest_loss', columns=['fc_index'],
                                       index='year_index', fill_value=None)
    if pa_name == 'Ivory Coast':
        pa_name = "Côte d'Ivoire"
    chart_fc = serialize(pivot_table_defor, render_to=container, output_type='json', type='spline',
                         xticks=years_defor,
                         title='Deforestation: ' + pa_name, )

    return chart_fc, lcs_defor


def fetch_forest_change_charts_by_aoi(aoi, owner, container):
    # generating highcharts chart object from python using pandas(forest cover change chart)
    lc_names = []
    df_defor = pd.DataFrame(list(ForestCoverStatistic.objects.filter(aoi_index__name=aoi).values()))
    if not df_defor.empty:
        lc_names = numpy.array(df_defor['fc_index'].unique()).tolist()
    if owner.is_authenticated:
        df_lc_defor_owner = ForestCoverCollection.objects.filter(owner=owner, name__in=lc_names).values()
        df_lc_defor_public = ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values()
        df_lc_defor = pd.DataFrame((df_lc_defor_owner.union(df_lc_defor_public).values()))
    else:
        df_lc_defor = pd.DataFrame(
            ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values())
    lcs_defor = df_lc_defor.to_dict('records')
    if df_defor.empty:
        chart_fc = serialize(pd.DataFrame(), render_to=container, output_type='json', type='spline',
                             xticks=[],
                             title="Net Forest Change: " + aoi)

        return chart_fc, lcs_defor
    df_defor["NFC"] = df_defor['forest_gain'] - df_defor['forest_loss']
    # df_defor["TotalArea"] = df_defor["initial_forest_area"] + df_defor["NFC"]
    # df_defor['fc_index'] = 'LC' + df_defor['fc_index'].apply(str)
    df_defor['fc_index_id'] = 'LC' + df_defor['fc_index'].apply(str)
    # print(df_defor)
    years_defor = list(df_defor['year_index'].unique())
    pivot_table_defor1 = pd.pivot_table(df_defor, values='NFC', columns=['fc_index'],
                                        index='year_index', fill_value=None)
    chart_fc1 = serialize(pivot_table_defor1, render_to=container, output_type='json', type='spline',
                          xticks=years_defor,
                          title="Net Forest Change: " + aoi)
    return chart_fc1, lcs_defor


def fetch_deforestation_charts_by_aoi(aoi, owner, container):
    # generating highcharts chart object from python using pandas(forest cover change chart)
    lc_names = []
    df_defor = pd.DataFrame(list(ForestCoverStatistic.objects.filter(aoi_index__name=aoi).values()))
    if not df_defor.empty:
        lc_names = numpy.array(df_defor['fc_index'].unique()).tolist()
    if owner.is_authenticated:
        df_lc_defor_owner = ForestCoverCollection.objects.filter(owner=owner, name__in=lc_names).values()
        df_lc_defor_public = ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values()
        df_lc_defor = pd.DataFrame((df_lc_defor_owner.union(df_lc_defor_public).values()))
    else:
        df_lc_defor = pd.DataFrame(
            ForestCoverCollection.objects.filter(access_level='Public', name__in=lc_names).values())
    lcs_defor = df_lc_defor.to_dict('records')
    if df_defor.empty:
        chart_fc = serialize(pd.DataFrame(), render_to=container, output_type='json', type='spline',
                             xticks=[],
                             title="Deforestation: " + aoi)

        return chart_fc, lcs_defor
    df_defor['fc_index_id'] = 'LC' + df_defor['fc_index'].apply(str)
    # print(df_defor)
    years_defor = list(df_defor['year_index'].unique())
    pivot_table_defor1 = pd.pivot_table(df_defor, values='forest_loss', columns=['fc_index'],
                                        index='year_index', fill_value=None)
    chart_fc1 = serialize(pivot_table_defor1, render_to=container, output_type='json', type='spline',
                          xticks=years_defor,
                          title="Deforestation: " + aoi)
    return chart_fc1, lcs_defor


def get_agg_check(request, country=0):
    result = CarbonStatistic.objects.all().order_by('year_index')
    data = list(result.values_list('year_index').distinct())
    years = []
    for x in range(len(data)):
        years.append(data[x][0])
    if request.method == 'POST':
        lcs = request.POST.getlist('lcs[]')
        agbs = request.POST.getlist('agbs[]')
        pa_name = country
        min_arr = []
        max_arr = []
        avg_arr = []
        if pa_name > 0:
            try:
                pa = PilotCountry.objects.get(id=country)
                aoi = AOIFeature.objects.get(id=pa.aoi_polygon.id)
                pa_name = aoi.id
            except:
                pass
            data1 = list(
                CarbonStatistic.objects.filter(fc_index__in=lcs, agb_index__in=agbs, aoi_index=pa_name).values(
                    'year_index').annotate(
                    min=Min('emissions'), max=Max('emissions'), avg=Avg('emissions')))

        else:
            print('in else')
            pa_name = country
            data1 = list(
                CarbonStatistic.objects.filter(fc_index__in=lcs, agb_index__in=agbs, aoi_index=pa_name).values(
                    'year_index').annotate(
                    min=Min('emissions'), max=Max('emissions'), avg=Avg('emissions')))
        if len(data1) == 0:
            return JsonResponse({"min": [], "max": [], "avg": []}, safe=False)
        data1.sort(key=lambda x: x['year_index'])

        for x in range(len(data1)):
            min_arr.append([data1[x]['year_index'], data1[x]['min']])
            max_arr.append([data1[x]['year_index'], data1[x]['max']])
            avg_arr.append([data1[x]['year_index'], data1[x]['avg']])

    return JsonResponse({"min": min_arr, "max": max_arr, "avg": avg_arr}, safe=False)


def get_agg_check_cs(request, country=0):
    result = CarbonStatistic.objects.all().order_by('year_index')
    data = list(result.values_list('year_index').distinct())
    years = []
    for x in range(len(data)):
        years.append(data[x][0])
    if request.method == 'POST':
        lcs = request.POST.getlist('lcs[]')
        agbs = request.POST.getlist('agbs[]')
        print(lcs)
        print(agbs)
        pa_name = country
        min_arr = []
        max_arr = []
        avg_arr = []
        if pa_name > 0:
            try:
                pa = PilotCountry.objects.get(id=country)
                aoi = AOIFeature.objects.get(id=pa.aoi_polygon.id)
                pa_name = aoi.id
            except:
                pass
            data1 = list(
                CarbonStatistic.objects.filter(fc_index__in=lcs, agb_index__in=agbs, aoi_index=pa_name).values(
                    'year_index').annotate(
                    min=Min('final_carbon_stock'), max=Max('final_carbon_stock'), avg=Avg('final_carbon_stock')))
        else:
            pa_name = country
            data1 = list(
                CarbonStatistic.objects.filter(fc_index__in=lcs, agb_index__in=agbs, aoi_index=pa_name).values(
                    'year_index').annotate(
                    min=Min('final_carbon_stock'), max=Max('final_carbon_stock'), avg=Avg('final_carbon_stock')))
        if len(data1) == 0:
            return JsonResponse({"min": [], "max": [], "avg": []}, safe=False)
        data1.sort(key=lambda x: x['year_index'])

        for x in range(len(data1)):
            min_arr.append([data1[x]['year_index'], data1[x]['min']])
            max_arr.append([data1[x]['year_index'], data1[x]['max']])
            avg_arr.append([data1[x]['year_index'], data1[x]['avg']])

    return JsonResponse({"min": min_arr, "max": max_arr, "avg": avg_arr}, safe=False)


def get_agg_check_cs_pa(request, country=0):
    result = CarbonStatistic.objects.all().order_by('year_index')
    data = list(result.values_list('year_index').distinct())
    years = []
    for x in range(len(data)):
        years.append(data[x][0])
    if request.method == 'POST':
        lcs = request.POST.getlist('lcs[]')
        agbs = request.POST.getlist('agbs[]')
        pa_id = country
        min_arr = []
        max_arr = []
        avg_arr = []
        data1 = list(
            CarbonStatistic.objects.filter(fc_index__in=lcs, agb_index__in=agbs, aoi_index=pa_id).values(
                'year_index').annotate(
                min=Min('final_carbon_stock'), max=Max('final_carbon_stock'), avg=Avg('final_carbon_stock')))
        if len(data1) == 0:
            return JsonResponse({"min": [], "max": [], "avg": []}, safe=False)
        data1.sort(key=lambda x: x['year_index'])

        for x in range(len(data1)):
            min_arr.append([data1[x]['year_index'], data1[x]['min']])
            max_arr.append([data1[x]['year_index'], data1[x]['max']])
            avg_arr.append([data1[x]['year_index'], data1[x]['avg']])

    return JsonResponse({"min": min_arr, "max": max_arr, "avg": avg_arr}, safe=False)


@csrf_exempt
def get_series_name(request):
    if request.method == 'POST':
        lc_id = request.POST.get('ds_lc')
        agb_id = request.POST.get('ds_agb')
        try:
            if lc_id[2:] != '':
                ds = ForestCoverCollection.objects.get(fc_index=lc_id[2:])
                lc_name = ds.name
                if agb_id != "":
                    ds = AGBCollection.objects.get(agb_index=agb_id[3:])
                    agb_name = ds.name
                else:
                    agb_name = ''
            else:
                lc_name = ''
                agb_name = ''
        except:
            ds = ForestCoverCollection.objects.get(fc_index=lc_id[2:])
            lc_name = ds.name
            if agb_id != "":
                ds = AGBCollection.objects.get(agb_index=agb_id[3:])
                agb_name = ds.name
            else:
                agb_name = ''

        return JsonResponse({"name": lc_name + ', ' + agb_name}, safe=False)


def get_updated_series(request, country=None):
    colors = []

    with open(settings.STATIC_ROOT + '/data/palette.txt') as f:
        for line in f:
            row = line.strip()
            temp = {}
            # print(row.split(',')[0])

            temp['LC'] = int(row.split(',')[0][2:])
            # print(temp['LC'])
            temp['AGB'] = int(row.split(',')[1][3:])
            temp['color'] = row.split(',')[2]
            colors.append(temp)

    if request.method == 'POST':
        if request.POST.get('pa_name'):
            pa_name = request.POST.get('pa_name')
        else:
            pa_name = country
        chart, lcs, agbs = fetch_carbon_charts(pa_name, 'emissions_chart_pa')
        chart_fc1, lcs_defor = fetch_forest_change_charts_by_aoi(pa_name, 'container_fcpa')
        return JsonResponse({'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                             'lcs_defor': json_lib.dumps(lcs_defor), 'lc_data': lcs_defor, 'region_country': pa_name})


def generate_fcc_file(request):
    try:
        year = request.GET.get('year')
        dataset = 'JAXA'
        l_dataset = dataset.lower()
        start = time.time()
        fcs = BoundaryFiles.objects.get(name_es=dataset)
        fcc = ForestCoverChangeFile()  # Create a new FCC file object
        A_TIF = r"your_path\fc\jaxa\fc_jaxa_peru_" + str(int(year) - 1) + "_1ha.tif"
        i = 1
        while (i < 10):
            B_TIF = r"your_path\fc\jaxa\fc_jaxa_peru_" + str(year) + "_1ha.tif"
            if os.path.isfile(B_TIF):
                fcc.year = year
                fcc.baseline_year = int(year) - i
                break
        # Following three files are temporary files that will be deleted later
        OUT_TIF = "temp.tif"
        gdaloutputA = 'temp_A.tif'
        gdaloutputB = 'temp_B.tif'
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(
            "-of Gtiff -ot Int16"))  # Explicitly mentioning the datatype as Int16, to convert from UInt8
        a = gdal.Translate(gdaloutputA, A_TIF, options=translateoptions)
        b = gdal.Translate(gdaloutputB, B_TIF, options=translateoptions)
        a = None
        b = None
        ds1 = gdal.Open(gdaloutputA, gdalconst.GA_ReadOnly)
        ds2 = gdal.Open(gdaloutputB, gdalconst.GA_ReadOnly)

        arr1 = ds1.ReadAsArray()
        arr2 = ds2.ReadAsArray()
        if arr1.shape < arr2.shape:
            arr1 = np.resize(arr1, arr2.shape)
        else:
            arr2 = np.resize(arr2, arr1.shape)
        # subtract every value from both rasters
        result = np.subtract(arr1, arr2)
        driver = gdal.GetDriverByName("GTiff")
        output = driver.Create(OUT_TIF, ds1.RasterXSize, ds1.RasterYSize, 1, gdalconst.GDT_Int16)
        output.SetGeoTransform(ds1.GetGeoTransform())
        output.SetProjection(ds1.GetProjection())
        output.GetRasterBand(1).WriteArray(result)
        output = None
        gdalinput = OUT_TIF
        gdaloutput = r"your_path\fcc\jaxa\fcc_" + l_dataset + "_peru_" + str(
            year) + "_1ha.tif"
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
        c = gdal.Translate(gdaloutput, gdalinput, options=translateoptions)  # compresses the output file
        c = None
        end = time.time()
        totaltime = end - start
        fcc.file_name = "fcc_" + l_dataset + "_peru_" + str(year) + "_1ha.tif"
        fcc.file_directory = r"your_path\fcc\jaxa"
        fcc.fc_source = fcs
        fcc.processing_time = totaltime
        fcc.save()
        return HttpResponse("Success")
    except Exception as e:
        print(e, __line_no__)
        return HttpResponse(str(e))


def get_available_colors():
    colors = []
    try:
        # generating list of colors from  the text file
        with open(settings.STATIC_ROOT + '/data/palette.txt') as f:
            for line in f:
                row = line.strip()
                temp = {}
                temp['LC'] = int(row.split(',')[0][2:])
                temp['AGB'] = int(row.split(',')[1][3:])
                temp['color'] = row.split(',')[2]
                colors.append(temp)
    except Exception as e:
        print(str(e))
    return colors


def get_available_agbs(collection, generating_carbon_files=False):
    owner = collection.owner
    scap_admin = User.objects.get(username='scap_admin')

    available_states = ["Processed", "Available"]
    source_file_states = ["Available"]
    publishing_states = ['Public']

    if generating_carbon_files:
        available_states += ["In Progress"]

    available_agbs_scap = []
    # Add SCAP datasets if the owner isn't SCAP_Admin
    if owner != scap_admin:
        available_agbs_scap = list(AGBCollection.objects.filter(owner=scap_admin,
                                                                processing_status__in=available_states,
                                                                source_file_status__in=source_file_states))
    else:
        # SCAP Admin can always access private datasets from other owners to update calculations
        publishing_states += ['Private']

    available_agbs = list(AGBCollection.objects.filter(owner=owner,
                                                       processing_status__in=available_states,
                                                       source_file_status__in=source_file_states)) + available_agbs_scap

    available_agbs += list(AGBCollection.objects.filter(processing_status__in=available_states,
                                                        source_file_status__in=source_file_states,
                                                        access_level__in=publishing_states).exclude(
        owner__in=[owner, scap_admin]))

    return available_agbs


@csrf_exempt
def update_boundary_file(request, pk):
    collection_type = request.POST.get('type')
    if collection_type == 'fc':
        fc = ForestCoverCollection.objects.get(owner=request.user, id=pk)
        fc.boundary_file = None
        fc.save()
    else:
        agb = AGBCollection.objects.get(owner=request.user, id=pk)
        agb.boundary_file = None
        agb.save()
    return JsonResponse({})


def get_available_fcs(collection, generating_carbon_files=False):
    owner = collection.owner
    scap_admin = User.objects.get(username='scap_admin')

    available_states = ["Processed", "Available"]
    source_file_states = ["Available"]
    publishing_states = ['Public']

    if generating_carbon_files:
        available_states += ["In Progress"]

    available_fcs_scap = []
    # Add SCAP datasets if the owner isn't SCAP_Admin
    if owner != scap_admin:
        available_fcs_scap = list(ForestCoverCollection.objects.filter(owner=scap_admin,
                                                                       processing_status__in=available_states,
                                                                       source_file_status__in=source_file_states))
    else:
        # SCAP Admin can always access private datasets from other owners to update calculations
        publishing_states += ['Private']

    available_fcs = (list(ForestCoverCollection.objects.filter(owner=owner,
                                                               processing_status__in=available_states,
                                                               source_file_status__in=source_file_states)) +
                     available_fcs_scap)

    available_fcs += list(ForestCoverCollection.objects.filter(processing_status__in=available_states,
                                                               source_file_status__in=source_file_states,
                                                               access_level__in=publishing_states).exclude(
        owner__in=[owner, scap_admin]))

    return available_fcs


def get_available_aois(collection):
    owner = collection.owner
    scap_admin = User.objects.get(username='scap_admin')

    available_states = ["Processed", "Available"]

    available_aois_scap = []
    if owner != scap_admin:
        available_aois_scap = list(AOICollection.objects.filter(owner=scap_admin,
                                                                processing_status__in=available_states))

    available_aois = (list(AOICollection.objects.filter(owner=owner, processing_status__in=available_states)) +
                      available_aois_scap)

    return available_aois


@csrf_exempt
def stage_for_processing(request, pk=0):
    collection_type = request.POST.get('type')
    approve_flag = True
    if collection_type == 'fc':
        fc_collection_name = request.POST.get('coll_name')
        collection = ForestCoverCollection.objects.get(name=fc_collection_name)
        fcfiles = ForestCoverFile.objects.filter(collection=ForestCoverCollection.objects.get(name=fc_collection_name))
        for fcfile in fcfiles:
            if fcfile.validation_status != 'Approved':
                approve_flag = False
                break
        if approve_flag:
            collection.approval_status = "Approved"
            collection.processing_status = "Staged"
            collection.save()
            try:
                process_updated_collection.delay(collection.id, collection_type)
            except Exception as error:
                print(error)
            return JsonResponse({'success': 'success'})
        else:
            return JsonResponse({'error': 'cannot approve a collection when all the files belonging to it are not '
                                          'approved. Please approve the individual files and retry.'})
    elif collection_type == 'agb':
        agb_collection_name = request.POST.get('agb_name')
        collection = AGBCollection.objects.get(name=agb_collection_name)
        collection.approval_status = "Approved"
        collection.processing_status = "Staged"
        collection.save()
        try:
            process_updated_collection.delay(collection.id, collection_type)
        except Exception as error:
            print(error)
        return JsonResponse({'success': 'success'})
    else:
        aoi_collection_name = request.POST.get('aoi_name')
        collection = AOICollection.objects.get(name=aoi_collection_name)
        try:
            process_updated_collection.delay(collection.id, collection_type)
        except Exception as error:
            print(error)
        return JsonResponse({'success': 'success'})


@csrf_exempt
def validate_collection(request, pk=0):
    collection_type = request.POST.get('type')
    if collection_type == 'fc':
        fc_collection_name = request.POST.get('coll_name')
        collection = ForestCoverCollection.objects.get(name=fc_collection_name)
        # add validation status check (not validated)


@csrf_exempt
def approve_fc_file(request):
    try:
        print(request.POST.get('coll_name'))

        collection = ForestCoverCollection.objects.get(name=request.POST.get('coll_name'))
        fc_file = ForestCoverFile.objects.get(collection=collection, year=request.POST.get('year'))
        fc_file.validation_status = "Approved"
        fc_file.save()
        return JsonResponse({'success': 'success'})
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)})


@csrf_exempt
def validation_list(request, pk=0):
    collections = ForestCoverCollection.objects.filter(approval_status='Submitted')
    ids = []
    names = []
    years = []
    bdata = []
    for c in collections:
        # if c.boundary_file:
        #     sFile = c.boundary_file.path
        #     print(sFile)
        #     gdf = gpd.read_file(sFile)
        #     bdata.append({'id':c.id,'gjson':json.loads(json.dumps(gdf.to_json()))})
        # else:
        #     bdata.append({'id':c.id,'gjson':None})
        ids.append(c.id)
        names.append(c.name)
        tiff_files = ForestCoverFile.objects.filter(collection=c)
        tyears = []
        for tfile in tiff_files:
            tyears.append(tfile.year)
        years.append(tyears)

    return JsonResponse({'ids': ids, 'names': names, 'years': years})


@csrf_exempt
def deny_notify_user(request):
    print(request.POST.get('type'))
    message = request.POST.get('message')
    user = User.objects.get(username=request.POST.get('user'))
    user_email = [user.email]
    coll_name = request.POST.get('coll_name')
    email = config['EMAIL_HOST_USER']
    if request.method == 'POST':
        if request.POST.get('type') == 'fc':
            print(request.POST.get('coll_name'))
            try:
                if len(request.POST.get('coll_name').split('_')) > 1:
                    us_arr = [pos for pos, char in enumerate(request.POST.get('coll_name')) if char == '_']
                    print(request.POST.get('coll_name').split('_')[0])


                    fc_coll = ForestCoverCollection.objects.get(name=request.POST.get('coll_name')[us_arr[1]+1:])
                    fcfile = ForestCoverFile.objects.get(year=request.POST.get('coll_name').split('_')[0],
                                                         collection=fc_coll)
                    fcfile.delete()
                    coll_name = request.POST.get('coll_name').split('_')[2] + ' (File: ' + fcfile.file.name.split('/')[
                        -1] + ')'
                else:
                    fc_coll = ForestCoverCollection.objects.get(name=request.POST.get('coll_name'))
                    fc_coll.approval_status = 'Denied'
                    fc_coll.save()

                if len(user_email[0]) > 0:
                    send_mail('[S-CAP] - Message about your collection: ' + coll_name, message, email, user_email)
                else:
                    return JsonResponse({'msg': 'No email address is associated with the user'})
                return JsonResponse({'msg': 'success'})
            except Exception as e:
                print(e)
                return JsonResponse({'msg': str(e)})
        elif request.POST.get('type') == 'agb':
            try:
                agb_coll = AGBCollection.objects.get(name=coll_name)
                agb_coll.delete()
                if len(user_email[0]) > 0:
                    send_mail('[S-CAP] - Message about your collection: ' + coll_name, message, email, user_email)
                else:
                    return JsonResponse({'msg': 'No email address is associated with the user'})
                return JsonResponse({'msg': 'success'})
            except Exception as e:
                print(e)
                return JsonResponse({'msg': str(e)})
        # TODO send email to user


def add_aoi_data(request):
    try:
        aoi_coll = AOICollection()
        aoi_coll.name = request.POST.get('aoi_name')
        aoi_coll.description = request.POST.get('aoi_desc')
        aoi_coll.metadata_link = request.POST.get('metadata_link')
        aoi_coll.doi_link = request.POST.get('doi_link')
        aoi_coll.owner = request.user
        import zipfile
        import shapefile
        client_file = request.FILES['file']
        shpname = None
        shxname = None
        dbfname = None
        # unzip the zip file to the same directory
        with zipfile.ZipFile(client_file, 'r') as zip_ref:
            for x in zip_ref.namelist():
                if x.endswith('.shp'):
                    shpname = x
                if x.endswith('.shx'):
                    shxname = x
                if x.endswith('.dbf'):
                    dbfname = x
            r = shapefile.Reader(shp=zip_ref.open(shpname),
                                 shx=zip_ref.open(shxname),
                                 dbf=zip_ref.open(dbfname), )
            bbox = r.bbox
            temp_bbox = [x for x in bbox if -180 <= x <= 180]
            res = bbox == temp_bbox
            res=False
            for x in bbox:
                if x>=-90 and x <= 90:
                    res=True
                else:
                    res=False
                    break
            if r.numShapes > 0 and res:
                aoi_coll.source_file = request.FILES['file']
                aoi_coll.access_level = request.POST.get('access')
                aoi_coll.approval_status = "Approved"
                aoi_coll.processing_status = "Staged"
                aoi_coll.save()
                process_updated_collection.delay(aoi_coll.id, 'aoi')
            else:
                return JsonResponse({"error": "Please check the file and retry."})
    except Exception as e:
        print(e)
        return JsonResponse({"error": "Please check the file contents and projection"})
    return JsonResponse({"error": ""})


def add_agb_data(request, pk=None):
    try:
        logger.info(str(request))
        try:
            boundary_file = request.FILES['boundary_file']
        except Exception as e:
            boundary_file = None
        try:
            file = request.FILES['file']
        except Exception as e:
            file = None
        if request.POST.get('opn') == 'edit':
            agb_coll = AGBCollection.objects.get(owner=request.user, pk=pk)
            agb_coll.description = request.POST.get('agb_desc')
            if file is not None:
                agb_coll.source_file = file
            agb_coll.boundary_file = boundary_file
            agb_coll.metadata_link = request.POST.get('metadata_link')
            agb_coll.doi_link = request.POST.get('doi_link')
            agb_coll.access_level = request.POST.get('access')
            agb_coll.year = request.POST.get('year')
            agb_coll.owner = request.user

        else:
            agb_coll = AGBCollection()
            agb_coll.name = request.POST.get('agb_name')
            agb_coll.description = request.POST.get('agb_desc')
            agb_coll.source_file = file
            agb_coll.boundary_file = boundary_file
            agb_coll.metadata_link = request.POST.get('metadata_link')
            agb_coll.doi_link = request.POST.get('doi_link')
            agb_coll.access_level = request.POST.get('access')
            agb_coll.year = request.POST.get('year')
            agb_coll.owner = request.user
        # agb_coll.processing_status = "Staged"
        agb_coll.processing_status = "Not Processed"
        agb_coll.approval_status = "Not Submitted"
        agb_coll.save()
        process_updated_collection.delay(agb_coll.id, 'agb')
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)})
    return JsonResponse({"error": ""})


@csrf_exempt
def save_message_to_db(name, organization, email, role, message):
    message_object = UserMessage()
    message_object.name = name
    message_object.organization = organization
    message_object.email = email
    message_object.role = role
    message_object.responded_on = None
    message_object.message = message
    message_object.save()


@csrf_exempt
def send_message_scap(request):
    name = request.POST.get('name')
    organization = request.POST.get('organization')
    email = request.POST.get('email')
    role = request.POST.get('role')
    message = request.POST.get('message')
    approver_group = Group.objects.get(name='scap_sysadmins')
    approvers = approver_group.user_set.all()
    approvers_emails = [approver.email for approver in approvers if approver.email]
    try:
        send_mail('[S-CAP] - Message from user', message, email, approvers_emails)
        save_message_to_db(name, organization, email, role, message)
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'error'})
    return JsonResponse({'result': 'success'})


@csrf_exempt
def get_statistics_for_map(request, country):
    result_obj = {}
    cs_result_left = None
    cs_result_right = None
    em_result_left = None
    em_result_right = None
    agb_result_left = None
    agb_result_right = None
    fc_doi_left = ''
    agb_doi_left = ''
    fc_doi_right = ''
    agb_doi_right = ''
    year_left = request.POST.get('year_left')
    year_right = request.POST.get('year_right')

    if request.POST.get('fc_name_left'):
        fc_name_left = request.POST.get('fc_name_left').replace('-', ' ')
        fc_coll_left = ForestCoverCollection.objects.get(name__iexact=fc_name_left)
        if fc_coll_left and fc_coll_left.doi_link:
            fc_doi_left = "FC DOI: " + fc_coll_left.doi_link
    else:
        fc_name_left = None
    if request.POST.get('agb_name_left'):
        agb_name_left = request.POST.get('agb_name_left').replace('-', ' ')
        agb_coll_left = AGBCollection.objects.get(name__iexact=agb_name_left)
        if agb_coll_left.doi_link:
            agb_doi_left = "AGB DOI: " + agb_coll_left.doi_link
    else:
        agb_name_left = None

    if request.POST.get('fc_name_right'):
        fc_name_right = request.POST.get('fc_name_right').replace('-', ' ')
        fc_coll_right = ForestCoverCollection.objects.get(name__iexact=fc_name_right)
        if fc_coll_right.doi_link:
            fc_doi_right = "FC DOI: " + fc_coll_right.doi_link
    else:
        fc_name_right = None
    if request.POST.get('agb_name_right'):
        agb_name_right = request.POST.get('agb_name_right').replace('-', ' ')
        agb_coll_right = AGBCollection.objects.get(name__iexact=agb_name_right)
        if agb_coll_right.doi_link:
            agb_doi_right = "AGB DOI: " + agb_coll_right.doi_link
    else:
        agb_name_right = None

    try:
        cs_result_right = list(
            CarbonStockFile.objects.filter(fc_index__name__iexact=fc_name_right, agb_index__name__iexact=agb_name_right,
                                           year_index=year_right).values())
        cs_result_left = list(
            CarbonStockFile.objects.filter(fc_index__name__iexact=fc_name_left, agb_index__name__iexact=agb_name_left,
                                           year_index=year_left).values())
    except:
        cs_result_right = None
        cs_result_left = None
    try:
        em_result_right = list(
            EmissionFile.objects.filter(fc_index__name__iexact=fc_name_right, agb_index__name__iexact=agb_name_right,
                                        year_index=year_right).values())
        em_result_left = list(
            EmissionFile.objects.filter(fc_index__name__iexact=fc_name_left, agb_index__name__iexact=agb_name_left,
                                        year_index=year_left).values())
    except:
        em_result_right = None
        em_result_left = None
    try:

        agb_result_right = list(
            AGBFile.objects.filter(agb_index__name__iexact=agb_name_right).values())

        agb_result_left = list(
            AGBFile.objects.filter(agb_index__name__iexact=agb_name_left).values())
    except:
        agb_result_left = None
        agb_result_right = None

    result_obj = {'cs_left': cs_result_left, 'cs_right': cs_result_right, 'em_left': em_result_left,
                  'em_right': em_result_right, 'agb_left': agb_result_left, 'agb_right': agb_result_right,
                  'fc_doi_left': fc_doi_left,
                  'agb_doi_left': agb_doi_left,
                  'fc_doi_right': fc_doi_right, 'agb_doi_right': agb_doi_right}
    return JsonResponse(result_obj)
