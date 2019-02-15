import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
import pickle
import os


def get_weather_data(weather_data_name, coordinates, pickle_load=False,
                     filename='pickle_dump.p', year=None,
                     temperature_heights=None):
    r"""
    Gets MERRA-2 or open_FRED weather data for the specified coordinates.
    Parameters
    ----------
    weather_data_name : String
        String specifying if open_FRED or MERRA data is retrieved in case
        `pickle_load` is False.
    coordinates : List
        List of coordinates [lat, lon] of location for loading data.
    pickle_load : Boolean
        True if data has already been dumped before. Default: False.
    filename : String
        Name (including path) of file to load data from or if MERRA data is
        retrieved function 'create_merra_df' is used. Default: 'pickle_dump.p'.
    year : int
        Specifies which year the weather data is retrieved for. Default: None.
    temperature_heights : List
        Contains heights for which the temperature of the MERRA-2 data shall be
        calculated. Default: None (as not needed for open_FRED data).
    Returns
    -------
    weather_df : pandas.DataFrame
        Weather data with datetime index and data like temperature and
        wind speed as columns.
    """
    if pickle_load:
        data_frame = pickle.load(open(filename, 'rb'))
    else:
        if weather_data_name == 'MERRA':
            data_frame = get_merra_data(
                year, heights=temperature_heights,
                filename=filename, pickle_load=pickle_load)
        if weather_data_name == 'open_FRED':
            fred_path = os.path.join(
                os.path.dirname(__file__), 'data/open_FRED',
                'fred_data_{0}_sh.csv'.format(year))
            data_frame = get_open_fred_data(
                year, filename=fred_path, pickle_filename=filename)
        pickle.dump(data_frame, open(filename, 'rb'))
    # Find closest coordinates to weather data point and create weather_df
    closest_coordinates = get_closest_coordinates(data_frame, coordinates)
    # print(closest_coordinates)
    data_frame = data_frame
    data_frame.sortlevel(inplace=True)
    # Select coordinates from data frame
    weather_df = data_frame.loc[(slice(None),
                                 [closest_coordinates['lat']],
                                 [closest_coordinates['lon']]), :].reset_index(
                                    level=[1, 2], drop=True)
    if weather_data_name == 'open_FRED':
        # Localize open_FRED data index
        weather_df.index = weather_df.index.tz_localize('UTC')
    # Add frequency attribute
    freq = pd.infer_freq(weather_df.index)
    weather_df.index.freq = pd.tseries.frequencies.to_offset(freq)
    # Convert index to local time zone
    weather_df.index = weather_df.index.tz_convert('Europe/Berlin')
    return weather_df


def return_unique_pairs(df, column_names):
    r"""
    Returns all unique pairs of values of DataFrame `df`.

    Returns
    -------
    pd.DataFrame
        Columns (`column_names`) contain unique pairs of values.

    """
    return df.groupby(column_names).size().reset_index().drop([0], axis=1)


def get_closest_coordinates(df, coordinates, column_names=['lat', 'lon']):
    r"""
    Finds the coordinates of a data frame that are closest to `coordinates`.

    Returns
    -------
    pd.Series
        Contains closest coordinates with `column_names`as indices.

    """
    coordinates_df = return_unique_pairs(df, column_names)
    tree = cKDTree(coordinates_df)
    dists, index = tree.query(np.array(coordinates), k=1)
    return coordinates_df.iloc[index]
