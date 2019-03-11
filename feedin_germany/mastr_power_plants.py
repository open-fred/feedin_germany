# -*- coding: utf-8 -*-
"""
todo add description

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import pandas as pd
import geopandas as gpd
import os

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry
from sqlalchemy import func
import oedialect
from shapely.geometry import Point
import shapely
import requests


# internal imports
from feedin_germany import oep_regions


def load_mastr_data_from_oedb():
    """
    Loads the MaStR power plant units ...todo

    Notes
    ----------------
    todo: login and token need to be adapted/automatized
    todo: possible --> engine creation as separate function

    todo: use sessionmaker um Anlagen auszuwählen

    todo: Inhalt nicht wie erwartet.... Ludwig??
    Returns
    --------------


    """
    # url of OpenEnergy Platform that contains the oedb
    oep_url = 'http://oep.iks.cs.ovgu.de/'
    # location of data
    schema = 'model_draft'
    table = 'bnetza_mastr_stromerzeuger'
    # load data
    result = requests.get(
        oep_url + '/api/v0/schema/{}/tables/{}/rows/?'.format(
            schema, table), )
    if not result.status_code == 200:
        raise ConnectionError("Database connection not successful. "
                              "Error: {}".format(result.status_code))
    # extract data
    register = pd.DataFrame(result.json())
    print(register)


def helper_load_mastr_from_file():
    r"""
    todo remove when not needed anymore
    """
    # interessante Spalten könnten sein:
    # UtmEast
    # UtmNorth
    # Nabenhoehe
    # Rotordurchmesser
    # HerstellerName
    # version_w
    # Einheitart	Einheittyp
    #
    # Typenbezeichnung
    # Technologie

    filename = os.path.join(
        '~/Daten_flexibel_01/bnetza_mastr/bnetza_mastr_power-units_v1.0/',
        'bnetza_mastr_1.0_wind.csv')
    usecols = [
        'UtmEast',
        # 'UtmNorth', 'Nabenhoehe', 'Rotordurchmesser',
               # 'HerstellerName', 'version_w', 'Einheitart', 'Einheittyp',
               # 'Typenbezeichnung', 'Technologie'
               ]
    mastr_data = pd.read_csv(filename, usecols=usecols)
    print(mastr_data.head())

if __name__ == "__main__":
    helper_load_mastr_from_file()
