# Copyright (c) 2019 Universidade da Coruña
# Authors:
#     - Jonatan Enes [main](jonatan.enes@udc.es, jonatan.enes.alvarez@gmail.com)
#     - Roberto R. Expósito
#     - Juan Touriño
#
# This file is part of the BDWatchdog framework, from
# now on referred to as BDWatchdog.
#
# BDWatchdog is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# BDWatchdog is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BDWatchdog. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import math

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from numpy import NaN

from src.opentsdb import bdwatchdog
from src.lineplotting.style import line_style, dashes_dict, line_marker, LEGEND_FONTSIZE
from src.common.config import OpenTSDBConfig, eprint
from src.common.utils import translate_metric, save_figure

# initialize the OpenTSDB handler
bdwatchdog_handler = bdwatchdog.BDWatchdog(OpenTSDBConfig())


def translate_plot_name_to_ylabel(plot_name):
    if plot_name == "cpu":
        return "CPU"
    elif plot_name == "mem":
        return "Memory (GiB)"
    elif plot_name == "accounting":
        return "Funds" # Changed from Accounting to billing due to a concept naming change in the paper
    elif plot_name == "tasks":
        return "Tasks"
    elif plot_name == "energy":
        return "Energy (J)"
    else:
        return plot_name


def rebase_ts_values(resource, timeseries):
    if resource == "mem":
        # Translate from MiB to GiB
        return list(map(lambda point: int(point / 1024), timeseries.values()))
    else:
        return list(timeseries.values())


