import json
import os
import shutil
import tempfile
import time
from pathlib import Path
import requests
from django.contrib.gis.geos import GEOSGeometry
import fiona
from django.http import JsonResponse
from rasterio import CRS
from shapely.geometry import shape
from django.contrib.gis.utils import LayerMapping
import rasterio
from rasterio.mask import mask
import ee
from django.views.decorators.csrf import csrf_exempt
from scap.models import BoundaryFiles, AOI, ForestCoverChange, ForestCoverChangeFile, ForestCoverFile, NewCollection, \
    UserProvidedAOI
import geopandas as gpd

from scap.utils import percent_inside, gdal_polygonize, getArea, create_temp_dir, delete_temp_dir, \
    get_projection_of_tif, get_resolution_of_tif, get_projection_of_boundary

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)

collections_global = []


# This method is used to generate geodjango objects for AOI or Boundary Data Source
# Uses LayerMapping technique to update the object from shape file
def generate_geodjango_objects_boundary(verbose=True):
    boundaryfiles_mapping = {
        'feature_id': 'feature_id',
        'name_es': 'name_es',
        'nomedep': 'nomedep',
        'nomemun': 'nomemun',
        'pais': 'pais',
        'fid': 'FID',
        'geom': 'MULTIPOLYGON',
    }
    boundary = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data',  r"C:\Users\gtondapu\Desktop\SCAP\Boundary\mapbiomas\mapbiomas_merged.shp"),
    )
    lm = LayerMapping(BoundaryFiles, boundary, boundaryfiles_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def generate_geodjango_objects_aoi(verbose=True):
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
    aoi = os.path.abspath(
        os.path.join('/home/alex/shared/SCAP/aois/peru/peru_pa.shp'),
    )

    lm = LayerMapping(AOI, aoi, aoi_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def getInitialForestArea_gee(year, dir, dataset, pa, val):
    credentials = ee.ServiceAccountCredentials(params['SERVICE_ACCOUNT'], params['SERVICE_ACCOUNT_JSON'])
    ee.Initialize(credentials)
    dataset = dataset.lower()
    file = dir + "fc_" + dataset + "_" + str(year) + "_1ha.tif"
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
    if dataset != "mapbiomas":
        file = dir + "/" + "fc_" + dataset + "_peru_" + str(year) + "_1ha.tif"
    else:
        file = dir + "/" + "fc_" + dataset + "_" + str(year) + "_1ha.tif"
    print(pa.name + str(val))
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
    # print(dir)
    with rasterio.open(file_out, "w", **out_meta) as dest:
        dest.write(out_image)
    return getArea(gdal_polygonize(dir,  r"masked_fc" + str(val)))
def getInitialForestArea_new(year, dir, dataset, pa, val):
    dataset = dataset.lower()
    if dataset != "mapbiomas":
        file = os.path.join(dir, f"fc_{dataset}_peru_{year}_1ha.tif")
    else:
        file = os.path.join(dir, f"fc_{dataset}_{year}_1ha.tif")

    with rasterio.open(file) as src:
        data = fiona.open(pa.geom.json)  # list of shapely geometries

        # Filter out invalid geometries
        valid_geometries = [shape(feat["geometry"]) for feat in data if feat["geometry"]]

        if not valid_geometries:
            raise ValueError("No valid geometries found.")

        out_image, out_transform = mask(src, valid_geometries, crop=True)

        # Calculate the area from the masked image directly, without writing to disk
        area = calculate_area(out_image, out_transform, src.crs,1)

    return area

def getConditionalForestArea_new(pa, dir, dataset, value, year, val):
    dataset = dataset.lower()
    if dataset != "mapbiomas":
        file = os.path.join(dir, f"fcc_{dataset}_peru_{year}_1ha.tif")
    else:
        file = os.path.join(dir, f"fcc_{dataset}_{year}_1ha.tif")

    with rasterio.open(file) as src:
        data = fiona.open(pa.geom.json)  # list of shapely geometries

        # Filter out invalid geometries
        valid_geometries = [shape(feat["geometry"]) for feat in data if feat["geometry"]]

        if not valid_geometries:
            raise ValueError("No valid geometries found.")

        out_image, out_transform = mask(src, valid_geometries, crop=True)

        # Calculate the area from the masked image directly, without writing to disk
        area = calculate_area(out_image, out_transform, src.crs,value)

    return area
def calculate_area(raster, transform, crs,value):
    crs_params = {
        'proj': 'cea',
        'lon_0': 0,
        'lat_ts': 0,
        'x_0': 0,
        'y_0': 0,
        'datum': 'WGS84',
        'units': 'm',
        'no_defs': True
    }
    esri_54009_crs = CRS.from_proj4('+proj=cea +lon_0=0 +lat_ts=30 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs')
    # Reproject the transform to match the CRS of the source raster
    print('here')
    minx, miny, maxx, maxy = rasterio.transform.array_bounds(raster.shape[1], raster.shape[2], transform)

    print('here 1')
    # Reproject the bounding box to match the desired CRS
    crs_transform = rasterio.warp.transform_bounds(crs, esri_54009_crs, minx, miny, maxx, maxy)
    print('here 2')
    print("Transformed bounding box:", str(crs_transform))
    # Assuming the raster contains only 1s and 0s representing forest and non-forest pixels
    # Calculate the area by summing the forest pixel count and multiplying by pixel area
    # Calculate the width and height of the bounding box
    width = crs_transform[2] - crs_transform[0]
    height = crs_transform[3] - crs_transform[1]

    # Calculate the area based on the reprojected bounding box
    pixel_area = abs(width * height)
    print('here 3')
    forest_pixel_count = (raster == value).sum()
    print('here 4')
    area = forest_pixel_count * pixel_area
    return area
# get the forest gain or forest loss of a FCC TIFF file
def getConditionalForestArea(pa, dir, dataset, value, year, val):
    # print(year)
    dataset = dataset.lower()
    if dataset != "mapbiomas":
        file = dir + "/" + "fcc_" + dataset + "_peru_" + str(year) + "_1ha.tif"
    else:
        file = dir + "/" + "fcc_" + dataset + "_" + str(year) + "_1ha.tif"
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
        # print(data_source)
        needed_aois = AOI.objects.filter(geom__intersects=GEOSGeometry(data_source.geom))
        # print(needed_aois)
        val = 0
        for aoi in needed_aois:
            if aoi.name!='peru':
                val = val + 1
                start = time.time()
                # print(percent_inside(aoi, data_source))
                # if percent_inside(aoi, data_source) > params["PERCENTAGE_INSIDE_DATASET"]:
                #     print("inside")
                fcchange = ForestCoverChange()
                fcchange.fc_source = data_source
                if l_dataset != "mapbiomas":
                    fcc = ForestCoverChangeFile.objects.get(
                        file_name='fcc_' + l_dataset + '_peru_' + str(year) + '_1ha.tif')
                    fc = ForestCoverFile.objects.get(
                        file_name='fc_' + l_dataset + '_peru_' + str(fcc.baseline_year) + '_1ha.tif')
                else:
                    fcc = ForestCoverChangeFile.objects.get(file_name='fcc_' + l_dataset + '_' + str(year) + '_1ha.tif')
                    fc = ForestCoverFile.objects.get(
                        file_name='fc_' + l_dataset + '_' + str(fcc.baseline_year) + '_1ha.tif')
                fcchange.baseline_year = fcc.baseline_year
                fcchange.year = year
                fcchange.aoi = aoi
                fcchange.initial_forest_area = getInitialForestArea(fcc.baseline_year,
                                                                    fc.file_directory, fc.fc_source.name_es, aoi,
                                                                    val)
                fcchange.forest_gain = getConditionalForestArea(aoi, fcc.file_directory, fcc.fc_source.name_es, 1,
                                                                fcc.year, val)
                fcchange.forest_loss = getConditionalForestArea(aoi, fcc.file_directory, fcc.fc_source.name_es, -1,
                                                                fcc.year, val)
                end = time.time()
                fcchange.processing_time = end - start
                fcchange.save()
                for file in os.listdir(fc.file_directory):
                    if os.path.isfile(file) and file.startswith("masked_fc"):
                        try:
                            os.chmod(file,0o777)
                            os.remove(file)
                        except Exception as e:
                            print(e)
                for file in os.listdir(fcc.file_directory):
                    if os.path.isfile(file) and file.startswith("masked_fcc"):
                        try:
                            os.chmod(file,0o777)
                            os.remove(file)
                        except Exception as e:
                            print(e)
    except Exception as e:
        print(e)
    finally:
        delete_temp_dir(params["PATH_TO_TEMP_FILES"])


def generate_from_lambda():
    import boto3
    lambda_client = boto3.client('lambda')
    # lambda_payload = {"name": name ,  "age" :age}
    lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-2:267380267443:function:final-python-forestcal-dev-image_upload',
        InvocationType='Event',
    )


@csrf_exempt
def savetomodel(request):
    uploaded_tiffs = request.FILES.getlist('FC_tiffs[]')
    original_names = request.POST.getlist('FC_tiffs_OriginalNames[]')
    uploaded_tiffs_names = request.POST.getlist('FC_tiffs_Name[]')
    path_to_boundary = os.path.join(params['PATH_TO_DATA'], request.POST['access'], request.user.username,
                                    "Collections", request.POST['coll_name'], "BoundaryFiles")
    path_to_tiffs = os.path.join(params['PATH_TO_DATA'], request.POST['access'], request.user.username,
                                 "Collections", request.POST['coll_name'], "FC_Tiffs")

    if not os.path.exists(path_to_boundary):
        os.makedirs(path_to_boundary)
    if not os.path.exists(path_to_tiffs):
        os.makedirs(path_to_tiffs)

    for i in range(len(uploaded_tiffs)):
        with open(os.path.join(path_to_tiffs, uploaded_tiffs_names[i]),
                  "wb") as file1:
            file1.write(uploaded_tiffs[i].read())

    with open(os.path.join(path_to_boundary, request.POST['boundaryFileName']), "wb") as file1:
        file1.write(request.FILES['boundaryFile'].read())

    try:
        # print(original_names)
        tiffs = uploaded_tiffs_names
        # boundary_proj=get_projection_of_boundary(os.path.join(path_to_boundary, request.POST['boundaryFileName']))
        # if 'Mollweide' in boundary_proj:
        #     pass
        # else:
        #     return JsonResponse({"result": "error", "error_message": "Invalid file " + original_names[i]})

        for i in range(len(tiffs)):
            new_collection = NewCollection()
            new_collection.collection_name = request.POST['coll_name']
            new_collection.collection_description = request.POST['coll_desc']
            new_collection.boundary_file = request.POST['boundaryFileName']
            new_collection.tiff_file = tiffs[i]
            new_collection.access_level = request.POST['access']
            new_collection.username = request.user.username
            tiff_file_path = os.path.join(path_to_tiffs, tiffs[i])
            new_collection.path_to_tif_file = path_to_tiffs
            new_collection.path_to_boundary_file = path_to_boundary
            proj = get_projection_of_tif(tiff_file_path)
            new_collection.projection = proj
            print(proj)
            new_collection.resolution = get_resolution_of_tif(tiff_file_path)
            if 'Mollweide' in proj:
                new_collection.save()
            else:
                return JsonResponse({"result": "error", "error_message": "Invalid file " + original_names[i]})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})


