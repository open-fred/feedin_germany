# imports
import os
from matplotlib import pyplot as plt

# internal imports
from feedin_germany import feedin

# Ziele
# 1. Feedin f. Landkreise berechnen und auf OEP laden
# 2. Feedin f. Übertr.netz.zonen berechnen und Validierung vornehmen


debug_mode = True  # Only 4 regions are calculated.

years = [2012]
categories = [
    #'Wind',
    'Solar',
    # 'Hydro'
]

# todo f. später evtl functions oder loops, sodass ein oder das andere gemacht wird;
#  auswählbar, je nachdem was noch umgesetzt wird; opsd/mastr, versch. parameter der pvlib/windpowerlib

# Upload of feed-in time series for "Landkreise" Germany
for year in years:
        feedin = feedin.calculate_feedin_germany(
            year=year, categories=categories, regions='landkreise',
            register_name='opsd', weather_data_name='open_FRED',
            oep_upload=False, debug_mode=debug_mode, wake_losses_model=None)
        print(feedin)

        feedin.plot()
        plt.ylabel('AC Power (W)')
        plt.show()