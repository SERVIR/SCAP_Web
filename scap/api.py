import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import doi
import requests
import pandas as pd
from django.http import JsonResponse
from pandas_highcharts.core import serialize
from shapely.geometry import shape
from django.contrib.gis.utils import LayerMapping
from django.views.decorators.csrf import csrf_exempt

from ScapTestProject import settings
from scap.models import (AOIFeature, ForestCoverFile, CarbonStatistic, ForestCoverStatistic,
                         AOICollection, ForestCoverCollection, AGBCollection, PilotCountry)
from scap.async_tasks import process_aoi_collection, process_fc_collection, process_agb_collection
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)


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
        os.path.join(r'C:\Users\gtondapu\Documents\pc_4326.shp'),
    )

    lm = LayerMapping(AOIFeature, aoi, aoi_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


@csrf_exempt
def save_forest_cover_file(request):
    try:
        coll=ForestCoverCollection.objects.get(name=request.POST['coll_name'])
        new_tiff = ForestCoverFile()
        new_tiff.year = request.POST['year']
        new_tiff.file = request.FILES['FC_tiff']
        new_tiff.metadata_link = request.POST['metadata']
        try:
            new_tiff.doi_link = doi.validate_doi(request.POST['doi'])

        except Exception as e:
            new_tiff.doi_link=""

        new_tiff.collection=coll
        new_tiff.save()

        return JsonResponse({"result": "success", "error_message": ""})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})

@csrf_exempt
def get_tiff_data(request,pk):
    return_obj = {'data':[]}

    try:
        coll_name=request.POST['coll_name']
        if coll_name:
            coll = ForestCoverCollection.objects.get(name=coll_name,owner__username=request.user.username)
            results_arr=[]
            tiffs=ForestCoverFile.objects.filter(collection=coll).values('year', 'file', 'metadata_link', 'doi_link')
            for tiff in tiffs:
                try:
                    doi_full = doi.validate_doi(tiff.get('doi_link'))
                except Exception as e:
                    doi_full=""
                results_arr.append({'userId':str(request.user),'year':tiff.get('year'),'filename':tiff.get('file').split('/')[-1],'metadata':tiff.get('metadata_link'),
                                    'doi':tiff.get('doi_link'),'doi_full_link':doi_full})
            return_obj['data']=results_arr
        return JsonResponse(return_obj)
    except Exception as e:
        return JsonResponse(return_obj)


@csrf_exempt
def get_tiff_id(request,pk):
    tiff = ForestCoverFile.objects.get(year=request.POST.get('year'),collection__name=request.POST.get('coll_name'))
    return JsonResponse({"id":tiff.id,"doi":tiff.doi_link})

@csrf_exempt
def add_tiff_record(request,pk):
    existing_coll = ForestCoverCollection.objects.get(name=request.POST.get('coll_name'),owner__username=request.user.username)
    try:
        new_tiff = ForestCoverFile()
        new_tiff.collection=existing_coll
        new_tiff.year=request.POST.get('year')
        new_tiff.file=request.FILES['file']
        new_tiff.metadata_link = request.POST.get('metadata_link')
        new_tiff.doi_link = request.POST.get('doi_link')
        new_tiff.save()
    except:
        return JsonResponse({"error": "error"})
    return JsonResponse({"added":"success"})

@csrf_exempt
def update_tiff_record(request,pk):
    return_obj={}
    existing_tiff = ForestCoverFile.objects.get(id=request.POST.get('id'))
    existing_tiff.year=request.POST.get('year')
    existing_tiff.metadata_link = request.POST.get('metadata_link')
    if request.FILES:
        existing_tiff.file=request.FILES['file']
    existing_tiff.doi_link=request.POST.get('doi_link')
    existing_tiff.save()
    return JsonResponse(return_obj)
@csrf_exempt
def delete_tiff_record(request,pk):
    tiff = ForestCoverFile.objects.get(year=request.POST.get('year'),collection__name=request.POST.get('coll_name'))
    tiff.delete()
    return JsonResponse({"deleted":"success"})

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
def save_AOI(request):
    try:
        aoi_path = os.path.join(config['PATH_TO_DATA'], "Private", request.user.username,
                                "AOIs")
        if not os.path.exists(aoi_path):
            os.makedirs(aoi_path)
        aois = request.FILES.getlist('aois[]')
        aoi_names = request.POST.getlist('aoi_names[]')
        for i in range(len(aois)):
            with open(os.path.join(aoi_path, aoi_names[i]), "wb") as file1:
                file1.write(aois[i].read())
            new_aoi = AOICollection()
            new_aoi.aoi_name = aoi_names[i]
            new_aoi.aoi_shape_file = os.path.join(aoi_path, aoi_names[i])
            new_aoi.path_to_aoi_file = aoi_path
            new_aoi.username = request.user.username
            new_aoi.save()
            return JsonResponse({"result": "success"})
    except Exception as e:
        print(e,__line_no__)
        return JsonResponse({"result": "error", "error_message": str(e)})


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
        print(e,__line_no__)
        return JsonResponse({"result": "error", "message": str(e)})


