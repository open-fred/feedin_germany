import matplotlib.pyplot as plt


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