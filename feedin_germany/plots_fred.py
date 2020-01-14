import os
import pandas as pd
import settings

# internal imports
import plots

settings.init()  # note: set your paths in settings.py
feedin_folder = settings.path_wam_ezr
validation_df_folder = os.path.join(feedin_folder, 'validation_dfs')
val_metrics_folder = os.path.join(feedin_folder,
                                  'validation_metrics')
plots_folder = os.path.join(feedin_folder, 'plots')

if not os.path.exists(plots_folder):
    os.makedirs(plots_folder, exist_ok=True)

categories = [
    'Wind',
    'Solar',
    # 'Hydro'  # not implemented, yet
]
register_names = [
    'opsd',  # fix decommissioning date...
    'MaStR'  # only use for category 'Wind'
]
weather_data_names = [
    'open_FRED',
    'ERA5'
]

smoothing = [
    True,
    False
]

print_metrics = True


for category in categories:
    if print_metrics:
        # read metrics
        metrics_df = pd.read_csv(os.path.join(
        val_metrics_folder, 'validation_metrics_50Hz_{cat}.csv'.format(
            cat=category)), index_col=0)
    combined_df = pd.DataFrame()
    for smooth in smoothing:
        if category == 'Solar' and smooth:
            pass
        else:
            for weather_data_name in weather_data_names:
                for register_name in register_names:
                    # create filename
                    if category == 'Wind':
                        if smooth:
                            add_on = '_smoothed'
                        else:
                            add_on = ''
                        filename = 'validation_df_{}_{}{}_{}.csv'.format(
                                category, weather_data_name, add_on,
                            register_name)
                        plot_title = '{reg}, {weather}, {add}'.format(
                            reg=register_name,
                            weather=weather_data_name, add=add_on.replace('_', ' ').replace('ed', 'ing'))
                    else:
                        filename = 'validation_df_{}_{}_{}.csv'.format(
                                category, weather_data_name, register_name)
                        plot_title = '{reg}, {weather}'.format(
                            cat=category, reg=register_name,
                            weather=weather_data_name)
                    val_filename = os.path.join(
                            validation_df_folder, filename)
                    # load validation df
                    validation_df = pd.read_csv(val_filename, parse_dates=True,
                                                index_col=0)
                    # feed-in in GW
                    validation_df['feedin'] = validation_df['feedin'] / 1e9
                    validation_df['feedin_val'] = validation_df['feedin_val'] / 1e9
                    if print_metrics:
                        # select metrics for plot
                        metrics = metrics_df.loc[
                            (metrics_df['register'] == register_name) &
                            (metrics_df['weather'] == weather_data_name)].drop(
                            ['register', 'weather', 'time_step_amount',
                             'pearson'], axis=1)
                        if category == 'Wind':
                            metrics = metrics.loc[
                                metrics['smoothing'] == smooth].drop(
                                'smoothing', axis=1)
                        metrics.rename(columns={'rmse_norm': 'RMSE$_{r}$',
                                                'rmse_norm_bias_corrected': 'RMSE$_{rbc}$',
                                                'mean_bias': 'bias'}, inplace=True)
                        metrics_dict = {}
                        for item in metrics.keys():
                            if item == 'bias':
                                metrics_dict[item] = '{:.2f} GW'.format(
                                    round(metrics[item].values[0] / 1e9, 2))
                            else:
                                metrics_dict[item] = '{:.2f} %'.format(
                                    round(metrics[item].values[0], 2))
                    else:
                        metrics_dict = None
                    filename_plot = os.path.join(
                        plots_folder, filename.replace('validation_df',
                                                           'qq_plot').replace('csv', 'png'))  # svg, png..
                    if category == 'Solar':
                        maximum = 9.0
                    elif category == 'Wind':
                        maximum = 18.0
                    plot_title = None  # überschreibt obigen titel
                    plots.plot_correlation(
                        df=validation_df, val_cols=['feedin', 'feedin_val'],
                        filename=filename_plot, title=plot_title,
                        ylabel='Calculated feed-in in GW',
                        xlabel='Validation feed-in in GW', color='darkblue',
                        marker_size=3, metrics=metrics_dict, maximum=maximum)