@csrf_exempt
def delete_AOI(request):
    try:
        aoi_name = request.POST['aoi_name']
        x = ForestCoverCollection.objects.filter(username=request.user.username, aoi_name=aoi_name)
        x.delete()
        aoi_path = os.path.join(config['PATH_TO_DATA'], "Private", request.user.username,
                                "AOIs")
        shutil.rmtree(aoi_path)
        return JsonResponse({"result": "success"})

    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "message": str(e)})
@csrf_exempt
def get_aoi_id(request,country=0):
    aoi=AOIFeature.objects.get(name=request.POST['aoi'],iso3=request.POST['iso3'],desig_eng=request.POST['desig_eng'])
    print(aoi)
    return JsonResponse({"id":aoi.id})
@csrf_exempt
def get_AOI(request, country=0):
    json_obj = {}
    try:
        vec = gpd.read_file(os.path.join(config['DATA_DIR'], 'aois/peru/peru_pa.shp'))
        pilot_country = list(PilotCountry.objects.filter(id=country).values())
        json_obj['latitude'] =pilot_country[0]['latitude']
        json_obj['longitude'] = pilot_country[0]['longitude']
        json_obj['zoom'] = pilot_country[0]['zoom_level']
        json_obj["data_pa"] = json.loads(vec.to_json())
    except:
        return JsonResponse({})
    return JsonResponse(json_obj)


def fetch_carbon_charts(pa_name, container):
    # TODO Add charts for carbon stock and AGB in addition to emissions
    try:
        # TODO Replace following with ForestCoverCollection query
        df_lc = pd.DataFrame([])
        lcs = df_lc.to_dict('records')
        # TODO Replace following with AGBCollection query
        df_agb = pd.DataFrame([])  # Get the AGB dataset data
        agbs = df_agb.to_dict('records')
        df = pd.DataFrame(list(CarbonStatistic.objects.filter(aoi_index__name=pa_name).values()))

        # TODO Fix this chart generator
        # df["lc_id_id"] = "LC" + df["lc_id_id"].apply(str)
        # df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
        # grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()
        # pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'],
        #                              index='year',
        #                              fill_value=None)
        # chart = serialize(pivot_table, render_to=container, output_type='json', type='spline',
        #                  title='CarbonStatistics: ' + pa_name)
        chart = None
    except Exception as e:
        error_msg = "Could not generate chart data for emissions"
        print(str(e))

    return chart, lcs, agbs


def fetch_forest_change_charts(pa_name, container):
    # TODO Add charts for reforestation, deforestation
    # TODO Not sure how to reformat this call, meet with me
    df_defor = pd.DataFrame()  # Get the ForestCoverChange dataset data
    # TODO Make ForestCoverCollection query to get names
    df_lc_defor = pd.DataFrame([])
    lcs_defor = df_lc_defor.to_dict('records')
    # TODO Fix this chat generator
    chart_fc = None
    #df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
    #df_defor["nfc"] = df_defor['forest_gain'] - df_defor['forest_loss']
    #years_defor = list(df_defor['year'].unique())
    #pivot_table_defor = pd.pivot_table(df_defor, values='nfc', columns=['fc_source_id'],
    #                                   index='year', fill_value=None)
    #chart_fc = serialize(pivot_table_defor, render_to=container, output_type='json', type='spline',
    #                     xticks=years_defor,
    #                     title='Change in Forest Cover: ' + pa_name, )

    return chart_fc, lcs_defor


def fetch_forest_change_charts_by_aoi(aoi, container):
    # generating highcharts chart object from python using pandas(forest cover change chart)
    df_defor = pd.DataFrame(list(ForestCoverStatistic.objects.filter(aoi_index=aoi).values()))
    # df_lc_defor = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es').order_by(
    #     'id')))
    # lcs_defor = df_lc_defor.to_dict('records')
    lcs_defor=[]
    # df_defor["NFC"] = df_defor['forest_gain'] - df_defor['forest_loss']
    # df_defor["TotalArea"] = df_defor["initial_forest_area"] + df_defor["NFC"]
    # df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
    # years_defor = list(df_defor['year_index'].unique())

    # pivot_table_defor1 = pd.pivot_table(df_defor, values='NFC', columns=['fc_source_id'],
    #                                     index='year', fill_value=None)

    # chart_fc1 = serialize(pivot_table_defor1, render_to=container, output_type='json', type='spline',
    #                       xticks=[],
    #                       title="Change in Forest Cover: " + aoi)
    return None, lcs_defor


