# -*- coding: utf-8 -*-
"""
todo add description

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# Internal modules
from feedin_germany import config
# Python libraries
import os
import logging
import collections



def create_pvmodule_dict():
    r"""
    creates dictionary of all pv-modules

    """
    pvlib_list = config.get('solar_sets', 'set_list')
    pvlib_sets = config.aslist(pvlib_list, flatten=True)
    modules = collections.OrderedDict()
    
    for pvlib_set in pvlib_sets:
        modules[pvlib_set]= config.as_dict(pvlib_set)
    return modules



def create_distribution_dict():
    r"""
    creates dictionary of the pv-module's distribution

    """
    
    distribution = config.as_dict('pv_types')
    return distribution


def parse_module_dict():
    module_dict = create_pvmodule_dict()
    for key in module_dict:
        module = module_dict[key]
        print(module)


if __name__ == "__main__":
    
    print(create_distribution_dict())
    #pvsets=create_pvmodule_dict()
    #print(pvsets['BP2150S_3'])