#!/usr/bin/env python3
"""
This file contains utility functions to connect to the K-CEMA Raspberry Pi 4
over SSH and start/stop an iperf3 server from running.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
None
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging
from ssh import SSH

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
RPI4_HOSTNAME = "ubuntu.local"
RPI4_USERNAME = "ubuntu"
RPI4_PASSWORD = "kcematest"

IPERF3_START_SERVER_CMD = "iperf3 -s -D -i 1"
IPERF3_DETECT_SERVER = "iperf3 -s"

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
def start_iperf3_server(hostname, username, password_dict, ps_cmd="ps aux"):
    with SSH(hostname, username, password_dict) as client:
        # Ensure any running iperf3 instances are killed
        client.send_command("killall -9 iperf3")

        # Start iperf3 running in server mode as a daemon mode
        client.send_command("iperf3 -s -D -i 1")

        # Check the iperf3 server is running
        return client.send_command("{} | grep iperf3".format(ps_cmd)).stdout.find(IPERF3_START_SERVER_CMD) != -1


def stop_iperf3_server(hostname, username, password_dict, ps_cmd="ps aux"):
    with SSH(hostname, username, password_dict) as client:
        # Ensure any running iperf3 instances are killed
        client.send_command("killall -9 iperf3")

        # Check that iperf3 is not running
        return client.send_command("{} | grep iperf3".format(ps_cmd)).stdout.find(IPERF3_DETECT_SERVER) == -1


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
