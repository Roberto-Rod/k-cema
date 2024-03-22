#!/usr/bin/env python3
"""
PoE power supply equipment reporting module, prints PoE PSE information.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import json
import logging
from os import popen

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
ENVIRONMENT_VARIABLES_CMD = "systemctl show-environment"
READ_TEMPERATURE_CMD = "cat /sys/bus/i2c/devices/1-0022/measure/temperature"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PoE PSE Report")
    parser.add_argument("-j", "--json", action="store_true", help="Dump data to JSON string")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    # Get the systemctl environment variables
    system_vars_str = popen(ENVIRONMENT_VARIABLES_CMD).read()
    system_vars_dict = {}
    for line in system_vars_str.splitlines():
        system_vars_dict[line.split('=')[0]] = line.split('=')[1]

    if args.json:
        json_data_dict = {**json.loads(open(system_vars_dict["POE_PORTS"], "r").read()),
                          **json.loads(open(system_vars_dict["POE_PORTS"], "r").read()),
                          **{"temperature":int(popen(READ_TEMPERATURE_CMD).read())}}
        print(json.dumps(json_data_dict))
    else:
        poe_status = json.loads(open(system_vars_dict["POE_PORTS"], "r").read())
        if poe_status.get("port1") is not None:
            print("Port 1 Status:")
            for key in poe_status["port1"].keys():
                print("{} - {}".format(key, poe_status["port1"][key]))
        else:
            print("Port 2 Status:")
            for key in poe_status["port2"].keys():
                print("{} - {}".format(key, poe_status["port2"][key]))

        poe_status = json.loads(open(system_vars_dict["POE_PORTS"], "r").read())
        if poe_status.get("port1") is not None:
            print("Port 1 Status:")
            for key in poe_status["port1"].keys():
                print("{} - {}".format(key, poe_status["port1"][key]))
        else:
            print("Port 2 Status:")
            for key in poe_status["port2"].keys():
                print("{} - {}".format(key, poe_status["port2"][key]))

        print("temperature - {}".format(popen(READ_TEMPERATURE_CMD).read()))
