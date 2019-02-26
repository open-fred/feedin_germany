from feedin_germany import opsd_power_plants
from feedinlib import tools
import os
import pandas as pd

# loading weather data
filename = os.path.abspath('/home/local/RL-INSTITUT/inia.steinbach/mount_ordner/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
if not os.path.isfile(filename):
    raise FileNotFoundError("Please adjust the path.")
weather_df = pd.read_csv(filename,
                         header=[0, 1], index_col=[0, 1, 2],
                         parse_dates=True)
# change type of height from str to int by resetting columns
weather_df.columns = [weather_df.axes[1].levels[0][
                          weather_df.axes[1].labels[0]],
                      weather_df.axes[1].levels[1][
                          weather_df.axes[1].labels[1]].astype(int)]

keep_cols_wind =  ['lat', 'lon', 'commissioning_date', 'capacity',
                   'com_year', 'decom_year', 'com_month', 'decom_month']
register_wind = opsd_power_plants.filter_pp_by_source_and_year(
    year=2012, energy_source='Wind', keep_cols=keep_cols_wind)

register_pv = opsd_power_plants.filter_pp_by_source_and_year(
    year=2012, energy_source='Wind')

# note: nans are dropped in filter function
# print('Missing coordinates pv: {}'.format(register_pv['lat'].isnull().sum()))
# print('Missing coordinates wind: {}'.format(
#     register_wind['lat'].isnull().sum()))
register_wind_locations = tools.add_weather_locations_to_register(
    register=register_wind, weather_coordinates=weather_df['wind_speed'])

print(register_wind)

register_pv_locations = tools.add_weather_locations_to_register(
    register=register_pv, weather_coordinates=weather_df)

print(register_pv)
