
def init():
    ## weather
    global weather_data_path, path_era5_netcdf, path_time_series_50_Hz
    # path to csv weather files
    weather_data_path = '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/weather_data'
    # path to ERA5 original netcdf files
    path_era5_netcdf = '/home/sabine/Daten_flexibel_01/Wetterdaten/ERA5/'

    ## power plant register
    global path_mastr_wind
    path_mastr_wind = '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/power_plant_register/'

    ## time series
    global path_time_series_50_Hz, path_wam_ezr
    # path to time series 50 Hertz
    path_time_series_50_Hz = '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/50Hz/'
    # path to wam time series
    path_wam_ezr = '/home/sabine/Daten_flexibel_01/Einspeisezeitreihen_open_FRED_WAM'

    ## validation
    # path to validation metrics paper
    global path_validation_metrics
    path_validation_metrics = '/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/50Hz/'

