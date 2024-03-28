import json
import operator
import os
import time
from pathlib import Path
import shutil
from subprocess import call

import numpy as np
import rasterio
from django.contrib.gis.gdal import SpatialReference, CoordTransform
import fiona
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rasterio import rio
from rasterio.mask import mask
from rasterio.warp import reproject
from shapely.geometry import shape
from osgeo import gdal, ogr, osr
import geopandas as gpd
from pyproj import CRS
import rioxarray

from scap.models import ForestCoverCollection, AGBCollection, AOICollection

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)

import doi


@csrf_exempt
def doi_valid(request,pk):
    if request.POST.get('doi')=='':
        return JsonResponse({"url": ""})
    try:
        url = doi.validate_doi(request.POST.get('doi'))
        return JsonResponse({"url": url})
    except Exception as e:
        return JsonResponse({"error": "error"})
@csrf_exempt
def stage_for_processing(request,pk):
    if request.POST.get('type')=='fc':
        coll=ForestCoverCollection.objects.get(collection_name=request.POST.get('coll_name'))
        coll.processing_status="Staged"
        coll.save()
    if request.POST.get('type')=='agb':
        coll=AGBCollection.objects.get(agb_name=request.POST.get('agb_name'))
        coll.processing_status="Staged"
        coll.save()
    if request.POST.get('type')=='aoi':
        coll=AOICollection.objects.get(aoi_name=request.POST.get('aoi_name'))
        coll.processing_status="Staged"
        coll.save()
    return JsonResponse({})

# This method uses the tif file and generates temporary shape file
def gdal_polygonize(dir, in_path):
    os.chdir(dir)
    # out_path = dir + "\\" + in_path + ".shp"
    out_path = in_path + ".shp"
    #  get raster datasource
    src_ds = gdal.Open(in_path + ".tif")
    srcband = src_ds.GetRasterBand(1)
    dst_layername = 'DN'  # This is the column that has values (0 or 1 or -1)
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(out_path)

    sp_ref = osr.SpatialReference()
    sp_ref.SetFromUserInput('EPSG:4326')
    dst_layer = dst_ds.CreateLayer(dst_layername, srs=sp_ref)

    fld = ogr.FieldDefn("DN", ogr.OFTInteger)
    dst_layer.CreateField(fld)
    dst_field = dst_layer.GetLayerDefn().GetFieldIndex("DN")

    gdal.Polygonize(srcband, None, dst_layer, dst_field, [], callback=None)
    print(out_path)
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
    # polygons.set_crs(epsg="4326", inplace=True)
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


# def process_chunk(chunk, value=99):
#     if value != 99:
#         filtered_chunk = chunk[chunk['DN'] == value]
#     else:
#         filtered_chunk = chunk[chunk['DN'] == 1]
#
#     filtered_chunk['area_hec'] = filtered_chunk['geometry'].area / 10000
#     return filtered_chunk['area_hec'].sum()
#
# def getArea(file, value=99, chunksize=10000):
#     area = 0
#     for chunk in gpd.read_file(file, chunksize=chunksize):
#         chunk = chunk.to_crs(CRS("ESRI:54009"))
#         area += process_chunk(chunk, value)
#     return area
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


def mask_with_tif():
    import numpy as np
    import rasterio
    from rasterio.warp import reproject
    from rasterio.warp import Resampling

    # Open the rasters to be clipped and masked
    with rasterio.open(r"path_to_tif") as src1:
        with rasterio.open(r"path_to_fc") as src2:
            # Read the shapes and transform them to the same coordinate reference system (CRS)

            # Clip the rasters
            shape_2, _ = reproject(
                source=src2.read(1),
                destination=np.zeros(src1.shape, dtype=np.uint8),
                src_transform=src2.transform,
                src_crs=src2.crs,
                dst_transform=src1.transform,
                dst_crs=src1.crs,
                resampling=rasterio.enums.Resampling.rms
            )

            # Create a mask based on the reprojected raster
            mask = shape_2 == 1

            # Read the first raster and convert to float
            clipped = src1.read().astype(np.float32)

            clipped = np.where(clipped, np.nan, mask)

            # Update the metadata to support NaN values
            profile = src1.profile
            profile.update(nodata=np.nan, dtype='float32')

            # Save the clipped raster
            with rasterio.open(r"fc_clipped_6.tif", "w", **profile) as dst:
                dst.write(clipped)

    # rds = rioxarray.open_rasterio(r"path_to_clipped_tif")
    # rds.name = "data"
    # df = rds.squeeze().to_dataframe().reset_index()
    # geometry = gpd.points_from_xy(df.x, df.y)
    # gdf = gpd.GeoDataFrame(df, crs=rds.rio.crs, geometry=geometry)
    # print(gdf.area / 10**6)


def get_resolution_of_tif(tif):
    try:
        src = gdal.Open(tif)
        xres, yres = operator.itemgetter(1, 5)(src.GetGeoTransform())
        return abs(xres * yres)
    except Exception as e:
        print(e)


def get_projection_of_tif(tif):
    from osgeo import gdal, osr

    ds = gdal.Open(tif)
    prj = ds.GetProjection()
    srs = osr.SpatialReference(wkt=prj)
    print(srs.GetAttrValue('projcs'))
    try:
        if srs.GetAttrValue('projcs') is None:
            return "INVALID"
        else:
            return srs.GetAttrValue('projcs')
    except Exception as e:
        return "INVALID"
        print(e)
    # print(srs.GetAttrValue('geogcs'))


def get_projection_of_boundary(shp):
    try:
        c = gpd.read_file(shp)
        crs = c.crs
        return str(crs)
    except Exception as e:
        print(e)
        return "INVALID"
