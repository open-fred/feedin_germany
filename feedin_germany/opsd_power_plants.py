# -*- coding: utf-8 -*-

"""Download and process the opsd power plants for Germany.

functions:
    * load_original_opsd_file()
    * convert_utm_code_opsd
    * guess_coordinates_by_postcode_opsd()
    * log_undefined_capacity
    * complete_opsd_geometries()
    * remove_cols()
    * prepare_dates()
    * prepare_opsd_file()
    * filter_solar_pp()
    * filter_wind_pp()
    
    
Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
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
from shapely.geometry import Point, Polygon

# oemof libraries
from oemof.tools import logger

# Internal modules
from feedin_germany import config as cfg
#import reegis.geometries as geo
from feedin_germany import geometries

# todo: delete unnecessary imports

def load_original_opsd_file(category, overwrite, latest=False):
    """Read file if exists."""
    
    opsd_directory = cfg.get('paths', 'opsd')
    print(opsd_directory)
    orig_csv_file = os.path.join(
        os.path.dirname(__file__), cfg.get('paths', 'opsd'),
        cfg.get('opsd', 'original_file_pattern').format(cat=category))

    if latest:
        url_section = 'opsd_url_latest'
    else:
        url_section = 'opsd_url_2017'

    # Download non existing files. If you think that there are newer files you
    # have to set overwrite=True to overwrite existing with downloaded files.
    if not os.path.exists(opsd_directory):
        os.makedirs(opsd_directory, exist_ok=True)

    if not os.path.isfile(orig_csv_file) or overwrite:
        logging.warning("File not found. Try to download it from server.")
        logging.warning("Check URL if download does not work.")
        req = requests.get(cfg.get(url_section, '{0}_data'.format(category)))
        with open(orig_csv_file, 'wb') as fout:
            fout.write(req.content)
        logging.warning("Downloaded from {0} and copied to '{1}'.".format(
            cfg.get(url_section, '{0}_data'.format(category)), orig_csv_file))
        req = requests.get(cfg.get(url_section, '{0}_readme'.format(category)))
        with open(
                os.path.join(
                    cfg.get('paths', 'opsd'),
                    cfg.get('opsd', 'readme_file_pattern').format(
                        cat=category)), 'wb') as fout:
            fout.write(req.content)
        req = requests.get(cfg.get(url_section, '{0}_json'.format(category)))
        with open(os.path.join(
                cfg.get('paths', 'opsd'),
                cfg.get('opsd', 'json_file_pattern').format(
                    cat=category)), 'wb') as fout:
            fout.write(req.content)

    if category == 'renewable':
        df = pd.read_csv(orig_csv_file)
    else:
        logging.error("Unknown category! Allowed: 'conventional, 'renewable'")
        df = None
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
                             cfg.get('geometry', 'postcode_polygon')),
                index_col='zip_code')
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


def complete_opsd_geometries(df, category, time=None,
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
        dir_messages=cfg.get('paths', 'messages')
        if not os.path.exists(dir_messages):
            os.makedirs(dir_messages, exist_ok=True)
        df.loc[incomplete].to_csv(os.path.join(
            os.path.dirname(__file__), cfg.get('paths', 'messages'),
            '{0}_incomplete_geometries_before.csv'.format(category)))

    incomplete = df.lon.isnull()
    if incomplete.any():
        df.loc[incomplete].to_csv(os.path.join(
            os.path.dirname(__file__), cfg.get('paths', 'messages'),
            '{0}_incomplete_geometries_after.csv'.format(category)))
    logging.debug("Gaps stored to: {0}".format(cfg.get('paths', 'messages')))

    statistics['total_capacity'] = total_capacity
    statistics.to_csv(os.path.join(
        os.path.dirname(__file__), cfg.get('paths', 'messages'),
        'statistics_{0}_pp.csv'.format(category)))

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


def prepare_dates(df, date_cols, month):
    # Commission year from float or string
    if df[date_cols[0]].dtype == np.float64:
        df['com_year'] = df[date_cols[0]].fillna(1800).astype(np.int64)
    else:
        df['com_year'] = pd.to_datetime(df[date_cols[0]].fillna(
            '1800-01-01')).dt.year

    # Decommission year from float or string
    if df[date_cols[1]].dtype == np.float64:
        df['decom_year'] = df[date_cols[1]].fillna(2050).astype(np.int64)
    else:
        df['decom_year'] = pd.to_datetime(df[date_cols[1]].fillna(
            '2050-12-31')).dt.year

    if month:
        df['com_month'] = pd.to_datetime(df[date_cols[0]].fillna(
            '1800-01-01')).dt.month
        df['decom_month'] = pd.to_datetime(df[date_cols[1]].fillna(
            '2050-12-31')).dt.month
    else:
        df['com_month'] = 6
        df['decom_month'] = 6

def prepare_opsd_file(category, overwrite):
    # Load original opsd file
    df = load_original_opsd_file(category, overwrite)

    # Load original file and set differences between conventional and
    # renewable power plants.
    if category == 'renewable':
        # capacity_column = 'electrical_capacity'
        remove_list = [
                'tso', 'dso', 'dso_id', 'eeg_id', 'bnetza_id', 'federal_state',
                'postcode', 'municipality_code', 'municipality', 'address',
                'address_number', 'utm_zone', 'utm_east', 'utm_north',
                'data_source']
        date_cols = ('commissioning_date', 'decommissioning_date')
        month = True

    else:
        logging.error("Unknown category!")
        return None
        # This function is adapted to the OPSD data set structure and might not
        # work with other data sets. Set opsd=False to skip it.

    df = df.rename(columns={'electrical_capacity': 'capacity',
                            'capacity_net_bnetza': 'capacity',
                            'efficiency_estimate': 'efficiency'})

    if len(df.loc[df.lon.isnull()]) > 0:
        df = complete_opsd_geometries(df, category, fs_column='state')
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

    prepare_dates(df, date_cols, month)

    #df.to_csv('prepared_opsd_data.csv')
    return df


def get_pp_by_year(year, register, overwrite_capacity=True):
    """

    Parameters
    ----------
    year : int
    overwrite_capacity : bool
        By default (False) a new column "capacity_<year>" is created. If set to
        True the old capacity column will be overwritten.

    Returns
    -------

    """
    pp = pd.DataFrame(register)

    filter_columns = ['capacity_{0}']

    # Get all powerplants for the given year.
    # If com_month exist the power plants will be considered month-wise.
    # Otherwise the commission/decommission within the given year is not
    # considered.

    for fcol in filter_columns:
        filter_column = fcol.format(year)
        orig_column = fcol[:-4]
        c1 = (pp['com_year'] < year) & (pp['decom_year'] > year)
        pp.loc[c1, filter_column] = pp.loc[c1, orig_column]

        c2 = pp['com_year'] == year
        pp.loc[c2, filter_column] = (pp.loc[c2, orig_column] *
                                     (12 - pp.loc[c2, 'com_month']) / 12)
        c3 = pp['decom_year'] == year
        pp.loc[c3, filter_column] = (pp.loc[c3, orig_column] *
                                     pp.loc[c3, 'com_month'] / 12)  # todo FRAGE @ Inia: beide Male com_month oder auch decom_month?

        if overwrite_capacity:
            pp[orig_column] = 0
            pp[orig_column] = pp[filter_column]
            del pp[filter_column]
        
        # delete all rows with com_year > year
        pp_filtered=pp.loc[pp['com_year'] < year+1]

    return pp_filtered


def filter_pp_by_source_and_year(year, energy_source, keep_cols=None):
    r"""
    Returns by energy source filtered OPSD register.

    Parameters
    ----------
    year : int
        todo
    energy_source : string todo: note: could be list but I think in feedinlib we only want registers separated by source
        Energy source as named in column 'energy_source_level_2' of register.
    keep_cols : list or None
        Column names to be selected from OPSD register. If None, all columns
        are kept. Default: 'None'.

    Returns
    -------
    register : pd.DataFrame
        ...
    """
    df = prepare_opsd_file(category='renewable', overwrite=False)
    register = df.loc[df['energy_source_level_2'] == energy_source]
    if keep_cols is not None:
        register = register[keep_cols]
    # remove_pp_with_missing_coordinates  # todo: check why they are missing. maybe adapt
    if register[['lat', 'lon']].isnull().values.any():
        amount = register[['lat', 'lon']].isnull().sum()[0]  # amount of lat
        register = register.dropna(subset=['lat', 'lon'])
        logging.warning(
            "Removed {} {} power plants with missing coordinates.".format(
                amount, energy_source.lower()))
    
    # filter_by_year
    register_filtered_by_year = get_pp_by_year(year=year, register=register)
    return register_filtered_by_year


def assign_turbine_data_by_wind_zone(register):
    r"""
    Assigns turbine data to a power plant register depending on wind zones.

    The wind zones are read from a shape file in the directory 'data/geometries' todo: source?! DIBt.
    Turbine types are selected per wind zone as typical turbine types for
    coastal, near-coastal, inland, far-inland areas. You can use your own file
    and specify your own turbine types per wind zone by adjusting the data in
    feedin_germany.ini.
    The following data is added as columns to `register`:
    - turbine type in column 'name',
    - hub height in column 'hub_height' and
    - rotor diameter in column 'rotor_diameter'.

    Parameters
    ----------
    register : pd.DataFrame
        Power plants register. Contains power plants' locations in columns
        'lat' and 'lon'. Other columns are ignored but are part of the output.

    Returns
    -------
    adapted_register : pd.DataFrame
        `register` which additionally contains turbine type ('name'), hub
        height ('hub_height') and rotor diameter ('rotor_diameter').

    """
    # get wind zones polygons
    path = cfg.get('paths', 'geometry')
    filename = cfg.get('geometry', 'wind_zones') # todo use dibt wind zones!!
    wind_zones = geometries.load(path=path, filename=filename)
    wind_zones.set_index('zone', inplace=True)

    # create geopandas.DataFrame from register
    register['coordinates'] = list(zip(register['lon'], register['lat']))
    register['geometry'] = register['coordinates'].apply(Point)
    gdf_register = gpd.GeoDataFrame(register, geometry='geometry')
    # add wind zones by sjoin
    jgdf = gpd.sjoin(gdf_register, wind_zones, how='left', op='within').rename(
        columns={'index_right': 'wind_zone'})
    adapted_register = pd.DataFrame(jgdf).drop(['coordinates',
                                                'geometry'], axis=1)

    # add data of typical turbine types to wind zones
    wind_zones['turbine_type'] = [cfg.get('wind_set{}'.format(wind_zone), 'name')
                                 for wind_zone in wind_zones.index]
    wind_zones['hub_height'] = [
        cfg.get('wind_set{}'.format(wind_zone), 'hub_height')
        for wind_zone in wind_zones.index]
    wind_zones['rotor_diameter'] = [
        cfg.get('wind_set{}'.format(wind_zone), 'rotor_diameter')
        for wind_zone in wind_zones.index]

    # add data of typical turbine types by wind zone to power plant register
    adapted_register = pd.merge(adapted_register, wind_zones[
        ['turbine_type', 'hub_height', 'rotor_diameter']], how='inner',
                        left_on='wind_zone', right_index=True)
    return adapted_register


if __name__ == "__main__":
    test_wind = True
    #load_original_opsd_file(category='renewable', overwrite=True, latest=False)
    logger.define_logging()
    print(filter_pp_by_source_and_year(2012, 'Solar'))

    # if test_wind:
    #     keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity',
    #                  'com_year', 'decom_year', 'com_month', 'decom_month']
    #     wind_register = filter_pp_by_source_and_year(
    #         year=2012, energy_source='Wind', keep_cols=keep_cols)
    #     adapted_wind_register = assign_turbine_data_by_wind_zone(
    #         register=wind_register)
    #     print(adapted_wind_register[0:10])
