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

from src.common.config import MongoDBConfig, eprint
from src.ExperimentReporter import ExperimentReporter
from TimestampsSnitch.src.mongodb.mongodb_agent import MongoDBTimestampAgent

mongoDBConfig = MongoDBConfig()
timestampingAgent = MongoDBTimestampAgent(mongoDBConfig.get_config_as_dict())
experimentReporter = ExperimentReporter()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Must specify an experiment name as the first argument")
    else:
        experiment_name = sys.argv[1]
        experiment = timestampingAgent.get_experiment(experiment_name, mongoDBConfig.get_username())
        if experiment:
            experimentReporter.report_experiment(experiment)
        else:
            eprint("Experiment '{0}' not found".format(experiment_name))
