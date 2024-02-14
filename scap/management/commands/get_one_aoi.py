import sys
import os
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
import fiona
from fiona.crs import from_epsg
from scap.models import AOI
import datetime
from shapely.geometry import shape, mapping
import rasterio as rio
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling
import rasterio.features as features
import json
import geopandas as gpd
import numpy as np
from osgeo import gdal, osr
import matplotlib.pyplot as plt

class Command(BaseCommand):
    help = ''

    # Function Handler
    def handle(self, *args, **options):
        needed_aois = AOI.objects.all()
        one = needed_aois[0].geom.json
        aoi_crs = CRS.from_epsg(4326)
        raster_crs = CRS.from_string("ESRI:54009")
        
        aoi_geometry_reprojected = rio.warp.transform_geom("EPSG:4326", "ESRI:54009", json.loads(one))

        geojson_obj = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": aoi_geometry_reprojected,
                    "properties": {}
                }
            ]
        }

        vec = gpd.read_file('/home/alex/shared/SCAP/aois/peru/peru_pa.shp')
        # rio.warp.transform_geom("EPSG:4326", "ESRI:54009", shapes)
        geom = [shapes for shapes in vec.geometry]

        raster = rio.open('/home/alex/shared/SCAP/fcc/esri/fcc_esri_peru_2018_1ha.tif')

        rasterized = features.rasterize(vec.geometry, out_shape=raster.shape, fill=0, out=None, transform=raster.transform, all_touched=False, default_value=1, dtype=np.int16)
        print(np.unique(rasterized))
        print(raster.profile)
        print(np.shape(rasterized))
        print(np.count_nonzero(rasterized))
        with rio.open('raster_test.tif', 'w', **(raster.profile)) as dest:
            dest.write(np.transpose(rasterized), indexes=1)


        with rio.open('raster_test.tif') as dest:
            print(np.unique(dest.read(1)))

        #source_obj = gdal.Open('/home/alex/shared/SCAP/fcc/esri/fcc_esri_peru_2018_1ha.tif')
        #src_proj = source_obj.GetProjection()
        #transform = source_obj.GetGeoTransform()
        #width = source_obj.RasterXSize
        #height = source_obj.RasterYSize
#
        ## Prepare destination file
        #driver = gdal.GetDriverByName("GTiff")
#
        #options = ["TILED=YES", "BLOCKXSIZE=256", "BLOCKYSIZE=256", "COMPRESS=LZW"]
        #output_path = 'raster_test.tif'
        #dtype = gdal.GDT_UInt16
#
        #if options != 0:
        #    dest = driver.Create(output_path, width, height, 1, dtype, options)
        #else:
        #    dest = driver.Create(output_path, width, height, 1, dtype)
#
        #print(transform)
        #dest.SetGeoTransform(transform)
        #wkt = src_proj
        #srs = osr.SpatialReference()
        #srs.ImportFromWkt(wkt)
        #dest.SetProjection(srs.ExportToWkt())
#
        #dest.GetRasterBand(1).WriteArray(rasterized)
#
        #dest=None
        
        plt.imshow(rasterized)
        plt.colorbar()
        plt.show()
        
        
        
