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
import time

from src.opentsdb import bdwatchdog
from src.common.config import OpenTSDBConfig, eprint
from src.common.config import Config

# initialize the OpenTSDB handler
bdw = bdwatchdog.BDWatchdog(OpenTSDBConfig())

# Get the config
cfg = Config()


# Generate the resource information
def generate_resources_timeseries(document, cfg):
    #  Check that the needed start and end time are present, otherwise abort
    if "end_time" not in document or "start_time" not in document:
        document["resource_aggregates"] = "n/a"
        eprint("Missing 'start_time' or 'end_time' for document".format(document["experiment_id"]))
        return document

    start, end = document["start_time"], document["end_time"]

    document["users"] = dict()
    for user in cfg.USERS_LIST:
        document["users"][user] = bdw.get_timeseries(
            user, start, end, cfg.BDWATCHDOG_USER_METRICS, downsample=cfg.DOWNSAMPLE)

    # Retrieve the timeseries from OpenTSDB and perform the per-structure aggregations
    # Slow loop due to network call
    document["resources"] = dict()
    for node_name in cfg.NODES_LIST:
        document["resources"][node_name] = bdw.get_timeseries(
            node_name, start, end, cfg.BDWATCHDOG_NODE_METRICS, downsample=cfg.DOWNSAMPLE)

    # Generate the aggregations of the retrieved resource metrics
    document["resource_aggregates"] = dict()
    for node_name in cfg.NODES_LIST:
        node_metrics = document["resources"][node_name]
        document["resource_aggregates"][node_name] = bdw.aggregate_metrics(start, end, node_metrics)

    # Generate the per-node 'usage' time series (e.g., structure.cpu.used)
    for node_name in cfg.NODES_LIST:
        node_metrics = document["resources"][node_name]
        for (usage_metric, source_metrics) in cfg.USAGE_METRICS_SOURCE:
            # Initialize
            if usage_metric not in node_metrics:
                node_metrics[usage_metric] = dict()

            # Get the first metric as the time reference, considering that all metrics should have
            # the same timestamps (they should be time-aligned)
            first_metric = node_metrics[source_metrics[0]]
            for time_point in first_metric:

                # Initialize
                node_metrics[usage_metric][time_point] = 0

                # Iterate through the metrics
                for metric in source_metrics:
                    # Timestamp from the first 'reference' metric is not present in other metric,
                    # this may be due to the head and tail data points of the time series
                    if time_point not in node_metrics[metric]:
                        continue
                    # Sum
                    node_metrics[usage_metric][time_point] += node_metrics[metric][time_point]

    # Generate the per-node 'usage' aggregations
    for node_name in cfg.NODES_LIST:
        for (usage_metric, metrics_to_aggregate) in cfg.USAGE_METRICS_SOURCE:
            aggregates = document["resource_aggregates"][node_name]

            # Initialize
            if usage_metric not in aggregates:
                aggregates[usage_metric] = {"SUM": 0, "AVG": 0}

            # Add up to create the SUM
            sum = 0
            for metric in metrics_to_aggregate:
                sum += aggregates[metric]["SUM"]
            aggregates[usage_metric]["SUM"] = sum

            # Create the AVG from the SUM
            aggregates[usage_metric]["AVG"] = sum / document["duration"]

    # Generate the 'ALL' pseudo-metrics for all the container nodes
    document["resources"]["ALL"] = dict()
    for node_name in cfg.NODES_LIST:
        for metric in document["resources"][node_name]:

                # If the first node, set the timeseries as base
            if metric not in document["resources"]["ALL"]:
                document["resources"]["ALL"][metric] = document["resources"][node_name][metric]
            else:

                # For the next nodes, add them up point by point
                doc_metric = document["resources"]["ALL"][metric]
                node_metric = document["resources"][node_name][metric]

                for time_point in node_metric:
                    try:
                        doc_metric[time_point] += node_metric[time_point]
                    except KeyError:
                        pass

    # Generate the 'ALL' pseudo-metrics aggregations
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
        document["resources"][app] = bdw.get_timeseries(
            app, start, end, cfg.BDWATCHDOG_APP_METRICS, downsample=cfg.DOWNSAMPLE)

        document["resource_aggregates"][app] = bdw.aggregate_metrics(
            start, end, document["resources"][app])

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
    else:
        eprint("Missing 'start_time' or 'end_time' for document {0}".format(document["experiment_id"]))
    return document


def create_output_directory(figure_filepath_directory):
    pathlib.Path(figure_filepath_directory).mkdir(parents=True, exist_ok=True)


