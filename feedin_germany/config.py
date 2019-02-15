#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 11:19:13 2019

@author: RL-INSTITUT\inia.steinbach
"""

# Python libraries
import os
import logging
import configparser
import sys

config = configparser.RawConfigParser()
configFilePath = 'feedin_germany.ini'
config.read(configFilePath)


def get(section, key):
    return config.get(section, key)
    
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