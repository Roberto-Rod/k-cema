#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 Zeroise FPGA, call script to execute test
standalone or import module and call run_test from higher level script
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
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from csm_zero_micro_test_intf import CsmZeroiseMircoTestInterface, CsmGpoSignals

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
    test_step = 0
    log.debug("Zeroise FPGA Test")

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_FPGA_PWR_EN, 1)
    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_I2C_FPGA_EN, 0) and test_pass
    time.sleep(0.5)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = not czm.set_zeroise_fpga_gpo_reg(0x00) and test_pass
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_I2C_FPGA_EN, 1) and test_pass
    time.sleep(0.5)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_zeroise_fpga_gpo_reg(0x55) and test_pass
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
    test_pass = test_pass and cmd_success and value == 0x55
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_zeroise_fpga_gpo_reg(0xCA) and test_pass
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
    test_pass = test_pass and cmd_success and value == 0xCA
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_FPGA_PWR_EN, 0) and test_pass
    time.sleep(0.5)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = not czm.set_zeroise_fpga_gpo_reg(0x00) and test_pass
    time.sleep(1.0)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_FPGA_PWR_EN, 1) and test_pass
    time.sleep(0.5)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_zeroise_fpga_gpo_reg(0xAA) and test_pass
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
    test_pass = test_pass and cmd_success and value == 0xAA
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_FPGA_RST, 1) and test_pass
    time.sleep(0.1)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = not czm.set_zeroise_fpga_gpo_reg(0x00) and test_pass
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    test_pass = czm.set_gpo_signal(CsmGpoSignals.ZER_FPGA_RST, 0) and test_pass
    time.sleep(0.1)
    test_step += 1
    log.debug("{} {}".format(test_step, test_pass))

    log.info("{} - Zeroise FPGA Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 Zeroise FPGA Production Test")
    parser.add_argument("-m", "--csm_micro_port", required=True, dest="csm_micro_port", action="store",
                        help="Name of CSM Zeroise Microcontroller COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    test_log_str = " - Overall Test Result"
    if run_test(args.csm_micro_port):
        log.info("PASS" + test_log_str)
    else:
        log.info("FAIL" + test_log_str)
