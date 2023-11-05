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

import configparser
import os
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class ConfigParams:
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = "../../conf/config.ini"
    config_keys = []
    default_config_values = {}


class DatabaseConfig:
    config = None

    def __init__(self, params):
        config_dict = {}
        config = configparser.ConfigParser()
        config_file_path = os.path.join(params.base_path, params.config_path)
        try:
            config.read(config_file_path)
        except (IOError, FileNotFoundError):
            print("Config file does not exist on {0} or is not accessible".format(config_file_path))

        for key in params.config_keys:
            try:
                config_dict[key] = config['DEFAULT'][key]
            except KeyError:
                config_dict[key] = params.default_config_values[key]
        self.config = config_dict

    def get_config_as_dict(self):
        return self.config


class OpenTSDBConfig(DatabaseConfig):
    def __init__(self):
        params = ConfigParams()
        params.config_path = "../../conf/data-retrieval/timeseries_config.ini"
        params.config_keys = [
            "OPENTSDB_IP",
            "OPENTSDB_PORT",
            "OPENTSDB_SUBDIR"
        ]
        params.default_config_values = {
            "OPENTSDB_IP": "opentsdb",
            "OPENTSDB_PORT": 4242,
            "OPENTSDB_SUBDIR": ""
        }
        DatabaseConfig.__init__(self, params)

    def getIp(self):
        return self.config["OPENTSDB_IP"]

    def getPort(self):
        return self.config["OPENTSDB_PORT"]

    def getSubdir(self):
        return self.config["OPENTSDB_SUBDIR"]


class MongoDBConfig(DatabaseConfig):

    def __init__(self):
        params = ConfigParams()
        params.config_path = "../../conf/data-retrieval/timestamping_config.ini"
        params.config_keys = [
            "TESTS_POST_ENDPOINT",
            "EXPERIMENTS_POST_ENDPOINT",
            "MAX_CONNECTION_TRIES",
            "MONGODB_IP",
            "MONGODB_PORT",
            "MONGODB_USER"
        ]
        params.default_config_values = {
            "TESTS_POST_ENDPOINT": "tests",
            "EXPERIMENTS_POST_ENDPOINT": "experiments",
            "MAX_CONNECTION_TRIES": 3,
            "MONGODB_IP": "times",
            "MONGODB_PORT": 8000,
            "MONGODB_USER": "root"
        }
        DatabaseConfig.__init__(self, params)

    def get_username(self):
        return self.config["MONGODB_USER"]


