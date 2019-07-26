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

# Ziele
# 1. Feedin f. Landkreise berechnen und auf OEP laden
# 2. Feedin f. Übertr.netz.zonen berechnen und Validierung vornehmen


debug_mode = False  # Only 4 regions are calculated.

feedin_folder = os.path.join(
    os.path.expanduser('~'),
    'Daten_flexibel_01/Einspeisezeitreihen_open_FRED_WAM')

weather_data_folder = os.path.join(
        os.path.expanduser('~'),
        'virtualenvs/lib_validation/lib_validation/dumps/weather/')

years = [
    2013, 2014, 2015,
    2016,
    2017
]
categories = [
    'Wind',
    # 'Solar',
    # 'Hydro'  # not implemented, yet
]
register_names = [
    'opsd',
    # 'MaStR'  # only use for category 'Wind'
]
weather_data_names = [
    # 'open_FRED',
    'ERA5'
]

###############################################################################
# Upload of feed-in time series for "Landkreise" Germany
# only for open_FRED weather data
###############################################################################
# for register_name in register_names:
#     for year in years:
#         feedin = f.calculate_feedin_germany(
#             year=year, categories=categories, regions='landkreise',
#             register_name=register_name, weather_data_name='open_FRED',
#             debug_mode=debug_mode, wake_losses_model=None,
#             weather_data_folder=weather_data_folder,
#             return_feedin=True)
#         feedin.to_csv('example_feedin_wam.csv')  # todo: automatisch in WAM ordner speichern siehe oben feedin_folder

###############################################################################
# Validation of PVlib and windpowerlib feed-in time series via "tso" zones
# for open_FRED and ERA5 weather data
###############################################################################
for register_name in register_names:
    for weather_data_name in weather_data_names:
        for year in years:
            start = time.time()
            feedin = f.calculate_feedin_germany(
                year=year, categories=categories, regions='tso',
                register_name=register_name,
                weather_data_name=weather_data_name,
                return_feedin=True, debug_mode=debug_mode,
                weather_data_folder=weather_data_folder,
                wake_losses_model=None)  # todo parameter windpowerlib wählen.
            end = time.time()
            print('Time calculate_feedin_germany year {}: {}'.format(year,
                                                                (end - start)))

            # # todo delete: is for debugging
            # import pickle
            # pickle.dump(feedin, open('debug_dump.p', 'wb'))
            # feedin = pickle.load(open('debug_dump.p', 'rb'))

            # get validation feed-in time series
            start = time.time()
            val_feedin = val_data.load_feedin_data(categories, year,
                                                   latest=False)
            end = time.time()
            print('Time get_validation_data year {}: {}'.format(year, (end-start)))

            # join data frame in the form needed by calculate_validation_metrics()
            validation_df = pd.merge(left=feedin, right=val_feedin, how='left',
                                     on=['time', 'technology', 'nuts'])
            # drop entries from other years (this comes from UTC/local time stamps)
            # todo solve in feedinlib?
            validation_df = validation_df[
                validation_df['time'] >= '01-01-{}'.format(year)]
            # calculate metrics and save to file
            validation_path = cfg.get('paths', 'validation')
            if not os.path.exists(validation_path):
                os.makedirs(validation_path, exist_ok=True)
            filename = os.path.join(
                os.path.dirname(__file__), validation_path,
                cfg.get('validation', 'filename').format(
                    reg=register_name, weather=weather_data_name, year=year))
            val_tools.calculate_validation_metrics(
                df=validation_df.set_index('time'),
                val_cols=['feedin', 'feedin_val'], metrics='standard',
                filter_cols=['nuts', 'technology'],
                filename=filename)
