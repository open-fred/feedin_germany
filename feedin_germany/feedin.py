# -*- coding: utf-8 -*-
"""
The `feedin` module contains functions for calculating feed-in time series of
renewable power plants.
calculate_feedin_germany() is a Germany specific function and automatically
downloads data needed for the calculations.

"""

#todo feedinlib: wetterdaten UTC? falls nicht aufpassen bei Validierung

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import logging
import time
import pickle

from feedinlib import region
from feedinlib import tools

# import internal modules
from feedin_germany import opsd_power_plants as opsd
from feedin_germany import oep_regions as oep
from feedin_germany import pv_modules
from feedin_germany import mastr_power_plants as mastr
from feedin_germany import weather



# Planung Funktionalitäten:
# - hochladen in OEP nach ausgemachtem Muster (machen nur wir)
# - Rückgabe für die Validierung:  db format.(nur bei geringer Anzahl an Regionen)
# - Umformungsfunktion für deflex - Muster siehe Jann


def calculate_feedin(year, register, regions, category, weather_data_folder,
                     return_feedin=False, weather_data_name='open_FRED',  # todo rename to weather_data and possibility of entering own weather data
                     scale_to=None, **kwargs):
    r"""
    Calculates feed-in of power plants in `register` for different `regions`.

    This function can be used for any region/country as long as you have the
    input data.
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
    category : string # todo kein Parameter sondern aus Anlagenregister - sonst verwirrend, da register hier schon gefiltert sein soll. Fehlermeldung wenn nicht gefiltert
        Energy source category for which feed-in time series are calculated.
        Options: 'Wind', 'Solar', 'Hydro'.
    return_feedin : boolean
        If True calculated feed-in is returned as pd.DataFrame. Columns see
        `feedin_df`. Should only be set to True if number of regions is
         small. Default: False. todo what does small mean?
    weather_data_name : string

    scale_to : str or ...
        Specifies if and which capacities feed-in time series are scaled to.
        Default: None. # todo note: Now it can only be chosen 'entsoe' - would be nice to enter own capacities

    Other parameters
    ----------------
    todo parameters for windpowerlib modelchains, pvlib modelchain

    Returns
    -------
    If return_feedin is True:
    feedin_df : pd.DataFrame
        Contains calculated feed-in for each region in `regions`. # todo form of return
    else: None.

    """
    if category == 'Solar':
        # todo delete the following lines when weather is integrated in feedinlib, + year input in feedinlib
        weather_df = weather.get_weather_data_germany(
            year=year, weather_data_name=weather_data_name, format_='pvlib',
            path=weather_data_folder)

        # prepare technical parameters and pv modules
        pv_modules_set = pv_modules.create_pvmodule_dict()
        distribution_dict = pv_modules.create_distribution_dict()

    # todo delete the following lines when weather is integrated in feedinlib, + year input in feedinlib
    if category == 'Wind':
        weather_df = weather.get_weather_data_germany(
            year=year, weather_data_name=weather_data_name,
            format_='windpowerlib', path=weather_data_folder)

    if return_feedin:
        feedin_df = pd.DataFrame()

    for nut in regions['nuts']:
        register_region = register.loc[register['nuts'] == nut]
        if register_region.empty:
            logging.debug(
                "No {} power plants in region {} in register.".format(category,
                                                                      nut))
        else:
            # todo: wenn feedinlib weiterentwickelt: feedinlib Aufruf für alle gleich möglich?
            if category == 'Solar':
                register_pv = register_region[
                    ['lat', 'lon', 'commissioning_date', 'capacity',
                     'Coordinates']]
                # open feedinlib to calculate feed in time series for region
                feedin = region.Region(
                    geom='no_geom',
                    weather=weather_df).pv_feedin_distribution_register(
                    distribution_dict=distribution_dict,
                    technical_parameters=pv_modules_set,
                    register=register_pv)
            elif category == 'Wind':
                feedin = region.Region(geom='no_geom',
                                       weather=weather_df).wind_feedin(
                    register_region, **kwargs)
            elif category == 'Hydro':
                raise ValueError("Hydro not working, yet.")
            else:
                raise ValueError("Invalid category {}".format(category) +
                                 "Choose from: 'Wind', 'Solar', 'Hydro'.")
            # scale time series to installed capacity in the respective year
            if scale_to == 'entsoe':
                installed_capacity = get_entsoe_capacity(year=year, region=nut,
                                                         category=category)
                if np.isnan(installed_capacity):
                    logging.warning('Time series of {} {} was not '.format(
                        nut, year) + 'scaled. Installed capacity is missing')
                else:
                    capacity_register = register_region['capacity'].sum()
                    feedin = feedin / capacity_register * installed_capacity
            if return_feedin:
                feedin = feedin_to_db_format(feedin=feedin, technology=category,
                                          nuts=nut)
                feedin_df = pd.concat([feedin_df, feedin])
    if return_feedin:
        return feedin_df
    else:
        pass


