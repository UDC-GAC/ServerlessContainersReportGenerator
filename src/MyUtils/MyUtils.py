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


from __future__ import print_function

import random
import time
import logging
import sys
import requests
import traceback
from termcolor import colored

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# DON'T NEED TO TEST
def resilient_beat(db_handler, service_name, max_tries=10):
    try:
        service = db_handler.get_service(service_name)
        service["heartbeat_human"] = time.strftime("%D %H:%M:%S", time.localtime())
        service["heartbeat"] = time.time()
        db_handler.update_service(service)
    except (requests.exceptions.HTTPError, ValueError) as e:
        if max_tries > 0:
            time.sleep((1000 + random.randint(1, 200)) / 1000)
            resilient_beat(db_handler, service_name, max_tries - 1)
        else:
            raise e


# DON'T NEED TO TEST
def beat(db_handler, service_name):
    resilient_beat(db_handler, service_name, max_tries=5)


class MyConfig:
    DEFAULTS_CONFIG = None
    config = None

    def __init__(self, DEFAULTS_CONFIG):
        self.DEFAULTS_CONFIG = DEFAULTS_CONFIG

    def get_config(self):
        return self.config

    def set_config(self, config):
        self.config = config

    def get_value(self, key):
        try:
            return self.config[key]
        except KeyError:
            return self.DEFAULTS_CONFIG[key]

    def set_value(self, key, value):
        self.config[key] = value

# DON'T NEED TO TEST
def get_config_value(config, default_config, key):
    try:
        return config[key]
    except KeyError:
        return default_config[key]


# DON'T NEED TO TEST
def log_info(message, debug):
    logging.info(message)
    if debug:
        print("[{0}] INFO: {1}".format(get_time_now_string(), message))


# DON'T NEED TO TEST
def log_warning(message, debug):
    logging.warning(message)
    if debug:
        print(colored("[{0}] WARN: {1}".format(get_time_now_string(), message), "yellow"))


# DON'T NEED TO TEST
def log_error(message, debug):
    logging.error(message)
    if debug:
        print(colored("[{0}] ERROR: {1}".format(get_time_now_string(), message), "red"))


# DON'T NEED TO TEST
def get_time_now_string():
    return str(time.strftime("%H:%M:%S", time.localtime()))


def get_host_containers(container_host_ip, container_host_port, rescaler_http_session, debug):
    try:
        full_address = "http://{0}:{1}/container/".format(container_host_ip, container_host_port)
        r = rescaler_http_session.get(full_address, headers={'Accept': 'application/json'})
        if r.status_code == 200:
            return dict(r.json())
        else:
            r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_error(
            "Error trying to get container info {0} {1}".format(str(e), traceback.format_exc()),
            debug)
        return None


# CAN'T TEST
def get_container_resources(container, rescaler_http_session, debug):
    container_name = container["name"]
    try:
        container_host_ip = container["host_rescaler_ip"]
        container_host_port = container["host_rescaler_port"]

        full_address = "http://{0}:{1}/container/{2}".format(container_host_ip, container_host_port, container_name)
        r = rescaler_http_session.get(full_address, headers={'Accept': 'application/json'})
        if r.status_code == 200:
            return dict(r.json())
        else:
            r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_error(
            "Error trying to get container {0} info {1} {2}".format(container_name, str(e), traceback.format_exc()),
            debug)
        return None


# CAN'T TEST
def register_service(db_handler, service):
    try:
        existing_service = db_handler.get_service(service["name"])
        # Service is registered, remove it
        db_handler.delete_service(existing_service)
    except ValueError:
        # Service is not registered, everything is fine
        pass
    db_handler.add_service(service)


# CAN'T TEST
def get_service(db_handler, service_name, max_allowed_failures=10, time_backoff_seconds=2):
    fails = 0
    success = False
    service = None
    # Get service info
    while not success:
        try:
            service = db_handler.get_service(service_name)
            success = True
        except (requests.exceptions.HTTPError, ValueError):
            # An error might have been thrown because database was recently updated or created
            # try again up to a maximum number of retries
            fails += 1
            if fails >= max_allowed_failures:
                message = "Fatal error, couldn't retrieve service."
                log_error(message, True)
                raise Exception(message)
            else:
                time.sleep(time_backoff_seconds)

    if not service or "config" not in service:
        message = "Fatal error, couldn't retrieve service configuration."
        log_error(message, True)
        raise Exception(message)

    return service


