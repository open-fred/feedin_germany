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
    if metrics == 'standard':
        metrics = ['rmse_norm', 'mean_bias', 'pearson'] # get all pairs of `filter_cols`
    filter_df = df.groupby(filter_cols).size().reset_index().drop(columns=[0],
                                                                   axis=1)
    metrics_df = pd.DataFrame()
    for filters, index in zip(filter_df.values, filter_df.index):
        df['temp'] = df[filter_cols].isin(filters).all(axis=1)
        val_df = df.loc[df['temp'] == True][val_cols]
        df.drop(columns=['temp'], inplace=True)

        metrics_temp_df = pd.DataFrame(data=filters[0],
                                       columns=[filter_cols[0]], index=[index])
        metrics_temp_df[filter_cols[1]] = filters[1] # todo schöner!- hatte keine Zeit
        for metric in metrics:
            metrics_temp_df[metric] = get_metric(
                metric=metric, validation_data=val_df, val_cols=val_cols)
        metrics_df = pd.concat([metrics_df, metrics_temp_df])
    # save results
    metrics_df.to_csv(filename)


def get_metric(metric, validation_data, val_cols):
    r"""

    """
    if metric == 'rmse_norm':
        metric_value = get_rmse(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]], normalized=True)[0]
    elif metric == 'mean_bias':
        metric_value = get_mean_bias(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]])
    elif metric == 'pearson':
        metric_value = get_pearson_s_r(df=validation_data, min_periods=None)  # todo min periods
    else:
        raise ValueError("Metric {} not added, yet.".format(metric))

    return metric_value


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
    min_periods : integer or None
        Minimum amount of periods for correlation. Default: None.

    Returns
    -------
    float
        Pearson's correlation coefficient (Pearson's R)
        of the input series.

    """
    return df.corr(method='pearson', min_periods=min_periods).iloc[1, 0]
