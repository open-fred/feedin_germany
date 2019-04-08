# -*- coding: utf-8 -*-
"""
The `database_tools` module contains ....

"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

# imports
import requests
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from feedin_germany import oep_regions as oep


def load_data_from_oedb_with_oedialect(schema, table_name):
    """
    Loads a table from OpenEnergy DataBase (oedb) and returns it as data frame.

    Parameters
    ----------
    schema : str
        Name of schema in oedb (see
        https://openenergy-platform.org/dataedit/schemas).
    table_name : str
        Name of table in oedb.

    Notes
    -----
    todo: login and token need to be adapted/automatized

    Returns
    -------
    data : pd.DataFrame
        Extracted data from oedb.

    """
    # Create Engine:
    user = ''
    token = ''
    engine = sa.create_engine(
        f'postgresql+oedialect://{user}:{token}@openenergy-platform.org')

    Base = declarative_base(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    class BkgVg2502Lan(Base):
        __tablename__ = table_name
        __table_args__ = {'schema': schema, 'autoload': True}

    try:
        # Stuff in session
        p = session.query(BkgVg2502Lan)
        gdf = oep.as_pandas(p, geometry="geom", params=None, crs=None,
                            hex=True)
        gdf_new = gdf.to_crs(epsg=4326)

        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

    return gdf_new


def load_data_from_oedb_with_api(schema, table):
    """
    Loads a table from OpenEnergy DataBase (oedb) and returns it as data frame.

    Parameters
    ----------
    schema : str
        Name of schema in oedb (see
        https://openenergy-platform.org/dataedit/schemas).
    table : str
        Name of table in oedb.

    Notes
    -----
    todo: use sessionmaker um Anlagen auszuwählen ??
    then todo: login and token need to be adapted/automatized
         todo: possible --> engine creation as separate function

    Returns
    -------
    data : pd.DataFrame
        Extracted data from oedb.

    """
    # url of OpenEnergy Platform that contains the oedb
    oep_url = 'http://oep.iks.cs.ovgu.de/'
    # load data
    result = requests.get(
        oep_url + '/api/v0/schema/{}/tables/{}/rows/?'.format(
            schema, table), )
    if not result.status_code == 200:
        raise ConnectionError("Database connection not successful. "
                              "Error: {}".format(result.status_code))
    # extract data
    data = pd.DataFrame(result.json())

    return data
