import numpy as np
from osgeo import gdal, osr, gdalconst
import rasterio as rio
import os

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
    """
    match = r"/servir_apps/data/SCAP/agb/global_agb_2000_liu_.tif"
    dtype = gdal.GDT_Byte
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

    gdal.ReprojectImage(source_obj, dest, src_proj, match_proj, gdalconst.GRA_Bilinear)

    # Close output raster dataset
    dest = None
    return outputpath

def calc_emissions(source):
    # Replace with your actual file paths and desired output name
    forest_change_path = "/home/alex/shared/SCAP/fcc_working/fcc/esri/INVERTED_REPROJECTED_fcc_esri_peru_2018_1ha.tif"
    AGB_path = "/home/alex/shared/SCAP/agb/Resampled_1ha/global_agb_2000_liu_.tif"
    output_path = "/home/alex/shared/SCAP/emissions_test.tif"

    with rio.open(forest_change_path) as src_change, rio.open(AGB_path) as src_AGB:
        # Check if resolutions match
        if src_change.transform != src_AGB.transform:
            raise ValueError("Rasters must have the same resolution and transform!")

        # Create output TIF with matching profile
        profile = src_AGB.profile.copy()
        profile.update({'count': 1})  # Update band count to 1 for masked output
        with rio.open(output_path, 'w', **profile) as dst:

            for (_, window) in src_change.block_windows(1):
                # Read blocks of data
                forest_change_block = src_change.read(1, window=window)
                AGB_block = src_AGB.read(1, window=window)

                # Create mask for the block
                forest_loss_mask = forest_change_block == 1
                print(forest_loss_mask.shape)

                # Apply mask to AGB block
                AGB_masked_block = np.multiply(AGB_block, forest_loss_mask)

                # Write masked block to output TIF
                dst.write(AGB_masked_block, window=window, indexes=1)

    print(f"Masked AGB values written to {output_path} in blocks")

def reproject_from_root(base_dir):
    subdirs = os.listdir(base_dir)
    for dir in subdirs:
        if dir != 'cci':
            dir_path = os.path.join(base_dir, dir)
            files = os.listdir(dir_path)
            for file in files:
                source = os.path.join(dir_path, file)

                print("Inverting {}".format(source))
                source = invert_gtiff(source)

                print("Reprojecting {}".format(source))
                source = reproject_gtiff(source)
        print("Done with {}".format(dir))
        print()

reproject_from_root('/servir_apps/data/SCAP/fcc/')
