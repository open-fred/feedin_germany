# -*- coding: utf-8 -*-

""" This module is designed for the use with the coastdat2 weather data set
of the Helmholtz-Zentrum Geesthacht.

A description of the coastdat2 data set can be found here:
https://www.earth-syst-sci-data.net/6/147/2014/

Copyright (c) 2016-2018 Uwe Krien <uwe.krien@rl-institut.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Uwe Krien <uwe.krien@rl-institut.de>"
__license__ = "GPLv3"


# Python libraries
import os
import datetime
import logging
import requests
import shutil
import configparser
import calendar

# External libraries
import pandas as pd
import pvlib
import shapely.wkt as wkt

# oemof libraries
from oemof.tools import logger

# Internal modules
import reegis.tools as tools
import reegis.feedin as feedin
import reegis.config as cfg
import reegis.powerplants as powerplants
import reegis.geometries as geometries
import reegis.bmwi

# Optional: database tool.
try:
    import oemof.db.coastdat as coastdat
    import oemof.db as db
    from sqlalchemy import exc
except ImportError:
    coastdat = None
    db = None
    exc = None

"""
dieses Skipt soll coastdat.py in reegis ersetzten und die openfred-Wetterdaten benutzen. Bisher sind enthalten:
    
    *normalised_feedin_for_each_data_set() -> vorher in reegis/coastdat.py
    *aggregate_by_region_openfred_feedin() -> vorher in reegis/coastdat.py
    *aggregate_by_region_openfred -> vorher in deflex/feedin.py
    
