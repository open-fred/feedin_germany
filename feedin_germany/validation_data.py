# -*- coding: utf-8 -*-
"""
The `validation_data` module contains functions ....

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import pandas as pd
import os
import logging
import requests
import io

from feedin_germany import config as cfg


def load_feedin_data(categories, year, latest=True, onshore=True):

    r"""
    Get feed-in time series of tso for specified categories and year.

    Loads time series from opsd url or from file if it exists. Frequency is
    1 hour and time zone 'UTC'.

    parameters
    ----------
    'latest': boolean

    onshore : boolean
        If True only onshore wind power is used.
        ONLY for the years 2016 and 2017 (before the values of on- and offshore
        are 0)

    Returns
    -------
    df : pd.DataFrame
        OPSD feed-in time series. todo: describe most important columns with units
        For description of further columns see
        https://data.open-power-system-data.org/renewable_power_plants/.
    """
    val_dir = os.path.join(os.path.dirname(__file__), 'data/validation')
    if not os.path.exists(val_dir):
        os.makedirs(val_dir, exist_ok=True)
    filename = os.path.join(val_dir, 'tso_feedin_{}.csv'.format(year))

    if os.path.exists(filename):
        df_agg = pd.read_csv(filename)
        # to datetime
        df_agg['utc_timestamp'] = pd.to_datetime(df_agg['utc_timestamp'],
                                                 utc=True)
    else:
        if latest:
            url_section = 'opsd_time_series_latest'
        else:
            url_section = 'opsd_time_series_2018'

        logging.warning("Start downloading the register file from server.")
        logging.warning("Check URL if download does not work.")
        req = requests.get(cfg.get(url_section, 'time_series')).content

        df = pd.read_csv(io.StringIO(req.decode('utf-8')))

        df['utc_timestamp'] = pd.to_datetime(df['utc_timestamp'], utc=True)
        df_year = df[df['utc_timestamp'].dt.year == year]
        df_agg = df_year.set_index('utc_timestamp').resample('H').mean().reset_index()
        df_agg[['utc_timestamp', 'DE_50hertz_solar_generation_actual',
                'DE_amprion_solar_generation_actual',
                'DE_tennet_solar_generation_actual',
                'DE_transnetbw_solar_generation_actual',
                'DE_50hertz_wind_generation_actual',
                'DE_50hertz_wind_onshore_generation_actual',
                'DE_amprion_wind_generation_actual',
                'DE_tennet_wind_generation_actual',
                'DE_tennet_wind_onshore_generation_actual',
                'DE_tennet_wind_offshore_generation_actual',
                'DE_50hertz_wind_offshore_generation_actual',
                'DE_transnetbw_wind_generation_actual']].to_csv(filename)

    for category in categories:
        if category == 'Solar':
            dpv=df_agg[['utc_timestamp',
                         'DE_50hertz_solar_generation_actual',
                         'DE_amprion_solar_generation_actual',
                         'DE_tennet_solar_generation_actual',
                         'DE_transnetbw_solar_generation_actual']]
            dpv_new=dpv.rename(index=str, columns={"utc_timestamp": "time",
                                                   "DE_50hertz_solar_generation_actual": "50 Hertz",
                                                   "DE_amprion_solar_generation_actual": "Amprion",
                                                   "DE_tennet_solar_generation_actual": "TenneT",
                                                   "DE_transnetbw_solar_generation_actual": "Transnet BW"})

            dpv_melt=dpv_new.melt(id_vars=['time'], var_name='nuts',
                                  value_name='feedin_val')

            dpv_melt['technology'] = 'Solar'
            dpv_melt['feedin_val'] = dpv_melt['feedin_val'] * (10 ** 6)

            val_data_pv= dpv_melt[['time', 'feedin_val', 'nuts', 'technology']]

            if len(categories) > 1:
                pass
            else:
                return val_data_pv

        if category == 'Wind':
            if onshore:
                add_on = '_onshore'
            else:
                add_on = ''
            dwind= df_agg[['utc_timestamp',
                            'DE_amprion_wind_generation_actual',
                            'DE_transnetbw_wind_generation_actual',
                            'DE_50hertz_wind{}_generation_actual'.format(add_on),
                            'DE_tennet_wind{}_generation_actual'.format(add_on)]]
            dwind_new = dwind.rename(index=str, columns={
                "utc_timestamp": "time",
                'DE_50hertz_wind{}_generation_actual'.format(add_on): "50 Hertz",
                "DE_amprion_wind_generation_actual": "Amprion",
                'DE_tennet_wind{}_generation_actual'.format(add_on): "TenneT",
                "DE_transnetbw_wind_generation_actual": "Transnet BW",})

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
    years = [2016, 2017]

    for year in years:
        df=  load_feedin_data(categories, year, latest=False)
        print(df.columns)


