import shutil
import json
import os

from django.views.decorators.csrf import csrf_exempt
from pathlib import Path

from scap.models import ForestCoverCollection, ForestCoverFile, AGBCollection, AOICollection, AOIFeature


BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)


def visualization_etl(raster_path, collection_name, collection_type, owner, year=None):
    # TODO Integrate with GenETL
    pass


def statistics_etl(raster_path, collection_name, collection_type, owner, year=None):
    filename = os.path.basename(raster_path)
    shutil.copyfile(raster_path,
                    os.path.join(config['DATA_DIR'],
                                 owner,
                                 collection_type,
                                 collection_name,
                                 filename))


def temp_load(filepath, collection_name, collection_type, owner):
    filename = os.path.basename(filepath)
    temp_dir = os.path.join(config['DATA_DIR'],
                            'temp',
                            owner.username,
                            collection_type,
                            collection_name)
    temp_filepath = os.path.join(temp_dir, filename)

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    shutil.copyfile(filepath, temp_filepath)


def snap_to_common_grid(input_raster_filepath):
    pass


def ensure_epsg_4326(input_raster_filepath):
    pass


def process_raster(input_raster_filepath, collection_name, collection_type, owner, year=None):
    pass
    #visualization_etl(ensure_epsg_4326(input_raster_filepath), collection_name, collection_type, owner, year)
    #statistics_etl(snap_to_common_grid(input_raster_filepath), collection_name, collection_type, owner, year)


def subtract_rasters(baseline_raster_filepath, change_raster_filepath):
    pass


def rasterize_aoi(input_geometry):
    # TODO cleanup
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
    if width > match_obj.RasterXSize:
        print('Clipping width to FC raster')
        width = match_obj.RasterXSize
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