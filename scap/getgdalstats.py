import xarray
from osgeo import gdal
import subprocess
import json
import os
from netCDF4 import Dataset
from scap.models import (ForestCoverCollection, AGBCollection,CarbonStockFile,EmissionFile)
def get_gdal_stats_as_json(raster_file_obj,name):
    test = raster_file_obj
    r = requests.get(test, timeout=10)
    with open(name, 'wb') as f:
        f.write(r.content)
    dataset = gdal.Open(name, gdal.GA_ReadOnly)

    #
    # if dataset is None:
    #     raise ValueError(f"Could not open raster file at path: {raster_path}")
    actual_json = json.loads(os.popen('gdalinfo -stats -json '+name).read())
    band = dataset.GetRasterBand(1)
    print(band.GetStatistics(True, True))
    stats = band.GetStatistics(True, True)
    st = {
        'minimum': stats[0],
        'maximum': stats[1],
        'statistics':actual_json
    }
    del dataset

    return st


# cs = CarbonStockFile.objects.all()
# for cs_obj in cs:
#     fc=ForestCoverFile.objects.filter(fc_index=cs_obj.fc_index)
#     gdal_stats_json = get_gdal_stats_as_json(fc.)
#     fc.statistics=json.dumps(gdal_stats_json)
#     fc.save()

from bs4 import BeautifulSoup
import requests


def list_dir_url(url, ext=''):
    url = 'https://thredds.servirglobal.net/thredds/catalog/scap/public/emissions/1/catalog.html'
    ext = 'nc4'
    page = requests.get(url).text

    soup = BeautifulSoup(page, 'html.parser')
    url = url[:url.rfind('/')]

    return [url + '/' + node.get('href') for node in soup.find_all('a')]


def list_nc4_url(url, ext=''):
    ext = 'nc4'
    page = requests.get(url).text

    soup = BeautifulSoup(page, 'html.parser')

    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]

# for file in list_dir_url('', ''):
    # try:
    #     urls=list_nc4_url(file, '')
    #     url_arr = urls[0].split('/')
    #     final ='https://thredds.servirglobal.net/thredds/fileServer/scap/public/'+  url_arr[7] + '/' +url_arr[8] + '/' + url_arr[9] + '/' + url_arr[-1]
    #     fc_agb = url_arr[9]
    #
    #     get_gdal_stats_as_json(final)
    #     break
    #
    # except Exception as e:
    #     print(e)

def gdal_stats():
    try:
        for file in list_dir_url('', ''):
            urls=list_nc4_url(file, '')
            print("1")
            for url in urls:
                url_arr = url.split('/')
                print('2')
                final ='https://thredds.servirglobal.net/thredds/fileServer/scap/public/'+  url_arr[7] + '/' +url_arr[8] + '/' + url_arr[9] + '/' + url_arr[-1]
                fc = url_arr[9].split('_')[0]
                fc=fc.replace('-',' ')
                agb = url_arr[9].split('_')[1]
                agb=agb.replace('-',' ')
                fc_coll=ForestCoverCollection.objects.get(name__iexact=fc)
                agb_coll=AGBCollection.objects.get(name__iexact=agb)
                result=get_gdal_stats_as_json(final, url_arr[-1])
                new_carbonstock_obj=EmissionFile()
                new_carbonstock_obj.statistics=result['statistics']
                new_carbonstock_obj.min=result['minimum']
                new_carbonstock_obj.max=result['maximum']
                new_carbonstock_obj.fc_index=fc_coll
                new_carbonstock_obj.agb_index=agb_coll
                new_carbonstock_obj.year_index=int(url_arr[-1].split('.')[-2])
                new_carbonstock_obj.save()
    except Exception as e:
        print(e)
