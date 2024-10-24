# utils.py
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

def validate_file(file,type):
    from rasterio.io import MemoryFile

    with MemoryFile(file) as memfile:
        with memfile.open() as dataset:
            data_array = dataset.read()
            meta = dataset.meta
            print(meta['crs'])
            stats = dataset.statistics(bidx=1, approx=True)  # min, max, mean, std
            print(stats.min, stats.max)
            if type == 'fc' and stats.min == 0.0 and stats.max == 1.0:
                return True
            elif type == 'agb' and stats.min >= 0.0 and stats.max <= 4000.0:
                return True
            else:
                return False

def upload_tiff_to_geoserver(name, path):
    try:
        layer_name = name
        file_path = path
        os.chmod(file_path, 0o777)
        print(layer_name)
        from geo.Geoserver import Geoserver
        geo = Geoserver('https://geodata.servirglobal.net/geoserver/', username=config['GEOSERVER_USERNAME'], password=config['GEOSERVER_PASSWORD'])
        geo.create_coveragestore(layer_name=layer_name, path=file_path, workspace='s-cap')
        geo.publish_style(layer_name=layer_name + '.', style_name='fc', workspace='s-cap')
    except Exception as e:
        print(str(e))
