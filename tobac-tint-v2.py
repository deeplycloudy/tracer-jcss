import argparse

parse_desc = """Create a tracked cell dataset using TOBAC/TINT v2 from gridded
NetCDF data. Saves a new NetCDF file.
"""

output_filename_help = """ Filename, including path, to use when writing data.
 If the filename includes {start} or {end} they will be replaced with the
 min and max times along the time dimension of the gridded dataset.
 Defaults to 'track_{start}_{end}.nc'
"""

default_track_params = {'FIELD_THRESH': 32,
 'ISO_THRESH': 8,
 'ISO_SMOOTH': 3,
 'MIN_SIZE': 8,
 'SEARCH_MARGIN': 4000,
 'FLOW_MARGIN': 10000,
 'MAX_DISPARITY': 999,
 'MAX_FLOW_MAG': 50,
 'MAX_SHIFT_DISP': 15,
 'GS_ALT': 1500}


def create_parser():
    parser = argparse.ArgumentParser(description=parse_desc)
    requiredNamed = parser.add_argument_group('required named arguments')
    optionalNamed = parser.add_argument_group('optional named arguments')

    parser.add_argument(dest='filenames',metavar='filename', nargs='*')
    requiredNamed.add_argument('-f', '--field', metavar='variable',
                        dest='track_field', action='store',
                        help='NetCDF variable to use for tracking')
    optionalNamed.add_argument('-o', '--outfile',
                        metavar='filename',
                        required=False, dest='outdir', action='store',
                        default='track_{start}_{end}.nc',
                        help=output_filename_help)
    optionalNamed.add_argument('-t', '--threshold', metavar='value', required=False,
                        dest='FIELD_THRESH', action='store', type=float,
                        help='Threshold value for tracking field, '
                             'default={FIELD_THRESH}'.format(**default_track_params))
    optionalNamed.add_argument('--isothresh', metavar='value', required=False,
                        dest='ISO_THRESH', action='store', type=float,
                        help='Isolation threshold for tracking field, '
                             'default={ISO_THRESH}'.format(**default_track_params))
    optionalNamed.add_argument('--isosmooth', metavar='value', required=False,
                        dest='ISO_SMOOTH', action='store', type=float,
                        help='Isolation smoothing for tracking field, '
                             'default={ISO_SMOOTH}'.format(**default_track_params))
    optionalNamed.add_argument('--minsize', metavar='value', required=False,
                        dest='MIN_SIZE', action='store', type=float,
                        help='Minimum size, '
                             'default={MIN_SIZE}'.format(**default_track_params))
    optionalNamed.add_argument('-d', '--searchmargin', metavar='value', required=False,
                        dest='SEARCH_MARGIN', action='store', type=float,
                        help='Search margin (m), '
                             'default={SEARCH_MARGIN}'.format(**default_track_params))
    optionalNamed.add_argument('--flowmargin', metavar='value', required=False,
                        dest='FLOW_MARGIN', action='store', type=float,
                        help='Flow margin (m), '
                             'default={FLOW_MARGIN}'.format(**default_track_params))
    optionalNamed.add_argument('--disparitymax', metavar='value', required=False,
                        dest='MAX_DISPARITY', action='store', type=float,
                        help='Maximum disparity, '
                             'default={MAX_DISPARITY}'.format(**default_track_params))
    optionalNamed.add_argument('--shiftdispmax', metavar='value', required=False,
                        dest='MAX_SHIFT_DISP', action='store', type=float,
                        help='Maximum shift disp., '
                             'default={MAX_SHIFT_DISP}'.format(**default_track_params))
    optionalNamed.add_argument('--flowmax', metavar='value', required=False,
                        dest='MAX_FLOW_MAG', action='store', type=float,
                        help='Maximum flow magnitude, '
                             'default={MAX_FLOW_MAG}'.format(**default_track_params))
    optionalNamed.add_argument('-z', '--altitude', metavar='value', required=False,
                        dest='GS_ALT', action='store', type=float,
                        help='Altitude to use for tracking (m), '
                             'default={GS_ALT}'.format(**default_track_params))
    # parser.add_argument('--start', metavar='yyyymmdd_hhmmss', required=True,
    #                     dest='start', action='store',
    #                     help='UTC start time, e.g., 20170704_080000')
    # parser.add_argument('--end', metavar='yyyymmdd_hhmmss', required=True,
    #                     dest='end', action='store',
    #                     help='UTC start time, e.g., 20170704_090000')
    return parser

# End parsing #


import os
from copy import deepcopy
import pandas as pd

def compress_all(nc_grids, min_dims=2):
    for var in nc_grids:
        if len(nc_grids[var].dims) >= min_dims:
            # print("Compressing ", var)
            nc_grids[var].encoding["zlib"] = True
            nc_grids[var].encoding["complevel"] = 4
            nc_grids[var].encoding["contiguous"] = False
    return nc_grids


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    track_params = deepcopy(default_track_params)
    track_param_names = list(track_params.keys())
    for k in track_param_names:
        k_val = getattr(args, k)
        if k_val is not None: track_params[k] = k_val
    print(track_params)

    from tobac.themes import tint

    nc_grid = tint.io.load_cfradial_grids(args.filenames)
    # print(nc_grid)
    tracks = tint.make_tracks(nc_grid, args.track_field, params=track_params)

    outdir = args.outdir
    dataset_name = outdir.format(
        start = pd.to_datetime(tracks.time.min().data).strftime('%Y%m%d%H%M%S'),
        end = pd.to_datetime(tracks.time.max().data).strftime('%Y%m%d%H%M%S'))

    compress_all(tracks).to_netcdf(dataset_name)




    # Copy over coordinate data, and fix swapped cell_mask coordinates.
    # tracks2=tracks.swap_dims({'x':'y2', 'y':'x2'}).rename_dims({'x2':'x', 'y2':'y'})
    # tracks2['x']=nc_grid['x']
    # tracks2['y']=nc_grid['y']
    # tracks2['z']=nc_grid['z']