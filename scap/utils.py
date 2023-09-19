import json
import os
import time
from pathlib import Path
import shutil
from django.contrib.gis.gdal import SpatialReference, CoordTransform
import fiona
from shapely.geometry import shape
from osgeo import gdal, ogr, osr
import geopandas as gpd
from pyproj import CRS

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)

# This method uses the tif file and generates temporary shape file
def gdal_polygonize(dir, in_path):
    os.chdir(dir)
    out_path = dir + in_path + ".shp"
    #  get raster datasource
    src_ds = gdal.Open(in_path + ".tif")
    srcband = src_ds.GetRasterBand(1)
    dst_layername = 'DN' # This is the column that has values (0 or 1 or -1)
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(out_path)

    sp_ref = osr.SpatialReference()
    sp_ref.SetFromUserInput('EPSG:4326')

    dst_layer = dst_ds.CreateLayer(dst_layername, srs=sp_ref)

    fld = ogr.FieldDefn("DN", ogr.OFTInteger)
    dst_layer.CreateField(fld)
    dst_field = dst_layer.GetLayerDefn().GetFieldIndex("DN")

    gdal.Polygonize(srcband, None, dst_layer, dst_field, [], callback=None)
    return out_path

# Alternative method to convert a tif to shp file - currently unused
def convert_tif_to_shp(filename):
    from osgeo import gdal
    import os

    inDs = gdal.Open('{}.tif'.format(filename))
    outDs = gdal.Translate('{}.xyz'.format(filename), inDs, format='XYZ', creationOptions=["ADD_HEADER_LINE=YES"])
    outDs = None
    try:
        os.remove('{}.csv'.format(filename))
        os.rename('{}.xyz'.format(filename), '{}.csv'.format(filename))
        val = os.system(
            'ogr2ogr -f "ESRI Shapefile" -oo X_POSSIBLE_NAMES=X* -oo Y_POSSIBLE_NAMES=Y* -oo KEEP_GEOM_COLUMNS=NO {0}.shp {0}.csv'.format(
                filename))
        if val == 0:
            print("shape file is generated")
            return filename + ".shp"
    except OSError as e:
        print(e)


# Get the area of the masked file in Mollweide Projection
def getArea(file, value=99):
    file_out = file
    polygons = gpd.read_file(file_out)
    polygons.set_crs(epsg="4326", inplace=True)
    area = 0
    new_polygons = polygons
    new_polygons.to_crs(CRS("ESRI:54009"), inplace=True)
    # print(new_polygons)
    for i in range(len(new_polygons)):
        # new_polygons.loc[i, 'area_m2'] = shape(new_polygons.loc[i, 'geometry']).area
        # new_polygons.loc[i, 'area_km2'] = (shape(new_polygons.loc[i, 'geometry']).area) / 1000000
        new_polygons.loc[i, 'area_hec'] = (shape(new_polygons.loc[i, 'geometry']).area) / 10000
        if value != 99:
            # forest gain(value=1) or forest loss(value=-1) calculation
            if new_polygons.loc[i, 'DN'] == value:
                area = area + new_polygons.loc[i, 'area_hec']
        else:
            # initial forest area calculation
            if new_polygons.loc[i, 'DN'] == 1:
                area = area + new_polygons.loc[i, 'area_hec']
    return area

# This method calculates the area of a protected area
def entire_area_pa(pa):
    x = pa.geom
    gcoord = SpatialReference(4326)
    mycoord = SpatialReference("ESRI:54009")
    trans = CoordTransform(gcoord, mycoord)
    x.transform(trans)
    print(x.srid)
    y = x.area
    print(y)

# def getArea(js):
#     from shapely.geometry import shape
#
#     try:
#         features = []
#         flag = False
#
#         for feature in js['features']:
#             features.append(feature)
#         print(len(features))
#         area = 0
#         for feature in features:
#             polygon = shape(feature['geometry'])
#             area = area + polygon.area
#         print(area)
#         return area
#     except Exception as e:
#         print(e)
#         return HttpResponse(str(e))


def percent_inside(pa, ds):
    polygon1 = fiona.open(pa.geom.json)
    polygon8 = fiona.open(ds.geom.json)

    geom_p1 = [shape(feat["geometry"]) for feat in polygon1]
    geom_p8 = [shape(feat["geometry"]) for feat in polygon8]

    for i, g1 in enumerate(geom_p1):
        for j, g8 in enumerate(geom_p8):
            if g1.intersects(g8):
                end = time.time()
                return (g1.intersection(g8).area / g1.area) * 100

# create a directory for temp files
def create_temp_dir(directory):
    if not os.path.exists(directory):
        # If it doesn't exist, create it
        os.makedirs(directory)

# delete the temp directory and its contents
def delete_temp_dir(directory):
    shutil.rmtree(directory)
