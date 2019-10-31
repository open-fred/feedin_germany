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
weather_data_folder = settings.weather_data_path
validation_path = settings.path_validation_metrics

years = [
    # 2013, 2014,
    # 2015,
    # 2016,
    2017
]
categories = [
    'Wind',
    # 'Solar',
    # 'Hydro'  # not implemented, yet
]
register_names = [
    # 'opsd',  # fix decommissioning date...
    'MaStR'  # only use for category 'Wind'
]
weather_data_names = [
    'open_FRED',
    # 'ERA5'
]

###############################################################################
# Calculate feed-in time series for "Landkreise" in 50 Hertz tso zone
# and save to `feedin_folder` (contains time series for all years -
# database format)
###############################################################################
region_filter = [
    'MeckPom', # todo delete
                 # 'DE8',  # Meck-Pom
                 # 'DE3',  # Berlin
                 # 'DE4',  # Brandenburg
                 # 'DED',  # Sachsen
                 # 'DEE',  # Sachsen-Anhalt
                 # 'DEG',  # Thühringen
                 # 'DE6'  # Hamburg
                 ] # filters 'regions' by nuts
                    # (f.e. ['DE8'] --> only feed-in of 'Landkreise' of
                    # Meck-Pom are calulated. Do not use
                    # if you enter your own data frame for `regions`.

for register_name in register_names:
    for nuts in region_filter:
        feedin_years = pd.DataFrame()
        for year in years:
            feedin = f.calculate_feedin_germany(
                year=year, categories=categories, regions='landkreise',
                register_name=register_name, weather_data_name='open_FRED',
                debug_mode=debug_mode, wake_losses_model=None,
                weather_data_folder=weather_data_folder,
                return_feedin=True, region_filter=region_filter)
            feedin_years = pd.concat([feedin_years, feedin])
        feedin_years.to_csv(os.path.join(
            feedin_folder, 'feedin_Landkreise_{}.csv'.format(nuts)))  # todo: if we use more registers, weather, ... add to name


###############################################################################
# Load feed-in of 'Landkreise' and sum up to 50 Hertz time series
###############################################################################
# todo noch zu testen mit pv und mit mehreren Bundesländern
feedin_df = pd.DataFrame()
for nuts in region_filter:
    # load time series of regionPom
    feedin = pd.read_csv(os.path.join(
        feedin_folder, 'feedin_Landkreise_{}.csv'.format(nuts)))
    df = f.form_feedin_for_deflex(feedin)
    feedin_df = pd.concat([feedin_df, df], axis=1)

# sum up 50 hertz feed-in by category and save to file
feedin_50hertz_df = pd.DataFrame()
for category in categories:
    # select category and sum up time series
    feedin_50hertz = feedin_df.xs(
        category.lower(), axis=1, level=1, drop_level=True).sum(axis=1)
    feedin_50hertz.name = 'feedin'
    # data base format
    feedin_50hertz = f.feedin_to_db_format(feedin_50hertz, technology=category,
                                           nuts='50 Hertz')
    feedin_50hertz_df = pd.concat([feedin_50hertz_df, feedin_50hertz])
# todo: save wind and solar separately if you want to...
feedin_50hertz_df.set_index('time').to_csv(os.path.join(
    feedin_folder, 'feedin_50Hertz.csv'))

###############################################################################
# Get validation time series 50 Hertz and save together with feed-in
###############################################################################
val_feedin_50hertz = pd.DataFrame()
for year in years:
    # get validation time series
    val_feedin_year = val_data.load_feedin_data(categories, year, latest=True)
    val_feedin_50hertz_year = val_feedin_year.loc[val_feedin_year['nuts'] == '50 Hertz']
    val_feedin_50hertz = pd.concat([val_feedin_50hertz, val_feedin_50hertz_year])

feedin_50hertz_df = pd.read_csv(os.path.join(
    feedin_folder, 'feedin_50Hertz.csv'),
    index_col=0, parse_dates=True).reset_index()

# join data frame in the form needed by
# calculate_validation_metrics()
validation_df = pd.merge(left=feedin_50hertz_df, right=val_feedin_50hertz,
                         how='left', on=['time', 'technology', 'nuts'])

validation_df.set_index('time').to_csv(os.path.join(
    feedin_folder, 'validation_df.csv'))
