#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:07:57 2019

@author: RL-INSTITUT\inia.steinbach
"""
import pandas as pd
from feedinlib import pv_region

# import internal modules
from feedin_germany import pv_modules
from feedin_germany import opsd_power_plants as opsd
from feedin_germany import oep_regions as oep
import logging


def feedin_germany(year, category):
    r"""
    calculates the pv-feedin-time series for germany

    calculates pv-feedin-time series of germany for a given year, a set of
    module-parameters and a given distribution about their occurence. Caulcula-
    tions are based on the openFred-weatherdata. The feedin for a given region
    (default germany) is devided into aggregation regions.
    
    Notes
    ----------------
    todo: loop over year, in dieser Funktion oder aussendrum? (Inia meint besser
    todo: aussen.)

    parameters
    ----------------
    year: int
    category: str
         'Solar' or 'Wind'
    
    returns
    --------------
    pandas.DataFrame
        feedin time series for a region

    """

    # load register and regions file
    if category not in ['Wind', 'Solar']:
        logging.warning("category must be 'Wind' or 'Solar'")

    register = opsd.filter_pp_by_source_and_year(year, category, keep_cols=None)
    regions = oep.load_regions_file()

    if category == 'Solar':
        pv_modules_set = pv_modules.create_pvmodule_dict()
        distribution_dict = pv_modules.create_distribution_dict()

    if category == 'Wind':
        #todo Sabine: Was brauchen wir für Wind
        pass

    # add region column 'nuts' to register
    # loop over regions and select all powerplants within one region
    register_df = oep.add_region_to_register(register, regions)
    for nut in regions['nuts']:
        register_region = register_df.loc[register_df['nuts'] == nut]

        if category == 'Solar':
            register_pv=register_region[['lat', 'lon', 'commissioning_date', 'capacity', 'Coordinates']]
            # open feedinlib to calculate feed in time series for that region
            feedin= pv_region.pv_feedin_distribution_register(distribution_dict=distribution_dict ,
                                                technical_parameters= pv_modules_set, register=register_pv)
            # save feedin
            feedin.to_csv('./data/feedin_pv')
            break

        if category == 'Wind':
            #todo Sabine: Aufbereitung des registers, Aufrufen der feedinlib, Aggregierung über regionen
            pass
    # return feedin
    pass


if __name__ == "__main__":
    print(feedin_germany(2012, 'Solar'))
