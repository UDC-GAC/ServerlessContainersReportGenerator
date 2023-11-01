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

import pathlib
import sys
import time
from tabulate import tabulate

from src.opentsdb import bdwatchdog
from src.common.config import OpenTSDBConfig
from src.latex.latex_output import latex_print
from src.common.config import Config




# initialize the OpenTSDB handler
bdwatchdog_handler = bdwatchdog.BDWatchdog(OpenTSDBConfig())



# Get the config
cfg = Config()

# Generate the resource information of both tests and experiments
def generate_resources_timeseries(document, cfg):
    #  Check that the needed start and end time are present, otherwise abort
    if "end_time" not in document or "start_time" not in document:
        document["resource_aggregates"] = "n/a"
        return document

    # Initialize variables
    document["resource_aggregates"], document["resources"], document["users"] = dict(), dict(), dict()
    start, end = document["start_time"], document["end_time"]

    for user in cfg.USERS_LIST:
        document["users"][user] = \
            bdwatchdog_handler.get_structure_timeseries(user, start, end, cfg.BDWATCHDOG_USER_METRICS,
                                                        downsample=cfg.DOWNSAMPLE)
        # TODO rename this function or create a get_user_timeseries

    # Retrieve the timeseries from OpenTSDB and perform the per-structure aggregations
    # Slow loop due to network call
    for node_name in cfg.NODES_LIST:
        document["resources"][node_name] = \
            bdwatchdog_handler.get_structure_timeseries(node_name, start, end, cfg.BDWATCHDOG_NODE_METRICS,
                                                            downsample=cfg.DOWNSAMPLE)

        metrics_to_agregate = document["resources"][node_name]
        document["resource_aggregates"][node_name] = \
            bdwatchdog_handler.perform_structure_metrics_aggregations(start, end, metrics_to_agregate)

    # Generate the per-node time series 'usage' metrics (e.g., structure.cpu.usage)
    for node_name in cfg.NODES_LIST:
        for agg_metric in cfg.USAGE_METRICS_SOURCE:
            agg_metric_name, metric_list = agg_metric
            metrics_to_agregate = document["resources"][node_name]

            # Initialize
            if agg_metric_name not in metrics_to_agregate:
                metrics_to_agregate[agg_metric_name] = dict()

            # Get the first metric as the time reference, considering that all metrics should have
            # the same timestamps
            first_metric = metrics_to_agregate[metric_list[0]]
            for time_point in first_metric:
                # Iterate through the metrics
                for metric in metric_list:
                    # Timestamp from the first 'reference' metric is not present in other metric,
                    # this may be due to the head and tail data points of the time series
                    if time_point not in metrics_to_agregate[metric]:
                        continue
                    # Initialize
                    if time_point not in metrics_to_agregate[agg_metric_name]:
                        metrics_to_agregate[agg_metric_name][time_point] = 0

                    # Sum
                    metrics_to_agregate[agg_metric_name][time_point] += \
                        metrics_to_agregate[metric][time_point]

    # Generate the per-node aggregated 'usage' metrics (e.g., structure.cpu.usage)
    for node_name in cfg.NODES_LIST:
        for agg_metric in cfg.USAGE_METRICS_SOURCE:
            agg_metric_name, metrics_to_aggregate = agg_metric
            aggregates = document["resource_aggregates"][node_name]

            # Initialize
            if agg_metric_name not in aggregates:
                aggregates[agg_metric_name] = {"SUM": 0, "AVG": 0}

            # Add up to create the SUM
            for metric in metrics_to_aggregate:
                aggregates[agg_metric_name]["SUM"] += aggregates[metric]["SUM"]

            # Create the AVG from the SUM
            aggregates[agg_metric_name]["AVG"] = aggregates[agg_metric_name]["SUM"] / document["duration"]

    # Generate the ALL pseudo-metrics for the overall application (all the container nodes)
    document["resources"]["ALL"] = dict()
    for node_name in cfg.NODES_LIST:
        for metric in document["resources"][node_name]:
            if metric not in document["resources"]["ALL"]:
                document["resources"]["ALL"][metric] = document["resources"][node_name][metric]
                continue

            for time_point in document["resources"][node_name][metric]:
                try:
                    document["resources"]["ALL"][metric][time_point] += \
                        document["resources"][node_name][metric][time_point]
                except KeyError:
                    pass

    # Generate the aggregated ALL pseudo-metrics for the overall application (all the container nodes)
    document["resource_aggregates"]["ALL"] = dict()
    for node_name in cfg.NODES_LIST:
        for metric in document["resource_aggregates"][node_name]:
            # Initialize
            if metric not in document["resource_aggregates"]["ALL"]:
                document["resource_aggregates"]["ALL"][metric] = dict()

            metric_global_aggregates = document["resource_aggregates"]["ALL"][metric]
            node_agg_metric = document["resource_aggregates"][node_name][metric]

            for aggregation in node_agg_metric:
                # Initialize
                if aggregation not in metric_global_aggregates:
                    metric_global_aggregates[aggregation] = 0

                # Add up
                metric_global_aggregates[aggregation] += node_agg_metric[aggregation]

    for app in cfg.APPS_LIST:
        document["resources"][app] = \
            bdwatchdog_handler.get_structure_timeseries(app, start, end, cfg.BDWATCHDOG_APP_METRICS,
                                                            downsample=cfg.DOWNSAMPLE)

        document["resource_aggregates"][app] = \
            bdwatchdog_handler.perform_structure_metrics_aggregations(start, end, document["resources"][app])

    # This metric is manually added because container structures do not have it, only application structures
    if "energy" in cfg.REPORTED_RESOURCES:
        document["resource_aggregates"]["ALL"]["structure.energy.max"] = {"SUM": 0, "AVG": 0}
        document["resources"]["ALL"]["structure.energy.max"] = {}
        for app in cfg.APPS_LIST:
            for time_point in document["resources"][app]["structure.energy.max"]:
                try:
                    document["resources"]["ALL"]["structure.energy.max"][time_point] += \
                        document["resources"][app]["structure.energy.max"][time_point]
                except KeyError:
                    document["resources"]["ALL"]["structure.energy.max"][time_point] = \
                        document["resources"][app]["structure.energy.max"][time_point]

            document["resource_aggregates"]["ALL"]["structure.energy.max"]["SUM"] += \
                document["resource_aggregates"][app]["structure.energy.max"]["SUM"]
            document["resource_aggregates"]["ALL"]["structure.energy.max"]["AVG"] += \
                document["resource_aggregates"][app]["structure.energy.max"]["AVG"]

    return document


