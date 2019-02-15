#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:25:35 2019

@author: RL-INSTITUT\inia.steinbach
"""
# Internal modules
import config
# Python libraries
import os
import logging
import collections


def create_pvmodule_dict():
    
    pvlib_list = config.get('solar_sets', 'set_list')
    pvlib_sets = config.aslist(pvlib_list, flatten=True)
    pvsets = collections.OrderedDict()
    
    for pvlib_set in pvlib_sets:
        set_name = config.get(pvlib_set, 'pv_set_name')
        module_name = config.get(pvlib_set, 'module_name')
        inverter_name = config.get(pvlib_set, 'inverter_name')
        azimuth = config.get(pvlib_set, 'azimuth')
        tilt = config.get(pvlib_set, 'tilt')
        albedo = config.get(pvlib_set, 'albedo')
        
        pvsets[set_name] = collections.OrderedDict()
        content = module_name, inverter_name, azimuth, tilt, albedo
        pvsets[set_name] = {content}
        pvsets = collections.OrderedDict(pvsets)
    return pvsets

def create_distribution_dict():
    
    distribution = config.todict('pv_types')
    return distribution

def parse_module_dict():
    module_dict = create_pvmodule_dict()
    for key in module_dict:
        module = module_dict[key]
        print(module)


if __name__ == "__main__":
    
    print(parse_module_dict())
    #pvsets=create_pvmodule_dict()
    #print(pvsets['BP2150S_3'])