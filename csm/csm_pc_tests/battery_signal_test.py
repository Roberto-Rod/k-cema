#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 battery signals, call script to execute test
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import argparse
import logging

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from csm_zero_micro_test_intf import CsmZeroiseMircoTestInterface

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------


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
def run_test(com_port):
    """
    Run the test
    :param com_port: name of serial port for CSM Zeroise Micro test interface :type string
    :return: True if
    """
    czm = CsmZeroiseMircoTestInterface(com_port)
    test_pass = True

    cmd_success, battery_fault_asserted = czm.get_battery_fault()

    if cmd_success and not battery_fault_asserted:
        log.info("PASS - Battery Fault NOT Asserted")
        test_pass &= True
    else:
        log.info("FAIL - Battery Fault Asserted OR Command Fault")
        test_pass &= False

    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM Battery Signal Production Test")
    parser.add_argument("-m", "--csm_micro_port", required=True, dest="csm_micro_port", action="store",
                        help="Name of CSM Zeroise Microcontroller COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run_test(args.csm_micro_port)
