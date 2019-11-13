
def init():
    path_to_server = '/home/birgit/rli-server'
    path_to_data_server = '/home/birgit/rli-daten/'

    ## weather
    global path_era5_netcdf, open_FRED_pkl
    path_era5_netcdf = path_to_data_server + '/Wetterdaten/ERA5/'
    open_FRED_pkl = path_to_data_server + '/open_FRED_Wetterdaten_pkl/'

    ## power plants and geometries
    global path_mastr_wind, path_mastr_pv, path_geometries
    path_mastr_wind = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/power_plant_register/'
    path_mastr_pv = '/home/birgit/virtualenvs/open_fred_validation_paper/git_repos/open_fred_validation_paper/pv_calculations/'
    #path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/power_plant_register/'
    path_geometries = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/geometries/'

    ## time series
    global path_time_series_50_Hz, path_wam_ezr
    # path to time series 50 Hertz
    path_time_series_50_Hz = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/time_series/50Hz/'
    # path to wam time series
    path_wam_ezr = path_to_data_server + '/Einspeisezeitreihen_open_FRED_bericht_und_WAM'

    ## validation
    # path to validation metrics paper
    global path_validation_metrics
    path_validation_metrics = path_to_server + '/04_Projekte/163_Open_FRED/03-Projektinhalte/AP7 Community/paper_data/validation_metrics/50Hz/'

