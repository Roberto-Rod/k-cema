#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 SoM EIA-422 interface, call script to execute test
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
from serial import Serial, SerialException

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
RX_TIMEOUT = 5
BAUD_RATE = 115200

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
def check_at_root_cmd_line(com_port, csm_username="root", csm_password="root"):
    """
    Try to ensure that we are at the root command line prompt:
        - send Ctr-X, just in case a microcom terminal is open
        - send login username and password credentials
    :param com_port: name of serial COM port to use :type: string
    :param csm_username: CSM username :type string
    :param csm_password: CSM password :type string
    :return: True, if at root cmd line, else False
    """
    return_val = False
    sp = open_com_port(com_port)

    if sp is not None:
        sp.write(b"\x18")
        time.sleep(1)
        sp.write("{}\r".format(csm_username).encode("UTF-8"))
        time.sleep(1)
        sp.write("{}\r".format(csm_password).encode("UTF-8"))
        time.sleep(1)
        resp_str = sp.read_until("{}@CSM-".format(csm_username).encode("UTF-8"))
        if "{}@CSM-".format(csm_username).encode("UTF-8") in resp_str:
            return_val = True
        else:
            return_val = False

        sp.close()

    return return_val


def open_com_port(com_port):
    """
    :param com_port: COM port to open :type: string
    :return: serial object if COM port opened, else None
    """
    try:
        sp = Serial(com_port, BAUD_RATE, timeout=RX_TIMEOUT,
                    xonxoff=False, rtscts=False, dsrdtr=False)
        log.debug("Opened COM port {}".format(com_port))
        return sp

    except ValueError or SerialException:
        log.critical("Failed to open COM port {}".format(com_port))
        return None


def close_com_port(serial_port):
    """
    :param serial_port: COM port to close :type Serial
    :return:
    """
    log.debug("Closing COM port {}".format(serial_port.name))
    serial_port.close()


def run_test(csm_micro_com_port, csm_master_port,
             csm_username="root", csm_password="root", rcu_serial_port="/dev/ttyUL2"):
    """
    Run the test
    :param csm_micro_com_port: name of serial port for CSM Zeroise Micro test interface :type string
    :param csm_master_port: name of serial port for CSM Master test interface :type string
    :param csm_username: CSM username :type string
    :param csm_password: CSM password :type string
    :param rcu_serial_port: CSM RCU serial port :type string
    :return: True if
    """
    test_pass = check_at_root_cmd_line(csm_master_port, csm_username, csm_password)
    czm = open_com_port(csm_micro_com_port)
    cmp = open_com_port(csm_master_port)

    if cmp and czm:
        cmp.write("microcom -s 115200 {}\r".format(rcu_serial_port).encode("UTF-8"))
        time.sleep(1)
        czm.write(b"\r#GPO 5 0\r")
        resp_str = cmp.read_until(b"#GPO 5 0\r")
        log.debug(resp_str)
        if b"#GPO 5 0\r" not in resp_str:
            log.debug("Set GPO 5 0 Fail")
            test_pass &= False

        cmp.write(b"The quick brown fox jumps over the lazy dog")
        resp_str = czm.read_until(b"The quick brown fox jumps over the lazy dog")
        log.debug(resp_str)
        if b"The quick brown fox jumps over the lazy dog" not in resp_str:
            log.debug("QBT Fail")
            test_pass &= False

        czm.write(b"\r#GPO 5 1\r")
        resp_str = czm.read_until(b"RCU_MICRO_TX_EN set to: 1\r\n>GPO\r")
        log.debug(resp_str)
        if b"RCU_MICRO_TX_EN set to: 1\r\n>GPO\r" not in resp_str:
            log.debug("Set GPO 5 1 Fail")
            test_pass &= False

        cmp.write(b"\x18")

        close_com_port(czm)
        close_com_port(cmp)

    else:
        test_pass &= False

    log.info("{} - Som EIA-422 Interface Test".format("PASS" if test_pass else "FAIL"))
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
    parser.add_argument("-c", "--csm_master_port", required=True, dest="csm_master_port", action="store",
                        help="Name of CSM Master COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    run_test(args.csm_micro_port, args.csm_master_port)
