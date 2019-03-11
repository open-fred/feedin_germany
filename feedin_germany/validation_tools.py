# imports
import numpy as np
import pandas as pd

# Überlegungen
# 4 Zonen, 2-3 Technologien (wind, pv, evtl wasser)
#
# Metrics:
#     rmse: normiert auf mittlere Leistungsabgabe der Region,
#     mittlerer bias,
#     pearson (?)
#     Möglichkeit metrics für versch. Perioden zu berechnen: Jahr, Monat, Woche..
#         - mittelung: ausgleich übers Jahr, Monat, Woche möglich
#         - slice time series: saisonale schwankungen. (einfacher: Jahresabschnitte einzeln berechnen, eingeben)


def get_standard_deviation(data_series):
    r"""
    Calculates the standard deviation of a data series.

    Parameters
    ----------
    data_series : list or pandas.Series
        Input data series (data points) of which the standard deviation
        will be calculated.

    Return
    ------
    float
        Standard deviation of the input data series.

    """
    average = data_series.mean()
    variance = ((data_series - average)**2).sum() / len(data_series)
    return np.sqrt(variance)


def get_rmse(simulation_series, validation_series, normalized=True):
    r"""
    Calculates the RMSE of simulation from validation series.

    Parameters
    ----------
    simulation_series : pd.Series
        Simulated feed-in time series.
    validation_series : pd.Series
        Validation feed-in time series.
    normalized : boolean
        If True the RMSE is normalized with the average annual power output.

    Returns
    -------
    rmse : float
        (Normalized) root mean squared error.

    """
    rmse = np.sqrt(((simulation_series - validation_series)**2).sum() /
                   len(simulation_series))
    if normalized:
        return rmse / validation_series.resample('A').mean().values * 100
    else:
        return rmse


def get_mean_bias(simulation_series, validation_series):
    r"""
    Compares two series concerning their mean deviation (bias).

    Parameters
    ----------
    simulation_series : pd.Series
        Simulated feed-in time series.
    validation_series : pd.Series
        Validation feed-in time series.

    Returns
    -------
    pd.Series
        Mean deviation (bias) of simulated series from validation series.

    """
    return (simulation_series - validation_series).mean()


def get_pearson_s_r(df, min_periods=None):
    r"""
    Calculates the Pearson's correlation coefficient of two series.

    Parameters
    ----------
    df : pd.DataFrame
        todo description
    min_periods : integer
        Minimum amount of periods for correlation. Default: None.

    Returns
    -------
    float
        Pearson's correlation coefficient (Pearson's R)
        of the input series.

    """
    return df.corr(method='pearson', min_periods=min_periods).iloc[1, 0]
