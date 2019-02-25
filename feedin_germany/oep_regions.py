#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 21 10:05:23 2019

@author: RL-INSTITUT\inia.steinbach
"""

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
    df = pd.read_sql(query.statement, query.session.bind, params=params)
   
    if geometry not in df:
        raise ValueError("Query missing geometry column '{}'".format(geometry))

    if len(df) > 0:
        obj = df[geometry].iloc[0]
        if crs is None:
            crs = dict(init=f"epsg:{obj.srid}")
        df[geometry] = df[geometry].map(lambda s: shapely.wkb.loads(str(s), hex=hex))

    return gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

def load_regions_file():
    """
    loads the region file from the oep-database
    
    Notes
    ----------------
    login and token need to be adapted/automatized
    
    returns
    --------------
    geopandas.GeoDataFrame with the nuts-id and the geom as shaply polygons
    
    """
    # Create Engine:
    user = 'Inia Steinbach'
    token = 'ed027eb9f85a0444188a997f5ed65ee4c81f2317'
    engine = sa.create_engine(f'postgresql+oedialect://{user}:{token}@openenergy-platform.org')

    Base = declarative_base(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    class BkgVg2502Lan(Base):
        __tablename__ =  "bkg_vg250_4_krs"
        __table_args__ = {'schema': 'boundaries', 'autoload': True}

    try:
        # Stuff in session
        p = session.query(BkgVg2502Lan)
        #gdf = gpd.read_postgis(p.statement, session.bind)
        gdf=as_pandas(p, geometry="geom", params=None, crs=None, hex=True)
        gdf_new=gdf.to_crs(epsg=4326)
        
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

    #gdf.to_csv('regions.csv')
    return(gdf_new[['nuts', 'geom']])
    
    
def register_per_region(register, region):
    
    """
    filters out all powerplants within a region for a given region and register
    
    Notes
    ----------------
    login and token need to be adapted/automatized
    
    Input
    ---------------
    register: pandas.DataFrame with collumns lat, lon
    region: geopandas.GeoDataFrame with only one row for the specific region
    
    returns
    --------------
    pandas.DataFrame with the nuts-id and the geom as shaply polygon
    
    """ 
    #register=opsd.filter_solar_pp()
    #regions = load_regions_file()
    
    # transform the lat/lon coordinates into a shapely point coordinates and add column named "coordinates"
    register['Coordinates'] = list(zip(register.lon, register.lat))
    register['Coordinates'] = register['Coordinates'].apply(Point)
    # create GeoDataFrames
    register_gdf = gpd.GeoDataFrame(register, geometry='Coordinates')
    region_gdf = gpd.GeoDataFrame(region, geometry='geom')
    # spacial join on the register
    new_register=gpd.sjoin(register_gdf, region_gdf, op='within')
    #new_register.plot()
    return(new_register)

if __name__ == "__main__":
#load_original_opsd_file(category='renewable', overwrite=True, latest=False)
    print(load_regions_file())