import os
import json
import math
import operator
import shutil

import rasterio as rio
import numpy as np

from osgeo import gdal, ogr, osr, gdalconst
from rasterio.windows import Window
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)


def get_raster_offset(offset_raster, control_raster):
    offset_obj = gdal.Open(offset_raster)
    control_obj = gdal.Open(control_raster)

    offset_transform = offset_obj.GetGeoTransform()
    control_transform = control_obj.GetGeoTransform()


    row_offset = int((control_transform[3] - offset_transform[3]) // 100)
    col_offset = int((offset_transform[0] - control_transform[0]) // 100)

    return row_offset, col_offset


def add_collection_name_field(shp, collection_name):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    source_file = driver.Open(shp, 1)  # 1 is read/write

    new_field = ogr.FieldDefn('SCAPName', ogr.OFTString)
    new_field.SetWidth(64)
    layer = source_file.GetLayer()

    layer.CreateField(new_field)

    for feat in layer:
        feat.SetField('SCAPName', collection_name)
        layer.SetFeature(feat)

    source_file = None


def rasterize_aoi(aoi_feature, filepath):
    geom = aoi_feature.geom.json

    # TODO modify to specific transform and projection
    match_path = "/home/alex/Desktop/global_agb_2000_liu_.tif"

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
    if width > match_obj.RasterXSize:
        width = match_obj.RasterXSize

    height = int((tl_moll[1] - br_moll[1]) // 100)

    # Prepare destination file
    driver = gdal.GetDriverByName("GTiff")

    options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]
    dtype = gdal.GDT_Byte

    if options != 0:
        dest = driver.Create(filepath, width, height, 1, dtype, options)
    else:
        dest = driver.Create(filepath, width, height, 1, dtype)

    transform = match_obj.GetGeoTransform()
    transform = list(transform)

    # Keep ones/tens/decimals from matching raster to align pixels
    new_origin_x = math.trunc(tl_moll[0] // 100 * 100) + (transform[0] % 100)
    new_origin_y = math.trunc(tl_moll[1] // 100 * 100) + (transform[3] % 100)

    if new_origin_x < transform[0]:
        new_origin_x = transform[0]

    if new_origin_y > transform[3]:
        new_origin_y = transform[3]

    transform[0] = new_origin_x
    transform[3] = new_origin_y

    transform = tuple(transform)
    dest.SetGeoTransform(transform)
    dest.SetProjection(srs.ExportToWkt())

    gdal.RasterizeLayer(dest, [1], layer)


def reproject_gtiff(source, outputpath, progress_callback):
    """
    Writes a geotiff.

    array: numpy array to write as geotiff
    gdal_obj: object created by gdal.Open() using a tiff that has the SAME CRS, geotransform, and size as the array you're writing
    outputpath: path including filename.tiff
    dtype (OPTIONAL): datatype to save as
    nodata (default: FALSE): set to any value you want to use for nodata; if FALSE, nodata is not set
    """
    match = "/home/alex/Desktop/global_agb_2000_liu_.tif"
    dtype = gdal.GDT_Int16
    nbands = 1
    nodata = 0

    source_obj = gdal.Open(source)
    match_obj = gdal.Open(match)

    src_proj = source_obj.GetProjection()
    match_proj = match_obj.GetProjection()

    gt = match_obj.GetGeoTransform()

    width = match_obj.RasterXSize
    height = match_obj.RasterYSize

    # Prepare destination file
    driver = gdal.GetDriverByName("GTiff")

    options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]

    if options != 0:
        dest = driver.Create(outputpath, width, height, nbands, dtype, options)
    else:
        dest = driver.Create(outputpath, width, height, nbands, dtype)

    # Set transform and projection
    dest.SetGeoTransform(gt)
    wkt = match_obj.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    dest.SetProjection(srs.ExportToWkt())

    if nodata is not False:
        dest.GetRasterBand(1).SetNoDataValue(nodata)

    gdal.ReprojectImage(source_obj, dest, src_proj, match_proj, gdalconst.GRA_Bilinear, callback=progress_callback)

    # Close output raster dataset
    dest = None
    return outputpath


def is_snapped_mollweide(source):
    match = "/home/alex/Desktop/global_agb_2000_liu_.tif"

    source_obj = gdal.Open(source)
    match_obj = gdal.Open(match)

    src_proj = source_obj.GetProjection()
    match_proj = match_obj.GetProjection()

    source_gt = source_obj.GetGeoTransform()
    match_gt = match_obj.GetGeoTransform()

    x_aligned = not ((source_gt[0] % 100) - (match_gt[0] % 100))
    y_aligned = not ((source_gt[3] % 100) - (match_gt[3] % 100))
    affine_aligned = (source_gt[1] == match_gt[1] and source_gt[2] == match_gt[2] and
                      source_gt[4] == match_gt[4] and source_gt[5] == match_gt[5])

    matching_transforms = x_aligned and y_aligned and affine_aligned

    return src_proj == match_proj and matching_transforms


def calculate_change_file(baseline_filepath, current_filepath, target_path):
    # Assumes both files are already Mollweide and snapped to SCAP grid

    with rio.open(baseline_filepath) as base_raster, rio.open(current_filepath) as curr_raster:
        profile = curr_raster.profile.copy()
        profile.update({'count': 1, 'dtype': rio.int16})
        with rio.open(target_path, 'w', **profile) as dst:
            for (_, window) in base_raster.block_windows(1):
                # Read blocks of data
                # Should be same transform, so no need to offset windows
                base_block_data = base_raster.read(1, window=window)
                curr_block_data = curr_raster.read(1, window=window)

                # Apply mask to AGB block
                change_block_data = np.subtract(curr_block_data, base_block_data)

                # Write masked block to output TIF
                dst.write(change_block_data, window=window, indexes=1)

    return outputpath


def copy_mollweide(source_file, target_path, progress_callback):
    if is_snapped_mollweide(source_file):
        shutil.copyfile(source_file, target_path)
    else:
        reproject_gtiff(source_file, target_path, progress_callback)


def generate_carbon_gtiff(fc_source, agb_source, fc_year, agb_year, output_path, carbon_type):
    target_fc_value = 1 if carbon_type == 'carbon-stock' else -1

    if agb_year > fc_year:
        # TODO Log message on skip?
        return

    with rio.open(fc_source) as fc_raster, rio.open(agb_source) as agb_raster:
        # Create output TIF with matching profile
        profile = fc_raster.profile.copy()
        profile.update({'count': 1, 'dtype': rio.uint16, 'nodata': 0})  # Update band count to 1 for masked output
        with rio.open(output_path, 'w', **profile) as dst:
            for (_, window) in fc_raster.block_windows(1):
                # Read blocks of data
                fc_block_data = fc_raster.read(1, window=window)

                # TODO Add offset for when tiffs are not loaded globally
                # sr = window.row_off  # + 85323
                # sc = window.col_off  # + 98901
                # corresponding_window = Window.from_slices((sr, sr + window.height), (sc, sc + window.width))
                # agb_block = agb_raster.read(1, window=corresponding_window)

                agb_block = agb_raster.read(1, window=window)

                # Create mask for the block
                forest_scaled_mask = (fc_block_data == target_fc_value) * 48

                # Apply mask to AGB block
                forest_carbon_total = np.multiply(agb_block, forest_scaled_mask)

                # Write masked block to output TIF
                dst.write(forest_carbon_total, window=window, indexes=1)


def compute_masked_pixels(data_raster, aoi, target_value, compute_function):
    row_offset, col_offset = get_raster_offset(aoi, data_raster)

    pixel_computation_sum = 0
    with rio.open(data_raster) as data_obj, rio.open(aoi) as aoi_obj:
        aoi_block = aoi_obj.read(1)
        corresponding_window = Window.from_slices((row_offset, row_offset + aoi_obj.height),
                                                  (col_offset, col_offset + aoi_obj.width))
        data_block = data_obj.read(1, window=corresponding_window)

        if target_value:
            target_change_arr = (data_block == target_value)
            pixel_computation_sum += compute_function((target_change_arr > 0) * (aoi_block > 0))
        else:
            pixel_computation_sum += compute_function(data_block * (aoi_block > 0))

    return pixel_computation_sum


def count_overlapping_pixels(lc_raster, aoi, target_value_type):
    target_value = -1 if target_value_type == 'loss' else 1

    area = compute_masked_pixels(lc_raster, aoi, target_value, np.count_nonzero)

    return area


def sum_overlapping_pixels(lc_raster, aoi):
    total = compute_masked_pixels(lc_raster, aoi, None, np.sum)

    return total


def mask_water(raster_file):
    pass


def stitch_geotiffs(input_dir, target_path):
    # Get list of input GeoTIFF files
    input_files = list(Path(input_dir).rglob('*.tif'))

    if not input_files:
        # TODO Log error
        return

    # Initialize variables to store total geographic extent
    min_x, max_y, max_x, min_y = float('inf'), float('-inf'), float('-inf'), float('inf')

    # Iterate over input files to calculate total extent
    for input_filepath in input_files:
        input_ds = gdal.Open(os.path.join(input_dir, input_filepath))
        geo_transform = input_ds.GetGeoTransform()
        x_size = input_ds.RasterXSize
        y_size = input_ds.RasterYSize
        min_x = min(min_x, geo_transform[0])
        max_y = max(max_y, geo_transform[3])
        max_x = max(max_x, geo_transform[0] + geo_transform[1] * x_size)
        min_y = min(min_y, geo_transform[3] + geo_transform[5] * y_size)

    # Calculate size of output GeoTIFF based on total extent
    output_x_size = int((max_x - min_x) / geo_transform[1])
    output_y_size = int((max_y - min_y) / abs(geo_transform[5]))

    # Create output GeoTIFF
    driver = gdal.GetDriverByName('GTiff')
    options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]

    output_ds = driver.Create(target_path, output_x_size, output_y_size, 1, gdal.GDT_Byte, options)
    output_ds.SetGeoTransform((min_x, geo_transform[1], 0, max_y, 0, geo_transform[5]))
    output_ds.SetProjection(input_ds.GetProjection())  # Set projection information
    output_ds.GetRasterBand(1).SetNoDataValue(0)  # Set no data value

    # Iterate over each input GeoTIFF file
    for input_filepath in input_files:
        # Open the input GeoTIFF file
        input_ds = gdal.Open(str(input_filepath))
        input_data = input_ds.GetRasterBand(1).ReadAsArray()

        # Get the geographic extent of the input file
        geo_transform = input_ds.GetGeoTransform()

        # Calculate offset based on geographic extent
        offset_x = int((geo_transform[0] - min_x) / geo_transform[1])
        offset_y = int((max_y - geo_transform[3]) / abs(geo_transform[5]))

        # Write data to output GeoTIFF
        output_ds.GetRasterBand(1).WriteArray(input_data, offset_x, offset_y)

        # Close the input file
        input_ds = None

    # Close the output file
    output_ds = None