def form_feedin_for_deflex(feedin):
    r"""
    Forms feed-in to the form deflex needs it.

    Feed-in from :py:func:`calculate_feedin` or
    :py:func:`calculate_feedin_germany` is formed to a MultiIndex data frame as
    needed by deflex. todo link ...

    Parameters
    ----------
    feedin : pd.DataFrame
        Feed-in as returned from :py:func:`calculate_feedin` or
        :py:func:`calculate_feedin_germany`.

    Returns
    -------
    feedin_df : pd.MuliIndex.DataFrame
        Contains calculated feed-in for each region in `regions`. First level
        columns contain nuts of regions, second level columns contain
        `category`.

    """
    # initialize data frame for output
    cols = pd.MultiIndex(levels=[[], []], codes=[[], []])
    deflex_feedin = pd.DataFrame(columns=cols)
    filter_df = feedin.groupby(['nuts', 'technology']).size().reset_index().drop(columns=[0],
                                                                   axis=1)
    for filters in filter_df.values:
        df = feedin.loc[(feedin['nuts'] == filters[0]) &
                        (feedin['technology'] == filters[1])].drop(
            columns=['nuts', 'technology']).set_index('time')
        deflex_feedin[filters[0], filters[1].lower()] = df['feedin']
    return deflex_feedin


def get_entsoe_capacity(year, region, category):
    """

    year : int
    region : str
        Options: '50 Hertz', 'Amprion', 'TenneT', 'Transnet BW'.
    """
    # todo nur test file..
    filename = os.path.join(os.path.dirname(__file__), 'data/entsoe',
                            'installed_capacities_unb_{}.csv'.format(category))
    df = pd.read_csv(filename, header=0, index_col=0)
    capacity = df[region][year]
    if np.isnan(capacity):
        return capacity
    else:
        # capacity in W
        return capacity * 10 ** 6


