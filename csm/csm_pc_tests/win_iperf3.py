#!/usr/bin/env python3
"""
This file contains utility functions to run an iperf3 client test on a
Windows machine.

Assumes that the iperf3 executable is in the following folder relative to this
script file: /iperf-3.1.3-win64
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
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
import json
import logging
import os

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
IPERF3_EXECUTABLE = "./iperf-3.1.3-win64/iperf3.exe"
CYGWIN_DLL = "./iperf-3.1.3-win64/cygwin1.dll"
IPERF3_RUN_CLIENT_TEST_CMD = "\"{}\" -c {} -t {} -J"    # .format(hostname, test_duration_sec)

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
def iperf3_client_test(server_hostname, duration):
    """
    Connects to the specified host and runs a iperf3 client test for the
    required number of seconds.  The minimum duration is constrained to 1 as
    the client test runs infinitely if the duration is set to 0.
    :param server_hostname: iperf3 server hostname :type string
    :param duration: client test duration in seconds, minimum is 1 :type int
    :return: [0] sender bits per second; [1] receiver bits per second; -1.0
    if an error occurs :type tuple pair of floats
    """
    # Parameter checking
    duration = int(duration)
    duration = 1 if duration < 1 else duration
    error_value = -1.0

    if not os.path.isfile(IPERF3_EXECUTABLE) or not os.path.isfile(CYGWIN_DLL):
        raise RuntimeError("Missing iperf3 executables")

    # Build the command for executing the iperf3 client test
    run_cmd = IPERF3_RUN_CLIENT_TEST_CMD.format(IPERF3_EXECUTABLE, server_hostname, duration)
    log.debug("Executing command: {}".format(run_cmd))
    output = json.loads(os.popen(run_cmd).read())
    log.debug(output)

    tx_bps = output.get('end', {}).get('streams', [{}])[0].get('sender', {}).get('bits_per_second', error_value)
    rx_bps = output.get('end', {}).get('streams', [{}])[0].get('receiver', {}).get('bits_per_second', error_value)

    return tx_bps, rx_bps


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
