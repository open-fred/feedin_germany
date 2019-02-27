
# imports
import pandas as pd
import os
from feedinlib import tools
from feedinlib import region

# import internal modules
from feedin_germany import opsd_power_plants as opsd
# import opsd_power_plants as opsd

# get example weather
filename = os.path.abspath('/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
weather_df = tools.example_weather_wind(filename)

# get opsd register
keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity',
             'com_year', 'decom_year', 'com_month', 'decom_month']
register = opsd.filter_pp_by_source_and_year(year=2012, energy_source='Wind',
                                             keep_cols=keep_cols)

# feedinlib region feed-in
example_region = region.Region(geom='no_geom', weather=weather_df)
feedin = example_region.wind_feedin(register)

