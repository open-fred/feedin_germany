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
from geoalchemy2.types import Geometry
from sqlalchemy import func
import oedialect
from shapely.geometry import Point
import shapely

from feedin_germany import config as cfg
from feedin_germany import opsd_power_plants as opsd


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


def load_regions_file(type='tso'):
    """
    Loads a region file from the oedb.

    Parameters
    ----------
    type : str
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

    if type == 'landkreise':
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

        return (gdf_new[['nuts', 'geom']])

    if type == 'tso':
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
    region_gdf = gpd.GeoDataFrame(region, geometry='geom')
    new_register = gpd.sjoin(register_gdf, region_gdf, op='within')

    return(new_register)


if __name__ == "__main__":
#    load_original_opsd_file(category='renewable', overwrite=True,
#                            latest=False)
    print(load_regions_file())
    