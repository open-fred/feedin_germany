from windpowerlib import wind_turbine as wt
import numpy as np
import pandas as pd

raw_data = wt.load_turbine_data_from_oedb(schema="supply",
                                          table="wind_turbine_library")
# turbines with power curve
turbine_types = raw_data[['turbine_type_v2' , 'rotor_diameter', 'hub_height',
                          'nominal_power', 'has_power_curve']]
# integers
turbine_types['rotor_diameter'] = turbine_types['rotor_diameter'].apply(int)
# turbine_types['hub_height'] = turbine_types['hub_height'].apply(int)

turbine_types['Leistungsdichte'] = turbine_types['nominal_power'] * 1000 / ((turbine_types['rotor_diameter'] / 2) ** 2 * np.pi)
# turbine_types['kW/m'] = turbine_types['nominal_power'] / turbine_types['hub_height']

# Mittel aus 2016 und 2017 % http://windmonitor.iee.fraunhofer.de/windmonitor_de/3_Onshore/2_technik/5_Stark-_und_Schwachwindanlagen/
wind_zone_dict = {
    '4': {'dichte': 397.5, 'kW/m': 30.58},
    '3': {'dichte': 337, 'kW/m': 26.145},
    '2': {'dichte': 301.5, 'kW/m': 22.49},
    '1': {'dichte': 277.5, 'kW/m': 20.505}
}
for wind_zone in ['4', '3', '2', '1']:
    # select turbine type by Leistungsdichte
    turbine_types['diff_{}'.format(wind_zone)] = abs(wind_zone_dict[wind_zone]['dichte'] -  turbine_types['Leistungsdichte'])
    minimum = min(turbine_types['diff_{}'.format(wind_zone)])
    turbine = turbine_types.loc[turbine_types['diff_{}'.format(wind_zone)] == minimum]

    # desired hub height
    hub_height = turbine.nominal_power.values / wind_zone_dict[wind_zone]['kW/m']

    print()
    print('Wind zone {}'.format(wind_zone))
    print(turbine.turbine_type_v2.values, turbine.hub_height.values, turbine.nominal_power.values, turbine.rotor_diameter.values)
    print('leistungsdichte {}'.format(turbine.Leistungsdichte.values))
    print('hub_height {}'.format(hub_height))

