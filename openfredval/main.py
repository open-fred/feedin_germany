#!/usr/bin/env python2

################ openfredval ################


# -*- coding: utf-8 -*-
"""
Created on Thu Jan 24 11:41:21 2019

@author: RL-INSTITUT\inia.steinbach
"""

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  3 16:59:27 2019

@author: RL-INSTITUT\inia.steinbach
"""

# Python libraries
import os
import logging
import warnings
import calendar
from collections import namedtuple

# External libraries
import pandas as pd

# internal modules
import reegis.config as cfg
import feedin


def scenario_feedin_pv(year, my_index, weather_year=None):    
    if weather_year is None:
        weather_year = year
    
    pv_types = cfg.get_dict('pv_types')
    pv_orientation = cfg.get_dict('pv_orientation')
    pv = feedin.get_openfredval_feedin(year, 'solar', weather_year)

    # combine different pv-sets to one feed-in time series
    feedin_ts = pd.DataFrame(columns=my_index, index=pv.index)
    orientation_fraction = pd.Series(pv_orientation)

    pv.sort_index(1, inplace=True)
    orientation_fraction.sort_index(inplace=True)
    base_set_column = 'coastdat_{0}_solar_{1}'.format(weather_year, '{0}')
    for reg in pv.columns.levels[0]:
        feedin_ts[reg, 'solar'] = 0
        for mset in pv_types.keys():
            set_col = base_set_column.format(mset)
            feedin_ts[reg, 'solar'] += pv[reg, set_col].multiply(
                orientation_fraction).sum(1).multiply(
                    pv_types[mset])
            # feedin_ts[reg, 'solar'] = rt
    # print(f.sum())
    # from matplotlib import pyplot as plt
    # f.plot()
    # plt.show()
    # exit(0)
    return feedin_ts.sort_index(1)

# def scenario_feedin_wind(year, my_index, weather_year=None):
#     """
#
#     Parameters
#     ----------
#     year
#     name
#     regions
#     feedin_ts
#     weather_year
#
#     Returns
#     -------
#
#     """
#     # Get fraction of windzone per region
#     wz = pd.read_csv(os.path.join(cfg.get('paths', 'powerplants'),
#                                   'windzone_{0}.csv'.format(name)),
#                      index_col=[0])
#
#     # Get normalised feedin time series
#     wind = feedin.get_openfredval_feedin(year=year, feedin_type='wind',
#                                          weather_year=weather_year)
#
#     if weather_year is not None:
#         if calendar.isleap(weather_year) and not calendar.isleap(year):
#             wind = wind.iloc[:8760]
#
#     # Rename columns and remove obsolete level
#     wind.columns = wind.columns.droplevel(2)
#     cols = wind.columns.get_level_values(1).unique()
#     rn = {c: c.replace('coastdat_2014_wind_', '') for c in cols}
#     wind.rename(columns=rn, level=1, inplace=True)
#     wind.sort_index(1, inplace=True)
#
#     # Get wind turbines by wind zone
#     wind_types = {float(k): v for (k, v) in cfg.get_dict('windzones').items()}
#     wind_types = pd.Series(wind_types).sort_index()
#
#     if regions is None:
#         regions = wind.columns.get_level_values(0).unique()
#
#     if feedin_ts is None or len(feedin_ts.index) == 0:
#         cols = pd.MultiIndex(levels=[[], []], labels=[[], []])
#         feedin_ts = pd.DataFrame(index=wind.index, columns=cols)
#
#     for region in regions:
#         frac = pd.merge(wz.loc[region], pd.DataFrame(wind_types), how='right',
#                         right_index=True, left_index=True).set_index(
#                             0, drop=True).fillna(0).sort_index()
#         feedin_ts[region, 'wind'] = wind[region].multiply(frac[2]).sum(1)
#     return feedin_ts.sort_index(1)


if __name__ == "__main__":

    my_index = pd.MultiIndex(
            levels=[[], []], labels=[[], []],
            names=['region', 'type'])
    # scenario_feedin_wind(year=2014, my_index=my_index)
    scenario_feedin_pv(2014, my_index, weather_year=None)