# TESTED
# Tranlsate something like '2-5,7' to [2,3,4,7]
def get_cpu_list(cpu_num_string):
    cpu_list = list()
    parts = cpu_num_string.split(",")
    for part in parts:
        ranges = part.split("-")
        if len(ranges) == 1:
            # Single core, no range (e.g., '5')
            cpu_list.append(ranges[0])
        else:
            # Range (e.g., '4-7' -> 4,5,6)
            cpu_list += range(int(ranges[0]), int(ranges[-1]) + 1)
    return [str(i) for i in cpu_list]


def copy_structure_base(structure):
    keys_to_copy = ["_id", "_rev", "type", "subtype", "name"]
    # TODO FIX, some structures types have specific fields, fix accordingly
    if structure["subtype"] == "container":
        keys_to_copy.append("host")
    new_struct = dict()
    for key in keys_to_copy:
        new_struct[key] = structure[key]
    return new_struct


def valid_resource(resource):
    if resource not in ["cpu", "mem", "disk", "net", "energy"]:
        return False
    else:
        return True

# DON'T NEED TO TEST
def get_resource(structure, resource):
    return structure["resources"][resource]


# CAN'T TEST
def update_structure(structure, db_handler, debug, max_tries=10):
    try:
        db_handler.update_structure(structure, max_tries=max_tries)
        log_info("{0} {1} ->  updated".format(structure["subtype"].capitalize(), structure["name"]), debug)
    except requests.exceptions.HTTPError:
        log_error("Error updating container " + structure["name"] + " " + traceback.format_exc(), debug)


def update_user(user, db_handler, debug, max_tries=10):
    try:
        db_handler.update_user(user, max_tries=max_tries)
        log_info("User {0} ->  updated".format(user["name"]), debug)
    except requests.exceptions.HTTPError:
        log_error("Error updating user " + user["name"] + " " + traceback.format_exc(), debug)


# CAN'T TEST
def get_structures(db_handler, debug, subtype="application"):
    try:
        return db_handler.get_structures(subtype=subtype)
    except (requests.exceptions.HTTPError, ValueError):
        log_warning("Couldn't retrieve " + subtype + " info.", debug=debug)
        return None

def wait_operation_thread(thread, debug):
    """This is used in services like the snapshoters or the Guardian that use threads to carry out operations.
    A main thread is launched that spawns the needed threads to carry out the operations. The service waits for this
    thread to finish.
    Args:
        thread (Python Thread): The thread that has spawned the basic threads that carry out operations as needed

    """
    if thread and thread.is_alive():
        log_warning("Previous thread didn't finish and next poll should start now", debug)
        log_warning("Going to wait until thread finishes before proceeding", debug)
        delay_start = time.time()
        thread.join()
        delay_end = time.time()
        log_warning("Resulting delay of: {0} seconds".format(str(delay_end - delay_start)), debug)


# TESTED
def generate_request_name(amount, resource):
    if amount == 0:
        raise ValueError("Amount is zero")
    elif amount is None:
        raise ValueError("Amount is missing")
    if int(amount) < 0:
        return resource.title() + "RescaleDown"
    elif int(amount) > 0:
        return resource.title() + "RescaleUp"
    else:
        raise ValueError("Invalid amount")


def structure_is_application(structure):
    return structure["subtype"] == "application"


def structure_is_container(structure):
    return structure["subtype"] == "container"

# TESTED
def generate_event_name(event, resource):
    if "scale" not in event:
        raise ValueError("Missing 'scale' key")

    if "up" not in event["scale"] and "down" not in event["scale"]:
        raise ValueError("Must have an 'up' or 'down count")

    elif "up" in event["scale"] and event["scale"]["up"] > 0 \
            and "down" in event["scale"] and event["scale"]["down"] > 0:
        # SPECIAL CASE OF HEAVY HYSTERESIS
        # raise ValueError("HYSTERESIS detected -> Can't have both up and down counts")
        if event["scale"]["up"] > event["scale"]["down"]:
            final_string = resource.title() + "Bottleneck"
        else:
            final_string = resource.title() + "Underuse"

    elif "down" in event["scale"] and event["scale"]["down"] > 0:
        final_string = resource.title() + "Underuse"

    elif "up" in event["scale"] and event["scale"]["up"] > 0:
        final_string = resource.title() + "Bottleneck"
    else:
        raise ValueError("Error generating event name")

    return final_string

def generate_structure_usage_metric(resource):
    return "structure.{0}.usage".format(resource)
