# -*- coding: utf-8 -*-
"""
The `feedin` module contains functions for calculating feed-in time series of
renewable power plants.
calculate_feedin_germany() is a Germany specific function and automatically
downloads data needed for the calculations.

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

from feedinlib import region
from feedinlib import pv_region
from feedinlib import tools

# import internal modules
from feedin_germany import opsd_power_plants as opsd
from feedin_germany import oep_regions as oep
from feedin_germany import pv_modules


# Planung Funktionalitäten:
# - hochladen in OEP nach ausgemachtem Muster (machen nur wir)
# - Rückgabe für deflex - Muster siehe Jann (nur bei geringer Anzahl an Regionen)
# - für die Validierung: nur eine Kategorie --> calculate_feedin_germany() mit
#   einer Kategorie. geringe Regionananzahl --> Rückgabe wie für deflex. Kann
#   auch gut zur Validierung verwendet werden.


def calculate_feedin(year, register, regions, category, return_feedin=False,
                     oep_upload=False, **kwargs):
    r"""
    Calculates feed-in of power plants in `register` for different `regions`.

    This function can be used for any region/country as long as you have the
    input data. # todo MERRA in feedinlib? oder Erklärung, dass eigenes Wetter in feedinlib eingegeben werden kann.
    For calculating feed-in time series for Germany it is recommended to use
    :py:func:`~.calculate_feedin_germany`.

    Parameters
    ----------
    year : int
        Year for which feed-in time series are calculated.
    register : pd.DataFrame
        todo format --> Anforderung aus feedinlib!
    regions : pandas.geoDataFrame
        Regions for which feed-in time series are calculated.
        todo: add required form of GeoDataFrame
    category : string # todo vllt kein Parameter sondern aus Anlagenregister - sonst verwirrend, da register hier schon gefiltert sein soll.
        Energy source category for which feed-in time series are calculated.
        Options: 'Wind', 'Solar', 'Hydro'.
    return_feedin : boolean
        If True calculated feed-in is returned as MultiIndexDataFrame
        (see `feedin_df`). Should only be set to True if number of regions is
         small. Default: False. todo what means small?
    oep_upload : boolean
        If True time series are uploaded to OEP. Default: False.

    Other parameters
    ----------------
    todo parameters for windpowerlib modelchains, pvlib modelchain

    Returns
    -------
    If return_feedin is True:
    feedin_df : pd.MuliIndex.DataFrame
        Contains calculated feed-in for each region in `regions`. First level
        columns contain nuts of regions, second level columns contain
        `category`.
    else: None.

    """
    if category == 'Solar':
        # prepare technical parameters and pv modules
        pv_modules_set = pv_modules.create_pvmodule_dict()
        distribution_dict = pv_modules.create_distribution_dict()

    # todo delete the following lines when weather is integrated in feedinlib, + year input in feedinlib
    if category == 'Wind':
        filename = os.path.abspath(
        '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
        weather_df = tools.example_weather_wind(filename)
    if return_feedin:
        # initialize data frame for output
        cols = pd.MultiIndex(levels=[[], []], codes=[[], []])
        feedin_df = pd.DataFrame(columns=cols)
    for nut in regions['nuts']:
        register_region = register.loc[register['nuts'] == nut]
        # todo: wenn feedinlib weiterentwickelt: feedinlib Aufruf für alle gleich möglich?
        if category == 'Solar':
            register_pv = register_region[
                ['lat', 'lon', 'commissioning_date', 'capacity',
                 'Coordinates']]
            # open feedinlib to calculate feed in time series for that region
            feedin = pv_region.pv_feedin_distribution_register(
                distribution_dict=distribution_dict,
                technical_parameters=pv_modules_set, register=register_pv)
        elif category == 'Wind':
            feedin = region.Region(geom='no_geom',
                                   weather=weather_df).wind_feedin(register,
                                                                   **kwargs)
        elif category == 'Hydro':
            pass
        else:
            raise ValueError("Invalid category {}".format(category) +
                             "Choose from: 'Wind', 'Solar', 'Hydro'.")
        if oep_upload:
            upload_time_series_to_oep(feedin=feedin, technology=category,
                                      nut=nut)
        if return_feedin is True:
            feedin_df[nut, category.lower()] = feedin
    if return_feedin is True:
        return feedin_df
    else:
        pass


def calculate_feedin_germany(year, categories, regions='landkreise',
                             register_name='opsd',
                             weather_data_name='open_FRED', oep_upload=False,
                             debug_mode=False, **kwargs):
    r"""

    Es sollen eigene Regionen eingegeben werden können,
    aber auch diejenigen aus der oedb geladen werden können.
    # todo note: auch register_name und weather_data_name könnte wie regions funktionieren.
        --> verschiedene Kombis möglich: eigenes Register, aber Landkreise etc..

    Parameters
    ----------
    year : int
        Year for which feed-in time series are calculated.
    categories : list of strings
        Energy source categories for which feed-in time series are calculated.
        Can include 'Wind', 'Solar', 'Hydro'.
    regions : geopandas.GeoDataFrame or string
        Regions for which feed-in time series are calculated
        (geopandas.GeoDataFrame) or specification of regions that are loaded
        from OEP. Options for string: 'landkreise', 'uebertragunsnetzzonen'.
        Default: 'landkreise'.
        todo: add exact required form of GeoDataFrame
    register_name : string
        todo
    weather_data_name : string
        Specifies the weather data source. Options: 'open_FRED', 'MERRA'.
         Default: 'open_FRED'. todo check
    oep_upload : boolean
        If True time series are uploaded to OEP. Default: False.
    debug_mode : boolean
        might be deleted

    Other parameters
    ----------------
    todo parameters for windpowerlib modelchains, pvlib modelchain

    Notes
    -----
    The returned feed-in is in the form as needed by the heat and power model
    deflex (https://github.com/reegis/deflex).
    However, `feedin_df` is only returned if `regions` contains less than 26 # todo adapt number?!
    regions as it is assumed that a energy system optimization of Germany would
    not be done for more nodes.

    Returns
    -------
    If `regions` contains less than 26 regions:
    feedin_df : pd.MuliIndex.DataFrame
        Contains calculated feed-in for each region in `regions`. First level
        columns contain nuts of regions, second level columns contain
        `category`.
    else: None.

    """
    # get regions from OEP if regions is not a geopandas.GeoDataFrame
    if regions == 'landkreise':
        region_gdf = oep.load_regions_file()
        if debug_mode:
            region_gdf = region_gdf[0:15]
    elif regions == 'uebertragunsnetzzonen':
        pass
    elif isinstance(regions, gpd.GeoDataFrame):
        region_gdf = regions

    if len(region_gdf) <= 25:
        return_feedin = True
        feedin_df = pd.DataFrame()
    else:
        return_feedin = False
    for category in categories:
        # get power plant register for all power plants in Germany
        if register_name == 'opsd':
            keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity']
            register = opsd.filter_pp_by_source_and_year(year, category,
                                                         keep_cols=keep_cols)
        elif register_name == 'MaStR':
            if category == 'Wind':
                pass  # todo add MaStR
            else:
                raise ValueError("Option 'MaStR' as `register_name` up to "
                                 "now only available for `category` 'Wind'.")
        else:
            raise ValueError("Invalid register name {}.".format(
                    register_name) + " Must be 'opsd' or 'MaStR.")
        # add region column 'nuts' to register
        register = oep.add_region_to_register(register, region_gdf)

        feedin = calculate_feedin(
            year=year, register=register, regions=region_gdf,
            category=category, return_feedin=return_feedin,
            oep_upload=oep_upload, **kwargs)
        if return_feedin:
            feedin_df = pd.concat([feedin_df, feedin], axis=1)
    if return_feedin:
        return feedin_df
    else:
        pass


def upload_time_series_to_oep(feedin, technology, nut):
    r"""
    Uploads feed-in time series to OEP 'model_draft' schema.

    Column 'time' contains the datetime index of `feedin`, 'feedin' the
    feed-in time series itself as in `feedin`, 'technology' the technology
    the feed-in origins from as in `technology` and 'nut' the region nut of the
    calculated feed-in as given in `nut`

    feedin : pd.Series
        Feed-in time series with datetime index.
    technology : string
        todo
    nut : ... todo

    """
    # prepare data frame for upload
    df = pd.DataFrame(feedin).reset_index('time')
    df['nut'] = nut
    df['technology'] = technology
    # todo upload  # @ Inia, könntest du das machen?


if __name__ == "__main__":
    # main.py
    years = [2012]
    categories = [
        'Wind',
        # 'Solar',
        # 'Hydro'
    ]
    for year in years:
            feedin = calculate_feedin_germany(
                year=year, categories=categories, regions='landkreise',
                register_name='opsd', weather_data_name='open_FRED',
                oep_upload=True, debug_mode=True)
            print(feedin)
