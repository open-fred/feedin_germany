# -*- coding: utf-8 -*-
"""
The `geometries` module contains functions for loading geometry data from
different file types and for creating geopandas.GeoDataFrames.

The code in this module is based on third party code which has been licensed
under GNU-LGPL3. The following functions are copied from:
https://github.com/reegis/reegis
* load()
* load_shp()
* load_hdf()
* lat_lon2point()
* load_csv()
* create_geo_df()

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import os
import logging
import pandas as pd
import geopandas as gpd
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry


def load(path=None, filename=None, fullname=None, hdf_key=None,
         index_col=None, crs=None):
    """Load csv-file into a DataFrame and a GeoDataFrame."""
    if fullname is None:
        fullname = os.path.join(os.path.dirname(__file__), path, filename)

    if fullname[-4:] == '.csv':
        df = load_csv(fullname=fullname, index_col=index_col)
        gdf = create_geo_df(df, crs=crs)

    elif fullname[-4:] == '.hdf':
        df = pd.DataFrame(load_hdf(fullname=fullname, key=hdf_key))
        gdf = create_geo_df(df, crs=crs)

    elif fullname[-4:] == '.shp' or fullname[-8:] == '.geojson':
        gdf = load_shp(fullname=fullname)

    else:
        raise ValueError("Cannot load file with a '{0}' extension.")

    return gdf


def load_shp(path=None, filename=None, fullname=None):
    if fullname is None:
        fullname = os.path.join(os.path.dirname(__file__), path, filename)
    return gpd.read_file(fullname)


def load_hdf(path=None, filename=None, fullname=None, key=None):
    if fullname is None:
        fullname = os.path.join(os.path.dirname(__file__), path, filename)
    return pd.read_hdf(fullname, key, mode='r')


def lat_lon2point(df):
    """Create shapely point object of latitude and longitude."""
    return Point(df['longitude'], df['latitude'])


def load_csv(path=None, filename=None, fullname=None,
             index_col=None):
    """Load csv-file into a DataFrame."""
    if fullname is None:
        fullname = os.path.join(os.path.dirname(__file__), path, filename)
    df = pd.read_csv(fullname)

    # Make the first column the index if all values are unique.
    if index_col is None:
        first_col = df.columns[0]
        if not any(df[first_col].duplicated()):
            df.set_index(first_col, drop=True, inplace=True)
    else:
        df.set_index(index_col, drop=True, inplace=True)
    return df


def create_geo_df(df, wkt_column=None, lon_column=None, lat_column=None,
                  crs=None):
    """Convert pandas.DataFrame to geopandas.geoDataFrame"""
    if 'geom' in df:
        df = df.rename(columns={'geom': 'geometry'})

    if lon_column is not None:
        if lon_column not in df:
            logging.error("Cannot find column for longitude: {0}".format(
                lon_column))
        else:
            df.rename(columns={lon_column: 'longitude'}, inplace=True)

    if lat_column is not None:
        if lat_column not in df:
            logging.error("Cannot find column for latitude: {0}".format(
                lat_column))
        else:
            df.rename(columns={lat_column: 'latitude'}, inplace=True)

    if wkt_column is not None:
        df['geometry'] = df[wkt_column].apply(wkt_loads)

    elif 'geometry' not in df and 'longitude' in df and 'latitude' in df:

        df['geometry'] = df.apply(lat_lon2point, axis=1)

    elif isinstance(df.iloc[0]['geometry'], str):
        df['geometry'] = df['geometry'].apply(wkt_loads)
    elif isinstance(df.iloc[0]['geometry'], BaseGeometry):
        pass
    else:
        msg = "Could not create GeoDataFrame. Missing geometries."
        logging.error(msg)
        return None

    if crs is None:
        crs = {'init': 'epsg:4326'}

    gdf = gpd.GeoDataFrame(df, crs=crs, geometry='geometry')

    logging.debug("GeoDataFrame created.")

    return gdf


def load_polygon(region='uckermark'):
    path = '/home/sabine/Daten_flexibel_01/Wetterdaten/ERA5/'
    if region == 'uckermark':
        filename = os.path.join(path, 'uckermark.geojson')
    elif (region == 'germany' or region == 'brandenburg'):
        filename = os.path.join(path, 'germany', 'germany_nuts_1.geojson')
    regions = gpd.read_file(filename)
    if region == 'uckermark':
        regions.rename(columns={'NUTS': 'nuts'}, inplace=True)
    if region == 'brandenburg':
        regions = regions[regions['nuts'] == 'DE40F']
        regions.index = [0]
    return regions[['geometry', 'nuts']]
