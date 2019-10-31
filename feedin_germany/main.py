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
# Upload of feed-in time series for "Landkreise" Germany
# only for open_FRED weather data  # todo: haven't used this part for a while. Check if everything works. Dump time series for CH.
###############################################################################
# for register_name in register_names:
#     for year in years:
#         feedin = f.calculate_feedin_germany(
#             year=year, categories=categories, regions='landkreise',
#             register_name=register_name, weather_data_name='open_FRED',
#             debug_mode=debug_mode, wake_losses_model=None,
#             weather_data_folder=weather_data_folder,
#             return_feedin=True)
#        # feedin.to_csv(os.path.join(feedin_folder, 'example_feedin_wam.csv'))  # todo: automatic saving in wam folder

###############################################################################
# Validation of PVlib and windpowerlib feed-in time series via "tso" zones
# for open_FRED and ERA5 weather data
###############################################################################
scale_to = '50 Hertz'  # scale time series to 'entsoe' or '50 Hertz' capacities
                     # or choose None for not scaling at all
commission_decommission = 'periods'  # Specifies how
                        # commission and decommission dates of power plants are
                        # handled.
                        # See :py:func:`~.feedin.calculate_feedin_germany` for
                        # more information
regions = '50 Hertz'  # 'tso' for all 4 UNB regions or '50 Hertz' for only 50hz
for register_name in register_names:
    for weather_data_name in weather_data_names:
        for year in years:
            start = time.time()
            feedin = f.calculate_feedin_germany(
                year=year, categories=categories, regions=regions,
                register_name=register_name,
                weather_data_name=weather_data_name,
                return_feedin=True, debug_mode=debug_mode,
                weather_data_folder=weather_data_folder, scale_to=scale_to,
                commission_decommission=commission_decommission,
                wake_losses_model='dena_mean', smoothing=True)
            end = time.time()
            print('Time calculate_feedin_germany year {}: {}'.format(year,
                                                                (end - start)))

            # get validation feed-in time series
            start = time.time()
            val_feedin = val_data.load_feedin_data(categories, year,
                                                   latest=False)
            end = time.time()
            print('Time get_validation_data year {}: {}'.format(year,
                                                                (end-start)))

            # join data frame in the form needed by
            # calculate_validation_metrics()
            validation_df = pd.merge(left=feedin, right=val_feedin, how='left',
                                     on=['time', 'technology', 'nuts'])
            # drop entries from other years (this comes from UTC/local time
            # stamps)
            # todo solve in feedinlib?
            validation_df = validation_df[
                validation_df['time'] >= '01-01-{}'.format(year)]

            # save time series data frame to csv
            validation_df.set_index('time').to_csv(os.path.join(
                time_series_df_folder,
                'time_series_df_50hz_{}_{}_{}.csv'.format(
                    register_name, weather_data_name, year)))

            # calculate metrics and save to file
            if not os.path.exists(validation_path):
                os.makedirs(validation_path, exist_ok=True)
            filename = os.path.join(
                os.path.dirname(__file__), validation_path,
                'validation_50Hz_{reg}_{weather}_{year}.csv'.format(
                    reg=register_name, weather=weather_data_name, year=year))
            val_tools.calculate_validation_metrics(
                df=validation_df.set_index('time'),
                val_cols=['feedin', 'feedin_val'], metrics='standard',
                filter_cols=['nuts', 'technology'],
                filename=filename)
