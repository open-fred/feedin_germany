# imports
import os
import pandas as pd
from matplotlib import pyplot as plt

# internal imports
from feedin_germany import feedin
from feedin_germany import config as cfg
from feedin_germany import validation_data as val_data
from feedin_germany import validation_tools as val_tools

# Ziele
# 1. Feedin f. Landkreise berechnen und auf OEP laden
# 2. Feedin f. Übertr.netz.zonen berechnen und Validierung vornehmen


debug_mode = True  # Only 4 regions are calculated.

years = [2016]
categories = [
    'Wind',
    'Solar',
    # 'Hydro'
]
register_names = [
    'opsd',
    # 'MaStR'  # only use for category 'Wind'
]
weather_data_name = 'open_FRED'

# Upload of feed-in time series for "Landkreise" Germany
# for register_name in register_names:
#     for year in years:
#        feedin = feedin.calculate_feedin_germany(
#            year=year, categories=categories, regions='landkreise',
#            register_name='opsd', weather_data_name='open_FRED',
#            oep_upload=False, debug_mode=debug_mode, wake_losses_model=None)
#        print(feedin)

        # feedin.plot()
        # plt.show()

# Validation of PVlib and windpowerlib feed-in time series via
# "Übertragungsnetzzonen"
for register_name in register_names:
    for year in years:
        feedin = feedin.calculate_feedin_germany(
            year=year, categories=categories, regions='landkreise', # todo: uebertragungsnetzzonen
            register_name=register_name, weather_data_name=weather_data_name,
            oep_upload=False, return_feedin=True, debug_mode=debug_mode,
            wake_losses_model=None)

    # # todo delete: is for debugging
    # import pickle
    # feedin = pickle.load(open('debug_dump.p', 'rb'))

        # get validation feed-in time series
        val_feedin = val_data.load_feedin_data(categories, year, latest=False)

        # join data frame in the form needed by calculate_validation_metrics()
        validation_df = pd.merge(left=feedin, right=val_feedin, how='left',
                                 on=['time', 'technology', 'nuts'])
        # calculate metrics and save to file
        validation_path = cfg.get('paths', 'validation')
        if not os.path.exists(validation_path):
            os.makedirs(validation_path, exist_ok=True)
        filename = os.path.join(os.path.dirname(__file__), validation_path,
                                cfg.get('validation', 'filename').format(
                                    reg=register_name, weather=weather_data_name,
                                    year=year))
        val_tools.calculate_validation_metrics(
            df=validation_df.set_index('time'),
            val_cols=['feedin', 'feedin_val'], metrics='standard',
            filter_cols=['nuts', 'technology'],
            filename=filename, print_out=True)
