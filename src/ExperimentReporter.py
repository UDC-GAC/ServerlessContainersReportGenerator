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
import sys
import time

from src.common.config import Config, MongoDBConfig, eprint

from src.latex.latex_output import print_latex_section, print_basic_doc_info
from src.TestReporter import TestReporter
from TimestampsSnitch.src.mongodb.mongodb_agent import MongoDBTimestampAgent
from src.common.utils import generate_duration, generate_resources_timeseries, nowt


class ExperimentReporter:
    def __init__(self):
        self.cfg = Config()
        mongoDBConfig = MongoDBConfig()
        self.timestampingAgent = MongoDBTimestampAgent(mongoDBConfig.get_config_as_dict())

    def report_tests(self, processed_tests):
        testRepo = TestReporter()

        test_reports = [
            ("Tests durations", testRepo.print_tests_times, True),
            ("Resource usages", testRepo.print_tests_resource_usage, True),
            ("Resource utilization", testRepo.print_tests_resource_utilization, True),
            ("Tests basic information", testRepo.print_test_report, self.cfg.PRINT_TEST_BASIC_INFORMATION),
            ("Missing information report", testRepo.report_resources_missing_data, self.cfg.PRINT_MISSING_INFO_REPORT),
        ]

        for report in test_reports:
            report_name, report_function, bool_apply = report
            if bool_apply:
                eprint("Doing {0} at {1}".format(report_name, nowt()))
                print_latex_section("{0}".format(report_name))
                report_function(processed_tests)

        if self.cfg.GENERATE_APP_PLOTS or self.cfg.GENERATE_NODES_PLOTS:
            eprint("Plotting resource plots for at {0}".format(nowt()))
            testRepo.generate_test_resource_plot(processed_tests)


    def report_experiment(self, experiment):
        testRepo = TestReporter()

        # Get the timeseries and compute durations for the experiment
        eprint("Generating experiment info at {0}".format(nowt()))
        experiment = generate_duration(experiment)
        experiment = generate_resources_timeseries(experiment, self.cfg)
        print_latex_section("Experiment basic information")
        print_basic_doc_info(experiment)

        # Get the experiment tests
        tests = self.timestampingAgent.get_experiment_tests(experiment["experiment_id"], experiment["username"])

        # Get the timeseries and compute durations for the tests
        processed_tests = list(testRepo.get_test_data(test) for test in tests)

        # Print the basic tests info
        self.report_tests(processed_tests)
