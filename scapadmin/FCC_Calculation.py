import json
import os
import time
from pathlib import Path

import numpy as np
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from osgeo import gdal
from osgeo import gdalconst
from shapely.geometry import shape

from scapadmin.models import ForestCoverSource, ForestCoverFile, ForestCoverChangeFile, ForestCoverChange
from scapadmin.models import PredefinedAOI

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
data = json.load(f)


# The FC tif files are already exported from GEE. In this method, we are just storing the details in django data model.
@csrf_exempt
def generate_fc(request):
    year = request.GET.get('year')
    fcs = ForestCoverSource.objects.get(fcs_name='MapBiomas')
    fc = ForestCoverFile()
    fc.file_name = "fc_mapbiomas_" + str(year) + "_1ha.tif"
    fc.file_directory = "/servir_apps/data/scap_data/fc/mapbiomas/"
    fc.fc_source = fcs
    fc.save()


# This method is used to calculate the forest cover change between two years using the FC tif files. The year is
# passed as a parameter from the browser.
@csrf_exempt
def generate_fcc(request):
    try:
        year = request.GET.get('year')
        start = time.time()
        fcs = ForestCoverSource.objects.get(fcs_name='RLCMS_HKH')
        fcc = ForestCoverChangeFile()  # Create a new FCC file object
        A_TIF = "path_to_first_FC_tif_file"
        i = 1
        while (i < 10):
            B_TIF = "path_to_second_FC_tif_file"
            if os.path.isfile(B_TIF):
                fcc.year = year
                fcc.baseline_year = int(year) - i
                break
        # Following three files are temporary files that will be deleted later
        OUT_TIF = "path_to_temp_output_tif_file"
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
        gdaloutput = "path_to_final_fcc_file_tif"
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
        c = gdal.Translate(gdaloutput, gdalinput, options=translateoptions)  # compresses the output file
        c = None
        end = time.time()
        totaltime = end - start
        fcc.file_name = "fcc_rlcms_hkh_" + str(year) + "_1ha.tif"
        fcc.file_directory = "path_to_final_fcc_file_tif"
        fcc.fc_source = fcs
        fcc.processing_time = totaltime
        fcc.save()
        return HttpResponse("Success")
    except Exception as e:
        print(e)
        return HttpResponse(str(e))


# This method is used to cloud optimize the existing FC and FCC tiffs
@csrf_exempt
def convert_fc_to_cog():
    years = [2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
             2020, 2021]
    for year in years:
        start = time.time()
        gdaloutputA = 'GDAL_' + str(year) + '.tif'
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16"))
        a = gdal.Translate(gdaloutputA, "file_to_optimize", options=translateoptions)
        ds1 = gdal.Open(gdaloutputA, gdalconst.GA_ReadOnly)

        # get attributes and set them to the output raster
        driver = gdal.GetDriverByName("MEM")
        output = driver.Create("", ds1.RasterXSize, ds1.RasterYSize, 1, gdalconst.GDT_Int16)
        output.SetGeoTransform(ds1.GetGeoTransform())
        output.SetProjection(ds1.GetProjection())
        output.GetRasterBand(1).WriteArray(ds1.ReadAsArray())
        output.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64])
        driver = gdal.GetDriverByName('GTiff')
        gdaloutput = "output_file_path"

        data_set = driver.CreateCopy(gdaloutput, output,
                                     options=["COPY_SRC_OVERVIEWS=YES", "TILED=YES", "COMPRESS=LZW"])
        end = time.time()
        totaltime = end - start
        print(totaltime)
        print(year)
        output = None
        data_set = None
        ds1 = None


# Get geojson from a file and store in the PredefinedAOI table
def getFeaturesFromFile(filename):
    features = []
    type = 'FeatureCollection'

    with open(filename, 'r', encoding="utf8") as f:
        featurecoll = json.loads(f.read())
        final_name = ""
        crs = featurecoll['crs']
        for feature in featurecoll['features']:
            features.append(feature['properties'])
            aoi = PredefinedAOI()
            name = feature['properties']['NAME']
            print(name)
            if ('-' in name):
                for x in range(len(name.strip().split('-'))):
                    str = name.split('-')[x].strip()
                    final_name = final_name + '_' + (str)
                final_name = final_name.lstrip('_')
                arr = final_name.split(' ')
                aoi.aoi_name = ('_').join(arr).lower()
            else:
                arr = name.split(' ')
                aoi.aoi_name = ('_').join(arr).lower()
            aoi.aoi_country = 'BT'
            new_feature = {"type": "FeatureCollection", "name": name, "crs": crs, "features": [feature]}

            aoi.aoi_geojson = json.dumps(new_feature)
            aoi.save()
            final_name = ""


