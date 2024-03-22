#!/usr/bin/env python3
"""
Module for accessing a Microchip 24AA025E48T
Relies on the I2C module that uses I2C tools to access the I2C bus.
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
import hardware_unit_config
from hardware_unit_config import AssemblyType

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
def run_test(serial_no, rev_no, batch_no):
    """
    Executes tests and determines overall test script result
    :param serial_no: assembly serial number of unit :type: string
    :param rev_no: assembly revision number of unit :type: string
    :param batch_no: assembly batch number of unit :type: string
    :return: None
    """
    log.info("KT-950-0351-00 CSM Production Test Script:")
    overall_pass = True

    if hardware_unit_config.set_config_info(serial_no, rev_no, batch_no, AssemblyType.CSM_ASSEMBLY):
        log.info("Written Unit Config Info:\tPASS")
    else:
        log.info("Written Unit Config Info:\tFAIL")

    if overall_pass:
        log.info("Overall Test Result:\t\tPASS")
    else:
        log.info("Overall Test Result:\t\tFAIL")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KT-950-0351-00 CSM Production Test")
    parser.add_argument("-s", "--serial_no", required=True, dest="serial_no", action="store",
                        help="Assembly serial number of unit, max length 15 characters")
    parser.add_argument("-r", "--rev_no", required=True, dest="rev_no", action="store",
                        help="Assembly revision number of board under test, max length 15 characters")
    parser.add_argument("-b", "--batch_no", required=True, dest="batch_no", action="store",
                        help="Assembly batch number of board under test, max length 15 characters")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run_test(args.serial_no, args.rev_no, args.batch_no)