def generate_duration(document):
    document["duration"] = "n/a"
    if "end_time" in document and "start_time" in document:
        document["duration"] = document["end_time"] - document["start_time"]
    return document


# PRINT EXPERIMENT OR TEST DOCUMENT INFORMATION
def print_basic_doc_info(doc):
    start_time_string, end_time_string, duration, duration_minutes = get_times_from_doc(doc)
    if "test_name" in doc:
        latex_print("\\textbf{TEST:}" + " {0}".format(doc["test_name"]))
    else:
        latex_print("\\textbf{EXPERIMENT:}" + " {0}".format(doc["experiment_id"]))
        latex_print("\\textbf{USER:}" + "{0}".format(doc["username"]))

    latex_print("\\textbf{START TIME:}" + " {0}".format(start_time_string))
    latex_print("\\textbf{END TIME:}" + " {0}".format(end_time_string))
    latex_print("\\textbf{DURATION:}" + " {0} seconds (about {1} minutes)".format(duration, duration_minutes) + "  ")


def flush_table(table, header, table_caption=None):
    # print_latex_vertical_space()
    print(tabulate(table, header))
    print("")
    if table_caption:
        latex_print("Table: " + table_caption)

def create_output_directory(figure_filepath_directory):
    pathlib.Path(figure_filepath_directory).mkdir(parents=True, exist_ok=True)