# This method obtains the area of a geojson
def getArea(js):
    features = []
    flag = False

    for feature in js['features']:
        features.append(feature)
    print(len(features))
    area = 0
    for feature in features:
        polygon = shape(feature['geometry'])
        area = area + polygon.area
    return area


# This method is used to get the area of the tif file
def getInitialForestArea(year):
    file = "path_to_tif_file"
    with open(file, 'r') as f:
        js = json.load(f)
    area = getArea(js)
    print(area)
    return area


# This method is used to get the data of the areas that belong to the datasources (90% inside)
def getAreaIntersection(p1, p2, year):
    try:
        start = time.time()
        for pa in PredefinedAOI.objects.all():
            p1 = json.loads(pa.aoi_geojson)
            p2 = r'C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomas_boundary.geojson'

            ar = 0.0
            import geopandas as gp
            poly1 = gp.GeoDataFrame.from_features(p1["features"])
            poly2 = gp.read_file(p2)
            data = []
            for index, orig in poly1.iterrows():
                for index2, ref in poly2.iterrows():
                    if ref['geometry'].intersects(orig['geometry']):
                        # owdspd = orig['id']
                        data.append({'geometry': ref['geometry'].intersection(orig['geometry'])})

            for geom in data:
                ar = ar + geom['geometry'].area
            a1 = ar
            a2 = getArea(p1)
            percent = (a1 / a2) * 100
            end = time.time()
            if percent > data["PERCENTAGE_INSIDE_DATASET"]:
                fcchange = ForestCoverChange()
                fcchange.fc_source = ForestCoverSource.objects.get(name='MapBiomas')
                fcc = ForestCoverChangeFile.objects.get(file_name='fcc_mapbiomas_' + str(year) + '_1ha.tif')
                fcchange.baseline_year = fcc.baseline_year
                fcchange.processing_time = end - start
                fcchange.year = year
                fcchange.aoi = pa
                fcchange.initial_forest_area = getInitialForestArea(fcc.baseline_year)
                fcchange.forest_gain = getConditionalForestArea(1, fcc.baseline_year)
                fcchange.forest_loss = getConditionalForestArea(-1, fcc.baseline_year)
                fcchange.save()
                return HttpResponse("Success")
    except Exception as e:
        return HttpResponse(str(e))


# This method is used to read the tiff file
def read_geotiff(filename):
    ds = gdal.Open(filename)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    return arr, ds


# This method is used to write the tiff file
def write_geotiff(filename, arr, in_ds):
    arr_type = gdal.GDT_Int16
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(filename, arr.shape[1], arr.shape[0], 1, arr_type)
    out_ds.SetProjection(in_ds.GetProjection())
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    band = out_ds.GetRasterBand(1)
    band.WriteArray(arr)
    band.FlushCache()
    band.ComputeStatistics(False)


# get the area of a tiff file with specific values
def getConditionalForestArea(value, year):
    file = "path_to_tiff_file"
    nlcd16_arr, nlcd16_ds = read_geotiff(file)

    nlcd16_val_arr = np.where(nlcd16_arr == value, 1, 0)
    nlcd16_val_ncells = np.sum(nlcd16_arr == value)
    write_geotiff("path_to_temp_file", nlcd16_val_arr, nlcd16_ds)
    translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
    c = gdal.Translate("output_file", "path_to_temp_file", options=translateoptions)
    # https://gdal.org/tutorials/geotransforms_tut.html
    dx = nlcd16_ds.GetGeoTransform()[1]
    dy = -nlcd16_ds.GetGeoTransform()[5]
    return nlcd16_val_ncells * dx * dy
