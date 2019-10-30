
def init():
    path_to_server = '/home/sabine/rl-institut'
    path_to_data_server = '/home/sabine/Daten_flexibel_01'

    ## weather
    global weather_data_path, path_era5_netcdf
    # path to csv weather files
    weather_data_path = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/weather_data'
    # path to ERA5 original netcdf files
    path_era5_netcdf = path_to_data_server + '/Wetterdaten/ERA5/'

    ## power plants and geometries
    global path_mastr_wind, path_mastr_pv, path_geometries
    path_mastr_wind = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/power_plant_register/'
    path_mastr_pv = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/power_plant_register/'
    path_geometries = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/geometries/'

    ## time series
    global path_time_series_50_Hz, path_wam_ezr
    # path to time series 50 Hertz
    path_time_series_50_Hz = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/50Hz/'
    # path to wam time series
    path_wam_ezr = path_to_data_server + '/Einspeisezeitreihen_open_FRED_WAM'

    ## validation
    # path to validation metrics paper
    global path_validation_metrics
    path_validation_metrics = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/50Hz/'