def plot_test_doc(test, doc_name, plots, cfg):
    def add_xticks():
        if cfg.STATIC_LIMITS:
            ticks = np.arange(0, right, step=cfg.XTICKS_STEP)
        else:
            ticks = np.arange(0, int(end_time) - int(start_time), step=cfg.XTICKS_STEP)
            # May be inaccurate up to +- 'downsample' seconds,
            # because the data may start a little after the specified 'start' time or end
            # a little before the specified 'end' time

        ROTATION = 0
        HORIZONTAL_ALIGN = "right"
        labels = ["{0}".format(t) for t in ticks]
        plt.xticks(ticks, labels=labels, rotation=ROTATION, ha=HORIZONTAL_ALIGN)


    start_time, end_time = test["start_time"], test["end_time"]
    test_name = test["test_name"]
    doc_ts = test["timeseries"][doc_name]
    for resource in plots:
        if resource not in cfg.REPORTED_RESOURCES:
            continue

        # Pre-Check for empty plot (no timeseries for all the metrics)
        empty_plot = True
        for metric in plots[resource]:
            metric_name = metric[0]
            if metric_name in doc_ts and doc_ts[metric_name]:
                empty_plot = False
                break

        if empty_plot:
            eprint("In test '{0}' plot '{1}' for doc '{2}' has no data, skipping".format(test_name, resource, doc_name))
            continue

        # Values used for setting the X and Y limits, without depending on actual time series values ####
        if cfg.STATIC_LIMITS:
            if doc_name not in cfg.XLIM:
                max_x_ts_point_value = cfg.XLIM["default"]
            else:
                max_x_ts_point_value = cfg.XLIM[doc_name]
            if doc_name not in cfg.YLIM or resource not in cfg.YLIM[doc_name]:
                max_y_ts_point_value = cfg.YLIM["default"][resource]
                min_y_ts_point_value = cfg.YMIN["default"][resource]
            else:
                max_y_ts_point_value = cfg.YLIM[doc_name][resource]
                min_y_ts_point_value = cfg.YMIN[doc_name][resource]
        else:
            max_y_ts_point_value, max_x_ts_point_value = 0, 0
            min_y_ts_point_value = 0

        size_y = cfg.FIGURE_SIZE_Y
        if cfg.SINGLE_PLOT_WITH_XLABEL:
            if resource == cfg.SINGLE_PLOT_WITH_XLABEL:
                size_y *= 1.1

        fig = plt.figure(figsize=(cfg.FIGURE_SIZE_X, size_y))
        ax1 = fig.add_subplot(111)

        ###########################################################

        for metric in plots[resource]:
            metric_name = metric[0]
            line_color = None

            # Hack to avoid plotting current and reserved in a non-serverless scenario
            if metric_name == "structure.cpu.current" and test_name == "4.noserv_noacct":
                continue
            elif metric_name == "structure.cpu.used" and test_name == "4.noserv_noacct":
                line_color = "tab:green"

            # Get the time series data
            if metric_name not in doc_ts or not doc_ts[metric_name]:
                continue

            timeseries = doc_ts[metric_name]

            # This was done for users, for some reason
            # timeseries = bdwatchdog_handler.perform_timeseries_range_apply(timeseries, 0, None)
            ##

            # Convert the time stamps to times relative to 0 (basetime)
            basetime = int(list(timeseries.keys())[0])

            ########### HOTFIX ################
            ## For transcoding basic experiments for the Blockchain serverless paper
            if cfg.SPLIT_LINEPLOTS_WHEN_TIME_GAPS:  # resource == "cpu":
                t = basetime
                splits = list()
                for k, v in timeseries.items():
                    if int(k) - t > 20:
                        eprint((k, v, int(k), basetime))
                        splits.append(int(k) - 5)
                        splits.append(t + 5)
                    t = int(k)
                for s in splits:
                    timeseries[str(s)] = np.nan
            ########### HOTFIX ################

            x = list(map(lambda point: int(point) - basetime, timeseries))

            # Get the time series points and rebase them if necessary
            y = rebase_ts_values(resource, timeseries)

            data = zip(x, y)
            data = sorted(data)
            x = [p[0] for p in data]
            y = [p[1] for p in data]

            # Set the maximum and minimum time series time and value points
            max_y_ts_point_value = max(max_y_ts_point_value, max(y))
            max_x_ts_point_value = max(max_x_ts_point_value, max(x))
            min_y_ts_point_value = min(min_y_ts_point_value, min(y))

            # Get the line style
            linestyle = line_style[resource][metric_name]

            ax1.plot(x, y,
                     label=translate_metric(metric_name, test_name),
                     linestyle=linestyle,
                     dashes=dashes_dict[linestyle],
                     marker=line_marker[resource][metric_name],
                     markersize=6,
                     markevery=cfg.LINE_MARK_EVERY,
                     color=line_color
                     )

        # Set x and y limits
        top, bottom = max_y_ts_point_value, min_y_ts_point_value
        left, right = -30, max_x_ts_point_value + 30

        # If not static limits apply an amplification factor or the max timeseries value will be at the plot "ceiling"
        if not cfg.STATIC_LIMITS:
            top = math.ceil(top * cfg.Y_AMPLIFICATION_FACTOR)
            bottom -= abs(math.floor(bottom * (cfg.Y_AMPLIFICATION_FACTOR - 1)))

        eprint((resource, top, bottom, left, right))

        plt.xlim(left=left, right=right)
        plt.ylim(top=top, bottom=bottom)

        ########### HOTFIX ################
        if bottom < 0 and resource == "accounting":
            # Make the 0 line thicker
            ax1.axhline(linewidth=1.5, color="red")
            # ax1.axvline(linewidth=1, color="k")
        ########### HOTFIX ################

        # Set properties to the whole plot
        if cfg.SINGLE_PLOT_WITH_XLABEL:
            if resource == cfg.SINGLE_PLOT_WITH_XLABEL:
                plt.xlabel('Time(s)', fontsize=12)
        else:
            plt.xlabel('Time(s)', fontsize=12)

        if cfg.PRINT_Y_LABEL:
            plt.ylabel(translate_plot_name_to_ylabel(resource), style="italic", weight="bold", fontsize=13)
        else:
            plt.ylabel(".", color="white") # This is so that the tweak of label space has effect

        ########### HOTFIX ################
        if "noserv_noacct" in test_name or "noserv_acct" in test_name:
            plt.ylabel(".", color="white")  # This is so that the tweak of label space has effect
        ########### HOTFIX ################

        plt.title('')
        plt.grid(True)
        
        ########### HOTFIX ################
        handles, labels = plt.gca().get_legend_handles_labels()
        if resource == "accounting":
            custom_order = ['Balance', 'Single task cost', 'Max allowed debt']
            # Get current handles and labels
            handles, labels = plt.gca().get_legend_handles_labels()
            # Build a dict to map labels to handles
            label_to_handle = dict(zip(labels, handles))
            # Sort handles and labels by custom order
            sorted_labels = [label for label in custom_order if label in label_to_handle]
            sorted_handles = [label_to_handle[label] for label in sorted_labels]
        else:
            sorted_labels = labels
            sorted_handles = handles
        ########### HOTFIX ################
        
        plt.legend(sorted_handles,
                   sorted_labels,
                   loc='upper right',
                   shadow=False,
                   fontsize=LEGEND_FONTSIZE,
                   fancybox=True,
                   facecolor='#afeeee',
                   labelspacing=0.15,
                   handletextpad=0.18,
                   borderpad=0.22,
                   framealpha=1)

        ########### HOTFIX ################
        ## For transcoding basic experiments for the Blockchain serverless paper
        if test_name == "2.serv_noacct" and resource == "cpu":
            plt.legend(loc='upper left',
                       shadow=False,
                       fontsize=LEGEND_FONTSIZE,
                       fancybox=True,
                       facecolor='#afeeee',
                       labelspacing=0.15,
                       handletextpad=0.18,
                       borderpad=0.22,
                       framealpha=1)
        ########### HOTFIX ################

        # if resource == "cpu":
        #     plt.axvline(x=4080, ymin=0.05, ymax=0.95, color='red', label='axvline - % of full height')

        ax1.yaxis.set_major_formatter(FormatStrFormatter("%5d"))

        # ADD YTICKS
        if cfg.STATIC_LIMITS:
            plt.yticks(np.arange(math.ceil(bottom), math.ceil(top), step=cfg.YTICKS_STEP[resource]))

        # ADD XTICKS
        add_xticks()
        if cfg.SINGLE_PLOT_WITH_XTICKS:
            if resource != cfg.SINGLE_PLOT_WITH_XLABEL:
                # Hide the xticks labels, keep the lines
                for tick in ax1.xaxis.get_major_ticks():
                    tick.tick1line.set_visible(True)
                    tick.label1.set_visible(False)

        # Add small pad as otherwise matplotlib might trim some letters on the left side,
        # or the plots' black box from the right side
        PAD_INCHES = 0.03

        # Tweak this parameter to position the ylabel closer or farther from the yticks
        # This indirectly affects the size and thus, allows to align several different plot resources in column in Latex
        ax1.yaxis.set_label_coords(cfg.RESOURCE_X_LABELSEP[resource], 0.5)

        # Save the plots
        figure_filepath_directory = "{0}/{1}".format("timeseries_plots", test_name)
        if "svg" in cfg.PLOTTING_FORMATS:
            figure_name = "{0}_{1}.{2}".format(doc_name, resource, "svg")
            save_figure(figure_filepath_directory, figure_name, fig, format="svg", pad_inches=PAD_INCHES)

        if "png" in cfg.PLOTTING_FORMATS:
            figure_name = "{0}_{1}.{2}".format(doc_name, resource, "png")
            save_figure(figure_filepath_directory, figure_name, fig, format="png", pad_inches=PAD_INCHES)

        plt.close()