def get_plots():
    plots = dict()
    plots["user"] = dict()

    plots["user"]["untreated"] = {"cpu": [], "energy": []}
    plots["user"]["serverless"] = {"cpu": [], "energy": []}
    plots["user"]["energy"] = {"cpu": [], "energy": []}

    plots["user"]["untreated"]["cpu"] = [('user.cpu.current', 'structure'), ('user.cpu.used', 'structure')]
    plots["user"]["serverless"]["cpu"] = plots["user"]["untreated"]["cpu"]
    plots["user"]["energy"]["cpu"] = plots["user"]["untreated"]["cpu"]

    plots["user"]["untreated"]["energy"] = [('user.energy.max', 'user'), ('user.energy.used', 'user')]
    plots["user"]["serverless"]["energy"] = plots["user"]["untreated"]["energy"]
    plots["user"]["energy"]["energy"] = plots["user"]["untreated"]["energy"]

    plots["app"] = dict()

    plots["app"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["app"]["serverless"] = {"cpu": [], "mem": [], "energy": []}
    plots["app"]["energy"] = {"cpu": [], "mem": [], "energy": []}

    plots["app"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure')]
    plots["app"]["serverless"]["cpu"] = plots["app"]["untreated"]["cpu"]
    plots["app"]["energy"]["cpu"] = plots["app"]["untreated"]["cpu"]

    plots["app"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure')]
    plots["app"]["serverless"]["mem"] = plots["app"]["untreated"]["mem"]
    plots["app"]["energy"]["mem"] = plots["app"]["untreated"]["mem"]

    if cfg.PRINT_ENERGY_MAX:
        plots["app"]["untreated"]["energy"] = [('structure.energy.max', 'structure')]
    plots["app"]["untreated"]["energy"].append(('structure.energy.used', 'structure'))
    plots["app"]["serverless"]["energy"] = plots["app"]["untreated"]["energy"]
    plots["app"]["energy"]["energy"] = plots["app"]["untreated"]["energy"]

    plots["node"] = dict()
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["serverless"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["energy"] = {"cpu": [], "mem": [], "energy": []}

    plots["node"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure')
                                         # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host')
                                         ]
    plots["node"]["serverless"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure'),
                                          # ('proc.cpu.user', 'host'),('proc.cpu.kernel', 'host'),
                                          ('limit.cpu.lower', 'structure'), ('limit.cpu.upper', 'structure')]
    plots["node"]["energy"]["cpu"] = plots["node"]["untreated"]["cpu"]

    plots["node"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure')]
    # ('proc.mem.resident', 'host')]
    plots["node"]["serverless"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure'),
                                          ('limit.mem.lower', 'structure'), ('limit.mem.upper', 'structure')]
    # ('proc.mem.resident', 'host'),
    plots["node"]["energy"]["mem"] = plots["node"]["untreated"]["mem"]

    plots["node"]["energy"]["energy"] = [('structure.energy.used', 'structure')]

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


def get_plots_metrics():
    plots = dict()
    plots["user"] = dict()

    plots["user"]["untreated"] = {"cpu": [], "energy": []}
    plots["user"]["energy"] = {"cpu": [], "energy": []}
    plots["user"]["serverless"] = {"cpu": [], "energy": []}

    plots["user"]["untreated"]["cpu"] = [('user.cpu.current', 'structure'), ('user.cpu.used', 'structure')]
    plots["user"]["serverless"]["cpu"] = plots["user"]["untreated"]["cpu"]
    plots["user"]["energy"]["cpu"] = plots["user"]["untreated"]["cpu"]

    plots["user"]["untreated"]["energy"] = [('user.energy.max', 'user'), ('user.energy.used', 'user')]
    plots["user"]["serverless"]["energy"] = plots["user"]["untreated"]["energy"]
    plots["user"]["energy"]["energy"] = plots["user"]["untreated"]["energy"]

    plots["app"] = dict()

    plots["app"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["app"]["serverless"] = {"cpu": [], "mem": [], "energy": []}
    plots["app"]["energy"] = {"cpu": [], "mem": [], "energy": []}

    plots["app"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure')]
    plots["app"]["serverless"]["cpu"] = plots["app"]["untreated"]["cpu"]
    plots["app"]["energy"]["cpu"] = plots["app"]["untreated"]["cpu"]

    plots["app"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure')]
    plots["app"]["serverless"]["mem"] = plots["app"]["untreated"]["mem"]
    plots["app"]["energy"]["mem"] = plots["app"]["untreated"]["mem"]

    if cfg.PRINT_ENERGY_MAX:
        plots["app"]["untreated"]["energy"] = [('structure.energy.max', 'structure')]
    plots["app"]["untreated"]["energy"].append(('structure.energy.used', 'structure'))
    plots["app"]["serverless"]["energy"] = plots["app"]["untreated"]["energy"]
    plots["app"]["energy"]["energy"] = plots["app"]["untreated"]["energy"]

    plots["node"] = dict()
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["untreated"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["serverless"] = {"cpu": [], "mem": [], "energy": []}
    plots["node"]["energy"] = {"cpu": [], "mem": [], "energy": []}

    plots["node"]["untreated"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure')]
    plots["node"]["serverless"]["cpu"] = [('structure.cpu.current', 'structure'), ('structure.cpu.used', 'structure'),
                                          ('limit.cpu.lower', 'structure'), ('limit.cpu.upper', 'structure')]
    plots["node"]["energy"]["cpu"] = plots["node"]["untreated"]["cpu"]

    plots["node"]["untreated"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure')]
    # ('proc.mem.resident', 'host')]
    plots["node"]["serverless"]["mem"] = [('structure.mem.current', 'structure'), ('structure.mem.used', 'structure'),
                                          ('limit.mem.lower', 'structure'), ('limit.mem.upper', 'structure')]
    # ('proc.mem.resident', 'host'),
    plots["node"]["energy"]["mem"] = plots["node"]["untreated"]["mem"]

    plots["node"]["energy"]["energy"] = [('structure.energy.used', 'structure')]

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
        if measure_kind == "used":
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


def nowt():
    return time.strftime("%D %H:%M:%S", time.localtime())