class Config:
    __base_path = os.path.dirname(os.path.abspath(__file__))
    __config_path = "../../conf/report_generator_config.ini"
    __config_keys = [
        "MAX_DIFF_TIME",
        "PRINT_MISSING_INFO_REPORT",
        "PRINT_TEST_BASIC_INFORMATION",
        "PRINT_NODE_INFO",
        "GENERATE_APP_PLOTS",
        "GENERATE_NODES_PLOTS",
        "GENERATE_USER_PLOTS",
        "PLOTTING_FORMATS",
        "NODES_LIST",
        "APPS_LIST",
        "USERS_LIST",
        "STATIC_LIMITS",
        "Y_AMPLIFICATION_FACTOR",
        "XLIM",
        "YLIM",
        "XTICKS_STEP",
        "REPORTED_RESOURCES",
        "EXPERIMENT_TYPE",
        "PRINT_ENERGY_MAX",
        "DOWNSAMPLE"
    ]
    __default_environment_values = {
        "MAX_DIFF_TIME": 10,
        "PRINT_MISSING_INFO_REPORT": "true",
        "PRINT_TEST_BASIC_INFORMATION": "true",
        "PRINT_NODE_INFO": "true",
        "GENERATE_APP_PLOTS": "true",
        "GENERATE_NODES_PLOTS": "true",
        "GENERATE_USER_PLOTS": "true",
        "PLOTTING_FORMATS": "svg",
        "STATIC_LIMITS": "true",
        "NODES_LIST": "cont0",
        "USERS_LIST": "user0",
        "APPS_LIST": "app0",
        "Y_AMPLIFICATION_FACTOR": 1.2,
        "XLIM": "default:1000",
        "YLIM": "cpu:default:1000,mem:default:10000",
        "XTICKS_STEP": 50,
        "REPORTED_RESOURCES": "cpu",
        "EXPERIMENT_TYPE": "serverless",
        "PRINT_ENERGY_MAX": "true",
        "DOWNSAMPLE": 5
    }

    def get_numeric_value(self, d, key, numeric_type):
        try:
            return numeric_type(d[key])
        except KeyError:
            default = self.__default_environment_values[key]
            eprint("Invalid configuration for {0}, using default value '{1}'".format(key, default))
            return default

    def get_float_value(self, d, key):
        return self.get_numeric_value(d, key, float)

    def get_int_value(self, d, key):
        return self.get_numeric_value(d, key, int)

    def read_config(self):
        config_dict = {}
        config = configparser.ConfigParser()
        config_file_path = os.path.join(self.__base_path, self.__config_path)

        try:
            config.read(config_file_path)
        except (IOError, FileNotFoundError):
            print('Config file does not exist or is not accessible')

        for key in self.__config_keys:
            try:
                config_dict[key] = config['DEFAULT'][key]
            except KeyError:
                pass  # Key is not configured, leave it
        return config_dict

    def create_environment(self):
        custom_environment = os.environ.copy()
        config_dict = self.read_config()
        for key in self.__config_keys:
            if key in config_dict.keys():
                custom_environment[key] = config_dict[key]
            else:
                custom_environment[key] = self.__default_environment_values[key]
        return custom_environment

    def __init__(self):

        def strip_quotes(string):
            return string.rstrip('"').lstrip('"')
        def parse_val_list(string):
            return strip_quotes(string).split(",")

        ENV = self.create_environment()

        self.EXPERIMENT_TYPE = strip_quotes(ENV["EXPERIMENT_TYPE"])

        self.REPORTED_RESOURCES = parse_val_list(ENV["REPORTED_RESOURCES"])
        self.MAX_DIFF_TIME = self.get_int_value(ENV, "MAX_DIFF_TIME")

        self.BDWATCHDOG_USER_METRICS = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_USER_METRICS.append(('user.cpu.current', 'user'))
            self.BDWATCHDOG_USER_METRICS.append(('user.cpu.used', 'user'))
        if "accounting" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_USER_METRICS.append(('user.accounting.coins', 'user'))
            self.BDWATCHDOG_USER_METRICS.append(('user.accounting.max_debt', 'user'))
            self.BDWATCHDOG_USER_METRICS.append(('user.accounting.min_balance', 'user'))
        if "energy" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_USER_METRICS.append(('user.energy.max', 'user'))
            self.BDWATCHDOG_USER_METRICS.append(('user.energy.used', 'user'))

        self.BDWATCHDOG_APP_METRICS = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_APP_METRICS.append(('structure.cpu.current', 'structure'))
            self.BDWATCHDOG_APP_METRICS.append(('structure.cpu.used', 'structure'))
        if "mem" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_APP_METRICS.append(('structure.mem.current', 'structure'))
            self.BDWATCHDOG_APP_METRICS.append(('structure.mem.used', 'structure'))
        if "energy" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_APP_METRICS.append(('structure.energy.max', 'structure'))
            self.BDWATCHDOG_APP_METRICS.append(('structure.energy.used', 'structure'))

        self.BDWATCHDOG_NODE_METRICS = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_NODE_METRICS.append(('structure.cpu.current', 'structure'))
            self.BDWATCHDOG_NODE_METRICS.append(('proc.cpu.user', 'host'))
            self.BDWATCHDOG_NODE_METRICS.append(('proc.cpu.kernel', 'host'))
            self.BDWATCHDOG_NODE_METRICS.append(('limit.cpu.upper', 'structure'))
            self.BDWATCHDOG_NODE_METRICS.append(('limit.cpu.lower', 'structure'))
        if "mem" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_NODE_METRICS.append(('structure.mem.current', 'structure'))
            self.BDWATCHDOG_NODE_METRICS.append(('proc.mem.resident', 'host'))
            self.BDWATCHDOG_NODE_METRICS.append(('proc.mem.virtual', 'host'))
            self.BDWATCHDOG_NODE_METRICS.append(('limit.mem.upper', 'structure'))
            self.BDWATCHDOG_NODE_METRICS.append(('limit.mem.lower', 'structure'))
        if "energy" in self.REPORTED_RESOURCES:
            self.BDWATCHDOG_NODE_METRICS.append(('sys.cpu.energy', 'host'))

        self.PRINT_ENERGY_MAX = ENV["PRINT_ENERGY_MAX"] == "true"
        self.PRINTED_METRICS = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.PRINTED_METRICS.append('structure.cpu.current')
            self.PRINTED_METRICS.append('structure.cpu.used')
            self.PRINTED_METRICS.append('proc.cpu.user')
            self.PRINTED_METRICS.append('proc.cpu.kernel')

        if "mem" in self.REPORTED_RESOURCES:
            self.PRINTED_METRICS.append('structure.mem.current')
            self.PRINTED_METRICS.append('structure.mem.used')
            self.PRINTED_METRICS.append('proc.mem.resident')

        if "accounting" in self.REPORTED_RESOURCES:
            self.PRINTED_METRICS.append('user.accounting.coins')
            self.PRINTED_METRICS.append('user.accounting.min_balance')
            self.PRINTED_METRICS.append('user.accounting.max_debt')

        if "energy" in self.REPORTED_RESOURCES:
            self.PRINTED_METRICS.append('structure.energy.max')
            self.PRINTED_METRICS.append('structure.energy.used')


        self.MAX_COLUMNS = {"print_test_resources": 5,
                            "print_summarized_tests_info": 8,
                            "print_tests_resource_utilization_report": 8,
                            "print_tests_resource_overhead_report": 8,
                            "print_tests_by_resource_report": 5}

        self.STATIC_LIMITS = ENV["STATIC_LIMITS"] == "true"

        self.Y_AMPLIFICATION_FACTOR = self.get_float_value(ENV, "Y_AMPLIFICATION_FACTOR")

        self.XLIM = {}
        for pair in parse_val_list(ENV["XLIM"]):
            structure_name, limit = pair.split(":")
            try:
                self.XLIM[structure_name] = int(limit)
            except ValueError:
                pass

        self.YLIM = dict()
        for pair in parse_val_list(ENV["YLIM"]):
            resource, structure_name, limit = pair.split(":")
            if resource in ["cpu", "energy"]:
                try:
                    if structure_name not in self.YLIM:
                        self.YLIM[structure_name] = dict()
                    self.YLIM[structure_name][resource] = int(limit)
                except ValueError:
                    pass

        self.XTICKS_STEP = self.get_int_value(ENV, "XTICKS_STEP")

        self.PRINT_NODE_INFO = ENV["PRINT_NODE_INFO"] == "true"

        self.GENERATE_APP_PLOTS = ENV["GENERATE_APP_PLOTS"] == "true"
        self.GENERATE_NODES_PLOTS = ENV["GENERATE_NODES_PLOTS"] == "true"
        self.GENERATE_USER_PLOTS = ENV["GENERATE_USER_PLOTS"] == "true"

        self.NODES_LIST = parse_val_list(ENV["NODES_LIST"])
        self.APPS_LIST = parse_val_list(ENV["APPS_LIST"])
        self.USERS_LIST = parse_val_list(ENV["USERS_LIST"])

        self.PLOTTING_FORMATS = list()
        plotting_formats = parse_val_list(ENV["PLOTTING_FORMATS"])
        if "png" in plotting_formats:
            self.PLOTTING_FORMATS.append("png")
        if "svg" in plotting_formats:
            self.PLOTTING_FORMATS.append("svg")

        self.DOWNSAMPLE = self.get_int_value(ENV, "DOWNSAMPLE")

        self.RESOURCE_UTILIZATION_TUPLES = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.RESOURCE_UTILIZATION_TUPLES.append(("cpu", "structure.cpu.current", "structure.cpu.used"))

        if "mem" in self.REPORTED_RESOURCES:
            self.RESOURCE_UTILIZATION_TUPLES.append(("mem", "structure.mem.current", "structure.mem.used"))

        if "energy" in self.REPORTED_RESOURCES:
            self.RESOURCE_UTILIZATION_TUPLES.append(("energy", "structure.energy.max", "structure.energy.used"))

        self.USAGE_METRICS_SOURCE = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.USAGE_METRICS_SOURCE.append(("structure.cpu.used", ['proc.cpu.user', 'proc.cpu.kernel']))
        if "mem" in self.REPORTED_RESOURCES:
            self.USAGE_METRICS_SOURCE.append(("structure.mem.used", ['proc.mem.resident']))
        if "energy" in self.REPORTED_RESOURCES:
            self.USAGE_METRICS_SOURCE.append(("structure.energy.used", ['sys.cpu.energy']))

        self.METRICS_TO_CHECK_FOR_MISSING_DATA = list()
        if "cpu" in self.REPORTED_RESOURCES:
            self.METRICS_TO_CHECK_FOR_MISSING_DATA += [('structure.cpu.current', 'structure'),
                                                       ('proc.cpu.user', 'host'),
                                                       ('proc.cpu.kernel', 'host')]
        if "mem" in self.REPORTED_RESOURCES:
            self.METRICS_TO_CHECK_FOR_MISSING_DATA += [('structure.mem.current', 'structure'),
                                                       ('proc.mem.resident', 'host')]

        if "energy" in self.REPORTED_RESOURCES:
            self.METRICS_TO_CHECK_FOR_MISSING_DATA += [('structure.energy.used', 'structure')]

        self.PRINT_MISSING_INFO_REPORT = ENV["PRINT_MISSING_INFO_REPORT"] == "true"
        self.PRINT_TEST_BASIC_INFORMATION = ENV["PRINT_TEST_BASIC_INFORMATION"] == "true"


