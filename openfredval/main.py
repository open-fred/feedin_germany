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

if __name__ == "__main__":

    my_index = pd.MultiIndex(
            levels=[[], []], labels=[[], []],
            names=['region', 'type'])
    scenario_feedin_pv(2014, my_index, weather_year=None)