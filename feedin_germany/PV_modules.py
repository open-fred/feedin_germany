#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 16:25:35 2019

@author: RL-INSTITUT\inia.steinbach
"""
# Internal modules
# Python libraries
import os
import logging
import configparser
import collections

def aslist_cronly(value):
    value = filter(None, [x.strip() for x in value.splitlines()])
    return list(value)

def aslist(value, flatten=True):
    """ Return a list of strings, separating the input based on newlines
    and, if flatten=True (the default), also split on spaces within
    each line."""
    values = aslist_cronly(value)
    if not flatten:
        return values
    result = []
    for value in values:
        subvalues = value.split()
        result.extend(subvalues)
    return result


def create_pvmodule_dict():
    config = configparser.RawConfigParser()
    configFilePath = '/home/local/RL-INSTITUT/inia.steinbach/Dokumente/deflex3.6_env/feedin_germany/feedin_germany/feedin_germany.ini'
    config.read(configFilePath)
    
    pvlib_list = config.get('solar_sets', 'set_list')
    pvlib_sets = aslist(pvlib_list, flatten=True)
    #pvlib_sets = cfg.get('solar', 'set_list')
    pvsets = collections.OrderedDict()
    
    for pvlib_set in pvlib_sets:
        set_name = config.get(pvlib_set, 'pv_set_name')
        module_name = config.get(pvlib_set, 'module_name')
        inverter_name = config.get(pvlib_set, 'inverter_name')
        azimuth = config.get(pvlib_set, 'azimuth')
        tilt = config.get(pvlib_set, 'tilt')
        albedo = config.get(pvlib_set, 'albedo')
        
        pvsets[set_name] = collections.OrderedDict()
        content = (module_name, inverter_name, azimuth, tilt, albedo)
        pvsets[set_name] = {content}
        pvsets = collections.OrderedDict(pvsets)
    return pvsets


if __name__ == "__main__":
    
    pvsets=create_pvmodule_dict()
    print(pvsets['BP2150S_3'])