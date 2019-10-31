from feedinlib import tools

import pandas as pd
import os
import pickle

from feedin_germany import settings as settings
settings.init()


def get_weather_data_germany(year, weather_data_name, format_):
    """

    format : str
        Options: 'windpowerlib', 'pvlib'
    path : str
        Path to where weather data csv files are located.
    """
    if weather_data_name == 'ERA5':
        filename = os.path.join(settings.weather_data_path,
                                'era5_wind_ger_{}.csv'.format(year))
        if format_ == 'windpowerlib':
            weather_df = pd.read_csv(filename, header=[0, 1],
                                     index_col=[0, 1, 2], parse_dates=True)
            weather_df.rename(columns={'wind speed': 'wind_speed'},
                              inplace=True)  # todo delete after fix in era5
            # change type of height from str to int by resetting columns
            l0 = [_[0] for _ in weather_df.columns]
            l1 = [int(_[1]) for _ in weather_df.columns]
            weather_df.columns = [l0, l1]
            # set time zone to UTC
            weather_df.index = weather_df.index.set_levels(
                weather_df.index.levels[0].tz_localize('UTC'), level=0)
        elif format_ == 'pvlib':
            weather_df = pd.read_csv(filename, header=[0, 1],
                                     index_col=0, parse_dates=True)
    elif weather_data_name == 'open_FRED':
        weather_df = load_open_fred_pkl
    return weather_df


def get_downloaded_weather_points_open_fred_pkl():
    """
    Function to get a list of all open_FRED weather data points weather
    data was downloaded for.

    Returns
    --------
    dict
        Dictionary with location IDs as keys and corresponding (lon, lat)
        tuple.

    """
    state_list = ['Mecklenburg-Vorpommern', 'Sachsen', 'Brandenburg',
                  'Sachsen-Anhalt', 'Thüringen', 'Berlin']  # + Hamburg
    locations_dict = {}
    for state in state_list:
        fname_loc = os.path.join(settings.open_FRED_pkl,
                                 "locations_dict_{}.pkl".format(state))
        if os.path.isfile(fname_loc):
            locations_dict.update(pickle.load(open(fname_loc, "rb")))
        else:
            print('No downloaded open_FRED weather data for {}.'.format(state))
    return locations_dict


def load_open_fred_pkl(lat, lon, **kwargs):
    """
    Function returns open_FRED weather dataframe for given lat and lon
    values and specified library.

    Weather data is loaded from pkl file.
    Lon and lat values must be values of the locations dictionary.

    Parameters
    ----------
    lat : float
    lon : float
    lib : str
        Defines for which library the dataframe is prepared. Must be 'pvlib'
        or 'windpowerlib'.
    year : int
        Year to retrieve data for.
    locations_dict : dict
        Dictionary with location IDs as keys and corresponding (lon, lat)
        tuple of all open_FRED weather data points weather data was downloaded
        for.

    Returns
    --------
    pandas.DataFrame

    """
    locations_dict = kwargs.get('locations_dict', None)
    if locations_dict is None:
        locations_dict = get_downloaded_weather_points_open_fred_pkl()
    lib = kwargs.get('lib', None)
    if lib is None:
        raise AttributeError("lib must either be 'pvlib' or 'windpowerlib'.")
    year = kwargs.get('year', None)
    if year is None:
        raise AttributeError("Year must be specified to retrieve open_FRED "
                             "weather data from pkl file.")

    # find location ID corresponding to lat and lon values
    try:
        location_id = (list(locations_dict.keys())[
            list(locations_dict.values()).index((lon, lat))])
    except:
        raise ValueError("No weather data downloaded for ({}, {}).".format(
            lat, lon))

    fname = os.path.join(settings.open_FRED_pkl,
                         '{}_{}.pkl'.format(location_id, year))
    open_FRED_weather = pickle.load(open(fname, "rb"))

    return open_FRED_weather.df(location=(lon, lat), lib=lib)


