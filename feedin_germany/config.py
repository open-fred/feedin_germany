#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 15 11:19:13 2019

@author: RL-INSTITUT\inia.steinbach
"""

# Python libraries
import configparser
import os

config = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), 'feedin_germany.ini')
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

def todict(section):
    
    """
    returns the values of a section as dictionary
    """
    dictionary = {}
    for option in config.options(section):
        dictionary[option] = config.get(section, option)
    return dictionary


def as_dict(section):
    """
    Converts a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.
    """
    the_dict = {}
   # if section in config.sections():
   #     the_dict = {}
    for key, val in config.items(section):
        the_dict[key] = val
    return the_dict