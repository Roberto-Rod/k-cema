#!/usr/bin/env python3
"""
Install a firmware file on the CTS Digital Board using the CTS Test Jig and s
Segger J-Link programmer
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-c, --cts_com_port, CTS COM port
-t, --test_jig_com_port, Test Jig COM Port
-f, --fw_file", Firmware binary file
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
import cts_program_devices as cpd
from cts_serial_msg_intf import *
from cts_test_jig_intf import *

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

JLINK_PATH_WIN32 = "C:\\Program Files (x86)\\SEGGER\\JLink\\JLink.exe"
JLINK_PATH_WIN64 = "C:\\Program Files\\SEGGER\\JLink\\JLink.exe"

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
def main(kw_args):
    with CtsTestJigInterface(kw_args.test_jig_com_port) as t:
        with CtsSerialMsgInterface(kw_args.cts_com_port) as c:
            log.info("Enabling CTS...")
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P12V_EN, True)
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P3V3_EN, True)
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_POWER_EN, True)

            time.sleep(3.0)
            if cpd.program_micro_device(kw_args.fw_file):
                log.info("Microcontroller programming successful: {}".format(kw_args.fw_file))
            else:
                log.info("Microcontroller programming FAILED: {}".format(kw_args.fw_file))

            time.sleep(3.0)
            cmd_success, msg = c.get_command(CtsMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                             CtsMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)

            if cmd_success:
                payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                    c.unpack_get_software_version_number_response(msg)
                log.info("Microcontroller firmware version: {}.{}.{}:{}".format(sw_major, sw_minor, sw_patch, sw_build))
            else:
                log.info("Microcontroller firmware version: read FAILED")

            log.info("Disabling CTS...")
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P12V_EN, False)
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P3V3_EN, False)
            t.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_POWER_EN, False)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ Process arguments, setup logging and call runtime procedure """
    cpd.JLINK_PATH_WIN32 = JLINK_PATH_WIN32
    cpd.JLINK_PATH_WIN64 = JLINK_PATH_WIN64

    parser = argparse.ArgumentParser(description="GbE Switch Interface")
    parser.add_argument("-c", "--cts_com_port", required=True, help="CTS COM port")
    parser.add_argument("-t", "--test_jig_com_port", required=True, help="Test Jig COM Port")
    parser.add_argument("-f", "--fw_file", required=True, help="Firmware binary file")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args)
