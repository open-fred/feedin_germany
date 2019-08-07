# imports
import numpy as np
import pandas as pd

# possible todos
#     Möglichkeit metrics für versch. Perioden zu berechnen: Jahr, Monat, Woche..
#         - mittelung: ausgleich übers Jahr, Monat, Woche möglich
#         - slice time series: saisonale schwankungen. (einfacher: Jahresabschnitte einzeln berechnen, eingeben)

# todo:
#   add other metrics


def calculate_validation_metrics(df, val_cols, metrics='standard',
                                 filter_cols=None, filename='test.csv',
                                 exclude_nans=True):
    r"""
    Calculates metrics for validating simulated data and saves results to file.

    Parameters
    ----------
    df : pd.DataFrame
        Contains simulation results and validation data in the columns as
        specified in `val_cols`. May include other columns which are filtered
        with column names as specified in `filter_cols` or other columns which
        will be ignored.
    val_cols : list of strings
        Contains columns names of (1) time series to be validated and (2)
        validation time series in the form [(1), (2)].
    metrics : list of strings or string
        Contains metrics (strings) to be calculated. If it is set to 'standard'
         standard metrics are used. Default: 'standard'.
    filter_cols : list of strings
        Contains column names by which `df` is filtered before the validation.
        col an erster Stelle wird Index
        see example todo example
    filename : string
        File name including path for saving validation metrics.
    exclude_nans : bool
        If True, time steps with nan values in either simulation or validation
         time series are excluded from the validation. Default: True.

    """
    if exclude_nans:
        # Set value of measured series to nan if respective calculated
        # value is nan and the other way round
        df[val_cols[0]].loc[df[val_cols[1]].isnull() == True] = np.nan
        df[val_cols[1]].loc[df[val_cols[0]].isnull() == True] = np.nan
        # drop nans
        df.dropna(inplace=True)
    if metrics == 'standard':
        metrics = ['rmse_norm', 'mean_bias', 'pearson', 'time_step_amount']
    if filter_cols:
        metrics_df = pd.DataFrame()
        # get all pairs of `filter_cols`
        filter_df = df.groupby(filter_cols).size().reset_index().drop(columns=[0],
                                                                   axis=1)
        for filters, index in zip(filter_df.values, filter_df.index):
            # select time series by filters
            df['temp'] = df[filter_cols].isin(filters).all(axis=1)
            val_df = df.loc[df['temp'] == True][val_cols]
            df.drop(columns=['temp'], inplace=True)

            metrics_temp_df = pd.DataFrame()
            for filter, col in zip(filters, filter_cols):
                metrics_temp_df = pd.concat([metrics_temp_df,
                                             pd.DataFrame(data=filter,
                                                          columns=[col],
                                                          index=[index])], axis=1)
            for metric in metrics:
                metrics_temp_df[metric] = get_metric(
                    metric=metric, validation_data=val_df, val_cols=val_cols)
            metrics_df = pd.concat([metrics_df, metrics_temp_df])
    else:
        metrics_df = pd.DataFrame(columns=metrics)
        for metric in metrics:
            metrics_df[metric] = [get_metric(metric=metric, validation_data=df,
                                            val_cols=val_cols)]
    # save results
    metrics_df.to_csv(filename)


def get_metric(metric, validation_data, val_cols):
    r"""
    Fetches metric of `validation_data` from single functions.

    Parameters
    ----------
    metric : string
        Specifies the metric that is calculated for `validation_data`. Options:
        'rsme_norm' (normalized RMSE), 'mean_bias' (mean bias), 'pearson'
        (pearson correlation coefficient).
    validation_data : pd.DataFrame
        Contains simulation results and validation data in the columns as
        specified in `val_cols`.
    val_cols : list of strings
        Contains columns names of (1) time series to be validated and (2)
        validation time series in the form [(1), (2)].

    Returns
    -------
    metric_value : float
        Calculated metric value.

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
    elif metric == 'time_step_amount':
        metric_value = len(validation_data)
    else:
        raise ValueError("Metric {} not added, yet.".format(metric))

    return metric_value


def get_standard_deviation(data_series):
    r"""
    Calculates the standard deviation of a data series.

    Parameters
    ----------
    data_series : list or pandas.Series
        Input data series (data points) of which the standard deviation is
        calculated.

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
