
# internal imports
from feedin_germany import feedin

years = [2012]
categories = [
    'Wind',
    # 'Solar',
    # 'Hydro'
]
for year in years:
        feedin = feedin.calculate_feedin_germany(
            year=year, categories=categories, regions='landkreise',
            register_name='opsd', weather_data_name='open_FRED',
            oep_upload=True, debug_mode=True)
        print(feedin)