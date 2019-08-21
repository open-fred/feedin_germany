# -*- coding: utf-8 -*-
"""
The `power_plant_register_tools` module contains functions preparing registers
for the feedinlib.

The code in this module is partly based on third party code which has been
licensed under GNU-LGPL3. The following functions are copied and adapted from:
https://github.com/reegis/reegis
* prepare_dates()

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import pandas as pd
import numpy as np
import logging


def prepare_dates(df, date_cols):
    r"""
    Prepare commissioning and decommissioning dates.

    Adds columns 'com_year' and 'decom_year', 'com_month' and 'decom_month'.

    Missing dates are filled as follows:
    com_year: 1800
    decom_year: 2050
    com_month: 1
    decom_month: 12

    `date_cols` are converted to_datetime() and missing dates are filled with
    com: '1800-01-01'
    decom: '2050-12-31'

    """
    # Commission year from float or string
    if df[date_cols[0]].dtype == np.float64:
        df['com_year'] = df[date_cols[0]].fillna(1800).astype(np.int64)
    else:
        df['com_year'] = pd.to_datetime(df[date_cols[0]].fillna(
            '1800-01-01')).dt.year

    # Decommission year from float or string
    if df[date_cols[1]].dtype == np.float64:
        df['decom_year'] = df[date_cols[1]].fillna(2050).astype(np.int64)
    else:
        df['decom_year'] = pd.to_datetime(df[date_cols[1]].fillna(
            '2050-12-31')).dt.year

    df['com_month'] = pd.to_datetime(df[date_cols[0]].fillna(
        '1800-01-01')).dt.month
    df['decom_month'] = pd.to_datetime(df[date_cols[1]].fillna(
        '2050-12-31')).dt.month

    # fill date_cols
    df[date_cols[0]].fillna('1800-01-01', inplace=True)
    df[date_cols[1]].fillna('2050-12-31', inplace=True)
    return df


def get_pp_by_year(year, register, overwrite_capacity=True,
                   month_wise_capacities=False):
    """
    Filter by year and scale capacity by commssioning and decommissioning month

    from Uwe

    Parameters
    ----------
    year : int
    overwrite_capacity : bool
        By default (False) a new column "capacity_<year>" is created. If set to
        True the old capacity column will be overwritten.
    month_wise_capacities : bool
        If True and com_month and decom_month exists the respective power
        plant's capacity will be reduced by the percentage of months it was
        installed during the year. Default: False.

    Notes
    -----
    If `month_wise_capacities` is True and com_month and decom_month exists the
    respective power plant's
    capacity will be reduced by the percentage of months it was installed
    during the year. Otherwise the decommissioning is considered to take place
    in the end of a year (month 12) and commissioning in the beginning of a
    year (month 1). If no decommissioning year is given it is set to 2050.

    Returns
    -------

    """
    pp = pd.DataFrame(register)

    # Set missing decom_year, decom_month and com_month values  # todo not needed if prepare_dates is used (?)
    indices = pp.loc[pp['decom_year'].isnull() == True].index
    pp['decom_year'].loc[indices] = int(2050)
    indices = pp.loc[pp['decom_month'].isnull() == True].index
    pp['decom_month'].loc[indices] = int(12)
    indices = pp.loc[pp['com_month'].isnull() == True].index
    pp['com_month'].loc[indices] = int(1)

    # Get all power plants for the given year.
    if month_wise_capacities:
        fcol = 'capacity_{0}'
        filter_column = fcol.format(year)
        orig_column = fcol[:-4]
        c1 = (pp['com_year'] < year) & (pp['decom_year'] > year)
        pp.loc[c1, filter_column] = pp.loc[c1, orig_column]

        c2 = pp['com_year'] == year
        pp.loc[c2, filter_column] = (pp.loc[c2, orig_column] *
                                     (12 - pp.loc[c2, 'com_month']) / 12)
        c3 = pp['decom_year'] == year
        pp.loc[c3, filter_column] = (pp.loc[c3, orig_column] *
                                     pp.loc[c3, 'decom_month'] / 12)

        if overwrite_capacity:
            pp[orig_column] = 0
            pp[orig_column] = pp[filter_column]
            del pp[filter_column]

        # delete all rows with com_year > year
        pp_filtered = pp.loc[pp['com_year'] < year+1]
    else:
        pp_filtered = pp.loc[(pp['com_year'] <= year) &
                             (pp['decom_year'] >= year)]

    return pp_filtered


def remove_pp_with_missing_coordinates(register, category, register_name):
    r"""
    Removes power plants with missing coordinates from register.

    Amount of removed power plants is given in a warning.

    """
    if register[['lat', 'lon']].isnull().values.any():
        amount = register[['lat', 'lon']].isnull().sum()[0]  # amount of lat
        register = register.dropna(subset=['lat', 'lon'])
        logging.warning(
            "Removed {} {} power plants with missing coordinates ".format(
                amount, category) + "from {} register". format(register_name))
    return register