def get_agg_check(request, country='None'):
    result = CarbonStatistic.objects.all().order_by('year')
    data = list(result.values_list('year').distinct())
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
        if len(pa_name) > 0:
            print(pa_name)

            data1 = list(
                CarbonStatistic.objects.filter(lc_id__in=lcs, agb_id__in=agbs, aoi_id__name=pa_name).values('year').annotate(
                    min=Min('lc_agb_value'), max=Max('lc_agb_value'), avg=Avg('lc_agb_value')))
            print(data1)
        else:
            pa_name = country
            data1 = list(
                CarbonStatistic.objects.filter(lc_id__in=lcs, agb_id__in=agbs, aoi_id__name=pa_name).values('year').annotate(
                    min=Min('lc_agb_value'), max=Max('lc_agb_value'), avg=Avg('lc_agb_value')))

        if len(data1) < 25:
            for y in years:
                if not any(d['year'] == y for d in data1):
                    data1.append({'year': y, 'min': None, 'max': None, 'avg': None})
                else:
                    pass
        data1.sort(key=lambda x: x['year'])
        print(data1)

        for x in range(len(data1)):
            min_arr.append([data1[x]['year'], data1[x]['min']])
            max_arr.append([data1[x]['year'], data1[x]['max']])
            avg_arr.append([data1[x]['year'], data1[x]['avg']])

    return JsonResponse({"min": min_arr, "max": max_arr, "avg": avg_arr}, safe=False)


@csrf_exempt
def get_series_name(request):
    if request.method == 'POST':
        lc_id = request.POST.get('ds_lc')
        agb_id = request.POST.get('ds_agb')
        try:
            if lc_id[2:] != '':
                ds = BoundaryFiles.objects.get(id=lc_id[2:])
                lc_name = ds.fcs_name
                if agb_id != "":
                    ds = AGBSource.objects.get(agb_id=agb_id[3:])
                    agb_name = ds.agb_name
                else:
                    agb_name = ''
            else:
                lc_name = ''
                agb_name = ''
        except:
            ds = BoundaryFiles.objects.get(id=lc_id[2:])
            lc_name = ds.name_es
            if agb_id != "":
                ds = AGBSource.objects.get(agb_id=agb_id[3:])
                agb_name = ds.agb_name
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
                             'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'region_country': pa_name})




def get_fc_area(fc_source, aoi, row_offset, col_offset):
    area = 0
    with rio.open(fc_source) as fc_obj, rio.open(aoi) as aoi_obj:
        aoi_block = aoi_obj.read(1)
        corresponding_window = Window.from_slices((row_offset, row_offset + aoi_obj.height),
                                                  (col_offset, col_offset + aoi_obj.width))
        fc_block = fc_obj.read(1, window=corresponding_window)
        area += np.count_nonzero(fc_block * (aoi_block > 0))

    return area


def get_change_area(fcc_source, aoi, change_type, row_offset, col_offset):
    if change_type == 'loss':
        target_value = -1
    else:
        # Default to gain
        target_value = 1

    area = 0
    with rio.open(fcc_source) as fcc_obj, rio.open(aoi) as aoi_obj:
        aoi_block = aoi_obj.read(1)
        corresponding_window = Window.from_slices((row_offset, row_offset + aoi_obj.height),
                                                  (col_offset, col_offset + aoi_obj.width))
        fcc_block = fcc_obj.read(1, window=corresponding_window)

        target_change_arr = (fcc_block == target_value)
        area += np.count_nonzero((target_change_arr > 0) * (aoi_block > 0))

    return area


def generate_fcc_file(request):
    try:
        year = request.GET.get('year')
        print(year)
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
        print(e,__line_no__)
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


@csrf_exempt
def stage_for_processing(request,pk):
    if request.POST.get('type')=='fc':
        fc_collection_name = request.POST.get('coll_name')
        coll=ForestCoverCollection.objects.get(name=fc_collection_name)

        coll.processing_status="Staged"
        coll.save()

        process_fc_collection.delay(fc_collection_name)
    if request.POST.get('type')=='agb':
        agb_collection_name = request.POST.get('agb_name')
        coll=AGBCollection.objects.get(name=agb_collection_name)

        coll.processing_status="Staged"
        coll.save()

        process_agb_collection.delay(agb_collection_name)
    if request.POST.get('type')=='aoi':
        aoi_collection_name = request.POST.get('aoi_name')
        coll=AOICollection.objects.get(name=aoi_collection_name)

        coll.processing_status="Staged"
        coll.save()

        process_aoi_collection.delay(aoi_collection_name)
    return JsonResponse({})
