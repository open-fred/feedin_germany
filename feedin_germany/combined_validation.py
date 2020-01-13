# imports
import os
import pandas as pd
from matplotlib import pyplot as plt
import time

# internal imports
from feedin_germany import feedin as f
from feedin_germany import config as cfg
from feedin_germany import validation_data as val_data
from feedin_germany import validation_tools as val_tools
import settings

# Ziele
# 1. Feedin f. Landkreise berechnen und auf OEP laden
# 2. Feedin f. Übertr.netz.zonen berechnen und Validierung vornehmen

debug_mode = False  # Only 4 regions are calculated.

# define folders
settings.init()  # note: set your paths in settings.py
feedin_folder = settings.path_wam_ezr
time_series_df_folder = settings.path_time_series_50_Hz
# validation_path = settings.path_validation_metrics  # /AP7 Community/paper_data

years = [
    # 2013, 2014,
    # 2015,
    2016,
    2017
]
categories = [
    'Wind',
    'Solar',
    # 'Hydro'  # not implemented, yet
]
register_names = [
    'opsd',  # fix decommissioning date...
    'MaStR'  # only use for category 'Wind'
]
weather_data_names = [
    'open_FRED',
    'ERA5'
]

smoothing = [
    True,
    False
]

# folder structure
if not os.path.exists(feedin_folder):
    os.makedirs(feedin_folder, exist_ok=True)
validation_df_folder = os.path.join(feedin_folder, 'validation_dfs')
if not os.path.exists(validation_df_folder):
    os.makedirs(validation_df_folder, exist_ok=True)
val_metrics_folder = os.path.join(feedin_folder,
                                  'validation_metrics')
if not os.path.exists(val_metrics_folder):
    os.makedirs(val_metrics_folder, exist_ok=True)

###############################################################################
# Get validation time series 50 Hertz and save together with feed-in for all years
###############################################################################

# get validation time series for all years
val_feedin_50hertz = pd.DataFrame()
for year in years:
    val_feedin_year = val_data.load_feedin_data(categories, year, latest=True)
    val_feedin_50hertz_year = val_feedin_year.loc[
        val_feedin_year['nuts'] == '50 Hertz']
    val_feedin_50hertz = pd.concat(
        [val_feedin_50hertz, val_feedin_50hertz_year])

# load feed-in and validation time series into one data frame
for category in categories:
    combined_df = pd.DataFrame()
    for smooth in smoothing:
        if category == 'Solar' and smooth:
            pass
        else:
            for weather_data_name in weather_data_names:
                for register_name in register_names:
                    # get calculated feed-in time series for all years
                    feedin_50hertz = pd.DataFrame()
                    for year in years:
                        if category == 'Wind':
                            if smooth:
                                add_on = '_smoothed'
                            else:
                                add_on = ''
                            filename_feedin = os.path.join(
                                feedin_folder, category,
                                'feedin_50Hz_{}_{}_{}{}.csv'.format(
                                    weather_data_name, register_name, year,
                                    add_on))
                        else:
                            filename_feedin = os.path.join(
                                feedin_folder, category, 'feedin_50Hz_{}_{}_{}.csv'.format(
                                    weather_data_name, register_name, year))
                        feedin_50hertz_year = pd.read_csv(filename_feedin,index_col=0,
                                                            parse_dates=True).reset_index()
                        feedin_50hertz = pd.concat([feedin_50hertz, feedin_50hertz_year])

                    feedin_50hertz['register'] = register_name
                    feedin_50hertz['weather'] = weather_data_name
                    if category == 'Wind':
                        feedin_50hertz['smoothing'] = smooth

                    # join data frame in the form needed by
                    # calculate_validation_metrics()
                    validation_df = pd.merge(left=feedin_50hertz, right=val_feedin_50hertz,
                                             how='left',
                                             on=['time', 'technology', 'nuts'])
                    if category == 'Wind':
                        val_filename = os.path.join(
                            validation_df_folder,
                            'validation_df_{}_{}_{}{}.csv'.format(
                                category, weather_data_name, register_name, add_on))
                    else:
                        val_filename = os.path.join(
                        validation_df_folder, 'validation_df_{}_{}_{}.csv'.format(
                            category, weather_data_name, register_name))
                    validation_df.set_index('time').to_csv(val_filename)
                    combined_df = pd.concat([combined_df, validation_df])

    combined_df.set_index('time', inplace=True)
    # combined_df.to_csv('...')

    # calculate metrics and save to file
    if category == 'Wind':
        filter_cols = ['weather', 'register', 'smoothing'
                     # 'nuts', 'technology'
                     ]
    else:
        filter_cols = ['weather', 'register',
                       # 'nuts', 'technology'
                       ]
    filename = os.path.join(
        val_metrics_folder, 'validation_metrics_50Hz_{cat}.csv'.format(
            cat=category))
    val_tools.calculate_validation_metrics(
        df=combined_df,
        val_cols=['feedin', 'feedin_val'], metrics='standard',
        filter_cols=filter_cols,
        filename=filename)