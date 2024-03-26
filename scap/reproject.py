import numpy as np
from osgeo import gdal, osr, gdalconst
from pathlib import Path
from rasterio.windows import Window
import rasterio as rio
import os
import json
import re

BASE_DIR = Path(__file__).resolve().parent.parent
config = json.load(open(str(BASE_DIR) + '/data.json', ))


def invert_gtiff(source_path):
    dtype = gdal.GDT_Byte

    filename = source_path.split('/')[-1]
    folder = '/'.join(source_path.split('/')[:-1]) + '/'

    output_path = folder + 'INVERTED_' + filename

    source_obj = gdal.Open(source_path)
    src_proj = source_obj.GetProjection()
    transform = source_obj.GetGeoTransform()
    width = source_obj.RasterXSize
    height = source_obj.RasterYSize

    # Prepare destination file
    driver = gdal.GetDriverByName("GTiff")

    options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]

    if options != 0:
        dest = driver.Create(output_path, width, height, 1, dtype, options)
    else:
        dest = driver.Create(output_path, width, height, 1, dtype)

    dest.SetGeoTransform(transform)
    wkt = src_proj
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    dest.SetProjection(srs.ExportToWkt())

    arr = source_obj.GetRasterBand(1).ReadAsArray()
    inverted_arr = arr * (-1)

    dest.GetRasterBand(1).WriteArray(inverted_arr)

    dest = None

    return output_path


def reproject_gtiff(source):
    """
    Writes a geotiff.

    array: numpy array to write as geotiff
    gdal_obj: object created by gdal.Open() using a tiff that has the SAME CRS, geotransform, and size as the array you're writing
    outputpath: path including filename.tiff
    dtype (OPTIONAL): datatype to save as
    nodata (default: FALSE): set to any value you want to use for nodata; if FALSE, nodata is not set
    """
    match = os.path.join(config['DATA_DIR'], 'agb', r"global_agb_2000_liu_.tif")
    dtype = gdal.GDT_Int16
    nbands = 1
    nodata = -9999

    filename = source.split('/')[-1]
    folder = '/'.join(source.split('/')[:-1]) + '/'

    outputpath = folder + 'REPROJECTED_' + filename

    source_obj = gdal.Open(source)
    match_obj = gdal.Open(match)

    src_proj = source_obj.GetProjection()
    match_proj = match_obj.GetProjection()

    gt = match_obj.GetGeoTransform()

    # CLIP TO PERU FOR DEMO
    gt = list(gt)
    decimal_x = float('0.' + str(gt[0]).split('.')[1])
    decimal_y = 1 - float('0.' + str(gt[3]).split('.')[1])
    gt[0] = -8150994 - decimal_x
    gt[3] = -4711 - decimal_y
    gt = tuple(gt)

    # CUT EXTENT TO PERU FOR DEMO
    width = 14889
    height = 22496

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

    gdal.ReprojectImage(source_obj, dest, src_proj, match_proj, gdalconst.GRA_Bilinear)

    # Close output raster dataset
    dest = None
    return outputpath


def generate_emissions_gtiff(source, agb):
    # Replace with your actual file paths and desired output name
    fcc_filename = '_'.join(source.split('/')[-1].split('_')[2:])
    agb_filename, _ = os.path.splitext(agb.split('/')[-1])
    agb_year = re.search('\\d{4}', agb_filename)
    fcc_year = re.search('\\d{4}', fcc_filename)
    if 'tropics' in agb_filename:
        print('This AGB does not have proper transform')
        return
    if (not (agb_year and fcc_year)) or (agb_year.group(0) > fcc_year.group(0)):
        print('Not generating emissions; AGB was created after the current year '
              '{}, {}'.format(agb_filename, fcc_filename))
        return

    output_path = os.path.join(config['DATA_DIR'], 'emissions', agb_filename, fcc_filename.replace('fcc', 'emissions'))

    with rio.open(source) as src_change, rio.open(agb) as src_AGB:
        # Check if resolutions match
        # Resolutions/transforms won't match bc they dont cover same extent
        # if src_change.transform != src_AGB.transform:
        #    raise ValueError("Rasters must have the same resolution and transform!")

        # Create output TIF with matching profile
        profile = src_change.profile.copy()
        profile.update({'count': 1, 'dtype': rio.uint16})  # Update band count to 1 for masked output
        with rio.open(output_path, 'w', **profile) as dst:
            for (_, window) in src_change.block_windows(1):
                # Read blocks of data
                forest_change_block = src_change.read(1, window=window)

                sr = window.row_off + 85323
                sc = window.col_off + 98901
                corresponding_window = Window.from_slices((sr, sr + window.height), (sc, sc + window.width))
                print(corresponding_window)

                AGB_block = src_AGB.read(1, window=corresponding_window)

                # Create mask for the block
                forest_loss_mask = (forest_change_block == 1) * 48

                # Apply mask to AGB block
                AGB_masked_block = np.multiply(AGB_block, forest_loss_mask)

                # Write masked block to output TIF
                dst.write(AGB_masked_block, window=window, indexes=1)

    print(f"Masked AGB values written to {output_path} in blocks")


def map_to_agbs(source):
    all_agbs = os.listdir(os.path.join(config['DATA_DIR'], 'agb'))
    for agb in all_agbs:
        print('Generating emissions for AGB {} and FCC {}'.format(agb, source))
        generate_emissions_gtiff(source, os.path.join(config['DATA_DIR'], 'agb', agb))


def process_directory(base_dir):
    subdirs = os.listdir(base_dir)
    for dir in subdirs:
        if dir != 'cci':
            dir_path = os.path.join(base_dir, dir)
            files = os.listdir(dir_path)
            for file in files:
                try:
                    if (not 'tif' in file) and ('xml' not in file):
                        print('Skipping file {}'.format(file))
                        continue
                    source = os.path.join(dir_path, file)
                    print('Processing file {}'.format(file))

                    print("Inverting {}".format(source))
                    source = invert_gtiff(source)

                    print("Reprojecting {}".format(source))
                    source = reproject_gtiff(source)

                    map_to_agbs(source)
                except:
                    print('ERROR processing file {}'.format(file))
                    continue
        print("Done with {}".format(dir))
        print()

# process_directory(os.path.join(config['DATA_DIR'], 'fcc'))