die Fuktion normalised_feedin_for_each_data_set() wurde für die openfred-Wetterdaten angepasst, 
Achtung: die namen der Wetterdaten im ini-file haben sich möglicherweise geändert!
Es wurde bisher nur eine einfache Spalte mit einer ID als referenz zu einem Wetterpunkt hinzugefügt, das muss noch geändert werden!!
Wind wurde bisher auskommentiert, da ich nicht wusste wie hier auf die Funktionen zugegriffen wird. (siehe ganz unten in der Funktion)
"""


def normalised_feedin_for_each_data_set(year, wind=True, solar=True,
                                        overwrite=False):
    """
    Loop over all weather data sets (regions) and calculate a normalised time
    series for each data set with the given parameters of the power plants.

    This file could be more elegant and shorter but it will be rewritten soon
    with the new feedinlib features.

    year : int
        The year of the weather data set to use.
    wind : boolean
        Set to True if you want to create wind feed-in time series.
    solar : boolean
        Set to True if you want to create solar feed-in time series.

    Returns
    -------

    """

    # Open coastdat-weather data csv file for the given year 
    #weather_file_name = os.path.join(cfg.get('paths', 'openfred_weather'),
    #                 cfg.get('openfred_weather', 'name##').format(year=year)) ## Hier Anpassen!
    #if not os.path.isfile(weather_file_name):
    #    print('no weather_file found')
        
	# IST: reading the weather-data and add a new collumn for data_points 
    weather=pd.read_csv(
            os.path.join(cfg.get('paths', 'openfred'), 
                         cfg.get('openfred', 'openfred_weather_file')), index_col='time')
    
    weather['data_points'] = weather.groupby(['lat','lon']).ngroup() + 1
    
    # Fetch openfred data heights from ini file.
    #IST : Frage: Was sind die data heights? wofürbrauchen wir die?
    data_height = cfg.get_dict('openfred_data_height')
    # Create basic file and path pattern for the resulting files
    openfred_path = os.path.join(cfg.get('paths_pattern', 'openfred_output'))
    feedin_file = os.path.join(openfred_path,
                               cfg.get('feedin', 'file_pattern'))

    # Fetch coastdat region-keys from weather file.
    #key_file_path = coastdat_path.format(year='', type='')[:-2]
    #key_file = os.path.join(key_file_path, 'coastdat_keys.csv')
    #if not os.path.isfile(key_file):
    #    coastdat_keys = weather.keys()
    #    if not os.path.isdir(key_file_path):
    #        os.makedirs(key_file_path)
    #    pd.Series(coastdat_keys).to_csv(key_file)
    #else:
    #    coastdat_keys = pd.read_csv(key_file, index_col=[0],
 #                                   squeeze=True, header=None)

    txt_create = "Creating normalised {0} feedin time series for {1}."
    hdf = {'wind': {}, 'solar': {}}
    if solar:
        logging.info(txt_create.format('solar', year))
        # Add directory if not present
        os.makedirs(openfred_path.format(year=year, type='solar'),
                    exist_ok=True)
        # Create the pv-sets defined in the solar.ini
        pv_sets = feedin.create_pvlib_sets()

        # Open a file for each main set (subsets are stored in columns)
        for pv_key, pv_set in pv_sets.items():
            filename = feedin_file.format(
                type='solar', year=year, set_name=pv_key)
            if not os.path.isfile(filename) or overwrite:
                hdf['solar'][pv_key] = pd.HDFStore(filename, mode='w')
    else:
        pv_sets = {}

    if wind:
        logging.info(txt_create.format('wind', year))
        # Add directory if not present
        os.makedirs(openfred_path.format(year=year, type='wind'),
                    exist_ok=True)
        # Create the pv-sets defined in the wind.ini
        wind_sets = feedin.create_windpowerlib_sets()
        # Open a file for each main set (subsets are stored in columns)
        for wind_key, wind_set in wind_sets.items():
            filename = feedin_file.format(
                type='wind', year=year, set_name=wind_key)
            if not os.path.isfile(filename) or overwrite:
                hdf['wind'][wind_key] = pd.HDFStore(filename, mode='w')
    else:
        wind_sets = {}

    # Define basic variables for time logging
   # remain = len(weather['data_points'].max())
   # done = 0
   # start = datetime.datetime.now()

    # IST: Loop over all regions by looping over data-points
    for data_point in weather['data_points']:
        # Get weather data set for one location
        local_weather_pv = weather.loc[weather['data_points'] == data_point, ['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']]

        # Adapt the coastdat weather format to the needs of pvlib.
        # The expression "len(list(hdf['solar'].keys()))" returns the number
        # of open hdf5 files. If no file is open, there is nothing to do.
        #IST: geändert zu der folgenden Zeile. Eventuell überarbeiten, wenn die Datenpunkte nicht der Reihe nach eingelesen werden!!
        if weather['data_points'].max()- data_point >= 0:										###### ??????????
            # IST: Get coordinates for the weather location
            local_points = weather.loc[weather['data_points'] == data_point, ['lat', 'lon']].head(1).reset_index()

            # IST Create a pvlib Location object
            location = pvlib.location.Location(
                latitude=local_points['lat'], longitude=local_points['lon'])

            # Create one DataFrame for each pv-set and store into the file
            for pv_key, pv_set in pv_sets.items():
                if pv_key in hdf['solar']:
                    hdf['solar'][pv_key][data_point] = feedin.feedin_pv_sets(
                        local_weather_pv, location, pv_set)

        # Create one DataFrame for each wind-set and store into the file
 #       if wind and len(list(hdf['wind'].keys())) > 0:
 #           local_weather_wind = adapt_coastdat_weather_to_windpowerlib(
 #               local_weather, data_height)
 #           for wind_key, wind_set in wind_sets.items():
 #               if wind_key in hdf['wind']:
 #                   hdf['wind'][wind_key][coastdat_key] = (
 #                       feedin.feedin_wind_sets(
 #                           local_weather_wind, wind_set))

        # Start- time logging *******
   #     remain -= 1
   #     done += 1
   #     if divmod(remain, 10)[1] == 0:
   #         elapsed_time = (datetime.datetime.now() - start).seconds
   #         remain_time = elapsed_time / done * remain
   #         end_time = datetime.datetime.now() + datetime.timedelta(
   #             seconds=remain_time)
   #         msg = "Actual time: {:%H:%M}, estimated end time: {:%H:%M}, "
   #         msg += "done: {0}, remain: {1}".format(done, remain)
   #         logging.info(msg.format(datetime.datetime.now(), end_time))
        # End - time logging ********

#    for k1 in hdf.keys():
#        for k2 in hdf[k1].keys():
#            hdf[k1][k2].close()
#    weather.close()
    logging.info("All feedin time series for {0} are stored in {1}".format(
        year, coastdat_path.format(year=year, type='')))

def aggregate_by_region_openfred_feedin(pp, regions, year, category, outfile,
                                        weather_year=None):
    cat = category.lower()
    logging.info("Aggregating {0} feed-in for {1}...".format(cat, year))
    if weather_year is None:
        weather_year = year
        weather_year_str = ""
    else:
        logging.info("Weather data taken from {0}.".format(weather_year))
        weather_year_str = " (weather: {0})".format(weather_year)

    # Define the path for the input files.
    openfred_path = os.path.join(cfg.get('paths_pattern', 'openfred_output')).format(
        year=weather_year, type=cat)
    if not os.path.isdir(openfred_path):
        normalised_feedin_for_each_data_set(weather_year)
    # Prepare the lists for the loops
    set_names = []
    set_name = None
    pwr = dict()
    columns = dict()
    replace_str = 'openfred_{0}_{1}_'.format(weather_year, category)
    for file in os.listdir(openfred_path):
        if file[-2:] == 'h5':
            set_name = file[:-3].replace(replace_str, '')
            set_names.append(set_name)
            pwr[set_name] = pd.HDFStore(os.path.join(openfred_path, file))
            columns[set_name] = pwr[set_name]['/A1129087'].columns

    # Create DataFrame with MultiColumns to take the results
    my_index = pwr[set_name]['/A1129087'].index
    my_cols = pd.MultiIndex(levels=[[], [], []], labels=[[], [], []],
                            names=[u'region', u'set', u'subset'])
    feed_in = pd.DataFrame(index=my_index, columns=my_cols)

    # Loop over all aggregation regions
    # Sum up time series for one region and divide it by the
    # capacity of the region to get a normalised time series.
    for region in regions:
        try:
            openfred_ids = pp.loc[(category, region)].index
        except KeyError:
            openfred_ids = []
        number_of_openfred_ids = len(openfred_ids)
        logging.info("{0}{3} - {1} ({2})".format(
            year, region, number_of_openfred_ids, weather_year_str))
        logging.debug("{0}".format(openfred_ids))

        # Loop over all sets that have been found in the openfred path
        if number_of_openfred_ids > 0:
            for name in set_names:
                # Loop over all sub-sets that have been found within each file.
                for col in columns[name]:
                    temp = pd.DataFrame(index=my_index)

                    # Loop over all coastdat ids, that intersect with the
                    # actual region.
                    for openfred_id in openfred_ids:
                        # Create a tmp table for each coastdat id.
                        openfred_key = '/A{0}'.format(int(openfred))
                        pp_inst = float(pp.loc[(category, region, openfred_id),
                                               'capacity_{0}'.format(year)])
                        temp[openfred_key] = (
                            pwr[name][openfred_key][col][:8760].multiply(
                                pp_inst))
                    # Sum up all coastdat columns to one region column
                    colname = '_'.join(col.split('_')[-3:])
                    feed_in[region, name, colname] = (
                        temp.sum(axis=1).divide(float(
                            pp.loc[(category, region), 'capacity_{0}'.format(
                                year)].sum())))

    feed_in.to_csv(outfile)
    for name_of_set in set_names:
        pwr[name_of_set].close()

def aggregate_by_region_openfred(year, pp=None, weather_year=None):
    # Create the path for the output files.
    feedin_openfredval_path = cfg.get('paths_pattern', 'openfredval_feedin').format(
        year=year, map=cfg.get('init', 'map'))

    if weather_year is not None:
        feedin_openfredval_path = os.path.join(feedin_openfredval_path,
                                          'weather_variations')

    os.makedirs(feedin_openfredval_path, exist_ok=True)

    # Create pattern for the name of the resulting files.
    if weather_year is None:
        feedin_openfredval_outfile_name = os.path.join(
            feedin_openfredval_path,
            cfg.get('feedin', 'feedin_openfredval_pattern').format(
                year=year, type='{type}', map=cfg.get('init', 'map')))
    else:
        feedin_openfredval_outfile_name = os.path.join(
            feedin_openfredval_path,
            cfg.get('feedin', 'feedin_openfredval_pattern_var').format(
                year=year, type='{type}', map=cfg.get('init', 'map'),
                weather_year=weather_year))

    # Filter the capacity of the powerplants for the given year.
    if pp is not None:
        region_column = '{0}_region'.format(cfg.get('init', 'map'))
        pp = pp.groupby(
            ['energy_source_level_2', region_column, 'coastdat2']).sum()
    else:
        pp = get_grouped_power_plants(year)

    regions = pp.index.get_level_values(1).unique().sort_values()

    # Loop over weather depending feed-in categories.
    # WIND and PV
    for cat in ['Wind', 'Solar']:
        outfile_name = feedin_openfredval_outfile_name.format(type=cat.lower())
        if not os.path.isfile(outfile_name):
            reegis.coastdat.aggregate_by_region_coastdat_feedin(
                pp, regions, year, cat, outfile_name, weather_year)

    # HYDRO
    outfile_name = feedin_openfredval_outfile_name.format(type='hydro')
    if not os.path.isfile(outfile_name):
        reegis.coastdat.aggregate_by_region_hydro(
            pp, regions, year, outfile_name)

    # GEOTHERMAL
    outfile_name = feedin_openfredval_outfile_name.format(type='geothermal')
    if not os.path.isfile(outfile_name):
        reegis.coastdat.aggregate_by_region_geothermal(
            regions, year, outfile_name)


if __name__ == "__main__":
    logger.define_logging()
    
normalised_feedin_for_each_data_set(2016, wind=False, solar=True,
                                        overwrite=False)