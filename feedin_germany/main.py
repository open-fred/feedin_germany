# imports
from matplotlib import pyplot as plt

# internal imports
from feedin_germany import feedin
from feedin_germany import config as cfg
from feedin_germany import validation_data as val_data
from feedin_germany import validation_tools as val_tools


debug_mode = True

years = [2012]
categories = [
    'Wind',
    # 'Solar',
    # 'Hydro'
]
for year in years:
        feedin = feedin.calculate_feedin_germany(
            year=year, categories=categories, regions='landkreise',
            register_name='opsd', weather_data_name='open_FRED',
            oep_upload=True, debug_mode=debug_mode, wake_losses_model=None)
        print(feedin)

        # feedin.plot()
        # plt.show()

# Validation of PVlib and windpowerlib feed-in time series via
# "Übertragungsnetzzonen"
# parameters for validation
register_name = 'opsd'
weather_data_name = 'open_FRED'
for year in years:
    feedin = feedin.calculate_feedin_germany(
        year=year, categories=categories, regions='landkreise', # todo: uebertragungsnetzzonen
        register_name=register_name, weather_data_name=weather_data_name,
        oep_upload=True, debug_mode=debug_mode, wake_losses_model=None)

    # get validation feed-in time series
    # val_feedin = val_data.load_feedin_data()  # todo adapt
    val_feedin = feedin.rename(columns={'feedin': 'feedin_val'}) # todo delete

    # join data frame in the form needed by calculate_validation_metrics()
    validation_df = feedin  # todo!!

    # calculate metrics and save to file
    filename = os.path.join(os.path.dirname(__file__),
                            cfg.get('paths', 'validation'),
                            cfg.get('validation', 'filename').format(
                                reg=register_name, weather=weather_data_name,
                                year=year))
    val_tools.calculate_validation_metrics(
        df=validation_df, val_cols=['feedin', 'feedin_val'],
        metrics='standard', filter_cols=['nuts', 'technology'],
        filename=filename, print_out=True)