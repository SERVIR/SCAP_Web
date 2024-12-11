# utils.py
import json
import os
from pathlib import Path
import zipfile
import shapefile
BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

def validate_file(file,type):
    from rasterio.io import MemoryFile

    with MemoryFile(file) as memfile:
        with memfile.open() as dataset:
            meta = dataset.meta
            print(meta['crs'])
            stats = dataset.statistics(bidx=1, approx=True)  # min, max, mean, std
            print(stats.min, stats.max)
            if type == 'fc' and stats.min == 0.0 and stats.max == 1.0:
                return True
            elif type == 'agb' and stats.min >= 0.0 and stats.max <= 4000.0:
                return True
            elif type == 'fc_boundary' or type == 'agb_boundary':
                shpname = None
                shxname = None
                dbfname = None
                # unzip the zip file to the same directory
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    for x in zip_ref.namelist():
                        if x.endswith('.shp'):
                            shpname = x
                        if x.endswith('.shx'):
                            shxname = x
                        if x.endswith('.dbf'):
                            dbfname = x
                    r = shapefile.Reader(shp=zip_ref.open(shpname),
                                         shx=zip_ref.open(shxname),
                                         dbf=zip_ref.open(dbfname), )
                    bbox = r.bbox
                    res = False
                    for x in range(len(bbox)):
                        if x == 0 or x == 2:
                            if -180.0 <= bbox[x] <= 180.0:
                                res = True
                            else:
                                res = False
                                break
                        else:
                            if -90.0 <= bbox[x] <= 90.0:
                                res = True
                            else:
                                res = False
                                break
                    if r.numShapes > 0 and res:
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
        geo = Geoserver(config['GEOSERVER_HOST'], username=config['GEOSERVER_USERNAME'], password=config['GEOSERVER_PASSWORD'])
        geo.create_coveragestore(layer_name=layer_name, path=file_path, workspace='s-cap')
        geo.publish_style(layer_name=layer_name + '.', style_name='fc', workspace='s-cap')
    except Exception as e:
        print(str(e))
