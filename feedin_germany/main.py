# imports
from matplotlib import pyplot as plt

# internal imports
from feedin_germany import feedin


debug_mode = True

years = [2012]
categories = [
    #'Wind',
    'Solar',
    # 'Hydro'
]
for year in years:
        feedin = feedin.calculate_feedin_germany(
            year=year, categories=categories, regions='landkreise',
            register_name='opsd', weather_data_name='open_FRED',
            oep_upload=False, debug_mode=debug_mode, wake_losses_model=None)
        print(feedin)

        feedin.plot()
        plt.ylabel('AC Power (W)')
        plt.show()