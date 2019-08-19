import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from os.path import join
import os

# internal imports
import geometries
import settings

# todo wind speed to wind_speed!!!
# todo: functions might have been updated in open_FRED paper Gogs by Pierre


def load_era5_data(year, data_path=join('data', 'era5_netcdf')):
    ds = xr.open_dataset(
        join(data_path, 'open_fred_compare_daten_set_{}.nc'.format(year)))
    ds = ds.rename(
        {
            't2m': 'temperature',
            'sp': 'pressure',
            'fsr': 'roughness_length',
            'ssrd': 'surface_solar_radiation_downwards',
            'fdir': 'surface_total_sky_direct_solar_radiation',
            'latitude': 'lat',
            'longitude': 'lon',
        }
    )

    return ds


def format_windpowerlib(xarr):
    """Formats the xarray into a pandas DataFrame
    The windpowerlib's ModelChain requires a weather DataFrame with time series for

    - wind speed `wind_speed` in m/s,
    - temperature `temperature` in K,
    - roughness length `roughness_length` in m,
    - pressure `pressure` in Pa.

    The columns of the DataFrame need to be a MultiIndex where the first level
    contains the variable name as string (e.g. 'wind_speed') and the second level
    contains the height as integer in m at which it applies (e.g. 10, if it was
    measured at a height of 10 m).

    :param xarr: xarray with ERA5 weather data
    :return: pandas DataFrame formatted for windpowerlib

    """

    # compute the norm of the wind speed
    xarr['wnd100m'] = (np.sqrt(xarr['u100'] ** 2 + xarr['v100'] ** 2)
                       .assign_attrs(units=xarr['u100'].attrs['units'],
                                     long_name="100 metre wind speed"))

    xarr['wnd10m'] = (np.sqrt(xarr['u10'] ** 2 + xarr['v10'] ** 2)
                      .assign_attrs(units=xarr['u10'].attrs['units'],
                                    long_name="10 metre wind speed"))

    xarr = xarr.drop(
        [
            'u100',
            'v100',
            'u10',
            'v10',
            'surface_solar_radiation_downwards',
            'surface_total_sky_direct_solar_radiation'
        ]
    )

    # reorder the multiindexing on the rows
    df = xarr.to_dataframe().reorder_levels(['time', 'lat', 'lon'])

    # reorder the columns of the dataframe
    df = df[
        ['wnd10m', 'wnd10m', 'pressure', 'temperature', 'roughness_length']]

    # define a multiindexing on the columns
    midx = pd.MultiIndex(
        levels=[
            ['wind speed', 'pressure', 'temperature', 'roughness_length'],
            # variable
            ['0', '2', '10', '100']  # height
        ],

        codes=[
            [0, 0, 1, 2, 3],  # indexes from variable list above
            [2, 3, 0, 1, 0]  # indexes from the height list above
        ],
        names=['variable', 'height']  # name of the levels
    )

    df.columns = midx

    return df.dropna()


def format_pvlib(xarr):
    """Formats the xarray into a pandas DataFrame
    The pvlib's ModelChain requires a weather DataFrame with time series for

    - wind speed `wind_speed` in m/s,
    - temperature `temp_air` in C,
    - direct irradiation 'dni' in W/m² (calculated later),
    - global horizontal irradiation 'ghi' in W/m²,
    - diffuse horizontal irradiation 'dhi' in W/m²

    :param xarr: xarray with ERA5 weather data
    :return: pandas DataFrame formatted for pvlib
    """

    # compute the norm of the wind speed
    xarr['wind_speed'] = (np.sqrt(xarr['u10'] ** 2 + xarr['v10'] ** 2)
                          .assign_attrs(units=xarr['u10'].attrs['units'],
                                        long_name="10 metre wind speed"))

    # convert temperature to Celsius (from Kelvin)
    xarr['temp_air'] = xarr.temperature - 273.15

    xarr['dirhi'] = (
                xarr.surface_total_sky_direct_solar_radiation / 3600.).assign_attrs(
        units='W/m^2')
    xarr['ghi'] = (
                xarr.surface_solar_radiation_downwards / 3600.).assign_attrs(
        units='W/m^2',
        long_name='global horizontal irradiation'
    )
    xarr['dhi'] = (xarr.ghi - xarr.dirhi).assign_attrs(
        units='W/m^2',
        long_name='direct irradiation'
    )

    xarr = xarr.drop(
        [
            'u100',
            'v100',
            'u10',
            'v10',
            'pressure',
            'roughness_length',
            'surface_solar_radiation_downwards',
            'surface_total_sky_direct_solar_radiation',
            'dirhi',
            'temperature'
        ]
    )

    # reorder the multiindexing on the rows
    df = xarr.to_dataframe().reorder_levels(['time', 'lat', 'lon'])

    # reorder the multiindexing on the rows
    df = df[['wind_speed', 'temp_air', 'ghi', 'dhi']]

    return df.dropna()


