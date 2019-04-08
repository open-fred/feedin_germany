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


def prepare_dates(df, date_cols, month):
    r"""
    von Uwe


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

    if month:
        df['com_month'] = pd.to_datetime(df[date_cols[0]].fillna(
            '1800-01-01')).dt.month
        df['decom_month'] = pd.to_datetime(df[date_cols[1]].fillna(
            '2050-12-31')).dt.month
    else:
        df['com_month'] = 6
        df['decom_month'] = 6

    return df


def get_pp_by_year(year, register, overwrite_capacity=True):
    """
    von Uwe

    Parameters
    ----------
    year : int
    overwrite_capacity : bool
        By default (False) a new column "capacity_<year>" is created. If set to
        True the old capacity column will be overwritten. todo changed, right? @ Inia

    Returns
    -------

    """
    pp = pd.DataFrame(register)

    filter_columns = ['capacity_{0}']

    # Get all power plants for the given year.
    # If com_month exist the power plants will be considered month-wise.
    # Otherwise the commission/decommission within the given year is not
    # considered.

    for fcol in filter_columns:
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
