import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import math
from feedin_germany.validation_tools import pv_feedin_drop_night_times


def plot_correlation(df, val_cols, filename='Tests/correlation_test.pdf',
                     title=None, xlabel=None, ylabel=None, color='darkblue',
                     marker_size=3, metrics=None, maximum=None):
    r"""
    Visualize the correlation between two feedin time series.

    Parameters
    ----------
    df : pd.DataFrame
        Contains simulation results and validation data in the columns as
        specified in `val_cols`.
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
    if maximum is None:
        maximum = max(data.iloc[:, 0].max(), data.iloc[:, 1].max())
    plt.xlim(xmin=0, xmax=maximum)
    plt.ylim(ymin=0, ymax=maximum)
    ideal, = plt.plot([0, maximum], [0, maximum], color='black',
                      linestyle='--', label='ideal correlation')
    deviation_100, = plt.plot([0, maximum], [0, maximum * 2], color='orange',
                              linestyle='--', label='100 % deviation')
    plt.plot([0, maximum * 2], [0, maximum], color='orange', linestyle='--')
    if title:
        plt.title(title)
    plt.legend(handles=[ideal, deviation_100], loc='upper left')
    # Add certain values to plot as text
    if metrics:
        annotation_str = ''.join(['{met} = {val} \n '.format(
            met=item, val=metrics[item]) for item in metrics])[0:-3]
        # annotation_str = ''.join(['{met} &= {val} \\ '.format(
        #     met=item, val=metrics[item]) for item in metrics])[0:-3]
        # annotation_str_aligned = '$\begin{align}' + annotation_str + '\end{align}$'

        plt.annotate(
            annotation_str,
            xy=(1, 0),  # x and y axis - for right lower corner (1, 0)
            xycoords='axes fraction',
            xytext=(-6, +6), textcoords='offset points',
            ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.5))
    plt.tight_layout()
    fig.savefig(filename)
    fig.savefig(filename.replace('png', 'pdf'))
    plt.close()


def box_plots_bias(df, filename='Tests/test.pdf', title='Test'):
    r"""
    Creates boxplots of the columns of a DataFrame.

    This function is mainly used for creating boxplots of the biases of time
    series.

    Parameters
    ----------
    df : pd.DataFrame
        Columns contain Series to be plotted as Box plots.
    filename : String
        Filename including path relatively to the active folder for saving
        the figure. Default: 'Tests/test.pdf'.
    title : String
        Title of figure. Default: 'Test'.

    """
    fig = plt.figure()
    g = sns.boxplot(data=df, palette='Set3')
    g.set_ylabel('Deviation in MW')
    g.set_title(title)
    fig.savefig(os.path.abspath(os.path.join(
                os.path.dirname(__file__), filename)))
    plt.close()

def histogram(validation_df, filename=None, freq=0.5, setting=None, unit='GW',
              unit_factor=1e9):
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
    unit : str
        Used for labels. Default: 'GW'.
    unit_factor : float
        To adapt the unit of metrics like RMSE, bias, ... (that are not in unit
        %) the metrics will be devided by this factor. Example: time series in
        W, desired unit of metrics GW --> `unit_factor` = 1e9. Default: 1e9

    """

    if setting is None:
        col1 = 'feedin_open_FRED'
        col2 = 'feedin_ERA5'
        val_col = 'feedin_val'
        label1 = 'open_FRED'
        label2 = 'ERA5'
    elif setting == 'smoothing_1':
        col1 = 'feedin_open_FRED'
        col2 = 'feedin_open_FRED_smoothed'
        val_col = 'feedin_val'
        label1 = 'berechnete Einspeisung (nicht geglättet)'
        label2 = 'berechnete Einspeisung (geglättet)'
    elif setting == 'smoothing_2':
        col1 = 'feedin_ERA5'
        col2 = 'feedin_ERA5_smoothed'
        val_col = 'feedin_val'
        label1 = 'berechnete Einspeisung (nicht geglättet)'
        label2 = 'berechnete Einspeisung (geglättet)'
    elif setting == 'ramps':
        col1 = 'ramp_feedin_open_FRED'
        col2 = 'ramp_feedin_ERA5'
        val_col = 'ramp_feedin_val'
        label1 = 'open_FRED'
        label2 = 'ERA5'

    validation_df = validation_df.loc[
                    :, [col1, col2, val_col]] / unit_factor
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
    plt.xlabel('Feed-in in {}'.format(unit))
    plt.ylabel('Probability')
    ax.legend()

    ax.set_xlim(0, math.ceil(validation_df.max().max()))
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


if __name__ == "__main__":
    from feedin_germany import validation_data as val_data
    from feedin_germany import settings

    settings.init()  # note: set your paths in settings.py
    feedin_folder = settings.path_wam_ezr

    years = [2016, 2017]
    category = 'Wind'
    # setting = 'smoothing_2' # 'ramps', 'smoothing'
    settings = [None, 'smoothing_1', 'smoothing_2', 'ramps'] # 'ramps', 'smoothing'

    register_names = ['MaStR', 'opsd']


    for setting in settings:
        for register_name in register_names:
            if setting == 'smoothing_2':
                weather_data_names = ['ERA5', 'ERA5_smoothed']
            elif setting == 'smoothing_1':
                weather_data_names = ['open_FRED', 'open_FRED_smoothed']
            else:
                weather_data_names = ['open_FRED', 'ERA5']

            filename = 'histogram_{}_{}_compare_{}'.format(
                category, register_name, setting)

            if setting == 'ramps':
                freq = 0.2
            else:
                freq = 0.5

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
            histogram(validation_df, filename=os.path.join(feedin_folder, 'plots',
                                                           filename),
                      freq=freq, setting=setting)

        #plot_capacities()
