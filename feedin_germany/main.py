#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 16:07:57 2019

@author: RL-INSTITUT\inia.steinbach
"""
import pandas as pd
import feedinlib

#import internal modules
import pv_modules
import opsd_power_plants as opsd


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
    # load the dictionary of pv_modules
    pv_modules_set = pv_modules.create_pvmodule_dict()
    # load the distribution of the pv_modules
    distribution_dict = pv_modules.create_distribution_dict()
    # load the register for solar powerplants
    register = opsd.filter_solar_pp()
    
    feedin= feedinlib.pv_feedin_distribution_register(distribution_dict, technical_parameters=pv_modules_set, register)
    
    
    return feedin
    
    
if __name__ == "__main__":

feedin=feedin_germany_pv()

feedin.fillna(0).plot()
plt.show()
    
    