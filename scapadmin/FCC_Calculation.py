import json
import os
import time
from pathlib import Path

import geopandas
import numpy as np
import pandas as pd
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from osgeo import gdal, ogr
from osgeo import gdalconst
from shapely.geometry import shape

from scapadmin.models import ForestCoverSource, ForestCoverFile, ForestCoverChangeFile, ForestCoverChange
from scapadmin.models import PredefinedAOI

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)


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
    years = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14",
                "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26m", "27m"]
    for year in years:
        start = time.time()
        gdaloutputA = 'GDAL_' + str(year) + '.tif'

        dataset = gdal.Open(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ea_cog\ea22"+year+".tif")
        print(dataset.GetRasterBand(1).GetNoDataValue())

        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Float32"))
        a = gdal.Translate(gdaloutputA, r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ea_cog\ea22"+year+".tif", options=translateoptions)
        ds1 = gdal.Open(gdaloutputA, gdalconst.GA_ReadOnly)

        # get attributes and set them to the output raster
        driver = gdal.GetDriverByName("MEM")
        output = driver.Create("", ds1.RasterXSize, ds1.RasterYSize, 1, gdalconst.GDT_Float32)
        output.SetGeoTransform(ds1.GetGeoTransform())
        output.SetProjection(ds1.GetProjection())
        output.GetRasterBand(1).SetNoDataValue(0.0)

        output.GetRasterBand(1).WriteArray(ds1.GetRasterBand(1).ReadAsArray())
        output.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64])
        driver = gdal.GetDriverByName('GTiff')
        gdaloutput = r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ea_cog_output\ea22"+year+".tif"

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
            aoi.aoi_country = 'NP'
            new_feature = {"type": "FeatureCollection", "name": name, "crs": crs, "features": [feature]}

            aoi.aoi_geojson = json.dumps(new_feature)
            aoi.save()
            final_name = ""


# This method obtains the area of a geojson
def getArea(js):
    try:
        features = []
        flag = False

        for feature in js['features']:
            features.append(feature)
        print(len(features))
        area = 0
        for feature in features:
            polygon = shape(feature['geometry'])
            area = area + polygon.area
        print(area)
        return area
    except Exception as e:
        print(e)
        return HttpResponse(str(e))