def select_area(xarr, lon, lat, g_step=0.25):
    """
    :param xarr: xarray for which one would like to select data based on a squared area
    :param lon: longitude as either a float or a tuple representing the west and east boundaries of a square
    :param lat: latitude as either a float or a tuple representing the south and north boundaries of a square
    :param g_step: grid step size (default is 0.25 for CDS data)
    :return: xarray with the area selected
    """
    select_point = True
    if np.size(lon) > 1:
        select_point = False
        lon_w, lon_e = lon
    else:
        lon_w = lon
        lon_e = lon + g_step

    if np.size(lat) > 1:
        select_point = False
        lat_s, lat_n = lat
    else:
        lat_s = lat
        lat_n = lat + g_step

    # if select_point is True:
    #    answer = xarr.sel(lat=lat, lon=lon, method='nearest')
    # else:
    answer = xarr.where(
        (lat_s < xarr.lat)
        & (xarr.lat <= lat_n)
        & (lon_w < xarr.lon)
        & (xarr.lon <= lon_e)
    )

    return answer


def apply_mask(xarr, mask_area):
    """
    :param xarr: xarray for which one would like to apply the mask area
    :param mask_area: shapely's compatible geometry object (i.e. Polygon, Multipolygon, etc...)
    :return: xarray with the area selected
    """
    geometry = []
    lon_vals = []
    lat_vals = []

    df = pd.DataFrame([], columns=['lon', 'lat'])

    for i, x in enumerate(xarr.lon):
        for j, y in enumerate(xarr.lat):
            lon_vals.append(x.values)
            lat_vals.append(y.values)
            geometry.append(Point(x, y))

    df['lon'] = lon_vals
    df['lat'] = lat_vals

    # create a geopandas to use the geometry functions
    crs = {'init': 'epsg:4326'}
    geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    inside_points = geo_df.within(mask_area)

    inside_lon = geo_df.loc[inside_points, 'lon'].values
    inside_lat = geo_df.loc[inside_points, 'lat'].values

    # prepare a list where the latitude and longitude of the points inside are formatted as xarray of bools
    logical_list = []
    for lon, lat in zip(inside_lon, inside_lat):
        logical_list.append(
            np.logical_and((xarr.lon == lon), (xarr.lat == lat)))

    # bind all conditions form the list
    cond = np.logical_or(*logical_list[:2])
    for new_cond in logical_list[2:]:
        cond = np.logical_or(cond, new_cond)

    # apply the condition to where
    return xarr.where(cond)


def prepare_windpowerlib_from_era5(year, data_path=join('data', 'era5_netcdf'),
                                   mask_area=None):
    ds = load_era5_data(year, data_path)

    if mask_area is not None:
        ds = apply_mask(ds, mask_area)

    return format_windpowerlib(ds)


def prepare_pvlib_from_era5(year, data_path=join('data', 'era5_netcdf'),
                            mask_area=None):
    ds = load_era5_data(year, data_path)

    if mask_area is not None:
        ds = apply_mask(ds, mask_area)

    return format_pvlib(ds)




if __name__ == "__main__":
    # get global variables
    settings.init()  # note: set your paths in settings.py

    # choose parameters
    uckermark_wpl = True  # Uckermark windpowerlib data
    brandenburg_wpl = True  # for whole Brandenburg windpowerlib data
    germany_wpl = True  # for whole Germany windpowerlib data
    germany_pvl = True  # for whole Germany pvlib data

    years = [
        2013,
        2014, 2015, 2016, 2017
    ]

    for year in years:
        ds_era5 = load_era5_data(year, settings.path_era5_netcdf)

        if uckermark_wpl:
            # select region
            region = geometries.load_polygon('uckermark')
            ws_select = apply_mask(ds_era5, region.loc[0, 'geometry'])
            # format to windpowerlib
            weather = format_windpowerlib(ws_select)
            weather.to_csv(os.path.join(settings.weather_data_path,
                             'era5_wind_um_{}.csv'.format(year)))

        if brandenburg_wpl:
            # select region
            region = geometries.load_polygon('brandenburg')
            ws_select = apply_mask(ds_era5, region.loc[0, 'geometry'])
            # format to windpowerlib
            weather = format_windpowerlib(ws_select)
            weather.to_csv(os.path.join(settings.weather_data_path,
                                        'era5_wind_bb_{}.csv'.format(year)))

        if (germany_wpl or germany_pvl):
            if germany_wpl:
                weather = format_windpowerlib(ds_era5)
                weather.to_csv(os.path.join(settings.weather_data_path,
                                            'era5_wind_ger_{}.csv'.format(
                                                year)))

            if germany_pvl:
                weather = format_pvlib(ds_era5)
                weather.to_csv(os.path.join(settings.weather_data_path,
                                            'era5_pv_ger_{}.csv'.format(
                                                year)))
