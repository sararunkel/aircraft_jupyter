#!/usr/bin/env python3

import xarray as xr
import numpy as np
import datetime as dt
import json
import argparse
import os
import pandas as pd

var_list = ['ATX', 'WIC', 'WDC', 'DPXC', 'PSX', 'WSC', 'GGALT']

def export_to_json(filename, project):
    base = filename.split('.')[0]
    print('Opening'+base)
    out_dir = f'/scr/raf_data/raf_visualization/data/{project}'
    ds = xr.open_dataset(f'/net/archive/data/eclipse2019/aircraft/gv_n677f/LRT/{filename}')   #f'/scr/raf_data/{project}/{filename}')
    ds['Time'] = pd.to_datetime(ds['Time'].values)

    # Filter out unwanted variables
    variables_to_drop = [
        var for var in ds.variables if len(ds[var].dims) != 1 or ds[var].dims[0] != 'Time'
    ]
    variables_to_drop += [var for var in ds.variables if 'Tdiff' in var]
    temp = ds.drop_vars(variables_to_drop).copy()
    temp = temp[var_list]
    # Drop timedelta variables that cannot be converted directly to JSON
    for var in temp.variables:
        if ds[var].dtype == 'timedelta64[ns]':
            print(f'!!!!!!!!!!!!!!!!!{var} is timedelta')
            temp = temp.drop_vars(var)

    # Format 'Time' for JSON
    temp['Time'] = temp['Time'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Fill NaNs with None to ensure compatibility with JSON
    temp = temp.fillna(value=None)

    # Convert dataset to dictionary, handling special values
    temp_dict = json.loads(json.dumps(temp.to_dict(), default=handle_special_values))
    ## Check that out_dir exists and make it if not
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print("Created directory:", out_dir)
    # Save main data JSON file
    with open(f'{out_dir}/{base}.json', 'w') as f:
        json.dump(temp_dict, f, indent=4)
    print('Saved data to JSON file')

    # Process track data
    track = ['GGLAT', 'GGLON']
    temp = ds[track]
    temp['Time'] = temp['Time'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    temp = temp.fillna(value=None)  # Replace NaNs with None

    # Convert to dictionary, handling special values
    temp_dict = json.loads(json.dumps(temp.to_dict(), default=handle_special_values))

    # Save track data JSON file
    with open(f'{out_dir}/{base}_track.json', 'w') as f:
        json.dump(temp_dict, f, indent=4)
    print('Saved track to JSON file')

# Helper function to handle special values
def handle_special_values(obj):
    if isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or obj == -32767:
            return None
    elif isinstance(obj, (np.integer, int)) and obj == -32767:
        return None
    elif isinstance(obj, (np.timedelta64, dt.timedelta)):
        return obj / np.timedelta64(1, 's')  # Convert timedelta to seconds
    return obj

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Export netCDF data to JSON.')
    parser.add_argument('project', type=str, help='Project name to output the data to.')
    args = parser.parse_args()

    # Process each netCDF file in the project directory
    for file in os.listdir('/net/archive/data/eclipse2019/aircraft/gv_n677f/LRT'): # f'/scr/{args.project}'):
        if 'WVISO' in file:
            continue
        if file.endswith("h.nc") or file.endswith('Z.nc') or file.endswith("s.nc") or file.endswith('SV.nc') or file.endswith('hrt.nc') or file.endswith('ff01.nc'):
            continue
        if file.endswith(".nc"):# and args.project in file:
            export_to_json(file, args.project)
            print(f'Exported {file} to JSON')

if __name__ == '__main__':
    main()
