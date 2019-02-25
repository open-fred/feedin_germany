#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:07:57 2019

@author: RL-INSTITUT\inia.steinbach
"""
import pandas as pd
#from feedinlib import region

#import internal modules
import pv_modules
import opsd_power_plants as opsd
import oep_regions as oep


def feedin_germany_pv():
    
    """
    calculates the pv-feedin-time series for germany for a given set of 
    module-parameters and a given distribution about their occurence with the 
    open-FRED weather dataset
    
    Notes
    ----------------
    check weather a specification of a weather year can be defined here
    
    returns
    --------------
    pandas.Series of feedin time series
    
    
    """
    #load register
    register = opsd.filter_solar_pp()
    # load the dictionary of pv_modules
    pv_modules_set = pv_modules.create_pvmodule_dict()
    # load the distribution of the pv_modules
    distribution_dict = pv_modules.create_distribution_dict()
    # load aggregation-regions
    regions= oep.load_regions_file()
    
    # add region column 'nuts' to register
    register=oep.add_region_to_register(register, regions)
    # loop over regions and select all powerplants within region
    for nut in regions['nuts']:
        register_region=register.loc[register['nuts'] == nut]
        register_region=register_region['lat', 'lon', 'commissioning_date', 'capacity', 'Coordinates']
        # open feedinlib to calculate feed in time series for that region
        #feedin= region.pv_feedin_distribution_register(distribution_dict=distribution_dict, technical_parameters=pv_modules_set, register=register)
        #save feedin
        #feedin.to_csv('...')

    #return feedin
    pass
    
if __name__ == "__main__":

    print(feedin_germany_pv())


    
    