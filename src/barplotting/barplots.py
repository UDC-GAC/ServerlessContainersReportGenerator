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
import pandas as pd
import matplotlib.pyplot as plt

from src.barplotting.utils import get_y_limit
from src.common.config import Config
from src.common.utils import translate_metric, save_figure

# Get the config
cfg = Config()


def translate_shares_to_vcore_minutes(bars):
    return [x / (100 * 60) for x in bars]


def translate_MBseconds_to_GBminutes(bars):
    return [x / (1024 * 60) for x in bars]


ylabels = {"cpu": "CPU (Vcore-minutes)", "mem": "Memory (GB-minutes)"}
convert_functions = {"cpu": translate_shares_to_vcore_minutes, "mem": translate_MBseconds_to_GBminutes}


def save_barplot_figure(figure_name, fig, benchmark_type):
    figure_filepath_directory = "resource_barplots/{0}".format(benchmark_type)
    save_figure(figure_filepath_directory, figure_name, fig)


def plot_tests_resource_usage(tests):
    width, height = int(len(tests) / 3), 8
    figure_size = (width, height)
    benchmark_type = tests[0]["test_name"].split("_")[0]
    resource_list = ["structure.cpu.current",
                     "structure.cpu.usage",
                     "structure.mem.current",
                     "structure.mem.usage",
                     "structure.energy.max",
                     "structure.energy.usage"]

    for resource in resource_list:
        labels = []
        values_sum, values_avg = [], []
        splits = resource.split(".")
        resource_label, resource_metric = splits[1], splits[2]

        for test in tests:
            labels.append(test["test_name"].split("_")[1])
            if test["resource_aggregates"] == "n/a":
                values_sum.append(0)
                values_avg.append(0)
            else:
                resource_aggregate = test["resource_aggregates"]["ALL"][resource]
                if resource_label == "cpu":
                    values_sum.append(resource_aggregate["SUM"] / (100 * 60))
                    values_avg.append(resource_aggregate["AVG"] / 100)
                elif resource_label == "mem":
                    values_sum.append(resource_aggregate["SUM"] / (1024 * 60))
                    values_avg.append(resource_aggregate["AVG"] / 1024)
                elif resource_label == "energy":
                    values_sum.append(resource_aggregate["SUM"])
                    values_avg.append(resource_aggregate["AVG"])
                else:
                    values_sum.append(resource_aggregate["SUM"])
                    values_avg.append(resource_aggregate["AVG"])

        # Plot the data
        df = pd.DataFrame({'SUM': values_sum, 'AVG': values_avg}, index=labels)
        ax = df.plot.bar(
            rot=0,
            title=[translate_metric(resource), ""],
            subplots=True,
            figsize=figure_size,
            sharex=False)

        # Set the labels
        if resource_label == "cpu":
            ax[0].set_ylabel("Vcore-minutes")
            ax[1].set_ylabel("Vcore-seconds/second")
        elif resource_label == "mem":
            ax[0].set_ylabel("GB-minutes")
            ax[1].set_ylabel("GB-second/second")
        elif resource_label == "energy":
            ax[0].set_ylabel("Watts·h")
            ax[1].set_ylabel("Watts·h/s")
        else:
            ax[0].set_ylabel("Unknown")
            ax[1].set_ylabel("Unknown")
        ax[0].set_xlabel("# test-run")
        ax[1].set_xlabel("# test-run")

        # Set the Y limits
        top, bottom = get_y_limit("resource_usage", max(values_sum),
                                  benchmark_type=benchmark_type, resource_label=resource, static_limits=False)
        ax[0].set_ylim(top=top, bottom=bottom)

        # Save the plot
        figure_name = "{0}_{1}.{2}".format(resource_label, resource_metric, "svg")
        fig = ax[0].get_figure()
        save_barplot_figure(figure_name, fig, benchmark_type)
        plt.close()



def plot_tests_times(tests):
    labels, durations_seconds, durations_minutes = [], [], []
    width, height = 8, int(len(tests) / 3)
    figure_size = (width, height)
    benchmark_type = tests[0]["test_name"].split("_")[0]

    for test in tests:
        seconds, minutes, overhead = 0, 0, 0
        labels.append(test["test_name"].split("_")[1])
        if test["duration"] != "n/a":
            seconds = test["duration"]
            minutes = "{:.2f}".format((test["duration"]) / 60)

        durations_seconds.append(seconds)
        durations_minutes.append(minutes)

    # Plot the data
    df = pd.DataFrame({'time': durations_seconds}, index=labels)
    ax = df.plot.barh(
        rot=0,
        title="Time and overheads",
        figsize=figure_size)

    # Set the labels
    ax.set_ylabel("test-run")
    ax.set_xlabel("Time (seconds)")

    # Save the plot
    figure_name = "{0}.{1}".format("times", "svg")
    fig = ax.get_figure()
    save_barplot_figure(figure_name, fig, benchmark_type)
    plt.close()
