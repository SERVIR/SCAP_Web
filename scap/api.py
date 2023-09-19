import json
import os
import time
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
import fiona
from shapely.geometry import shape
from django.contrib.gis.utils import LayerMapping
import rasterio
from rasterio.mask import mask

from scap.models import BoundaryFiles, AOI, ForestCoverChange, ForestCoverChangeFile, ForestCoverFile

from scap.utils import percent_inside, gdal_polygonize, getArea, create_temp_dir, delete_temp_dir

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)

# This method is used to generate geodjango objects for AOI or Boundary Data Source
# Uses LayerMapping technique to update the object from shape file
def generate_geodjango_objects(verbose=True):
    boundaryfiles_mapping = {
        'feature_id': 'feature_id',
        'name_es': 'name_es',
        'nomedep': 'nomedep',
        'nomemun': 'nomemun',
        'pais': 'pais',
        'fid': 'FID',
        'geom': 'MULTIPOLYGON',
    }
    aoi_mapping = {
        'wdpaid': 'WDPAID',
        'wdpa_pid': 'WDPA_PID',
        'pa_def': 'PA_DEF',
        'name': 'NAME',
        'orig_name': 'ORIG_NAME',
        'desig': 'DESIG',
        'desig_eng': 'DESIG_ENG',
        'desig_type': 'DESIG_TYPE',
        'iucn_cat': 'IUCN_CAT',
        'int_crit': 'INT_CRIT',
        'marine': 'MARINE',
        'rep_m_area': 'REP_M_AREA',
        'gis_m_area': 'GIS_M_AREA',
        'rep_area': 'REP_AREA',
        'gis_area': 'GIS_AREA',
        'no_take': 'NO_TAKE',
        'no_tk_area': 'NO_TK_AREA',
        'status': 'STATUS',
        'status_yr': 'STATUS_YR',
        'gov_type': 'GOV_TYPE',
        'own_type': 'OWN_TYPE',
        'mang_auth': 'MANG_AUTH',
        'mang_plan': 'MANG_PLAN',
        'verif': 'VERIF',
        'metadataid': 'METADATAID',
        'sub_loc': 'SUB_LOC',
        'parent_iso': 'PARENT_ISO',
        'iso3': 'ISO3',
        'supp_info': 'SUPP_INFO',
        'cons_obj': 'CONS_OBJ',
        'layer': 'layer',
        'path': 'path',
        'geom': 'MULTIPOLYGON',
    }

    boundary = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'data', r'C:\Users\gtondapu\Documents\nepal.shp'),
    )

    # lm = LayerMapping(BoundaryFiles, boundary, boundaryfiles_mapping, transform=False)
    # lm.save(strict=True, verbose=verbose)
    lm = LayerMapping(AOI, boundary, aoi_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)

# Calculating the forest area of baseline year's FC TIFF file
def getInitialForestArea(year, dir, dataset, pa, val):
    # print("year", year)
    dataset = dataset.lower()
    file = dir + "fc_" + dataset + "_" + str(year) + "_1ha.tif"
    print(pa.name)
    data = fiona.open(pa.geom.json)  # list of shapely geometries
    geometry = [shape(feat["geometry"]) for feat in data]
    # load the raster, mask it by the FC TIFF and crop it
    with rasterio.open(file) as src:
        # print(src.profile)
        out_image, out_transform = mask(src, geometry, crop=True)
    out_meta = src.meta.copy()

    # save the resulting raster
    out_meta.update({"driver": "GTiff",

                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    file_out = r"masked_fc" + str(val) + ".tif"
    os.chdir(dir)
    with rasterio.open(file_out, "w", **out_meta) as dest:
        dest.write(out_image)
    return getArea(gdal_polygonize(dir, r"masked_fc" + str(val)))


# get the forest gain or forest loss of a FCC TIFF file
def getConditionalForestArea(pa, dir, dataset, value, year, val):
    # print(year)
    file = dir + "fcc_" + dataset + "_" + str(year) + "_1ha.tif"
    data = fiona.open(pa.geom.json)  # get the json of a protected area
    geometry = [shape(feat["geometry"]) for feat in data]
    # load the raster, mask it by the FCC TIFF and crop it
    with rasterio.open(file) as src:
        out_image, out_transform = mask(src, geometry, crop=True)
    out_meta = src.meta.copy()

    # save the resulting raster
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    file_out = r"masked_fcc" + str(val) + ".tif"
    os.chdir(dir)
    with rasterio.open(file_out, "w", **out_meta) as dest:
        dest.write(out_image)
    return getArea(gdal_polygonize(dir, r"masked_fcc" + str(val)), value)


# Find all the files that are atleast 90% inside the datasource
# For each Protected Area that is inside the datasource, calculate the FCC object fields
def generate_fcc_fields(dataset,year):
    try:
        create_temp_dir(params["PATH_TO_TEMP_FILES"])
        l_dataset=dataset.lower()
        data_source = (BoundaryFiles.objects.get(name_es=dataset))
        needed_aois = AOI.objects.filter(geom__intersects=GEOSGeometry(data_source.geom))
        val = 0
        for aoi in needed_aois:
            val = val + 1
            start = time.time()
            if percent_inside(aoi, data_source) > params["PERCENTAGE_INSIDE_DATASET"]:
                fcchange = ForestCoverChange()
                fcchange.fc_source = data_source
                fcc = ForestCoverChangeFile.objects.get(file_name='fcc_'+l_dataset+'_' + str(year) + '_1ha.tif')
                fc = ForestCoverFile.objects.get(file_name='fc_'+l_dataset+'_' + str(fcc.baseline_year) + '_1ha.tif')
                fcchange.baseline_year = fcc.baseline_year
                fcchange.year = year
                fcchange.aoi = aoi
                fcchange.initial_forest_area = getInitialForestArea(fcc.baseline_year,
                                                                    fc.file_directory, fc.fc_source.name_es, aoi, val)
                fcchange.forest_gain = getConditionalForestArea(aoi, fcc.file_directory,fcc.fc_source.name_es, 1, fcc.year, val)
                fcchange.forest_loss = getConditionalForestArea(aoi, fcc.file_directory,fcc.fc_source.name_es, -1, fcc.year, val)
                end = time.time()
                fcchange.processing_time = end - start
                fcchange.save()
    except Exception as e:
        print(e)
    finally:
        delete_temp_dir(params["PATH_TO_TEMP_FILES"])