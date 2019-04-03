# -*- coding: utf-8 -*-
"""
The `mastr_power_plant` module contains functions for downloading and
processing renewable power plant data for Germany from the
Markstammdatenregister (MaStR). todo source orginial + OEP

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
from feedin_germany import power_plant_register_tools as ppr_tools


def load_mastr_data_from_oedb():
    """
    Loads the MaStR power plant units ...todo

    Notes
    -----
    todo: login and token need to be adapted/automatized
    todo: possible --> engine creation as separate function

    todo: use sessionmaker um Anlagen auszuwählen

    Returns
    -------


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


def helper_load_mastr_from_file(category):
    r"""
    todo remove when loaded from oedb

    andere interessante Spalten könnten sein (gerade keine Einträge):
    - Erzeugungsleistung

    Notes
    -----
    - Manche "Bruttoleistungen" scheinen falsch zu sein: 0 oder krumme Zahl.

    Parameters
    ----------
    category : string
        Energy source category for which the register is loaded. Options:
        'Wind', ... to be added.

    Returns
    -------

    """
    if category == 'Wind':
        filename = os.path.join(
            '~/Daten_flexibel_01/bnetza_mastr/bnetza_mastr_power-units_v1.2/',
            'bnetza_mastr_1.2_wind.csv'.format(category.lower()))
        usecols = [
            'Nabenhoehe', 'Rotordurchmesser',
            # 'HerstellerName', 'Einheitart', 'Einheittyp', 'Technologie',
            'Typenbezeichnung', 'Laengengrad', 'Breitengrad',
            'Inbetriebnahmedatum', 'DatumEndgueltigeStilllegung',
            'DatumBeginnVoruebergehendeStilllegung',
            'DatumWiederaufnahmeBetrieb', 'Bruttoleistung'
                ]
    elif category == 'Solar':
        raise ValueError("Solar MaStR data not added, yet.")
    else:
        raise ValueError("Category {} not existent. ".format(category) +
                         "Choose from: 'Wind', ...") # todo add
    mastr_data = pd.read_csv(filename, sep=';', encoding='utf-8',
                             header=0, usecols=usecols)
    return mastr_data


def prepare_mastr_data(mastr_data, category):
    r"""

    - translation to english
    - short cuts

    - decom, com month etc. as in opsd
    - remove rows with nans
    - filter by year.. rausziehen in tools

    possible
    - remove pp with missing coordinates
    -


    Parameters
    ----------
    mastr_data : pd.DataFrame
        Contains raw MaStR data as loaded in
        `:py:func:helper_load_mastr_from_file`.
    category : string
        Energy source category for which the register is loaded. Options:
        'Wind', ... to be added.

    Returns
    -------

    """
    if category == 'Wind':  # todo: add 'name' column of name matching from Ludwig!!!
        mastr_data.rename(columns={
            'Nabenhoehe': 'hub_height', 'Rotordurchmesser': 'rotor_diameter',
            # 'HerstellerName', 'Einheitart', 'Einheittyp', 'Technologie',
            'Typenbezeichnung': 'turbine_type', 'Laengengrad': 'lon',
            'Breitengrad': 'lat', 'Inbetriebnahmedatum': 'commissioning_date',
            'DatumEndgueltigeStilllegung': 'decommissioning_date',
            'DatumBeginnVoruebergehendeStilllegung': 'temporary_decom_date',
            'DatumWiederaufnahmeBetrieb': 'resumption_date',
            'Bruttoleistung': 'capacity'
        }, inplace=True)
    #
    date_cols = ('commissioning_date', 'decommissioning_date')
    prepared_df = ppr_tools.prepare_dates(df=mastr_data, date_cols=date_cols,
                                          month=True)
    return prepared_df


def get_mastr_pp_filtered_by_year(category, year):
    r"""


    """
    mastr_pp = helper_load_mastr_from_file(category=category)
    prepared_data = prepare_mastr_data(mastr_pp, category)
    filtered_register = ppr_tools.get_pp_by_year(year=year,
                                                 register=prepared_data)
    filtered_register = ppr_tools.remove_pp_with_missing_coordinates(
        register=filtered_register, category=category, register_name='MaStR')
    return filtered_register


if __name__ == "__main__":
    year = 2012
    cat = 'Wind'
    mastr_pp = get_mastr_pp_filtered_by_year(category=cat, year=year)
    print(mastr_pp.head())
