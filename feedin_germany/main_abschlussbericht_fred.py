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
# windpowerlib parameters
wake_losses_model = 'dena_mean'
smoothing = True  # todo: compare time series with and without smoothing?!
pv_losses_model = 'pvwatts'

###############################################################################
# Calculate feed-in time series for "Landkreise" in 50 Hertz tso zone
# and save to `feedin_folder` (contains time series for all years -
# database format)
###############################################################################
scale_to = '50 Hertz'  # scale time series to 'entsoe' or '50 Hertz' capacities
                       # or choose None for not scaling at all
                       # IMPORTANT: wind: scaling just for onshore! (todo)
decom_20 = False  # If True, life time of power plant is 20 years
                 # (if com date is given, else: 2050). todo delete if not needed, or split if not wanted for pv in feedin.py l. 396
wind_technology = 'onshore'  # or 'offshore' or not given at all. only works for wind

for weather_data_name in weather_data_names:
    for register_name in register_names:
        for year in years:
            print('Calculating feed-in for weather dataset {}, year {} and'
                  'power plant register {}.'.format(
                weather_data_name, year, register_name))
            feedin = f.calculate_feedin_germany(
                year=year, categories=categories, regions='50 Hertz',  # note: uses ÜNB shape and selects 50 Hertz shape
                register_name=register_name, weather_data_name=weather_data_name,
                debug_mode=debug_mode, wake_losses_model=wake_losses_model,
                scale_to=scale_to, return_feedin=True, decom_20=decom_20,
                wind_technology=wind_technology, smoothing=smoothing,
                pv_losses_model=pv_losses_model)
            feedin.set_index('time').to_csv(os.path.join(
                feedin_folder, 'feedin_50Hz_{}_{}_{}.csv'.format(
                    weather_data_name, register_name, year)))


###############################################################################
# Load feed-in of 'Landkreise' and sum up to 50 Hertz time series todo delete
###############################################################################
# feedin_df = pd.DataFrame()
#
# for register_name in register_names:
#     for year in years:
#         feedin = pd.read_csv(os.path.join(
#                 feedin_folder, 'feedin_Landkreise_{}_{}.csv'.format(register_name, year)))
#         df = f.form_feedin_for_deflex(feedin)
#         feedin_df = pd.concat([feedin_df, df], axis=1)
#
# # sum up 50 hertz feed-in by category and save to file
# feedin_50hertz_df = pd.DataFrame()
# for category in categories:
#     # select category and sum up time series
#     feedin_50hertz = feedin_df.xs(
#         category.lower(), axis=1, level=1, drop_level=True).sum(axis=1)
#     feedin_50hertz.name = 'feedin'
#     # data base format
#     feedin_50hertz = f.feedin_to_db_format(feedin_50hertz, technology=category,
#                                            nuts='50 Hertz')
#     feedin_50hertz_df = pd.concat([feedin_50hertz_df, feedin_50hertz])
# # todo: save wind and solar separately if you want to...
# feedin_50hertz_df.set_index('time').to_csv(os.path.join(
#     feedin_folder, 'feedin_50Hertz.csv'))

###############################################################################
# Get validation time series 50 Hertz and save together with feed-in for all years
#
# If you have calculated your time series above, you can start the script from here
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
for weather_data_name in weather_data_names:
    for register_name in register_names:
        # get calculated feed-in time series for all years
        feedin_50hertz = pd.DataFrame()
        for year in years:
            filename_feedin = os.path.join(
                feedin_folder, 'feedin_50Hz_{}_{}_{}.csv'.format(
                    weather_data_name, register_name, year))
            feedin_50hertz_year = pd.read_csv(filename_feedin,index_col=0,
                                                parse_dates=True).reset_index()
            feedin_50hertz = pd.concat([feedin_50hertz, feedin_50hertz_year])

        # join data frame in the form needed by
        # calculate_validation_metrics()
        validation_df = pd.merge(left=feedin_50hertz, right=val_feedin_50hertz,
                                 how='left', on=['time', 'technology', 'nuts'])

        validation_df.set_index('time').to_csv(os.path.join(
            feedin_folder, 'validation_df_{}_{}.csv'.format(
                weather_data_name, register_name)))

###############################################################################
# calculate metrics and save to file (for each register and each weather data)
###############################################################################

if not os.path.exists(feedin_folder):
    os.makedirs(feedin_folder, exist_ok=True)
for weather_data_name in weather_data_names:
    for register_name in register_names:
        # load validation data frame
        val_filename = os.path.join(feedin_folder, 'validation_df_{}_{}.csv'.format(
            weather_data_name, register_name))
        validation_df = pd.read_csv(val_filename, parse_dates=True, index_col=0)
        filename = os.path.join(
            feedin_folder, 'validation_metrics_50Hz_{reg}_{weather}.csv'.format(
                reg=register_name, weather=weather_data_name))
        val_tools.calculate_validation_metrics(
            df=validation_df,
            val_cols=['feedin', 'feedin_val'], metrics='standard',
            filter_cols=['nuts', 'technology'],
            filename=filename)