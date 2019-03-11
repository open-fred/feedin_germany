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


# Funktion
#     bekommt
#         df mit berechneter und validierungszeitreihe. (nenne spaltennamen)
#         spalten, nach denen erst noch gefiltert werden sollte (optional) z.B. in unserem Fall: technology, region


def calculate_validation_metrics(df, val_cols, metrics='standard',
                                 filter_cols=None, filename='test.csv',
                                 print_out=False):
    r"""

    Parameters
    ----------
    df
        darf mehrere Zeitreihen im Datenbankformat enthalten.. wird gefiltet.
    val_cols : list of strings
        Contains columns names of (1) time series to be validated and (2)
        validation time series in the form [(1), (2)].
    metrics

    filter_cols : list of strings
        Contains column names by which `df` is filtered before the validation.
        col an erster Stelle wird Index
        see example todo example
    filename
        -- for saving
    print_out
        todo

    """
    # todo: beliebig viele Spalten zur Filterung möglich
    col_1 = filter_cols[0]
    col_2 = filter_cols[1]
    metrics_df = pd.DataFrame(columns=[val_cols])  # todo multiindex filter_1, filter_2
    for filter_1 in df[col_1].groupby():  # oder unique()
        for filter_2 in df[col_2].groupby():  # oder unique()
            val_df = df.loc[(df[col_1] == filter_1) & (df[col_2] == filter_2)].drop([col_1, col_2], axis=1)
            if metrics == 'standard':
                metrics = ['rmse_norm', 'mean_bias', 'pearson']
            for metric in metrics:
                pass
                # alle metrics in df schreiben
                #metrics_df mit index filter_1, filter_2 [metric] = ...
            # val metrics für diese beiden Zeitreihen
            # todo vllt in eigener Funktion, die schon gefilterte Zeitreihen bekommt - dann könnte man auch nur die verwenden
            # speichern


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