@csrf_exempt
def updatetomodel(request):
    try:

        coll_name = request.POST['coll_name']
        existing_collection = NewCollection.objects.filter(collection_name=coll_name).first()
        print(existing_collection.collection_description)
        uploaded_tiffs = request.FILES.getlist('FC_tiffs_New[]')
        original_names = request.POST.getlist('FC_tiffs_New_OriginalNames[]')
        uploaded_tiffs_names = request.POST.getlist('FC_tiffs_New_Name[]')

        for i in range(len(uploaded_tiffs)):
            with open(os.path.join(existing_collection.path_to_tif_file, uploaded_tiffs_names[i]),
                      "wb") as file1:
                file1.write(uploaded_tiffs[i].read())
        tiffs = uploaded_tiffs_names

        for tiff in tiffs:
            new_collection = NewCollection()
            new_collection.collection_name = coll_name
            new_collection.collection_description = existing_collection.collection_description
            new_collection.boundary_file = existing_collection.boundary_file
            new_collection.tiff_file = tiff
            new_collection.access_level = existing_collection.access_level
            new_collection.username = request.user.username
            tiff_file_path = os.path.join(existing_collection.path_to_tif_file, tiffs[i])
            proj = get_projection_of_tif(tiff_file_path)
            new_collection.projection = proj
            new_collection.resolution = get_resolution_of_tif(tiff_file_path)
            if 'Mollweide' in proj:
                new_collection.save()
            else:
                return JsonResponse({"result": "error", "error_message": "Invalid file " + original_names[i]})
            return JsonResponse({"result": "success"})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})


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
def getcollections(request):
    arr = []
    collections = list(
        NewCollection.objects.filter(username=request.user.username).values('collection_name').distinct())

    # print(collections)
    for c in collections:
        arr.append(c['collection_name'])
    collections_global = arr
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
        aoi_path = os.path.join(params['PATH_TO_DATA'], "Private", request.user.username,
                                "AOIs")
        if not os.path.exists(aoi_path):
            os.makedirs(aoi_path)
        aois = request.FILES.getlist('aois[]')
        aoi_names = request.POST.getlist('aoi_names[]')
        for i in range(len(aois)):
            with open(os.path.join(aoi_path, aoi_names[i]), "wb") as file1:
                file1.write(aois[i].read())
            new_aoi = UserProvidedAOI()
            new_aoi.aoi_name = aoi_names[i]
            new_aoi.aoi_shape_file = os.path.join(aoi_path, aoi_names[i])
            new_aoi.path_to_aoi_file = aoi_path
            new_aoi.username = request.user.username
            new_aoi.save()
            return JsonResponse({"result": "success"})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "error_message": str(e)})


