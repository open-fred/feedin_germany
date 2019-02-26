#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:25:35 2019

@author: RL-INSTITUT\inia.steinbach
"""
# Internal modules
from feedin_germany import config
# Python libraries
import os
import logging
import collections



def create_pvmodule_dict():
    
    pvlib_list = config.get('solar_sets', 'set_list')
    pvlib_sets = config.aslist(pvlib_list, flatten=True)
    modules = collections.OrderedDict()
    
    for pvlib_set in pvlib_sets:
        modules[pvlib_set]= config.as_dict(pvlib_set)
        #content = module_name, inverter_name, azimuth, tilt, albedo
        #pvsets[set_name] = {content}
        #pvsets = collections.OrderedDict(pvsets)
    return modules



def create_distribution_dict():
    
    distribution = config.todict('pv_types')
    return distribution

def parse_module_dict():
    module_dict = create_pvmodule_dict()
    for key in module_dict:
        module = module_dict[key]
        print(module)


if __name__ == "__main__":
    
    print(create_pvmodule_dict2())
    #pvsets=create_pvmodule_dict()
    #print(pvsets['BP2150S_3'])