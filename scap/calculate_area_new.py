import json
from osgeo import gdal, osr, ogr
from pathlib import Path
import os
import numpy as np
import rasterio as rio
from rasterio.windows import Window
import math

BASE_DIR = Path(__file__).resolve().parent.parent
config = json.load(open(str(BASE_DIR) + '/data.json', ))


def rasterize_aoi(aoi, match_path):
    geom = aoi.geom.json

    match_obj = gdal.Open(match_path)
    src_proj = match_obj.GetProjection()
    wkt = src_proj
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)

    geom_gdal_obj = gdal.OpenEx(geom)
    layer = geom_gdal_obj.GetLayer()

    for feature in layer:
        (minX, maxX, minY, maxY) = feature.GetGeometryRef().GetEnvelope()
        aoi_srs = osr.SpatialReference()
        aoi_srs.ImportFromEPSG(4326)
        
        # Reproject top left point of extent to Mollweide
        tl = ogr.Geometry(ogr.wkbPoint)
        tl.AddPoint(maxY, minX)
        tl.AssignSpatialReference(aoi_srs)
        tl.TransformTo(srs)
        tl_moll = (tl.GetX(), tl.GetY())

        # Reproject bottom right point of extent to Mollweide
        br = ogr.Geometry(ogr.wkbPoint)
        br.AddPoint(minY, maxX)
        br.AssignSpatialReference(aoi_srs)
        br.TransformTo(srs)
        br_moll = (br.GetX(), br.GetY())

    width = int((br_moll[0] - tl_moll[0]) // 100)
    height = int((tl_moll[1] - br_moll[1]) // 100)

    # Prepare destination file
    driver = gdal.GetDriverByName("GTiff")

    options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]
    output_path = os.path.join(config['DATA_DIR'], 'temp', "{}_rasterized.tif".format(aoi.name))
    dtype = gdal.GDT_UInt16

    if options != 0:
        dest = driver.Create(output_path, width, height, 1, dtype, options)
    else:
        dest = driver.Create(output_path, width, height, 1, dtype)

    transform = match_obj.GetGeoTransform()
    transform = list(transform)
    
    # Keep ones/tens/decimals from matching raster to align pixels
    new_origin_x = math.trunc(tl_moll[0] // 100 * 100) + (transform[0] % 100)
    new_origin_y = math.trunc(tl_moll[1] // 100 * 100) + (transform[3] % 100)
    
    # Calculate top left pixel offset comparing top left pixels of each raster's extent
    row_offset = int((transform[3] - new_origin_y) // 100)
    col_offset = int((new_origin_x - transform[0]) // 100)

    if new_origin_x < transform[0]:
        print('Clipping AOI origin X to FC file')
        new_origin_x = transform[0]
        col_offset = 0

    if new_origin_y > transform[3]:
        print('Clipping AOI origin Y to FC file')
        new_origin_y = transform[3]
        row_offset = 0

    
    transform[0] = new_origin_x
    transform[3] = new_origin_y

    transform = tuple(transform)
    dest.SetGeoTransform(transform)
    dest.SetProjection(srs.ExportToWkt())

    gdal.RasterizeLayer(dest, [1], layer)
    
    return output_path, row_offset, col_offset


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