@csrf_exempt
def get_aoi_list(request):
    try:
        aois = UserProvidedAOI.objects.filter(username=request.user.username).values()
        print(request.user.username)
        print(aois)
        names = []
        last_accessed_on = []
        for i in range(len(aois)):
            names.append(aois[i]['aoi_name'])
            last_accessed_on.append(aois[i]['last_accessed_on'])
        return JsonResponse({"result": "success", "names": names, "last_accessed_on": last_accessed_on})
    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "message": str(e)})


@csrf_exempt
def delete_AOI(request):
    try:
        aoi_name = request.POST['aoi_name']
        x = UserProvidedAOI.objects.filter(username=request.user.username, aoi_name=aoi_name)
        x.delete()
        aoi_path = os.path.join(params['PATH_TO_DATA'], "Private", request.user.username,
                                "AOIs")
        shutil.rmtree(aoi_path)
        return JsonResponse({"result": "success"})

    except Exception as e:
        print(e)
        return JsonResponse({"result": "error", "message": str(e)})


@csrf_exempt
def get_AOI(request):
    json_obj = {}
    try:
        vec = gpd.read_file('/home/alex/shared/SCAP/aois/peru/peru_pa.shp')

        json_obj["data"] = json.loads(vec.to_json())
    except:
        return JsonResponse({})
    return JsonResponse(json_obj)