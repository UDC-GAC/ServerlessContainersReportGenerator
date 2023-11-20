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

from src.opentsdb import bdwatchdog
from src.lineplotting.style import line_style, dashes_dict, line_marker, LEGEND_FONTSIZE, LINE_MARK_EVERY
from src.common.config import OpenTSDBConfig, eprint
from src.common.utils import translate_metric, save_figure

# initialize the OpenTSDB handler
bdwatchdog_handler = bdwatchdog.BDWatchdog(OpenTSDBConfig())

def translate_plot_name_to_ylabel(plot_name):
    if plot_name == "cpu":
        return "CPU (shares)"
    elif plot_name == "mem":
        return "Memory (GiB)"
    elif plot_name == "accounting":
        return "Accounting"
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
        return timeseries.values()


def plot_test_doc(test, doc_name, plots, cfg):
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

        fig = plt.figure(figsize=(cfg.FIGURE_SIZE_X, cfg.FIGURE_SIZE_Y))
        ax1 = fig.add_subplot(111)

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

        ###########################################################

        for metric in plots[resource]:
            metric_name = metric[0]

            # Get the time series data
            if metric_name not in doc_ts or not doc_ts[metric_name]:
                continue

            timeseries = doc_ts[metric_name]

            # This was done for users, for some reason
            # timeseries = bdwatchdog_handler.perform_timeseries_range_apply(timeseries, 0, None)
            ##

            # Convert the time stamps to times relative to 0 (basetime)
            basetime = int(list(timeseries.keys())[0])
            x = list(map(lambda point: int(point) - basetime, timeseries))

            # Get the time series points and rebase them if necessary
            y = rebase_ts_values(resource, timeseries)

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
                     markersize=5,
                     markevery=LINE_MARK_EVERY
                     )

        # Set x and y limits
        top, bottom = max_y_ts_point_value, min_y_ts_point_value
        left, right = -30, max_x_ts_point_value + 30

        # If not static limits apply an amplification factor or the max timeseries value will be at the plot "ceiling"
        if not cfg.STATIC_LIMITS:
            top = math.ceil(top * cfg.Y_AMPLIFICATION_FACTOR)
            bottom -= abs(math.floor(bottom * (cfg.Y_AMPLIFICATION_FACTOR-1)))

        plt.xlim(left=left, right=right)
        plt.ylim(top=top, bottom=bottom)

        if bottom < 0:
            # Make the 0 line thicker
            ax1.axhline(linewidth=1.5, color="red")
            # ax1.axvline(linewidth=1, color="k")

        # Set properties to the whole plot
        plt.xlabel('Time(s)', fontsize=11)
        plt.ylabel(translate_plot_name_to_ylabel(resource), style="italic", weight="bold", fontsize=13)
        plt.title('')
        plt.grid(True)
        plt.legend(loc='upper right',
                   shadow=False,
                   fontsize=LEGEND_FONTSIZE,
                   fancybox=True,
                   facecolor='#afeeee',
                   labelspacing=0.15,
                   handletextpad=0.18,
                   borderpad=0.22)

        if cfg.STATIC_LIMITS:
            plt.xticks(np.arange(0, right, step=cfg.XTICKS_STEP))
        else:
            # May be inaccurate up to +- 'downsample' seconds,
            # because the data may start a little after the specified 'start' time or end
            # a little before the specified 'end' time
            plt.xticks(np.arange(0, int(end_time) - int(start_time), step=cfg.XTICKS_STEP))

        # Save the plots
        figure_filepath_directory = "{0}/{1}".format("timeseries_plots", test_name)
        if "svg" in cfg.PLOTTING_FORMATS:
            figure_name = "{0}_{1}.{2}".format(doc_name, resource, "svg")
            save_figure(figure_filepath_directory, figure_name, fig, format="svg")

        if "png" in cfg.PLOTTING_FORMATS:
            figure_name = "{0}_{1}.{2}".format(doc_name, resource, "png")
            save_figure(figure_filepath_directory, figure_name, fig, format="png")

        plt.close()