def calculate_feedin_germany(year, categories, weather_data_folder,
                             regions='tso', register_name='opsd',
                             weather_data_name='open_FRED',
                             return_feedin=False, debug_mode=False,
                             scale_to=None, **kwargs):
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
    weather_data_folder : string

    regions : geopandas.GeoDataFrame or string
        Regions for which feed-in time series are calculated
        (geopandas.GeoDataFrame) or specification of regions that are loaded
        from OEP. Options for string: 'landkreise', 'uebertragunsnetzzonen'.
        Default: 'landkreise'.
        todo: add exact required form of GeoDataFrame
    register_name : pd.DataFrame or string
        todo
    weather_data_name : string
        Specifies the weather data source. Options: 'open_FRED', 'ERA5'.
         Default: 'open_FRED'. todo check
    return_feedin : boolean
        If True calculated feed-in is returned as pd.DataFrame. Columns see
        `feedin_df`. Should only be set to True if number of regions is
         small. Default: False. todo what does small mean?
    debug_mode : boolean
        might be deleted
    scale_to

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
    feedin_df : pd.DataFrame
        Contains calculated feed-in for each region in `regions`. # todo form of return
    else: None.

    """
    # get regions from OEP if regions is not a geopandas.GeoDataFrame
    if isinstance(regions, gpd.GeoDataFrame):
        region_gdf = regions
    elif regions == 'landkreise' or regions =='tso':
        start = time.time()
        # todo delete or with parameter in function
        regions_file = os.path.join(os.path.dirname(__file__), 'data/dumps',
                                    'regions_ger_{}.p'.format(regions))
        if os.path.exists(regions_file):
            region_gdf = pickle.load(open(regions_file, 'rb'))
        else:
            region_gdf = oep.load_regions_file(regions)
            pickle.dump(region_gdf, open(regions_file, 'wb'))
        end = time.time()
        print(
            'Time load_regions_file year {}: {}'.format(year, (end - start)))
        if debug_mode:
            region_gdf = region_gdf[0:5]
    else:
        raise ValueError("`regions` should be 'landkreise',"
                         "'tso' or gpd.GeoDataFrame.")

    if return_feedin:
        feedin_df = pd.DataFrame()
    for category in categories:
        # get power plant register if register is not pd.DataFrame
        if isinstance(register_name, pd.DataFrame):
            register = register_name  # possible todo: check if right format
        elif register_name == 'opsd':
            keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity',
                         'technology']  # technology needed for offshore wind
            register = opsd.filter_pp_by_source_and_year(year, category,
                                                         keep_cols=keep_cols)
        elif register_name == 'MaStR':
            if category == 'Wind':
                register = mastr.get_mastr_pp_filtered_by_year(
                    energy_source=category, year=year)
                register.dropna(subset=['name', 'hub_height',
                                        'rotor_diameter'], inplace=True)  # todo remove after mastr is complete or fix
            else:
                raise ValueError("Option 'MaStR' as `register_name` until "
                                 "now only available for `category` 'Wind'.")
        else:
            raise ValueError("Invalid register name {}.".format(
                    register_name) + " Must be 'opsd' or 'MaStR or "
                                     "pd.DataFrame.")
        # add region column 'nuts' to register
        register = oep.add_region_to_register(register, region_gdf)

        feedin = calculate_feedin(
            year=year, register=register, regions=region_gdf,
            category=category, return_feedin=return_feedin,
            weather_data_name=weather_data_name,
            weather_data_folder=weather_data_folder, scale_to=scale_to,
            **kwargs)
        if return_feedin:
            feedin_df = pd.concat([feedin_df, feedin])  # todo check axis when solar + wind
    if return_feedin:
        return feedin_df
    else:
        pass


def feedin_to_db_format(feedin, technology, nuts):
    r"""
    ..... todo

    Column 'time' contains the datetime index of `feedin`, 'feedin' the
    feed-in time series itself as in `feedin`, 'technology' the technology
    the feed-in origins from as in `technology` and 'nut' the region nut of the
    calculated feed-in as given in `nut`

    feedin : pd.Series
        Feed-in time series with datetime index.
    technology : string
        todo
    nuts : ... todo

    """
    df = pd.DataFrame(feedin).reset_index('time')
    df['nuts'] = nuts
    df['technology'] = technology
    return df


def upload_time_series_to_oep(feedin, technology, nuts):
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
    nuts : ... todo

    """
    # prepare data frame for upload
    df = feedin_to_db_format(feedin=feedin, technology=technology, nuts=nuts)
    # todo upload  --> maybe form of Günni.... er weiß Bescheid, dass er uns Input geben soll.


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
            year=year, categories=categories, regions='tso',
            register_name='opsd', weather_data_name='open_FRED',
            return_feedin=True, debug_mode=False)
        print(feedin)
        deflex_feedin = form_feedin_for_deflex(feedin=feedin)
        print(deflex_feedin.head())
