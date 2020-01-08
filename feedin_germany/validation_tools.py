# imports
import numpy as np
import pandas as pd
from pvlib.location import Location

# possible todos
#     Möglichkeit metrics für versch. Perioden zu berechnen: Jahr, Monat, Woche..
#         - mittelung: ausgleich übers Jahr, Monat, Woche möglich
#         - slice time series: saisonale schwankungen. (einfacher: Jahresabschnitte einzeln berechnen, eingeben)

# todo:
#   add other metrics


def calculate_validation_metrics(df, val_cols, metrics='standard',
                                 filter_cols=None, filename='test.csv',
                                 exclude_nans=True, **kwargs):
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
    filter_cols : list of strings or None
        Contains column names by which `df` is filtered before the validation.
        col an erster Stelle wird Index
        see example todo example
    filename : string
        File name including path for saving validation metrics.
    exclude_nans : bool
        If True, time steps with nan values in either simulation or validation
         time series are excluded from the validation. Default: True.

    Other Parameters
    ----------------
    unit_factor : float (optional)
        To adapt the unit of metrics like RMSE, bias, ... (that are not in unit
        %) the metrics will be devided by this factor. Example: time series in
        W, desired unit of metrics GW --> `unit_factor` = 1e9

    """
    if exclude_nans:
        # Set value of measured series to nan if respective calculated
        # value is nan and the other way round
        df[val_cols[0]].loc[df[val_cols[1]].isnull() == True] = np.nan
        df[val_cols[1]].loc[df[val_cols[0]].isnull() == True] = np.nan
        # drop nans
        df.dropna(inplace=True)
    if metrics == 'standard':
        metrics = ['rmse_norm', 'rmse_norm_bias_corrected', 'mean_bias',
                   'rmse', 'energy_yield_deviation',
                   'pearson', 'time_step_amount']
    if filter_cols:
        metrics_df = pd.DataFrame()
        # get all pairs of `filter_cols`
        filter_df = df.groupby(filter_cols).size().reset_index().drop(
            columns=[0], axis=1)
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
                    metric=metric, validation_data=val_df, val_cols=val_cols,
                    **kwargs)
            metrics_df = pd.concat([metrics_df, metrics_temp_df])
    else:
        metrics_df = pd.DataFrame(columns=metrics)
        for metric in metrics:
            metrics_df[metric] = [get_metric(metric=metric, validation_data=df,
                                             val_cols=val_cols)]
    # save results
    metrics_df.to_csv(filename)
    return metrics_df


def get_metric(metric, validation_data, val_cols, **kwargs):
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

    Other Parameters
    ----------------
    unit_factor : float (optional)
        To adapt the unit of metrics like RMSE, bias, ... (that are not in unit
        %) the metrics will be devided by this factor. Example: time series in
        W, desired unit of metrics GW --> `unit_factor` = 1e9

    Returns
    -------
    metric_value : float
        Calculated metric value.

    """
    unit_factor = kwargs.get('unit_factor')
    if not unit_factor:
        unit_factor = 1
    if metric == 'rmse_norm':
        metric_value = get_rmse(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]], normalized=True)[0]
    elif metric == 'mean_bias':
        metric_value = get_mean_bias(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]]) / unit_factor
    elif metric == 'rmse_norm_bias_corrected':
        metric_value = get_rmse(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]], normalized=True,
            bias_corrected=True)[0]
    elif metric == 'rmse':
        metric_value = get_rmse(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]], normalized=False,
            bias_corrected=False) / unit_factor
    elif metric == 'standard_deviation_simulation_results':
        metric_value = (get_standard_deviation(validation_data[val_cols[0]]) /
                        unit_factor)
    elif metric == 'standard_deviation_validation_data':
        metric_value = (get_standard_deviation(validation_data[val_cols[1]]) /
                        unit_factor)
    elif metric == 'pearson':
        metric_value = get_pearson_s_r(df=validation_data, min_periods=None)  # todo min periods
    elif metric == 'time_step_amount':
        metric_value = len(validation_data)
    elif metric == 'energy_yield_deviation':
        metric_value = get_energy_yield_deviation(
            simulation_series=validation_data[val_cols[0]],
            validation_series=validation_data[val_cols[1]])
    else:
        raise ValueError("Metric {} not added, yet.".format(metric))

    return metric_value


def get_energy_yield_deviation(simulation_series, validation_series):
    r"""
    Calculates energy yield deviation of simulation from validation series.

    Parameters
    ----------
    simulation_series : pd.Series
        Simulated feed-in time series.
    validation_series : pd.Series
        Validation feed-in time series. Must have the same frequency as
        `simulation_series`.

    Notes
    -----
    Attention: `simulation_series` and `validation_series` time series must
    have the same frequency as this function does not calculate the energy
    yield but just sums up the power output of one year.

    Returns
    -------
    deviation : float
        Deviation from the energy yield in %.

    """
    return ((simulation_series.sum() - validation_series.sum()) /
            validation_series.sum() * 100)


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


def get_rmse(simulation_series, validation_series, normalized=True,
             bias_corrected=False):
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
    bias_corrected : boolean
        If True the simulation_series is bias corrected before RMSE is
        calculated.

    Returns
    -------
    rmse : float
        (Normalized) root mean squared error.

    """
    if bias_corrected:
        simulation_series = simulation_series - get_mean_bias(
            simulation_series, validation_series)
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


def pv_feedin_drop_night_times(feedin_df, lat, lon):
    """
    Drops night time values of PV feed-in.

    :param feedin_df: index needs to be time zone aware
    :param lat:
    :param lon:
    :return: feedin_df with dropped night time steps
    """
    tz = feedin_df.index.tz
    location = Location(latitude=lat, longitude=lon, tz=tz)
    solar_position = location.get_solarposition(feedin_df.index)
    ind = solar_position[solar_position['zenith'] < 90].index
    return feedin_df.loc[ind]


def resample_with_nan_theshold(df, frequency, threshold):
    """

    :param df: dataframe with arbitrary columns to be resampled
    :param frequency: resample frequency
    :param threshold: if less data points than specified in threshold can be
    used in the resampling then value is set to nan
    :return:
    """
    if threshold is None:
        resampled_df = df.resample(frequency).mean()
    else:
        resampled_df = df.resample(frequency).mean()
        df_count = df.resample(frequency).count()
        for col in df.columns:
            resampled_df.loc[df_count[col] < threshold, col] = np.nan
    return resampled_df
