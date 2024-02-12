import json
import os
from pathlib import Path

import numpy as np
from django.http import HttpResponse
import time
from osgeo import gdal
from osgeo import gdalconst

from scap.models import BoundaryFiles, ForestCoverFile, ForestCoverChangeFile

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)


# Generate FC file by passing the required year and dataset and save the Django object with data
def generate_fc_file(request):
    try:
        years = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]

        for x in years:
            dataset = 'JAXA'
            l_dataset = dataset.lower()
            fcs = BoundaryFiles.objects.get(name_es=dataset)
            fc = ForestCoverFile()
            fc.file_name = "fc_" + l_dataset + "_peru_" + str(x) + "_1ha.tif"
            fc.file_directory = r"your_path"
            fc.fc_source = fcs
            fc.save()
    except:
        print("Unable to generate the files")


# Generate a FCC file by passing the required year and dataset in the request
# and save the Django object with data
def generate_fcc_file(request):
    try:
        year = request.GET.get('year')
        print(year)
        dataset = 'JAXA'
        l_dataset = dataset.lower()
        start = time.time()
        fcs = BoundaryFiles.objects.get(name_es=dataset)
        fcc = ForestCoverChangeFile()  # Create a new FCC file object
        A_TIF = r"your_path\fc\jaxa\fc_jaxa_peru_" + str(int(year) - 1) + "_1ha.tif"
        i = 1
        while (i < 10):
            B_TIF = r"your_path\fc\jaxa\fc_jaxa_peru_" + str(year) + "_1ha.tif"
            if os.path.isfile(B_TIF):
                fcc.year = year
                fcc.baseline_year = int(year) - i
                break
        # Following three files are temporary files that will be deleted later
        OUT_TIF = "temp.tif"
        gdaloutputA = 'temp_A.tif'
        gdaloutputB = 'temp_B.tif'
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(
            "-of Gtiff -ot Int16"))  # Explicitly mentioning the datatype as Int16, to convert from UInt8
        a = gdal.Translate(gdaloutputA, A_TIF, options=translateoptions)
        b = gdal.Translate(gdaloutputB, B_TIF, options=translateoptions)
        a = None
        b = None
        ds1 = gdal.Open(gdaloutputA, gdalconst.GA_ReadOnly)
        ds2 = gdal.Open(gdaloutputB, gdalconst.GA_ReadOnly)

        arr1 = ds1.ReadAsArray()
        arr2 = ds2.ReadAsArray()
        if arr1.shape < arr2.shape:
            arr1 = np.resize(arr1, arr2.shape)
        else:
            arr2 = np.resize(arr2, arr1.shape)
        # subtract every value from both rasters
        result = np.subtract(arr1, arr2)
        driver = gdal.GetDriverByName("GTiff")
        output = driver.Create(OUT_TIF, ds1.RasterXSize, ds1.RasterYSize, 1, gdalconst.GDT_Int16)
        output.SetGeoTransform(ds1.GetGeoTransform())
        output.SetProjection(ds1.GetProjection())
        output.GetRasterBand(1).WriteArray(result)
        output = None
        gdalinput = OUT_TIF
        gdaloutput = r"your_path\fcc\jaxa\fcc_" + l_dataset + "_peru_" + str(
            year) + "_1ha.tif"
        translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine("-of Gtiff -ot Int16 -co COMPRESS=LZW"))
        c = gdal.Translate(gdaloutput, gdalinput, options=translateoptions)  # compresses the output file
        c = None
        end = time.time()
        totaltime = end - start
        fcc.file_name = "fcc_" + l_dataset + "_peru_" + str(year) + "_1ha.tif"
        fcc.file_directory = r"your_path\fcc\jaxa"
        fcc.fc_source = fcs
        fcc.processing_time = totaltime
        fcc.save()
        return HttpResponse("Success")
    except Exception as e:
        print(e)
        return HttpResponse(str(e))