def get_plots():
    plots = dict()
    plots["user"] = dict()

    plots["user"]["untreated"] = {"cpu": [], "energy": []}
    plots["user"]["energy"] = {"cpu": [], "energy": []}
    plots["user"]["serverless"] = {"cpu": [], "energy": []}

    plots["user"]["untreated"]["cpu"] = [('user.cpu.current', 'structure'), ('user.cpu.usage', 'structure')]
    plots["user"]["serverless"]["cpu"] = plots["user"]["untreated"]["cpu"]
    plots["user"]["energy"]["cpu"] = plots["user"]["untreated"]["cpu"]

    plots["user"]["untreated"]["energy"] = [('user.energy.max', 'user'), ('user.energy.used', 'user')]
    plots["user"]["serverless"]["energy"] = plots["user"]["untreated"]["energy"]
    plots["user"]["energy"]["energy"] = plots["user"]["untreated"]["energy"]

    plots["app"] = dict()

    plots["app"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["app"]["serverless"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["app"]["energy"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}

    plots["app"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure')]
    plots["app"]["serverless"]["cpu"] = plots["app"]["untreated"]["cpu"]
    plots["app"]["energy"]["cpu"] = plots["app"]["untreated"]["cpu"]

    plots["app"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure')]
    plots["app"]["serverless"]["mem"] = plots["app"]["untreated"]["mem"]
    plots["app"]["energy"]["mem"] = plots["app"]["untreated"]["mem"]

    plots["app"]["untreated"]["disk"] = [('structure.disk.current', 'structure'), ('structure.disk.usage', 'structure')]
    plots["app"]["serverless"]["disk"] = plots["app"]["untreated"]["disk"]
    plots["app"]["energy"]["disk"] = plots["app"]["untreated"]["disk"]

    plots["app"]["untreated"]["net"] = [('structure.net.current', 'structure'), ('structure.net.usage', 'structure')]
    plots["app"]["serverless"]["net"] = plots["app"]["untreated"]["net"]
    plots["app"]["energy"]["net"] = plots["app"]["untreated"]["net"]

    if cfg.PRINT_ENERGY_MAX:
        plots["app"]["untreated"]["energy"] = [('structure.energy.max', 'structure')]
    plots["app"]["untreated"]["energy"].append(('structure.energy.usage', 'structure'))
    plots["app"]["serverless"]["energy"] = plots["app"]["untreated"]["energy"]
    plots["app"]["energy"]["energy"] = plots["app"]["untreated"]["energy"]

    plots["node"] = dict()
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["serverless"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["energy"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}

    plots["node"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure')
                                         # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host')
                                         ]
    plots["node"]["serverless"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure'),
                                          # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host'),
                                          ('limit.cpu.lower', 'structure'), ('limit.cpu.upper', 'structure')]
    plots["node"]["energy"]["cpu"] = plots["node"]["untreated"]["cpu"]

    plots["node"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure')]
    # ('proc.mem.resident', 'host')]
    plots["node"]["serverless"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure'),
                                          ('limit.mem.lower', 'structure'), ('limit.mem.upper', 'structure')]
    # ('proc.mem.resident', 'host'),
    plots["node"]["energy"]["mem"] = plots["node"]["untreated"]["mem"]

    plots["node"]["untreated"]["disk"] = [('structure.disk.current', 'structure'), ('proc.disk.reads.mb', 'host'),
                                          ('proc.disk.writes.mb', 'host')]
    plots["node"]["serverless"]["disk"] = plots["node"]["untreated"]["disk"]
    plots["node"]["energy"]["disk"] = plots["node"]["untreated"]["disk"]

    plots["node"]["untreated"]["net"] = [('structure.net.current', 'structure'), ('proc.net.tcp.in.mb', 'host'),
                                         ('proc.net.tcp.out.mb', 'host')]
    plots["node"]["serverless"]["net"] = plots["node"]["untreated"]["net"]
    plots["node"]["energy"]["net"] = plots["node"]["untreated"]["net"]

    plots["node"]["energy"]["energy"] = [('structure.energy.usage', 'structure')]

    return plots

def save_figure(figure_filepath_directory, figure_name, figure, format="svg"):
    figure_filepath = "{0}/{1}".format(figure_filepath_directory, figure_name)
    create_output_directory(figure_filepath_directory)
    # figure.savefig(figure_filepath, transparent=True, bbox_inches='tight', pad_inches=0, format=format)
    # figure.savefig(figure_filepath, transparent=True, bbox_inches='tight', pad_inches=0, format=format)
    figure.savefig(figure_filepath, bbox_inches='tight', pad_inches=0, format=format)

def format_metric(value, label, aggregation):
    if aggregation == "AVG":
        number_format = "{:.2f}"
    else:
        number_format = "{:.0f}"

    if label.startswith("structure.cpu") or label.startswith("proc.cpu"):
        formatted_metric = "{0} vcore-s".format(number_format.format(value / 100))
    elif label.startswith("structure.mem") or label.startswith("proc.mem"):
        formatted_metric = "{0} GB-s".format(number_format.format(value / 1024))
    elif label.startswith("structure.disk") or label.startswith("proc.disk"):
        formatted_metric = "{0} GB".format(number_format.format(value / 1024))
    elif label.startswith("structure.net") or label.startswith("proc.net"):
        formatted_metric = "{0} Gbit".format(number_format.format(value / 1024))
    elif label.startswith("structure.energy"):
        if value >= 10000:
            value = value / 1000
        formatted_metric = "{0} KJoule".format(number_format.format(value))
    else:
        formatted_metric = value

    if aggregation == "AVG":
        formatted_metric += "/s"
    return formatted_metric


def some_test_has_missing_aggregate_information(tests):
    for test in tests:
        if test["resource_aggregates"] == "n/a":
            return True
    return False


def get_plots():
    plots = dict()
    plots["user"] = dict()

    plots["user"]["untreated"] = {"cpu": [], "energy": []}
    plots["user"]["energy"] = {"cpu": [], "energy": []}
    plots["user"]["serverless"] = {"cpu": [], "energy": []}

    plots["user"]["untreated"]["cpu"] = [('user.cpu.current', 'structure'), ('user.cpu.usage', 'structure')]
    plots["user"]["serverless"]["cpu"] = plots["user"]["untreated"]["cpu"]
    plots["user"]["energy"]["cpu"] = plots["user"]["untreated"]["cpu"]

    plots["user"]["untreated"]["energy"] = [('user.energy.max', 'user'), ('user.energy.used', 'user')]
    plots["user"]["serverless"]["energy"] = plots["user"]["untreated"]["energy"]
    plots["user"]["energy"]["energy"] = plots["user"]["untreated"]["energy"]

    plots["app"] = dict()

    plots["app"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["app"]["serverless"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["app"]["energy"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}

    plots["app"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure')]
    plots["app"]["serverless"]["cpu"] = plots["app"]["untreated"]["cpu"]
    plots["app"]["energy"]["cpu"] = plots["app"]["untreated"]["cpu"]

    plots["app"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure')]
    plots["app"]["serverless"]["mem"] = plots["app"]["untreated"]["mem"]
    plots["app"]["energy"]["mem"] = plots["app"]["untreated"]["mem"]

    plots["app"]["untreated"]["disk"] = [('structure.disk.current', 'structure'), ('structure.disk.usage', 'structure')]
    plots["app"]["serverless"]["disk"] = plots["app"]["untreated"]["disk"]
    plots["app"]["energy"]["disk"] = plots["app"]["untreated"]["disk"]

    plots["app"]["untreated"]["net"] = [('structure.net.current', 'structure'), ('structure.net.usage', 'structure')]
    plots["app"]["serverless"]["net"] = plots["app"]["untreated"]["net"]
    plots["app"]["energy"]["net"] = plots["app"]["untreated"]["net"]

    if cfg.PRINT_ENERGY_MAX:
        plots["app"]["untreated"]["energy"] = [('structure.energy.max', 'structure')]
    plots["app"]["untreated"]["energy"].append(('structure.energy.usage', 'structure'))
    plots["app"]["serverless"]["energy"] = plots["app"]["untreated"]["energy"]
    plots["app"]["energy"]["energy"] = plots["app"]["untreated"]["energy"]

    plots["node"] = dict()
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["serverless"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}
    plots["node"]["energy"] = {"cpu": [], "mem": [], "disk": [], "net": [], "energy": []}

    plots["node"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure')
                                         # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host')
                                         ]
    plots["node"]["serverless"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.usage', 'structure'),
                                          # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host'),
                                          ('limit.cpu.lower', 'structure'), ('limit.cpu.upper', 'structure')]
    plots["node"]["energy"]["cpu"] = plots["node"]["untreated"]["cpu"]

    plots["node"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure')]
    # ('proc.mem.resident', 'host')]
    plots["node"]["serverless"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.usage', 'structure'),
                                          ('limit.mem.lower', 'structure'), ('limit.mem.upper', 'structure')]
    # ('proc.mem.resident', 'host'),
    plots["node"]["energy"]["mem"] = plots["node"]["untreated"]["mem"]

    plots["node"]["untreated"]["disk"] = [('structure.disk.current', 'structure'), ('proc.disk.reads.mb', 'host'),
                                          ('proc.disk.writes.mb', 'host')]
    plots["node"]["serverless"]["disk"] = plots["node"]["untreated"]["disk"]
    plots["node"]["energy"]["disk"] = plots["node"]["untreated"]["disk"]

    plots["node"]["untreated"]["net"] = [('structure.net.current', 'structure'), ('proc.net.tcp.in.mb', 'host'),
                                         ('proc.net.tcp.out.mb', 'host')]
    plots["node"]["serverless"]["net"] = plots["node"]["untreated"]["net"]
    plots["node"]["energy"]["net"] = plots["node"]["untreated"]["net"]

    plots["node"]["energy"]["energy"] = [('structure.energy.usage', 'structure')]

    return plots

def translate_metric(metric):
    translated_metric = list()
    metric_fields = metric.split(".")

    metric_type = metric_fields[0]
    resource = metric_fields[1]
    measure_kind = metric_fields[2]

    if metric_type == "user":
        if measure_kind == "used":
            # translated_metric.append("{0} used".format(resource))
            translated_metric.append("Used".format(resource))
        elif measure_kind == "current":
            # translated_metric.append("{0} allocated".format(resource))
            translated_metric.append("Allocated".format(resource))
        elif measure_kind == "max":
            # TODO Hotfix
            if metric == "user.energy.max":
                translated_metric.append("Power budget".format(resource))
            else:
                # translated_metric.append("{0} reserved".format(resource))
                translated_metric.append("Reserved".format(resource))
        else:
            translated_metric.append(measure_kind)
    elif metric_type == "structure":
        if measure_kind == "usage":
            # translated_metric.append("{0} used".format(resource))
            translated_metric.append("Used".format(resource))
        elif measure_kind == "current":
            # translated_metric.append("{0} allocated".format(resource))
            translated_metric.append("Allocated".format(resource))
        elif measure_kind == "max":
            # TODO Hotfix
            if metric == "structure.energy.max":
                translated_metric.append("Power budget".format(resource))
            else:
                # translated_metric.append("{0} reserved".format(resource))
                translated_metric.append("Reserved".format(resource))
        else:
            translated_metric.append(measure_kind)

    elif metric_type == "limit":
        if measure_kind == "upper":
            translated_metric.append("upper")
        elif measure_kind == "lower":
            translated_metric.append("lower")
        else:
            translated_metric.append(measure_kind)
        translated_metric.append("limit")

    elif metric_type == "proc":
        translated_metric.append(" ".join(metric_fields[2:]))

    return " ".join(translated_metric).capitalize()


def get_times_from_doc(doc):
    start_time_string, end_time_string, duration, duration_minutes = "n/a", "n/a", "n/a", "n/a"

    if "start_time" in doc:
        start_time_string = time.strftime("%D %H:%M:%S", time.localtime(doc["start_time"]))

    if "end_time" in doc:
        end_time_string = time.strftime("%D %H:%M:%S", time.localtime(doc["end_time"]))

    if "end_time" in doc and "start_time" in doc:
        duration = doc["duration"]
        duration_minutes = "{:.2f}".format(duration / 60)

    return start_time_string, end_time_string, duration, duration_minutes


def split_tests_by_test_type(tests):
    benchmarks = dict()
    for test in tests:
        test_benchmark = test["test_name"].split("_")[0]
        if test_benchmark not in benchmarks:
            benchmarks[test_benchmark] = list()
        benchmarks[test_benchmark].append(test)
    return benchmarks
