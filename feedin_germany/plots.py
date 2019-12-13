import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import math
from feedin_germany.validation_tools import pv_feedin_drop_night_times


def plot_correlation(df, val_cols, filename='Tests/correlation_test.pdf',
                     title=None, xlabel=None, ylabel=None, color='darkblue',
                     marker_size=3):
    r"""
    Visualize the correlation between two feedin time series.

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
    filename : String
        File name including path for saving plot.
    title : String
        Title of figure.
    """

    fig, ax = plt.subplots()
    data = df[val_cols]
    data.plot.scatter(x=list(data)[1], y=list(data)[0],
                      ax=ax, c=color, s=marker_size)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)

    # Maximum value for xlim and ylim and line
    maximum = max(df.iloc[:, 0].max(), df.iloc[:, 1].max())
    plt.xlim(xmin=0, xmax=maximum)
    plt.ylim(ymin=0, ymax=maximum)
    ideal, = plt.plot([0, maximum], [0, maximum], color='black',
                      linestyle='--', label='ideal correlation')
    deviation_100, = plt.plot([0, maximum], [0, maximum * 2], color='orange',
                              linestyle='--', label='100 % deviation')
    plt.plot([0, maximum * 2], [0, maximum], color='orange', linestyle='--')
    if title:
        plt.title(title)
    plt.legend(handles=[ideal, deviation_100])
    # Add certain values to plot as text
    # plt.annotate(
    #     'RMSE = {0} \n Pr = {1} \n mean bias = {2}{3} \n std dev = {4}'.format(
    #         round(validation_object.rmse, 2),
    #         round(validation_object.pearson_s_r, 2),
    #         round(validation_object.mean_bias, 2), 'MW',
    #         round(validation_object.standard_deviation, 2)) + 'MW',
    #     xy=(1, 1), xycoords='axes fraction',
    #     xytext=(-6, -6), textcoords='offset points',
    #     ha='right', va='top', bbox=dict(facecolor='white', alpha=0.5))
    plt.tight_layout()
    fig.savefig(filename)
    plt.close()


def histogram(validation_df, filename=None, freq=0.5, setting=None):
    """
    Histogram for calculated and validation data for two calculated time
    series, one on positive and one on negative y-axis.

    Parameters
    ----------
    validation_df : pd.DataFrame
        Dataframe with calculated and validation time series.
    filename : str
        Filename (incl. path, without format extension, e.g. without .png)
        to save figure under. Figure is saved as pdf and png.
    freq : float
        Bin width.
    setting : str or None
        Specifies which columns are used and how to label them.

    """

    if setting is None:
        col1 = 'feedin_open_FRED'
        col2 = 'feedin_ERA5'
        val_col = 'feedin_val'
        label1 = 'open_FRED'
        label2 = 'ERA5'
    elif setting == 'smoothing':
        col1 = 'feedin_open_FRED'
        col2 = 'feedin_open_FRED_smoothed'
        val_col = 'feedin_val'
        label1 = 'calculated feed-in (not smoothed)'
        label2 = 'calculated feed-in (smoothed)'
    elif setting == 'ramps':
        col1 = 'ramp_feedin_open_FRED'
        col2 = 'ramp_feedin_ERA5'
        val_col = 'ramp_feedin_val'
        label1 = 'open_FRED'
        label2 = 'ERA5'

    validation_df = validation_df.loc[
                    :, [col1, col2, val_col]] / 1e9
    bins = pd.interval_range(start=0.0,
                             end=math.ceil(validation_df.max().max()),
                             closed='left', freq=freq)
    calc_data_1 = validation_df.loc[:, col1]
    calc_data_2 = validation_df.loc[:, col2]
    val_data = validation_df.loc[:, val_col]
    calc_data_1_density = calc_data_1.groupby(
        pd.cut(calc_data_1, bins=bins)).count() / len(calc_data_1)
    calc_data_2_density = calc_data_2.groupby(
        pd.cut(calc_data_2, bins=bins)).count() / len(calc_data_2)
    val_data_density = val_data.groupby(
        pd.cut(val_data, bins=bins)).count() / len(val_data)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # open Fred
    ax.bar(bins.mid + freq / 4, val_data_density, width=freq / 2,
           label='50 Hz', color='c')
    ax.bar(bins.mid - freq / 4, calc_data_1_density, width=freq/2,
           label=label1, color='b')


    # ERA5
    ax.bar(bins.mid - freq / 4, -calc_data_2_density, width=freq/2,
           label=label2, color='r')
    ax.bar(bins.mid + freq / 4, -val_data_density, width=freq/2, color='c')

    plt.grid(True, alpha=0.5)
    plt.xlabel('Feed-in in GW')
    plt.ylabel('Probability')
    ax.legend()

    ax.set_xlim(0, 3)#math.ceil(validation_df.max().max()))
    max_density = max(calc_data_1_density.max(),
                        calc_data_2_density.max(),
                        val_data_density.max())
    ylim = round(max_density*1.1, 2)
    ax.set_ylim(-ylim, ylim)

    yticks = np.arange(start=0, stop=ylim, step=np.round(ylim / 5, 2))
    ax.set_yticks(np.round(np.append(yticks, -yticks[1:]), 2))
    ax.set_yticklabels([str(abs(x)) for x in ax.get_yticks()])

    if filename is not None:
        plt.savefig(filename + '.png')
        plt.savefig(filename + '.pdf')
        plt.close()
    else:
        plt.show()


