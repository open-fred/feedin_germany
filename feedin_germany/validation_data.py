# -*- coding: utf-8 -*-
"""
The `validation_data` module contains functions ....

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import pandas as pd
import datetime as dt
import geopandas as gpd
import os
import logging
import requests
import io

from feedin_germany import config as cfg

def load_feedin_data(category, year, latest=False): # _from_...? todo get data

    r"""
    loads register from server

    parameters
    ----------
    'latest': boolean

    Returns
    -------
    df : pd.DataFrame
        OPSD power plant data. todo: describe most important columns with units
        For description of further columns see
        https://data.open-power-system-data.org/renewable_power_plants/.
    """

    if latest:
        url_section = 'opsd_time_series_latest'
    else:
        url_section = 'opsd_time_series_2018'

    # Download non existing files. If you think that there are newer files you
    # have to set overwrite=True to overwrite existing with downloaded files.

    logging.warning("Start downloading the register file from server.")
    logging.warning("Check URL if download does not work.")
    req = requests.get(cfg.get(url_section, 'time_series')).content

    df = pd.read_csv(io.StringIO(req.decode('utf-8')))


    df['utc_timestamp'] = pd.to_datetime(df['utc_timestamp'])
    df_year = df[df['utc_timestamp'].dt.year == year]

    if category == 'Solar':
        dpv=df_year[['utc_timestamp',
                     'DE_solar_capacity',
                     'DE_solar_generation_actual',
                     'DE_solar_profile',
                     'DE_50hertz_solar_generation_actual',
                     'DE_amprion_solar_generation_actual',
                     'DE_tennet_solar_generation_actual',
                     'DE_transnetbw_solar_generation_actual']]

        return dpv
    
    if category == 'Wind':
        dwind= df_year[['utc_timestamp','DE_wind_capacity',
       'DE_wind_generation_actual', 'DE_wind_profile',
       'DE_wind_offshore_capacity', 'DE_wind_offshore_generation_actual',
       'DE_wind_offshore_profile', 'DE_wind_onshore_capacity',
       'DE_wind_onshore_generation_actual', 'DE_wind_onshore_profile']]

        return dwind

    # load übertragunsnetz feed-in time series
    # prepare like our feed-in time series (columns: time, technology, nuts, feedin_val)
    # Zwischenspeichern ? je nachdem wie schnell...


if __name__ == "__main__":

    category='Wind'
    year=2012

    df=  load_feedin_data(category, year, latest=False)
    print(df.columns)


