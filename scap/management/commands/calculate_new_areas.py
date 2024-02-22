import sys
import os
from django.core.management.base import BaseCommand
from scap.models import AOI, ForestCoverChangeNew, BoundaryFiles, ForestCoverChange
import json
import numpy as np
from osgeo import gdal, osr, ogr
from scap.reproject import reproject_gtiff
import scap.calculate_area_new as new_calcs
from pathlib import Path
import re
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
config = json.load(open(str(BASE_DIR) + '/data.json', ))

class Command(BaseCommand):
    help = ''

    # Function Handler
    def handle(self, *args, **options):
        datasets = os.listdir(os.path.join(config['DATA_DIR'], 'fc'))
        for l_dataset in datasets:
            # TODO change when we go global
            needed_aois = AOI.objects.all()
            
            fc_data_dir = os.path.join(config['DATA_DIR'], 'fc', l_dataset)
            fcc_data_dir = os.path.join(config['DATA_DIR'], 'fcc', l_dataset)

            fc_datasets = os.listdir(fc_data_dir)
            for fc_dataset in fc_datasets:
                if 'REPROJECTED' in fc_dataset:
                    continue
                baseline_year = re.search('\\d{4}', fc_dataset)
                if baseline_year:
                    baseline_year = baseline_year.group(0)
                else:
                    continue
                change_year = int(baseline_year) + 1
                fcc_dataset = 'fcc_' + l_dataset + '_peru_' + str(change_year) + '_1ha.tif'

                fc_source = os.path.join(fc_data_dir, fc_dataset)
                fcc_source = os.path.join(fcc_data_dir, fcc_dataset)

                if not os.path.isfile(fcc_source):
                    continue

                print("Reprojecting {}".format(fc_source))
                reprojected_fc_source = reproject_gtiff(fc_source)
                print("Reprojecting {}".format(fcc_source))
                reprojected_fcc_source = reproject_gtiff(fcc_source)

                for aoi in needed_aois:
                    try:
                        start = time.time()
                        aoi_raster_path, row_offset, col_offset = new_calcs.rasterize_aoi(aoi, reprojected_fc_source)
                        print(aoi_raster_path, row_offset, col_offset)
                        fc_area = new_calcs.get_fc_area(reprojected_fc_source, aoi_raster_path, row_offset, col_offset)
                        fc_loss_area = new_calcs.get_change_area(reprojected_fcc_source, aoi_raster_path,
                                                                 'loss', row_offset, col_offset)
                        fc_gain_area = new_calcs.get_change_area(reprojected_fcc_source, aoi_raster_path,
                                                                 'gain', row_offset, col_offset)

                        end = time.time()
                        model_row = ForestCoverChangeNew()
                        model_row.fc_filename = l_dataset
                        model_row.aoi = aoi
                        model_row.year = change_year
                        model_row.baseline_year = baseline_year
                        model_row.initial_forest_area = fc_area
                        model_row.forest_gain = fc_gain_area
                        model_row.forest_loss = fc_loss_area
                        model_row.processing_time = (end - start)

                        boundary_name = l_dataset.upper() if l_dataset != 'mapbiomas' else l_dataset.capitalize()
                        boundary_file = BoundaryFiles.objects.get(name_es=boundary_name)
                        prev_calc = ForestCoverChange.objects.filter(fc_source=boundary_file, year=change_year,
                                                                     baseline_year=baseline_year, aoi=aoi).first()
                        if prev_calc:
                            model_row.speedup = prev_calc.processing_time / (end - start) 

                        model_row.save()
                    except Exception as error:
                        exc_type, exc_obj, exc_tb = sys.exc_info()

                        print('Uncaught exception for AOI {} at line {}: {}'.format(aoi.name, exc_tb.tb_lineno, error))