def plot_capacities():
    cap_2016 = pd.DataFrame(
        {'BNetzA': [16.8, 9.92],
         'MaStR': [18.52, 12.89],
         'OPSD': [21.62, 10.42]},
        index=['Wind', 'PV']
    )
    cap = pd.DataFrame(
        {'BNetzA': [17.93, 10.47],
         'MaStR': [20.29, 13.45],
         'OPSD': [21.94, 10.49]},
        index=['Wind', 'PV']
    )
    cap_all = pd.DataFrame(
        {'BNetzA': [16.8, 17.93, 9.92, 10.47],
         'MaStR': [18.52, 20.29, 12.89, 13.45],
         'OPSD': [21.62, 21.94, 10.42, 10.49]},
        index=[('Wind', 2016), ('Wind', 2017), ('PV', 2016), ('PV', 2017)]
    )
    cap.plot.bar(rot=0, color=['c', 'b', 'r'])
    plt.ylabel('Installed capacity in GW')
    #plt.show()
    plt.savefig('installed_capacities.png')


if __name__ == "__main__":

    years = [2016, 2017]
    category = 'Wind'
    freq = 0.1
    setting = 'ramps' # 'ramps', 'smoothing'
    weather_data_names = ['open_FRED', 'ERA5']
    register_name = 'MaStR'
    filename = 'histogram_{}_{}_compare_ramps'.format(category, register_name)

    from feedin_germany import validation_data as val_data
    from feedin_germany import settings
    settings.init()  # note: set your paths in settings.py
    feedin_folder = settings.path_wam_ezr

    # get validation time series for all years
    val_feedin_50hertz = pd.DataFrame()
    for year in years:
        val_feedin_year = val_data.load_feedin_data([category], year,
                                                    latest=True)
        val_feedin_50hertz_year = val_feedin_year.loc[
            val_feedin_year['nuts'] == '50 Hertz']
        val_feedin_50hertz = pd.concat(
            [val_feedin_50hertz, val_feedin_50hertz_year])

    validation_df = val_feedin_50hertz
    for weather_data_name in weather_data_names:
        feedin_50hertz = pd.DataFrame()
        for year in years:
            filename_feedin = os.path.join(
                feedin_folder, category, 'feedin_50Hz_{}_{}_{}.csv'.format(
                    weather_data_name, register_name, year))
            feedin_50hertz_year = pd.read_csv(filename_feedin, index_col=0,
                                              parse_dates=True).reset_index()
            feedin_50hertz = pd.concat([feedin_50hertz, feedin_50hertz_year])
        feedin_50hertz = feedin_50hertz.rename(
            columns={'feedin': 'feedin_{}'.format(weather_data_name)})
        validation_df = pd.merge(left=validation_df, right=feedin_50hertz,
                                 how='left', on=['time', 'technology', 'nuts'])

    if category is 'Solar':
        # filter night time values
        lat = 52.456032
        lon = 13.525282
        validation_df = pv_feedin_drop_night_times(
            validation_df.set_index('time'), lat=lat, lon=lon)
    else:
        validation_df.set_index('time', inplace=True)

    # plots for only one weather data set
    #special_histogram(validation_df)
    #histogram(validation_df)
    #simple_histogram(validation_df)

    # calculate ramp
    ind_2 = validation_df.index - pd.Timedelta(hours=1)
    cols = ['feedin_{}'.format(_) for _ in weather_data_names]
    cols.append('feedin_val')
    for col in cols:
        validation_df['ramp_{}'.format(col)] = \
            validation_df.loc[:, col].values - \
            validation_df.loc[ind_2, col].values
    # plot for both weather data sets
    histogram(validation_df, filename, freq=freq, setting=setting)

    #plot_capacities()
