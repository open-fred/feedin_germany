
# imports
import os
from matplotlib import pyplot as plt

from feedinlib import tools
from feedinlib import region


# import internal modules
from feedin_germany import opsd_power_plants as opsd

# get example weather
filename = os.path.abspath('/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
weather_df = tools.example_weather_wind(filename)

# get opsd register
keep_cols = ['lat', 'lon', 'commissioning_date', 'capacity']
register = opsd.filter_pp_by_source_and_year(year=2012, energy_source='Wind',
                                             keep_cols=keep_cols)

# feedinlib region feed-in
feedin = region.Region(geom='no_geom',
                               weather=weather_df).wind_feedin(register)
feedin.plot()
plt.show()