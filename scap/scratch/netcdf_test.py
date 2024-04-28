import xarray as xr
import numpy as np
import netCDF4
import rasterio
import datetime
import pandas as pd
import os

from collections import OrderedDict

def test_load(source, final_load_path):
    year = 2000
    variable_name = 'agb'
    with xr.open_dataset(source, engine="rasterio", chunks=dict(band=1,x=256, y=256)) as file:
        ds = file.isel(band=0, x=slice(0,1000), y=slice(0,1000)).rename({'band_data': variable_name})

        # Set default timestamps
        start_time = datetime.datetime.strptime('{}{}{}'.format(year, 1, 1), '%Y%m%d')
        end_time = datetime.datetime.strptime('{}{}{}'.format(year, 12, 31), '%Y%m%d')
        ds_time_index = datetime.datetime.strptime('{}{}{}'.format(year, 12, 31), '%Y%m%d')
        epoch_time = datetime.datetime(1970, 1, 1)

        # Add the time dimension as a new coordinate.
        print('Assigning times')
        ds = ds.assign_coords(time=ds_time_index).expand_dims(dim='time', axis=0)
        ds['time_bnds'] = xr.DataArray([[start_time, end_time]], dims=['time', 'nbnds'])
        print('Times assigned')
        # 3) Rename and add attributes to this dataset.
        print('Assinging lat/lon')
        ds = ds.rename({'y': 'latitude', 'x': 'longitude'})
        ds = ds.assign_coords(latitude=np.around(ds.latitude.values, decimals=6),
                              longitude=np.around(ds.longitude.values, decimals=6))
        print('Assinged lat/lon')

        # 4) Reorder latitude dimension into ascending order
        if ds.latitude.values[1] - ds.latitude.values[0] < 0:
            print('Reordering lat/lon')
            ds = ds.reindex(latitude=ds.latitude[::-1])
            print('Reordered lat/lon')

        lat_attr = OrderedDict([('long_name', 'latitude'), ('units', 'degrees_north'), ('axis', 'Y')])
        lon_attr = OrderedDict([('long_name', 'longitude'), ('units', 'degrees_east'), ('axis', 'X')])

        time_attr = OrderedDict([('long_name', 'time'), ('axis', 'T'), ('bounds', 'time_bnds')])
        time_bounds_attr = OrderedDict([('long_name', 'time_bounds')])

        metadata_dict = {'description': 'Filler', 'contact': 'Contact Filler', 'version': '1', 'reference': 'Reference',
                         'temporal_resolution': 'Resolution', 'spatial_resolution': 'Spatial Resolution', 'source': 'None',
                         'south': np.min(ds.latitude.values), 'north': np.max(ds.latitude.values),
                         'east': np.max(ds.longitude.values), 'west': np.min(ds.longitude.values)}

        file_attr = OrderedDict([('Description', metadata_dict['description']),
                                 ('DateCreated', pd.Timestamp.now().strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('Contact', metadata_dict['contact']),
                                 ('Source', metadata_dict['source']),
                                 ('Version', metadata_dict['version']),
                                 ('Reference', metadata_dict['reference']),
                                 ('RangeStartTime', datetime.date(year=year, month=1, day=1).strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('RangeEndTime', datetime.date(year=year, month=12, day=31).strftime('%Y-%m-%dT%H:%M:%SZ')),
                                 ('SouthernmostLatitude', metadata_dict['south']),
                                 ('NorthernmostLatitude', metadata_dict['north']),
                                 ('WesternmostLongitude', metadata_dict['west']),
                                 ('EasternmostLongitude', metadata_dict['east']),
                                 ('TemporalResolution', metadata_dict['temporal_resolution']),
                                 ('SpatialResolution', metadata_dict['spatial_resolution'])])


        time_encoding = {'units': 'seconds since 1970-01-01T00:00:00Z', 'dtype': np.dtype('int32')}
        time_bounds_encoding = {'units': 'seconds since 1970-01-01T00:00:00Z', 'dtype': np.dtype('int32')}

        print('Assigning attributes')
        # Set the Attributes
        ds.latitude.attrs = lat_attr
        ds.longitude.attrs = lon_attr
        print('Assigning time attributes')
        ds.time.attrs = time_attr
        ds.time_bnds.attrs = time_bounds_attr
        ds.time.encoding = time_encoding
        ds.time_bnds.encoding = time_bounds_encoding

        print('Assigning file attributes')
        ds.attrs = file_attr

        var_attrs = OrderedDict([('long_name', 'Dataset'),
                                 ('units', 'None'),
                                 ('accumulation_interval', 'yearly'),
                                 ('comment', 'SCAP Dataset')])# TODO
        ds[variable_name].attrs = var_attrs

        ds_dtype = ds[variable_name].dtype
        ds[variable_name].encoding = OrderedDict([('dtype', ds_dtype),
                                                  ('_FillValue', np.zeros(1,ds_dtype)[0]),
                                                  ('chunksizes', (1, 256, 256)),
                                                  ('missing_value', np.zeros(1,ds_dtype)[0]),
                                                  ('zlib', True),
                                                  ('complevel', 5)])# TODO

        print('To netcdf')
        if os.path.isfile(final_load_path):
            os.remove(final_load_path)

        start_time = (start_time - epoch_time).total_seconds()
        end_time = (end_time - epoch_time).total_seconds()
        ds_time_index = (ds_time_index - epoch_time).total_seconds()

        with netCDF4.Dataset(final_load_path, 'w', format='NETCDF4') as ncd:
            # Create variables, add encodings, attributes, coordinate variables
            ncd.createDimension('latitude', len(ds['latitude']))
            ncd.createDimension('longitude', len(ds['longitude']))
            ncd.createDimension('time', None)
            ncd.createDimension('nbnds', 2)

            latitude = ncd.createVariable('latitude', ds['latitude'][0].dtype, ('latitude',))
            latitude.setncatts(lat_attr)
            latitude = ds.latitude

            print(len(ds.latitude))
            print(len(ds.longitude))

            longitude = ncd.createVariable('longitude', ds['longitude'][0].dtype, ('longitude',))
            longitude.setncatts(lon_attr)
            longitude = ds.longitude

            time = ncd.createVariable('time', np.dtype('int32'), ('time',))
            time.setncatts(time_attr)
            time.units = "seconds since 1970-01-01T00:00:00Z"
            time[0] = ds_time_index

            ncd.createVariable('nbnds', int, ('nbnds',))

            variable = ncd.createVariable(variable_name, ds_dtype, ('time', 'latitude', 'longitude'), chunksizes=(1, 256, 256), fill_value=np.zeros(1,ds_dtype)[0], zlib=True, complevel=5)
            variable.setncatts(var_attrs)

            time_bnds = ncd.createVariable('time_bnds', np.dtype('int32'), ('time','nbnds',))
            time_bnds.setncatts(time_bounds_attr)
            time_bnds.units = "seconds since 1970-01-01T00:00:00Z"
            time_bnds[0][0] = start_time
            time_bnds[0][1] = end_time

            ncd.sync()

            all_blocks = ds[variable_name].data.blocks
            _, lat_offset, _ = all_blocks[0,0,-1].shape

            (time_bcount, lat_bcount, long_bcount) = all_blocks.shape
            total_blocks = (time_bcount*lat_bcount*long_bcount)
            print("Total blocks: {}".format(total_blocks))
            for lat_i in range(lat_bcount):
                for long_i in range(long_bcount):
                    i = lat_i * long_bcount + long_i
                    print("Currently processing chunk {} of {}".format(i, total_blocks))
                    # Write chunk
                    block = all_blocks[0, lat_i, long_i]
                    print(block)
                    cor_lat_i = (lat_i - 1) * 256 + lat_offset if lat_i else 0
                    cor_long_i = long_i * 256
                    _, lat_len, long_len = block.shape
                    print(block.compute())
                    
                    variable[0][cor_lat_i : cor_lat_i+lat_len][cor_long_i : cor_long_i+long_len] = block.compute()
                    if i % 25000 == 24999:
                        print("Syncing and clearing temp buffer")
                        ncd.sync()

            # Write global attributes
            ncd.setncatts(file_attr)
            
        
        print('Done Computing')
        ds = None
