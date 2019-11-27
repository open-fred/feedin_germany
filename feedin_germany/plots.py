import matplotlib.pyplot as plt


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
    plt.legend(handles=[ideal, deviation_100])
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

