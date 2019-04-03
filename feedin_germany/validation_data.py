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


def load_feedin_data(categories, year, latest=False):

    r"""
    loads register from server

    parameters
    ----------
    'latest': boolean

    Returns
    -------
    df : pd.DataFrame
        OPSD feed-in time series. todo: describe most important columns with units
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
    df_agg = df.set_index('utc_timestamp').resample('30Min').sum().reset_index()


    for category in categories:
        if category == 'Solar':
            dpv=df_agg[['utc_timestamp',
                         'DE_50hertz_solar_generation_actual',
                         'DE_amprion_solar_generation_actual',
                         'DE_tennet_solar_generation_actual',
                         'DE_transnetbw_solar_generation_actual']]
            dpv_new=dpv.rename(index=str, columns={"utc_timestamp": "time",
                                                   "DE_50hertz_solar_generation_actual": "50herz",
                                                   "DE_amprion_solar_generation_actual": "amprion",
                                                   "DE_tennet_solar_generation_actual": "tennet",
                                                   "DE_transnetbw_solar_generation_actual": "transnetbw"})

            dpv_melt=dpv_new.melt(id_vars=['time'], var_name='nuts',
                                  value_name='feedin_val')

            dpv_melt['technology'] = 'Solar'
            dpv_melt['capacity'] = dpv_melt['feedin_val'] * (10 ** 6)

            val_data_pv= dpv_melt[['time', 'feedin_val', 'nuts', 'technology']]

            if len(categories) > 1:
                pass
            else: return val_data_pv

    
        if category == 'Wind':
            dwind= df_agg[['utc_timestamp',
                            'DE_50hertz_wind_generation_actual',
                            'DE_amprion_wind_generation_actual',
                            'DE_tennet_wind_generation_actual',
                            'DE_transnetbw_wind_generation_actual'
                            ]]
            dwind_new = dwind.rename(index=str, columns={"utc_timestamp": "time",
                                                     "DE_50hertz_wind_generation_actual": "50herz",
                                                     "DE_amprion_wind_generation_actual": "amprion",
                                                     "DE_tennet_wind_generation_actual": "tennet",
                                                     "DE_transnetbw_wind_generation_actual": "transnetbw"})

            dwind_melt = dwind_new.melt(id_vars=['time'], var_name='nuts',
                                    value_name='feedin_val')

            dwind_melt['technology'] = 'Wind'
            dwind_melt['feedin_val'] = dwind_melt['feedin_val'] * (10 ** 6)
            val_data_wind=dwind_melt[['time', 'feedin_val', 'nuts', 'technology']]

            if len(categories) > 1:
                pass
            else:
                return val_data_wind

    return pd.concat([val_data_pv, val_data_wind])

    # load übertragunsnetz feed-in time series
    # prepare like our feed-in time series (columns: time, technology, nuts, feedin_val)
    # Zwischenspeichern ? je nachdem wie schnell...


if __name__ == "__main__":

    categories=['Wind', 'Solar']
    year=2012

    df=  load_feedin_data(categories, year, latest=False)
    print(df.columns)


