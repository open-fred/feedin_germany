# -*- coding: utf-8 -*-
"""
The `opsd_power_plant` module contains functions for downloading and processing
renewable power plant data for Germany from opsd
(https://data.open-power-system-data.org/).

The code in this module is partly based on third party code which has been
licensed under GNU-LGPL3. The following functions are copied and adapted from:
https://github.com/reegis/reegis
* load_original_opsd_file()
* convert_utm_code_opsd
* guess_coordinates_by_postcode_opsd()
* log_undefined_capacity
* complete_opsd_geometries()
* remove_cols()
* prepare_opsd_file()
# todo @ Inia: please check

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# Python libraries
import os
import logging
import datetime

# External libraries
import numpy as np
import pandas as pd
import geopandas as gpd
import pyproj
import requests
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Point
import io

# oemof libraries
from oemof.tools import logger

# Internal modules
from feedin_germany import config as cfg
from feedin_germany import geometries
from feedin_germany import power_plant_register_tools as ppr_tools
from feedin_germany import database_tools as db_tools


def load_original_opsd_file(latest=False):
    r"""
    loads register from server

    parameters
    ----------
    'latest': boolean

    Returns
    -------
    df : pd.DataFrame
        OPSD power plant data. todo: describe most important columns with units
        For description of further columns see
        https://data.open-power-system-data.org/renewable_power_plants/.
    """

    if latest:
        url_section = 'opsd_url_latest'
    else:
        url_section = 'opsd_url_2017'

    # Download non existing files. If you think that there are newer files you
    # have to set overwrite=True to overwrite existing with downloaded files.

    logging.warning("Start downloading the register file from server.")
    logging.warning("Check URL if download does not work.")
    req = requests.get(cfg.get(url_section, 'renewable_data')).content

    df = pd.read_csv(io.StringIO(req.decode('utf-8')))

    return df


def convert_utm_code_opsd(df):
    # *** Convert utm if present ***
    utm_zones = list()
    # Get all utm zones.
    if 'utm_zone' in df:
        df_utm = df.loc[(df.lon.isnull()) & (df.utm_zone.notnull())]

        utm_zones = df_utm.utm_zone.unique()

    # Loop over utm zones and convert utm coordinates to latitude/longitude.
    for zone in utm_zones:
        my_utm = pyproj.Proj(
            "+proj=utm +zone={0},+north,+ellps=WGS84,".format(str(int(zone))) +
            "+datum=WGS84,+units=m,+no_defs")
        utm_df = df_utm.loc[df_utm.utm_zone == int(zone),
                            ('utm_east', 'utm_north')]
        coord = my_utm(utm_df.utm_east.values, utm_df.utm_north.values,
                       inverse=True)
        df.loc[(df.lon.isnull()) & (df.utm_zone == int(zone)), 'lat'] = (
            coord[1])
        df.loc[(df.lon.isnull()) & (df.utm_zone == int(zone)), 'lon'] = (
            coord[0])
    return df


def guess_coordinates_by_postcode_opsd(df):
    # *** Use postcode ***
    if 'postcode' in df:
        df_pstc = df.loc[(df.lon.isnull() & df.postcode.notnull())]
        if len(df_pstc) > 0:
            pstc = pd.read_csv(os.path.join(
                os.path.dirname(__file__), cfg.get('paths', 'geometry'),
                cfg.get('geometry', 'postcode_polygon')), index_col='zip_code')
        for idx, val in df_pstc.iterrows():
            try:
                # If the postcode is not number the integer conversion will
                # raise a ValueError. Some postcode look like this '123XX'.
                # It would be possible to add the mayor regions to the postcode
                # map in order to search for the first two/three digits.
                postcode = int(val.postcode)
                if postcode in pstc.index:
                    df.loc[df.id == val.id, 'lon'] = wkt_loads(
                        pstc.loc[postcode].values[0]).centroid.x
                    df.loc[df.id == val.id, 'lat'] = wkt_loads(
                        pstc.loc[postcode].values[0]).centroid.y
                # Replace the last number with a zero and try again.
                elif round(postcode / 10) * 10 in pstc.index:
                    postcode = round(postcode / 10) * 10
                    df.loc[df.id == val.id, 'lon'] = wkt_loads(
                        pstc.loc[postcode].values[0]).centroid.x
                    df.loc[df.id == val.id, 'lat'] = wkt_loads(
                        pstc.loc[postcode].values[0]).centroid.y
                else:
                    logging.debug("Cannot find postcode {0}.".format(postcode))
            except ValueError:
                logging.debug("Cannot find postcode {0}.".format(val.postcode))
    return df


def guess_coordinates_by_spatial_names_opsd(df, fs_column, cap_col,
                                            total_cap, stat):
    # *** Use municipal_code and federal_state to define coordinates ***
    if fs_column in df:
        if 'municipality_code' in df:
            if df.municipality_code.dtype == str:
                df.loc[df.municipality_code == 'AWZ', fs_column] = 'AWZ_NS'
        if 'postcode' in df:
            df.loc[df.postcode == '000XX', fs_column] = 'AWZ'
        states = df.loc[df.lon.isnull()].groupby(
            fs_column).sum()[cap_col]
        logging.debug("Fraction of undefined capacity by federal state " +
                      "(percentage):")
        for (state, capacity) in states.iteritems():
            logging.debug("{0}: {1:.4f}".format(
                state, capacity / total_cap * 100))
            stat.loc[state, 'undefined_capacity'] = capacity

        # A simple table with the centroid of each federal state.
        f2c = pd.read_csv(
            os.path.join(
                os.path.dirname(__file__), cfg.get('paths', 'geometry'),
                cfg.get('geometry', 'federalstates_centroid')),
                    index_col='name')

        # Use the centroid of each federal state if the federal state is given.
        # This is not very precise and should not be used for a high fraction
        # of plants.
        f2c = f2c.applymap(wkt_loads).centroid
        for l in df.loc[(df.lon.isnull() & df[fs_column].notnull())].index:
            if df.loc[l, fs_column] in f2c.index:
                df.loc[l, 'lon'] = f2c[df.loc[l, fs_column]].x
                df.loc[l, 'lat'] = f2c[df.loc[l, fs_column]].y
    return df


def log_undefined_capacity(df, cap_col, total_cap, msg):
    logging.debug(msg)
    if len(df.loc[df.lon.isnull()]) == 0:
        undefined_cap = 0
    else:
        undefined_cap = df.loc[df.lon.isnull()][cap_col].sum()
    logging.info("{0} percent of capacity is undefined.".format(
        undefined_cap / total_cap * 100))
    return undefined_cap


def complete_opsd_geometries(df, time=None,
                             fs_column='federal_state'):
    """
    Try different methods to fill missing coordinates.
    """
    cap_col = 'capacity'

    if 'id' not in df:
        df['id'] = df.index
        no_id = True
    else:
        no_id = False

    if time is None:
        time = datetime.datetime.now()

    # Get index of incomplete rows.
    incomplete = df.lon.isnull()

    statistics = pd.DataFrame()

    # Calculate total capacity
    total_capacity = df[cap_col].sum()
    statistics.loc['original', 'undefined_capacity'] = log_undefined_capacity(
        df, cap_col, total_capacity,
        "IDs without coordinates found. Trying to fill the gaps.")

    df = convert_utm_code_opsd(df)
    statistics.loc['utm', 'undefined_capacity'] = log_undefined_capacity(
        df, cap_col, total_capacity,
        "Reduced undefined plants by utm conversion.")

    df = guess_coordinates_by_postcode_opsd(df)
    statistics.loc['postcode', 'undefined_capacity'] = log_undefined_capacity(
        df, cap_col, total_capacity, "Reduced undefined plants by postcode.")

    df = guess_coordinates_by_spatial_names_opsd(
        df, fs_column, cap_col, total_capacity, statistics)
    statistics.loc['name', 'undefined_capacity'] = log_undefined_capacity(
        df, cap_col, total_capacity,
        "Reduced undefined plants by federal_state centroid.")

    # Store table of undefined sets to csv-file
    if incomplete.any():
        dir_messages = cfg.get('paths', 'messages')
        if not os.path.exists(dir_messages):
            os.makedirs(dir_messages, exist_ok=True)
        df.loc[incomplete].to_csv(os.path.join(
            cfg.get('paths', 'messages'),
            'incomplete_geometries_before.csv'))

    incomplete = df.lon.isnull()
    if incomplete.any():
        df.loc[incomplete].to_csv(os.path.join(
            cfg.get('paths', 'messages'),
            'incomplete_geometries_after.csv'))
    logging.debug("Gaps stored to: {0}".format(cfg.get('paths', 'messages')))

    #statistics['total_capacity'] = total_capacity
    #statistics.to_csv(os.path.join(cfg.get('paths', 'messages'),
    #                               'statistics_renewable_pp.csv'))

    # Log information
    geo_check = not df.lon.isnull().any()
    if not geo_check:
        logging.warning("Plants with unknown geometry.")
    logging.info('Geometry check: {0}'.format(str(geo_check)))
    logging.info("Geometry supplemented: {0}".format(
        str(datetime.datetime.now() - time)))

    if no_id:
        del df['id']
    return df


def remove_cols(df, cols):
    """Safely remove columns from dict."""
    for key in cols:
        try:
            del df[key]
        except KeyError:
            pass
    return df


def prepare_opsd_file(overwrite):
    r"""
    Loads original opsd file and processes it.

    The processing includes: renaming columns, comleting geometries, removing
    powerplants without capacity, remove columns that are not used

    capacity in W

    Parameters
    ----------
    overwrite : boolean

    Returns
    -------
    df : pd. DataFrame()
        todo..
    """
    opsd_directory = cfg.get('paths', 'opsd')
    prepared_filename = os.path.join(
            os.path.dirname(__file__),
            cfg.get('paths', 'opsd'),
            cfg.get('opsd', 'opsd_prepared'))

    if os.path.isfile(prepared_filename):
        logging.warning("OPSD prepared-register already exist and is loaded "
                        "from csv")
        df = pd.read_csv(prepared_filename)
        return df

    if not os.path.exists(opsd_directory):
        os.makedirs(opsd_directory, exist_ok=True)

    df = load_original_opsd_file(overwrite)

    remove_list = [
            'tso', 'dso', 'dso_id', 'eeg_id', 'bnetza_id', 'federal_state',
            'postcode', 'municipality_code', 'municipality', 'address',
            'address_number', 'utm_zone', 'utm_east', 'utm_north',
            'data_source']
    date_cols = ('commissioning_date', 'decommissioning_date')
    month = True

    df = df.rename(columns={'electrical_capacity': 'capacity',
                            'capacity_net_bnetza': 'capacity',
                            'efficiency_estimate': 'efficiency'})

    if len(df.loc[df.lon.isnull()]) > 0:
        df = complete_opsd_geometries(df, fs_column='state')
    else:
        logging.info("Skipped 'complete_opsd_geometries' function.")

    # Remove power plants with no capacity:
    number = len(df[df['capacity'].isnull()])
    df = df[df['capacity'].notnull()]
    if number > 0:
        msg = "{0} power plants have been removed, because the capacity was 0."
        logging.warning(msg.format(number))

    # To save disc and RAM capacity unused column are removed.
    if remove_list is not None:
        df = remove_cols(df, remove_list)

    ppr_tools.prepare_dates(df=df, date_cols=date_cols,
                            month=month)

    # capacity in W
    df['capacity'] = df['capacity'] * (10 ** 6)

    df.to_csv(prepared_filename)
    return df


def filter_pp_by_source_and_year(year, energy_source, keep_cols=None):  # todo evtl get
    r"""
    Returns by `energy_source` and `year` filtered OPSD register.

    If the `energy_source` is 'Wind' typical wind turbine types depending on
    the wind zones as well as wind power plant specific data is added to the
    register (see :py:func:`~.assign_turbine_data_by_wind_zone`).

    Parameters
    ----------
    year : int
        Power plants already installed and still running during this year are
        contemplated.
    energy_source : string
        Energy source as named in column 'energy_source_level_2' of register.
    keep_cols : list or None
        Column names to be selected from OPSD register. If None, all columns
        are kept. Default: 'None'.

    Returns
    -------
    filtered_register : pd.DataFrame
        ...
    """
    df = prepare_opsd_file(overwrite=False)
    if energy_source not in ['Wind', 'Solar']:
        logging.warning("category must be 'Wind' or 'Solar'")
    register = df.loc[df['energy_source_level_2'] == energy_source]
    register = ppr_tools.remove_pp_with_missing_coordinates(
        register=register, category=energy_source, register_name='opsd')

    # filter by year
    filtered_register = ppr_tools.get_pp_by_year(year=year,
                                                 register=register)
    if keep_cols is not None:
        filtered_register = filtered_register[keep_cols]
    if energy_source == 'Wind':
        filtered_register = assign_turbine_data_by_wind_zone(filtered_register)
    return filtered_register


def assign_turbine_data_by_wind_zone(register):
    r"""
    Assigns turbine data to a power plant register depending on wind zones.
    todo: source?! DIBt.
    todo: load from oedb when they are there
    todo: move to feedinlib when oedb load works
    The wind zones are read from a shape file in the directory
    'data/geometries'. Turbine types are selected per wind zone as typical
    turbine types for coastal, near-coastal, inland, far-inland areas. You can
    use your own file and specify your own turbine types per wind zone by
    adjusting the data in feedin_germany.ini.

    The following data is added as columns to `register`:
    - turbine type in column 'name',
    - hub height in m in column 'hub_height' and
    - rotor diameter in m in column 'rotor_diameter',
    - unambiguous turbine id in column 'id' with the pattern
      'name_height_diameter'.

    Parameters
    ----------
    register : pd.DataFrame
        Power plants register. Contains power plants' locations in columns
        'lat' and 'lon'. Other columns are ignored but are part of the output.

    Returns
    -------
    adapted_register : pd.DataFrame
        `register` which additionally contains turbine type ('name'), hub
        height in m ('hub_height'), rotor diameter in m ('rotor_diameter') and
        unambiguous turbine id ('id').

    """
    wind_zones = db_tools.load_data_from_oedb_with_oedialect(
        schema='model_draft', table_name='rli_dibt_windzone')
    wind_zones = wind_zones[['dibt_wind_zone', 'geom']]
    wind_zones.set_index('dibt_wind_zone', inplace=True)

    # create geopandas.DataFrame from register
    register['coordinates'] = list(zip(register['lon'], register['lat']))
    register['geometry'] = register['coordinates'].apply(Point)
    gdf_register = gpd.GeoDataFrame(register, geometry='geometry')
    # add wind zones by sjoin
    jgdf = gpd.sjoin(gdf_register, wind_zones, how='left', op='within').rename(
        columns={'index_right': 'wind_zone'})
    # set missing wind zones to 4
    jgdf.loc[jgdf['wind_zone'].isnull(), 'wind_zone'] = 4.0
    adapted_register = pd.DataFrame(jgdf).drop(['coordinates',
                                                'geometry'], axis=1)

    # add data of typical turbine types to wind zones
    wind_zones['name'] = [cfg.get('wind_set{}'.format(wind_zone), 'name')
                          for wind_zone in wind_zones.index]
    wind_zones['hub_height'] = [
        int(cfg.get('wind_set{}'.format(wind_zone), 'hub_height'))
        for wind_zone in wind_zones.index]
    wind_zones['rotor_diameter'] = [
        int(cfg.get('wind_set{}'.format(wind_zone), 'rotor_diameter'))
        for wind_zone in wind_zones.index]
    wind_zones['id'] = [
        cfg.get('wind_set{}'.format(wind_zone), 'set_name')
        for wind_zone in wind_zones.index]  # todo with less code

    # add data of typical turbine types by wind zone to power plant register
    adapted_register = pd.merge(adapted_register, wind_zones[
        ['name', 'hub_height', 'rotor_diameter', 'id']], how='inner',
                                left_on='wind_zone', right_index=True)
    return adapted_register


if __name__ == "__main__":
    test_wind = True
    #load_original_opsd_file(category='renewable', overwrite=True, latest=False)
    print(filter_pp_by_source_and_year(2012, 'Solar'))

    # if test_wind:
    #     keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity',
    #                  'com_year', 'decom_year', 'com_month', 'decom_month']
    #     wind_register = filter_pp_by_source_and_year(
    #         year=2012, energy_source='Wind', keep_cols=keep_cols)
    #     adapted_wind_register = assign_turbine_data_by_wind_zone(
    #         register=wind_register)
    #     print(adapted_wind_register[0:10])
