#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:49:34 2019

@author: RL-INSTITUT\inia.steinbach
"""
import os
import reegis.config as cfg
import pandas as pd
import getpass
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import oedialect

from sqlalchemy import ARRAY, BigInteger, Column, Date, DateTime, Float, Integer, Numeric, SmallInteger, String, Table, Text, text
from geoalchemy2.types import Geometry
from sqlalchemy.ext.declarative import declarative_base
import geopandas

def get_oep_landkreise():
    # Whitespaces are not a problem for setting up the url!
    user = 'Inia Steinbach'
    token = 'ed027eb9f85a0444188a997f5ed65ee4c81f2317'
    
    
    # Create Engine:
    OEP_URL = 'oep.iks.cs.ovgu.de'
    OED_STRING = f'postgresql+oedialect://{user}:{token}@{OEP_URL}'
    
    engine = sa.create_engine(OED_STRING)
    metadata = sa.MetaData(bind=engine)
    
    # session
    Session=sessionmaker(autocommit=False, autoflush=False)
    session = Session(bind=engine)
    
    Base = declarative_base()
    metadata = Base.metadata
    
    t_bkg_vg250_4_krs_mview = Table(
    'bkg_vg250_4_krs_mview', metadata,
    Column('reference_date', Text),
    Column('id', Integer, unique=True),
    Column('gen', Text),
    Column('bez', Text),
    Column('nuts', String(5)),
    Column('rs_0', String(12)),
    Column('ags_0', String(12)),
    Column('area_ha', Float(53)),
    Column('geom', Geometry('MULTIPOLYGON', 3035), index=True),
    schema='boundaries'
    )
    
    landkreise =session.query(t_bkg_vg250_4_krs_mview.columns.nuts, 
                         t_bkg_vg250_4_krs_mview.columns.geom)

    filename_out=os.path.join(cfg.get('paths', 'geometry'),
                               cfg.get('geometry', 'region_polygon'))
    
    ld = pd.DataFrame(landkreise)
    ld.to_csv(filename_out)

    return landkreise


def get_openego_powerplants():
    # Whitespaces are not a problem for setting up the url!
    user = 'Inia Steinbach'
    token = 'ed027eb9f85a0444188a997f5ed65ee4c81f2317'
    
    
    # Create Engine:
    OEP_URL = 'oep.iks.cs.ovgu.de'
    OED_STRING = f'postgresql+oedialect://{user}:{token}@{OEP_URL}'
    
    engine = sa.create_engine(OED_STRING)
    metadata = sa.MetaData(bind=engine)
    
    # session
    Session=sessionmaker(autocommit=False, autoflush=False)
    session = Session(bind=engine)
    
    Base = declarative_base()
    metadata = Base.metadata
    
    t_ego_dp_res_powerplant_sq_mview = Table(
        'ego_dp_res_powerplant_sq_mview', metadata,
        Column('version', Text),
        Column('id', BigInteger),
        Column('start_up_date', DateTime),
        Column('electrical_capacity', Numeric),
        Column('generation_type', Text),
        Column('generation_subtype', String),
        Column('thermal_capacity', Numeric),
        Column('city', String),
        Column('postcode', String),
        Column('address', String),
        Column('lon', Numeric),
        Column('lat', Numeric),
        Column('gps_accuracy', String),
        Column('validation', String),
        Column('notification_reason', String),
        Column('eeg_id', String),
        Column('tso', Float(53)),
        Column('tso_eic', String),
        Column('dso_id', String),
        Column('dso', String),
        Column('voltage_level_var', String),
        Column('network_node', String),
        Column('power_plant_id', String),
        Column('source', String),
        Column('comment', String),
        Column('geom', Geometry('POINT', 4326)),
        Column('subst_id', BigInteger),
        Column('otg_id', BigInteger),
        Column('un_id', BigInteger),
        Column('voltage_level', SmallInteger),
        Column('la_id', Integer),
        Column('mvlv_subst_id', Integer),
        Column('rea_sort', Integer),
        Column('rea_flag', String),
        Column('rea_geom_line', Geometry('LINESTRING', 3035)),
        Column('rea_geom_new', Geometry('POINT', 3035)),
        Column('preversion', Text),
        Column('flag', String),
        Column('scenario', String),
        Column('nuts', String),
        Column('w_id', BigInteger),
        schema='supply'
    )
    
    powerplants =session.query(t_ego_dp_res_powerplant_sq_mview.columns.id, 
                         t_ego_dp_res_powerplant_sq_mview.columns.geom, 
                         t_ego_dp_res_powerplant_sq_mview.columns.start_up_date, 
                         t_ego_dp_res_powerplant_sq_mview.columns.electrical_capacity, 
                         t_ego_dp_res_powerplant_sq_mview.columns.generation_subtype).filter(t_ego_dp_res_powerplant_sq_mview.columns.generation_type == 'solar').all()
    
    pp = pd.DataFrame(powerplants)
    
    filename_out= os.path.join(cfg.get('paths', 'powerplants'),
                               cfg.get('powerplants', 'openfredval_pp'))
    pp.to_hdf(filename_out, 'powerplants')
    
    return pp

    
def add_region_to_pp():
    pp_in = os.path.join(cfg.get('paths', 'powerplants'),
                               cfg.get('powerplants', 'openfredval_pp'))
    
    region_in = os.path.join(cfg.get('paths', 'geometry'),
                               cfg.get('geometry', 'region_polygon'))
    
    if not os.path.isfile(pp_in):
#        msg = "File '{0}' does not exist. Will create it from opsd file."
#        logging.debug(msg.format(filename_in))
        pp = get_openego_powerplants()
    else:
        pp=pd.read_hdf(pp_in, 'pp', mode='r')
    
    if not os.path.isfile(region_in):
#        msg = "File '{0}' does not exist. Will create it from opsd file."
#        logging.debug(msg.format(filename_in))
        region = get_oep_landkreise()
    else:
        region = pd.read_csv(region_in, index_col=[0], header=None)  
    
    pp_with_region = geopandas.sjoin(pp, region, on='geom', how="inner", op='intersects')
    
    df = pd.DataFrame(pp_with_region)
    
    filename_out='./data/openfred/pp_with_region.h5'
    df.to_hdf(filename_out, 'df')
    return filename_out

# def add_openfred_weatherpoint(pp, weathercells):
    
    
    
 
def add_capacity_by_year(year, pp=None, filename=None, key='pp'):
    if pp is None:
        pp = pd.read_hdf(filename, key, mode='r')
    
    filter_cap_col = 'capacity_{0}'.format(year)

    # Get all powerplants for the given year.
    c1 = (pp['start_up_date'] <= year) & (pp['start_up_date'+15] > year)
    pp.loc[c1, filter_cap_col] = pp.loc[c1, 'capacity']

    return pp




if __name__ == "__main__":
  
    df=add_region_to_pp()
    import pickle
    df.to_pickle("./filtered_ego_dp_res_powerplant_sq.pkl")