# This method is used to get the area of the tif file
def getAreaTif(file):
    try:
        # with open(file, 'r') as f:
        #     js = json.load(f.read())
        nlcd16_arr, nlcd16_ds = read_geotiff(file)

        nlcd16_val_arr = np.where(nlcd16_arr == 1, 1, 0)
        nlcd16_val_ncells = np.sum(nlcd16_arr == 1)
        write_geotiff(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\tempI.tif", nlcd16_val_arr, nlcd16_ds)
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
        c = gdal.Translate(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\outputI.tif",
                           r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\tempI.tif",
                           options=translateoptions)
        # https://gdal.org/tutorials/geotransforms_tut.html
        dx = nlcd16_ds.GetGeoTransform()[1]
        dy = -nlcd16_ds.GetGeoTransform()[5]
        area = nlcd16_val_ncells * dx * dy
        print(area)
        return area
    except Exception as e:
        print(e)

# This method is used to get the area of the tif file
def getInitialForestArea(year,pa):
    print("year", year)
    file = r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\fc\fc_mapbiomas_"+str(year)+"_1ha.tif"
    import rasterio
    from rasterio.mask import mask
    import geopandas as gp

    # the polygon GeoJSON geometry
    print(pa.aoi_name)
    p1 = json.loads(pa.aoi_geojson)
    poly1 = gp.GeoDataFrame.from_features(p1["features"])
    print("loading raster")
    geoms = poly1.geometry.values  # list of shapely geometries
    print(geoms)
    # load the raster, mask it by the polygon and crop it
    with rasterio.open(file) as src:
        out_image, out_transform = mask(src, geoms, crop=True)
    out_meta = src.meta.copy()

    # save the resulting raster
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open("masked.tif", "w", **out_meta) as dest:
        dest.write(out_image)
    return getAreaTif("masked.tif")

# This method is used to get the data of the areas that belong to the datasources (90% inside)
def getAreaIntersection(request):
    try:
        year = request.GET.get('year')
        print(year)
        start = time.time()
        for pa in PredefinedAOI.objects.all():
            print(pa.aoi_name)
            if pa.aoi_country=='GY':
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
                if percent >= params["PERCENTAGE_INSIDE_DATASET"]:
                    print("here")
                    fcchange = ForestCoverChange()
                    fcchange.fc_source = ForestCoverSource.objects.get(fcs_name='MapBioMas')
                    fcc = ForestCoverChangeFile.objects.get(file_name='fcc_mapbiomas_' + str(year) + '_1ha.tif')
                    fcchange.baseline_year = fcc.baseline_year
                    fcchange.processing_time = end - start
                    fcchange.year = year
                    fcchange.aoi = pa
                    print("here")
                    fcchange.initial_forest_area = getInitialForestArea(fcc.baseline_year, pa)
                    print("after1")
                    fcchange.forest_gain = getConditionalForestArea(1, fcc.year)
                    print("after2")
                    fcchange.forest_loss = getConditionalForestArea(-1, fcc.year)
                    print("after3")
                    fcchange.save()
                else:
                    continue
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
    file = "masked.tif"
    nlcd16_arr, nlcd16_ds = read_geotiff(file)

    nlcd16_val_arr = np.where(nlcd16_arr == value, 1, 0)
    nlcd16_val_ncells = np.sum(nlcd16_arr == value)
    write_geotiff(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\temp.tif", nlcd16_val_arr, nlcd16_ds)
    translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
    c = gdal.Translate(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\RLCMS_HKH\output.tif", r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\temp.tif", options=translateoptions)
    # https://gdal.org/tutorials/geotransforms_tut.html
    dx = nlcd16_ds.GetGeoTransform()[1]
    dy = -nlcd16_ds.GetGeoTransform()[5]
    area_m = 111319*nlcd16_val_ncells * dx * dy
    return area_m


def test():
        import requests
        import xmltodict
        url = requests.get("http://216.218.226.164:8080/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities")
        names=[]
        titles=[]
        links=[]
        data = xmltodict.parse(url.text)['WMS_Capabilities']['Capability']['Layer']
        for key, value in data.items():
            if key == 'Layer':
                for i in value:
                    names.append(i['Name'])
                    titles.append(i['Title'])
                    if i['Style']:
                        print('inside')
                        try:
                            links.append(i['Style']['LegendURL']['OnlineResource']['@xlink:href'])
                        except:
                            links.append('None')

                    else:
                        links.append('None')

        print(links)
        my_dict = {
            'Name': names,
            'Title': titles,
            'Link': links
        }
        df = pd.DataFrame(my_dict)
        df.to_csv('result.csv', index=False)

def new_test():
    # import rioxarray as rxr
    # import xarray as xr
    #
    # dataarray = r'C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\MapBiomass\fc\fc_mapbiomas_2001_1ha.tif'
    #
    #
    # gdal.Warp("output.tif", dataarray, dstSRS='ESRI:54009')
    # ds = gdal.Open(r'output.tif', 0)
    # gt = ds.GetGeoTransform()
    # pixel_area = gt[1] * abs(gt[5])
    # print(pixel_area)
    import os
    import geopandas as gpd
    polygons=gpd.read_file(r"C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\ShapeFiles\GUY_AOIS\Guyana_WDPA_epsg4326.shp")
    x=polygons.crs
    print(x)
    from pyproj import CRS
    CRS("ESRI:54009")
    polygons.to_crs(CRS("ESRI:54009"), inplace=True)
    sum=0
    print(polygons)
    for i in range(len(polygons)):
        polygons.loc[i,'area_m2']=shape(polygons.loc[i,'geometry']).area
        polygons.loc[i,'area_km2']=(shape(polygons.loc[i,'geometry']).area)/1000000

        polygons.loc[i,'area_hec']=(shape(polygons.loc[i,'geometry']).area)/10000
        sum=sum+polygons.loc[i,'area_km2']


    print(polygons)

def convert_to_100m():
    import rasterio
    from rasterio.enums import Resampling

    xres, yres =100, 100

    with rasterio.open(r'C:\Users\gtondapu\OneDrive - NASA\Desktop\ASCAP\agb1\agb\cevans_source_files\x_clipped\tropics_agb_2000_avitabile_.tif') as dataset:
        scale_factor_x = dataset.res[0] / xres
        scale_factor_y = dataset.res[1] / yres

        profile = dataset.profile.copy()
        # resample data to target shape
        data = dataset.read(
            out_shape=(
                dataset.count,
                int(dataset.height * scale_factor_y),
                int(dataset.width * scale_factor_x)
            ),
            resampling=Resampling.nearest
        )

        # scale image transform
        transform = dataset.transform * dataset.transform.scale(
            (1 / scale_factor_x),
            (1 / scale_factor_y)
        )
        profile.update({"height": data.shape[-2],
                        "width": data.shape[-1],
                        "transform": transform})

    with rasterio.open("tropics_agb_2000_avitable_nearest.tif", "w", **profile) as dataset:
        dataset.write(data)

def get_links(url):
    import os
    import requests
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup
    result = requests.get(url).content
    soup = BeautifulSoup(result, 'html.parser')
    data = soup.find_all('a')
    return data

def test_py():
    import os
    import requests
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup

    url = "https://apps.rcmrd.org:8443/forecasts_final/Country/"

    # If there is no such folder, the script will create one automatically
    folder_location = r'C:\Users\gtondapu\Desktop\ARANGELANDS'
    result = requests.get(url).content
    soup = BeautifulSoup(result, 'html.parser')
    data = soup.find_all('a')
    ls=get_links(url)
    hrefs=[]
    for i in range(len(ls)):
        if i>=272:
            hrefs.append(ls[i])

    for link in ls:
        if link:
            links = []
            names_of_mp3_files = []
            for l in get_links(urljoin(url, link.contents[0])):
                links.append(urljoin(url, l['href']))
                names_of_mp3_files.append(l.contents[0])
            print(links)
            print(names_of_mp3_files)
            for place in range(1,len(links)):
                isExist = os.path.exists("test_c"+'\\'+link.contents[0])
                # os.chmod(folder_location,0o777)
                if not isExist:
                    # Create a new directory because it does not exist
                    os.makedirs("test_c"+'\\'+link.contents[0],0o777)
                with open("test_c"+'\\'+link.contents[0]+'\\'+names_of_mp3_files[place], 'wb') as f:
                    content = requests.get(links[place]).content
                    f.write(content)


def upload_shapefiles():
    watershed_path=r"C:\Users\gtondapu\OneDrive - NASA\Desktop\RDST_data\rangelands"
    print('Watershed Data')
    for file in os.listdir(watershed_path):
        if file.endswith('.zip'):
            path = os.path.join(watershed_path, file)
            storename = file.split('.')[0]
            print('uploading ' + storename + ' to geoserver')
            headers = {'Content-type': 'application/zip', }
            user = "admin"
            password = "SERVIR@dmin*2013"
            data = open(path, 'rb').read()

        request_url = '{0}workspaces/{1}/datastores/{2}/file.shp'.format("http://216.218.226.154/geoserver/rest/",
                                                                         "rangelands",
                                                                         storename)

        requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))


def publish_raster():
    import requests

    # Define GeoServer information
    geoserver_url = 'https://thredds.servirglobal.net/'
    username = 'admin'
    password = 'SERVIR@dmin*2013'

    # Authenticate with GeoServer
    auth_endpoint = f'{geoserver_url}/geoserver/rest/security/j_spring_security_check'
    auth_response = requests.post(auth_endpoint, data={'j_username': username, 'j_password': password})

    # Loop through layers and publish
    layers = [r"C:\Users\gtondapu\OneDrive - NASA\Desktop\RDST_data\rangelands\modis.dekadal.20020411.tif"]  # List of layers to publish
    for layer in layers:
        # Create a data store for the layer
        create_datastore_url = f'{geoserver_url}/geoserver/rest/workspaces/{layer.workspace}/datastores'
        # Make a POST request with appropriate data store configuration

        # Publish the layer
        publish_layer_url = f'{geoserver_url}/geoserver/rest/workspaces/{layer.workspace}/datastores/{layer.datastore}/featuretypes'
        # Make a POST request with appropriate layer configuration

        # Handle errors and log status

    # Verify the layers have been published