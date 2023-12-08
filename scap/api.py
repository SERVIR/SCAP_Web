import json
import os
import tempfile
import time
from pathlib import Path
import requests
from django.contrib.gis.geos import GEOSGeometry
import fiona
from django.http import JsonResponse
from shapely.geometry import shape
from django.contrib.gis.utils import LayerMapping
import rasterio
from rasterio.mask import mask
import ee
from scap.models import BoundaryFiles, AOI, ForestCoverChange, ForestCoverChangeFile, ForestCoverFile, NewCollection, \
    UserProvidedAOI

from scap.utils import percent_inside, gdal_polygonize, getArea, create_temp_dir, delete_temp_dir, \
    get_projection_of_tif, get_resolution_of_tif

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)

collections_global=[]
# This method is used to generate geodjango objects for AOI or Boundary Data Source
# Uses LayerMapping technique to update the object from shape file
def generate_geodjango_objects(verbose=True):
    boundaryfiles_mapping = {
        'feature_id': 'feature_id',
        'name_es': 'name_es',
        'nomedep': 'nomedep',
        'nomemun': 'nomemun',
        'pais': 'pais',
        'fid': 'FID',
        'geom': 'MULTIPOLYGON',
    }
    aoi_mapping = {
        'wdpaid': 'WDPAID',
        'wdpa_pid': 'WDPA_PID',
        'pa_def': 'PA_DEF',
        'name': 'NAME',
        'orig_name': 'ORIG_NAME',
        'desig': 'DESIG',
        'desig_eng': 'DESIG_ENG',
        'desig_type': 'DESIG_TYPE',
        'iucn_cat': 'IUCN_CAT',
        'int_crit': 'INT_CRIT',
        'marine': 'MARINE',
        'rep_m_area': 'REP_M_AREA',
        'gis_m_area': 'GIS_M_AREA',
        'rep_area': 'REP_AREA',
        'gis_area': 'GIS_AREA',
        'no_take': 'NO_TAKE',
        'no_tk_area': 'NO_TK_AREA',
        'status': 'STATUS',
        'status_yr': 'STATUS_YR',
        'gov_type': 'GOV_TYPE',
        'own_type': 'OWN_TYPE',
        'mang_auth': 'MANG_AUTH',
        'mang_plan': 'MANG_PLAN',
        'verif': 'VERIF',
        'metadataid': 'METADATAID',
        'sub_loc': 'SUB_LOC',
        'parent_iso': 'PARENT_ISO',
        'iso3': 'ISO3',
        'supp_info': 'SUPP_INFO',
        'cons_obj': 'CONS_OBJ',
        'layer': 'layer',
        'path': 'path',
        'geom': 'MULTIPOLYGON',
    }

    boundary = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data', r'C:\Users\gtondapu\Documents\nepal.shp'),
    )

    # lm = LayerMapping(BoundaryFiles, boundary, boundaryfiles_mapping, transform=False)
    # lm.save(strict=True, verbose=verbose)
    lm = LayerMapping(AOI, boundary, aoi_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def getInitialForestArea_new(year, dir, dataset, pa, val):
    sa = "airqualityservice@airquality-255511.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(sa, r'C:\Users\gtondapu\Downloads\airquality-255511-eb61b92cb290.json')
    ee.Initialize(credentials)
    dataset = dataset.lower()
    file = dir + "fc_" + dataset + "_" + str(year) + "_1ha.tif"
    print(pa.name)
    data = fiona.open(pa.geom.json)  # list of shapely geometries
    geometry = [shape(feat["geometry"]) for feat in data]
    ee_geom = ee.Geometry.MultiPolygon(
        coords=[pa.geom.json],
        proj='EPSG:4326'
    )
    img = ee.Image('projects/servir-sco-assets/assets/tmp_servir_cms/regionalLC/MapBiomas_AMZ/FNF/MapBiomas_FNF_00')
    forest_mask = img.select('remapped').eq(1)  # forest
    area = ee.Image.pixelArea().divide(10000)  # hectares
    img_masked = img.updateMask(forest_mask)
    new_mask = img_masked.multiply(area).select([0], ['forest'])

    # img_masked = img_masked.clip(ee_geom)
    # print(img_masked.bandNames())

    total_area = new_mask.reduceRegion(
        {
            'reducer': ee.Reducer.sum(),
            'geometry': img.geometry(),

        }
    )
    print(total_area)


# Calculating the forest area of baseline year's FC TIFF file
def getInitialForestArea(year, dir, dataset, pa, val):
    # print("year", year)
    dataset = dataset.lower()
    file = dir + "fc_" + dataset + "_" + str(year) + "_1ha.tif"
    print(pa.name)
    data = fiona.open(pa.geom.json)  # list of shapely geometries
    geometry = [shape(feat["geometry"]) for feat in data]
    # load the raster, mask it by the FC TIFF and crop it
    with rasterio.open(file) as src:
        # print(src.profile)
        out_image, out_transform = mask(src, geometry, crop=True)
    out_meta = src.meta.copy()

    # save the resulting raster
    out_meta.update({"driver": "GTiff",

                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    file_out = r"masked_fc" + str(val) + ".tif"
    os.chdir(dir)
    with rasterio.open(file_out, "w", **out_meta) as dest:
        dest.write(out_image)
    return getArea(gdal_polygonize(dir, r"masked_fc" + str(val)))


# get the forest gain or forest loss of a FCC TIFF file
def getConditionalForestArea(pa, dir, dataset, value, year, val):
    # print(year)
    file = dir + "fcc_" + dataset + "_" + str(year) + "_1ha.tif"
    data = fiona.open(pa.geom.json)  # get the json of a protected area
    geometry = [shape(feat["geometry"]) for feat in data]
    # load the raster, mask it by the FCC TIFF and crop it
    with rasterio.open(file) as src:
        out_image, out_transform = mask(src, geometry, crop=True)
    out_meta = src.meta.copy()

    # save the resulting raster
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    file_out = r"masked_fcc" + str(val) + ".tif"
    os.chdir(dir)
    with rasterio.open(file_out, "w", **out_meta) as dest:
        dest.write(out_image)
    return getArea(gdal_polygonize(dir, r"masked_fcc" + str(val)), value)


# Find all the files that are atleast 90% inside the datasource
# For each Protected Area that is inside the datasource, calculate the FCC object fields
def generate_fcc_fields(dataset, year):
    try:
        create_temp_dir(params["PATH_TO_TEMP_FILES"])
        l_dataset = dataset.lower()
        data_source = (BoundaryFiles.objects.get(name_es=dataset))
        needed_aois = AOI.objects.filter(geom__intersects=GEOSGeometry(data_source.geom))
        val = 0
        for aoi in needed_aois:
            val = val + 1
            start = time.time()
            if percent_inside(aoi, data_source) > params["PERCENTAGE_INSIDE_DATASET"]:
                fcchange = ForestCoverChange()
                fcchange.fc_source = data_source
                fcc = ForestCoverChangeFile.objects.get(file_name='fcc_' + l_dataset + '_' + str(year) + '_1ha.tif')
                fc = ForestCoverFile.objects.get(
                    file_name='fc_' + l_dataset + '_' + str(fcc.baseline_year) + '_1ha.tif')
                fcchange.baseline_year = fcc.baseline_year
                fcchange.year = year
                fcchange.aoi = aoi
                fcchange.initial_forest_area = getInitialForestArea_new(fcc.baseline_year,
                                                                        fc.file_directory, fc.fc_source.name_es, aoi,
                                                                        val)
                # fcchange.forest_gain = getConditionalForestArea(aoi, fcc.file_directory,fcc.fc_source.name_es, 1, fcc.year, val)
                # fcchange.forest_loss = getConditionalForestArea(aoi, fcc.file_directory,fcc.fc_source.name_es, -1, fcc.year, val)
                # end = time.time()
                # fcchange.processing_time = end - start
                # fcchange.save()
    except Exception as e:
        print(e)
    # finally:
    #     delete_temp_dir(params["PATH_TO_TEMP_FILES"])


def generate_from_lambda():
    import boto3
    lambda_client = boto3.client('lambda')
    # lambda_payload = {"name": name ,  "age" :age}
    lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-2:267380267443:function:final-python-forestcal-dev-image_upload',
        InvocationType='Event',
    )


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def savetomodel(request):
    print("in")
    print(request.FILES['boundaryFile'] )
    uploaded_tiffs=request.FILES.getlist('FC_tiffs[]')
    # print(type(uploaded_tiffs[0]))
    # proj=get_projection_of_tif(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public\fc_yghug_77_1ha.tif')
    # res=get_resolution_of_tif(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public\fc_yghug_77_1ha.tif')
    # if res == 100.0:
    #     print("in correct resolution")
    # if "Mollweide" in proj:
    #     print("yes in correct projection")
    uploaded_tiffs_names=request.POST.getlist('FC_tiffs_Name[]')
    for i in range(len(uploaded_tiffs)):
        with open(os.path.join(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public', uploaded_tiffs_names[i]),
                  "wb") as file1:
            file1.write(uploaded_tiffs[i].read())
    with open(os.path.join(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public', request.POST['boundaryFileName']), "wb") as file1:
        file1.write(request.FILES['boundaryFile'].read())

    try:
        tiffs = uploaded_tiffs_names
        for tiff in tiffs:
            new_collection = NewCollection()
            new_collection.collection_name = request.POST['coll_name']
            new_collection.collection_description = request.POST['coll_desc']
            new_collection.boundary_file = request.POST['boundaryFileName']
            new_collection.tiff_file = tiff
            new_collection.access_level = request.POST['access']
            new_collection.username = request.user.username
            print(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public'+'\\'+tiff)
            new_collection.projection=get_projection_of_tif(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public'+'\\'+tiff)
            new_collection.resolution=get_resolution_of_tif(r'C:\Users\gtondapu\Downloads\SCAP\Data\Public'+'\\'+tiff)

            new_collection.save()
            print(request.user.username)

    except Exception as e:
        print(e)
        return JsonResponse({"result": "error","error_message":str(e)})

@csrf_exempt
def check_if_coll_exists(request):
    collections = list(NewCollection.objects.values('collection_name').distinct())
    arr = []
    # print(collections)
    for c in collections:
        arr.append(c['collection_name'])
    print(arr)
    if request.POST['coll_name'] not in arr:
        return JsonResponse({"result": "success"})
    else:
        return JsonResponse({"result": "error", "error_message": "Please choose a different name for collection"})


@csrf_exempt
def updatetomodel(request):
    print("update")

    try:
        tiffs = request.POST.getlist('tiffs[]')
        coll_name = request.POST['coll_name']
        existing_collection = NewCollection.objects.filter(collection_name=coll_name).first()
        print(existing_collection.collection_description)
        for tiff in tiffs:
            new_collection = NewCollection()
            new_collection.collection_name = coll_name
            new_collection.collection_description = existing_collection.collection_description
            new_collection.boundary_file = existing_collection.boundary_file
            new_collection.tiff_file = tiff
            new_collection.access_level = existing_collection.access_level
            new_collection.username= request.user.username
            new_collection.save()
            return JsonResponse({"result": "success"})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error","error_message":str(e)})


@csrf_exempt
def getcollections(request):
    arr = []
    collections = list(NewCollection.objects.values('collection_name').distinct())

    # print(collections)
    for c in collections:
        arr.append(c['collection_name'])
    collections_global=arr
    # print(collections_global)
    return JsonResponse({"coll": arr})


@csrf_exempt
def getfilesfromcollection(request):
    coll_name = request.POST['coll_name']
    files = list(NewCollection.objects.filter(collection_name=coll_name))
    arr = []
    print(files)
    for c in files:
        arr.append(c.tiff_file)
    return JsonResponse({"tiffs": arr})

@csrf_exempt
def saveAOItomodel(request):
    try:
        aois = request.POST.getlist('aois[]')
        for aoi in aois:
            new_aoi = UserProvidedAOI()
            new_aoi.aoi_name = aoi
            new_aoi.aoi_shape_file = "path_to_shape_file"
            new_aoi.username = request.user.username
            existing_aois = list(UserProvidedAOI.objects.values('aoi_name').distinct())
            arr=[]
            for a in existing_aois:
                arr.append(a['aoi_name'])

            if aoi not in arr:
                new_aoi.save()
                return JsonResponse({"result": "success"})
            else:
                return JsonResponse({"result": "error","error_message":"Please choose a different name for your aois"})

    except Exception as e:
        print(e)
        return JsonResponse({"result": "error","error_message":str(e)})