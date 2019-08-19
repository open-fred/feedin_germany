
from feedinlib import tools

import pandas as pd
import os


def get_weather_data_germany(year, weather_data_name, format_, path):
    """

    format : str
        Options: 'windpowerlib', 'pvlib'
    path : str
        Path to where weather data csv files are located.
    """
    if weather_data_name == 'ERA5':
        if format_ == 'windpowerlib':
            filename = os.path.join(path, 'era5_wind_ger_{}.csv'.format(year))
            weather_df = pd.read_csv(filename, header=[0, 1],
                                     index_col=[0, 1, 2], parse_dates=True)
            weather_df.rename(columns={'wind speed': 'wind_speed'}, inplace=True)  # todo delete after fix in era5
            # change type of height from str to int by resetting columns
            l0 = [_[0] for _ in weather_df.columns]
            l1 = [int(_[1]) for _ in weather_df.columns]
            weather_df.columns = [l0, l1]
            # set time zone to UTC
            weather_df.index = weather_df.index.set_levels(
                weather_df.index.levels[0].tz_localize('UTC'), level=0)
        elif format_ == 'pvlib':
            filename = os.path.join(path, 'era5_pv_ger_{}.csv'.format(year))
            weather_df = pd.read_csv(filename, header=[0, 1],
                                     index_col=0, parse_dates=True)
    if weather_data_name == 'open_FRED':
        if format_ == 'windpowerlib':
            # filename = os.path.join(path, 'of_wind_ger_{}.csv'.format(year))
            filename = os.path.join(
                '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/',
                'fred_data_2016_sh.csv')
            weather_df = tools.example_weather_wind(filename)
        elif format_ == 'pvlib':
            # filename = os.path.join(path, 'of_pv_ger_{}.csv'.format(year))
            filename = os.path.join(
                '~/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/',
                'fred_data_test_2016.csv')
            weather_df = pd.read_csv(filename, skiprows=range(1, 50),
                                     nrows=(5000), index_col=0,
                                     date_parser=lambda idx: pd.to_datetime(
                                         idx, utc=True))
            weather_df.index = pd.to_datetime(weather_df.index, utc=True)
            # calculate ghi
            weather_df['ghi'] = weather_df.dirhi + weather_df.dhi
            weather_df = weather_df.dropna()

    return weather_df