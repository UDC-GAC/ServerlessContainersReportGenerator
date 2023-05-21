#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Universidade da Coruña
# Authors:
#     - Jonatan Enes [main](jonatan.enes@udc.es)
#     - Roberto R. Expósito
#     - Juan Touriño
#
# This file is part of the ServerlessContainers framework, from
# now on referred to as ServerlessContainers.
#
# ServerlessContainers is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# ServerlessContainers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ServerlessContainers. If not, see <http://www.gnu.org/licenses/>.

from json_logic import jsonLogic

from src.MyUtils import MyUtils

CONFIG_DEFAULT_VALUES = {"WINDOW_TIMELAPSE": 20,
                         "WINDOW_DELAY": 10,
                         "REBALANCE_USERS": False,
                         "DEBUG": True,
                         "ACTIVE": False,
                         "ENERGY_DIFF_PERCENTAGE": 0.40,
                         "ENERGY_STOLEN_PERCENTAGE": 0.40
                         }


def get_user_apps(applications, user):
    user_apps = list()
    for app in applications:
        if app["name"] in user["applications"]:
            user_apps.append(app)
    return user_apps


def app_can_be_rebalanced(application, rebalancing_level, couchdb_handler):
    try:
        data = {
                # "energy":
                #     {"structure":
                #          {"energy":
                #               {"usage": application["resources"]["energy"]["usage"],
                #                "max": application["resources"]["energy"]["max"]}}},
                "cpu":
                    {"structure":
                         {"cpu":
                              {"usage": application["resources"]["cpu"]["usage"],
                               "min": application["resources"]["cpu"]["min"],
                               "current": application["resources"]["cpu"]["current"]}}}
                }
    except KeyError:
        return False

    if rebalancing_level != "container" and rebalancing_level != "application":
        MyUtils.log_error("Invalid app rebalancing policy '{0}'".format(rebalancing_level), debug=True)
        return False

    # rule_low_usage = couchdb_handler.get_rule("energy_exceeded_upper")
    # if jsonLogic(rule_low_usage["rule"], data):
    #     # Application is overusing energy
    #     if rebalancing_level == "container":
    #         # Let the Guardian or the dynamic energy balancing deal with it
    #         return False
    #     elif rebalancing_level == "application":
    #         # It may be a receiver for dynamic energy rebalancing
    #         return True
    #
    # rule_high_usage = couchdb_handler.get_rule("energy_dropped_lower")
    # if jsonLogic(rule_high_usage["rule"], data):
    #     # Application is underusing energy
    #     if rebalancing_level == "container":
    #         # Let the Guardian or the dynamic energy balancing deal with it
    #         return False
    #         # It may be a donor for dynamic energy rebalancing
    #     elif rebalancing_level == "application":
    #         return True

    # The application is in the middle area of energy utilization
    if rebalancing_level == "container":
        # Perform an internal balancing through container cpu limit rebalancing
        return True
    elif rebalancing_level == "application":
        # It may need internal container rebalancing
        return False
