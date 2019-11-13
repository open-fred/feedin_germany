#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
todo add description
"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import pandas as pd
import geopandas as gpd

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from shapely.geometry import Point
import shapely
import oedialect
from shapely.ops import cascaded_union


def as_pandas(query, geometry="geom", params=None, crs=None, hex=True):
    r"""
    returns Geopandas.DataFrame from query with Point/Polygon geometry

    parameters
    ----------
    query: session-query()
    geometry: str
    hex: boolean

    return
    ---------
    Geopandas.DataFrame
    """
    df = pd.read_sql(query.statement, query.session.bind, params=params)

    if geometry not in df:
        raise ValueError("Query missing geometry column '{}'".format(geometry))

    if len(df) > 0:
        obj = df[geometry].iloc[0]
        if crs is None:
            crs = dict(init=f"epsg:{obj.srid}")
        df[geometry] = df[geometry].map(lambda s: shapely.wkb.loads(str(s),
                                        hex=hex))

    return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)


def load_regions_file(region_type='tso'):
    """
    Loads a region file from the oedb.

    Parameters
    ----------
    region_type : str
        Defines the region type:  Transmission System Operator ('tso'), or
        administrative districts ('landkreise'). Default: 'tso'.

    Notes
    ----------------
    todo: login and token need to be adapted/automatized
    todo: possibility of selecting different region files - Landkreise, Übertragunsnetzbetreiberzonen, ...
    todo: engine creation as separate function  ---> see database_tools (already used in opsd_power_plants for windzones)
    todo: Speicherung, damit offline verwendbar, wenn OEP nicht funktioniert.
    returns
    --------------
    geopandas.GeoDataFrame
        with the nuts-id and the geom as shaply polygons

    """
    # Create Engine:
    user = ''
    token = ''
    engine = sa.create_engine(
            f'postgresql+oedialect://{user}:{token}@openenergy-platform.org')

    Base = declarative_base(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if region_type == 'landkreise':
        class BkgVg2502Lan(Base):
            __tablename__ = "bkg_vg250_4_krs"
            __table_args__ = {'schema': 'boundaries', 'autoload': True}

        try:
            # Stuff in session
            p = session.query(BkgVg2502Lan)
            gdf = as_pandas(p, geometry="geom", params=None, crs=None,
                            hex=True)
            gdf_new = gdf.to_crs(epsg=4326)

            session.commit()
        except:
            session.rollback()
        finally:
            session.close()

        landkreise_shape = gdf_new[['nuts', 'geom']]

        for nut_id in landkreise_shape.nuts.unique():
            tmp_df = landkreise_shape[landkreise_shape.nuts == nut_id]
            if len(tmp_df) > 1:
                polyg = cascaded_union(tmp_df.geom)
                counter = 0
                for index, row in tmp_df.iterrows():
                    if counter == 0:
                        landkreise_shape.loc[index, 'geom'] = polyg
                    else:
                        landkreise_shape.drop(index=[index], inplace=True)
                    counter += 1

        # landkreise_shape.to_file('landkreise_dump_dropped_duplicates.shp') # todo autmatic save

        return landkreise_shape

    if region_type == 'tso':

        import os
        import pickle

        regions_file = os.path.join(
            os.path.dirname(__file__), 'data/dumps/tso.pkl')

        if os.path.exists(regions_file):
            return pickle.load(open(regions_file, 'rb'))

        class Ffe_tso_controlarea(Base):
            __tablename__ = "ffe_tso_controlarea"
            __table_args__ = {'schema': 'model_draft', 'autoload': True}

        try:
            # Stuff in session
            p = session.query(Ffe_tso_controlarea)
            gdf = as_pandas(p, geometry="geom", params=None, crs=None,
                            hex=True)
            gdf_new = gdf.to_crs(epsg=4326)

            session.commit()
        except:
            session.rollback()
        finally:
            session.close()

        gdf_new.rename(columns={"uenb": "nuts"}, inplace=True)
        pickle.dump(gdf_tso, open(regions_file, 'wb'))

        return (gdf_new[['nuts', 'geom']])


def add_region_to_register(register, region):
    """
    filters out all powerplants within a region for a given region and register
    # todo Frage an Inia: die Funktion fügt nur die Spalte mit nuts hinzu, keine Filterung oder?

    Input
    ---------------
    'register': pandas.DataFrame
        with columns lat, lon
    'region': geopandas.GeoDataFrame
        with only one row for the specific region

    returns
    --------------
    pandas.DataFrame
        with the nuts-id and the geom as shaply polygon

    """
    # transform the lat/lon coordinates into a shapely point coordinates and
    # add column named "coordinates"
    register['Coordinates'] = list(zip(register.lon, register.lat))
    register['Coordinates'] = register['Coordinates'].apply(Point)
    register_gdf = gpd.GeoDataFrame(register, geometry='Coordinates')
    #region_gdf = gpd.GeoDataFrame(region, geometry='geom')
    new_register = gpd.sjoin(register_gdf, region, op='within')

    return new_register


if __name__ == "__main__":

    gdf = load_regions_file(region_type='landkreise')
    gdf_tso = load_regions_file(region_type='tso')

    # dump tso gdf
    import os
    import pickle
    regions_file = os.path.join(
        os.path.dirname(__file__), 'data/dumps/tso.pkl')
    pickle.dump(gdf_tso, open(regions_file, 'wb'))
    # filter Hamburg
    Hamburg_gdf = gdf[gdf['nuts'].apply(
        lambda x: True if 'DE6' in x else False)]
    Hamburg_gdf.to_file('hamburg.shp')
    print(gdf)
    