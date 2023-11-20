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

from src.opentsdb import bdwatchdog
from src.common.config import OpenTSDBConfig, eprint
from src.latex.latex_output import latex_print, print_latex_stress, flush_table, print_basic_doc_info
from src.lineplotting.lineplots import plot_test_doc
from src.common.utils import generate_duration, translate_metric, format_metric, generate_resources_timeseries, \
    get_plots_metrics


class TestReporter:
    def __init__(self, cfg):
        # Get the config
        self.cfg = cfg
        self.bdwatchdog_handler = bdwatchdog.BDWatchdog(OpenTSDBConfig())

    def get_test_data(self, test):
        test = generate_duration(test)
        test = generate_resources_timeseries(test, self.cfg)
        return test

    def generate_test_resource_plot(self, tests):
        report_type = self.cfg.EXPERIMENT_TYPE

        for test in tests:
            if "end_time" not in test or "start_time" not in test:
                return

            plots = get_plots_metrics()

            if self.cfg.GENERATE_NODES_PLOTS:
                test_plots = plots["node"][report_type]
                for node_name in self.cfg.NODES_LIST:
                    plot_test_doc(test, node_name, test_plots, self.cfg)

            if self.cfg.GENERATE_APP_PLOTS:
                app_plots = plots["app"][report_type]
                for app_name in self.cfg.APPS_LIST:
                    plot_test_doc(test, app_name, app_plots, self.cfg)

            if self.cfg.GENERATE_USER_PLOTS:
                user_plots = plots["user"][report_type]
                for user_name in self.cfg.USERS_LIST:
                    plot_test_doc(test, user_name, user_plots, self.cfg)

    # PRINT TEST RESOURCE USAGES
    def print_test_resources(self, test, structures_list):
        if not test["aggregates"] or test["aggregates"] == "n/a":
            latex_print("RESOURCE INFO NOT AVAILABLE")
            return

        max_columns = self.cfg.MAX_COLUMNS["print_test_resources"]
        headers, rows, remaining_data, num_columns = ["structure", "aggregation"], dict(), False, 0
        for metric_name in self.cfg.PRINTED_METRICS:
            headers.append(translate_metric(metric_name, test["test_name"]))
            for structure_name in structures_list:

                # Initialize
                if structure_name not in rows:
                    rows[structure_name] = dict()

                for agg in ["SUM", "AVG", "MAX", "MIN", "DIFF_MAX_MIN", "FIRST", "LAST"]:
                    if agg not in rows[structure_name]:
                        rows[structure_name][agg] = [structure_name, agg]

                    try:
                        rows[structure_name][agg].append(format_metric(test["aggregates"][structure_name][metric_name][agg], metric_name, agg))
                    except KeyError:
                        rows[structure_name][agg].append("n/a")

            num_columns += 1
            remaining_data = True
            if num_columns >= max_columns:
                self.flush_rows_with_aggregations(rows, headers)
                headers, rows, remaining_data, num_columns = ["structure", "aggregation"], dict(), False, 0

        if remaining_data:
            self.flush_rows_with_aggregations(rows, headers)

    def flush_rows_with_aggregations(self, rows, headers, table_caption=None):
        final_rows = list()
        for row in rows:
            final_rows += list(rows[row].values())
        flush_table(final_rows, headers, table_caption)

    # PRINT TEST RESOURCE UTILIZATION
    def print_tests_resource_utilization(self, tests):
        max_columns = self.cfg.MAX_COLUMNS["print_tests_resource_utilization_report"]
        table_caption = "TESTs resource utilization"

        headers, rows, num_columns, remaining_data = ["resource"], dict(), 0, False

        for test in tests:
            headers.append(test["test_name"])

            for resource_tuple in self.cfg.RESOURCE_UTILIZATION_TUPLES:
                resource, current, usage = resource_tuple
                if resource not in rows:
                    rows[resource] = [resource]
                if test["aggregates"] == "n/a":
                    rows[resource].append("n/a")
                else:
                    try:
                        available = test["aggregates"]["ALL"][current]["SUM"]
                        used = test["aggregates"]["ALL"][usage]["SUM"]
                        if available <= 0:
                            raise KeyError
                        else:
                            rows[resource].append(str(int(100 * used / available) - 1) + '%')
                    except KeyError:
                        eprint("Resource utilization for '{0}' skipped as no value for applied resource limits are "
                               "present and thus not utilization ratio can be computed".format(resource))
                        continue

            num_columns += 1
            remaining_data = True
            if num_columns >= max_columns:
                flush_table(rows.values(), headers, table_caption)
                table_caption = None
                headers, rows, num_columns, remaining_data = ["resource"], dict(), 0, False

        if remaining_data:
            flush_table(rows.values(), headers)

    # PRINT TEST RESOURCE MISSING DATA
    def report_resources_missing_data(self, tests):
        for test in tests:
            if "end_time" not in test or "start_time" not in test:
                return

            structures_list = self.cfg.NODES_LIST
            misses = dict()
            for metric in self.cfg.METRICS_TO_CHECK_FOR_MISSING_DATA:
                metric_name = metric[0]
                for structure in structures_list:
                    if metric_name in test["timeseries"][structure]:
                        timeseries = test["timeseries"][structure][metric_name]
                    else:
                        timeseries = None
                    if bool(timeseries):
                        structure_misses_list = self.bdwatchdog_handler.perform_check_for_missing_metric_info(
                            timeseries, self.cfg.MAX_DIFF_TIME)
                        if not structure_misses_list:
                            continue
                    else:
                        # No timeseries were retrieved, so it is a 100% lost
                        structure_misses_list = [{"time": 0, "diff_time": test["duration"]}]

                    if metric_name not in misses:
                        misses[metric_name] = dict()
                    misses[metric_name][structure] = structure_misses_list

            if misses:
                latex_print("\\textbf{TEST:} " + test["test_name"])
                latex_print("&nbsp;")

                aggregated_misses = dict()
                for metric in misses:
                    aggregated_misses[metric] = dict()
                    for structure in misses[metric]:
                        aggregated_misses[metric][structure] = sum(
                            miss['diff_time'] for miss in misses[metric][structure])

                for metric in aggregated_misses:
                    latex_print("For metric: {0}".format(metric))
                    total_missed_time = 0
                    for structure in aggregated_misses[metric]:
                        structure_missed_time = aggregated_misses[metric][structure]

                        latex_print(
                            "Silence of {0} seconds at node {1} accounting for a total of {2:.2f}\%".format(
                                structure_missed_time, structure,
                                float(100 * structure_missed_time / test["duration"])))
                        total_missed_time += structure_missed_time

                    print_latex_stress(
                        "Silence of {0} seconds at for ALL nodes accounting for a total of {1:.2f}\%".format(
                            total_missed_time,
                            float(100 * total_missed_time / (len(structures_list) * test["duration"]))))
                    latex_print("&nbsp;")
                latex_print("&nbsp;")

    def print_tests_resource_usage(self, tests):
        table_caption = "TESTs total resource usages"
        max_columns = self.cfg.MAX_COLUMNS["print_tests_by_resource_report"]
        headers, rows, num_columns, remaining_data = ["resource", "aggregation"], dict(), 0, False
        for test in tests:
            headers.append(test["test_name"])
            metrics = list()
            for t in self.cfg.RESOURCE_UTILIZATION_TUPLES:
                metrics.append(t[1])
                metrics.append(t[2])
            for resource in metrics:
                if resource not in rows:
                    rows[resource] = dict()

                for agg in ["SUM", "AVG"]:
                    if agg not in rows[resource]:
                        rows[resource][agg] = [translate_metric(resource, test["test_name"]), agg]

                    if test["aggregates"] == "n/a":
                        rows[resource][agg].append("n/a")
                    else:
                        try:
                            rows[resource][agg].append(
                                format_metric(test["aggregates"]["ALL"][resource][agg], resource, agg))
                        except KeyError:
                            rows[resource][agg].append("n/a")

            num_columns += 1
            remaining_data = True
            if num_columns >= max_columns:
                self.flush_rows_with_aggregations(rows, headers, table_caption)
                table_caption = None
                headers, rows, num_columns, remaining_data = ["resource", "aggregation"], dict(), 0, False

        if remaining_data:
            self.flush_rows_with_aggregations(rows, headers, table_caption)

    def print_test_report(self, tests):

        for test in tests:
            print_basic_doc_info(test)

            rows = list()
            if self.cfg.PRINT_NODE_INFO:
                rows += self.cfg.NODES_LIST

            rows += ["ALL"]

            rows += self.cfg.APPS_LIST

            rows += self.cfg.USERS_LIST

            self.print_test_resources(test, rows)
            print("")

    def print_tests_times(self, tests):
        max_columns = self.cfg.MAX_COLUMNS["print_summarized_tests_info"]
        table_caption = "TESTs durations and time benchmarking "

        headers, durations_seconds, durations_minutes, num_columns, remaining_data = \
            ["time"], ["seconds"], ["minutes"], 0, False

        for test in tests:
            headers.append(test["test_name"])
            seconds, minutes, overhead = "n/a", "n/a", "n/a"
            if test["duration"] != "n/a":
                seconds = test["duration"]
                minutes = "{:.2f}".format((test["duration"]) / 60)

            durations_seconds.append(seconds)
            durations_minutes.append(minutes)

            num_columns += 1
            remaining_data = True
            if num_columns >= max_columns:
                flush_table([durations_seconds, durations_minutes], headers, table_caption)
                table_caption = None
                headers, durations_seconds, durations_minutes, num_columns, remaining_data = \
                    ["time"], ["seconds"], ["minutes"], 0, False

        if remaining_data:
            flush_table([durations_seconds, durations_minutes], headers, table_caption)
