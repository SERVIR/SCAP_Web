import json
import operator
import shutil

from osgeo import gdal, ogr, osr
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)


def get_raster_resolution(tif):
    try:
        src = gdal.Open(tif)
        xres, yres = operator.itemgetter(1, 5)(src.GetGeoTransform())
        return abs(xres * yres)
    except Exception as e:
        print(e)


def get_raster_projection(tif):
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


def get_polygon_projection(shp):
    try:
        c = gpd.read_file(shp)
        crs = c.crs
        return str(crs)
    except Exception as e:
        print(e)
        return "INVALID"