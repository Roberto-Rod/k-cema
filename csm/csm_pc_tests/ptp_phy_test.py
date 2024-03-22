#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 battery signals, call script to execute test.

todo: This module could be migrated to work of an SSH connection rather than use the CSM Master serial port.
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
from os import popen
import platform
import time

# Third-party imports -----------------------------------------------
from serial import Serial, SerialException

# Our own imports ---------------------------------------------------


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

        sp.close()

    return return_val


def ping_ip(ip_address, retries=1):
    """
    Calls the system ping command for the specified IP address
    :param ip_address: ip address to ping :type: string
    :param retries: number of times to retry failed ping before giving up :type: integer
    :return: True if the IP address is successfully pinged with retries attempts, else False
    """
    try:
        return_val = False

        if platform.system().lower() == "windows":
            count_param = "n"
        else:
            count_param = "c"

        for i in range(0, retries):
            output = popen("ping -{} 1 {}".format(count_param, ip_address)).read()
            log.debug("Ping {}:".format(i))
            log.debug(output)

            if not output or "unreachable" in output or "0 packets received" in output or \
                    "could not find" in output or "Request timed out" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

    except Exception as ex:
        log.critical("Something went wrong with the ping! - {}".format(ex))
        return False


def bring_up_ptp_phy(com_port, csm_username="root"):
    """
    Brings UP the PTP PHY, assumes logged in Linux terminal, handles 3x scenarios:
    1 - PTP PHY is already UP
    2 - PTP PHY is DOWN immediately following reboot
    3 - PTP PHY is DOWN having previously been UP
    :param com_port: name of serial COM port to use :type: string
    :param csm_username: CSM username :type string
    :return: True if PTP PHY is brought UP, else False
    """
    return_val = False
    sp = open_com_port(com_port)

    if sp is not None:
        # Check if the PTP PHY is already up
        sp.write(b"ifconfig eth1\r")
        resp_str = sp.read_until("{}@CSM-".format(csm_username).encode("UTF-8"))
        log.debug(resp_str)

        if b"UP " in resp_str:
            return_val = True
        else:
            # PTP PHY isn't up so try to bring it up
            return_val = False
            sp.write(b"ethtool -s eth1 speed 100 duplex full autoneg off\r")
            resp_str = sp.read_until("{}@CSM-".format(csm_username).encode("UTF-8"))
            log.debug(resp_str)
            sp.write(b"ifconfig eth1 up\r")

            for i in range(0, 10):
                resp_str = sp.read_until(b"eth1:")
                log.debug(resp_str)
                if b"eth1:" in resp_str:
                    resp_str = sp.read_until(b"\r")
                    log.debug(resp_str)
                    if b"link up" in resp_str or b"link becomes ready" in resp_str:
                        return_val = True
                        break

        close_com_port(sp)

    return return_val


def bring_down_ptp_phy(com_port, csm_username="root"):
    """
    Brings the PTP PHY DOWN, assumes logged in Linux terminal, handles 2x scenarios:
    1 - PTP PHY is already DOWN
    2 - PTP PHY is UP
    :param com_port: name of serial COM port to use :type: string
    :param csm_username: CSM username :type string
    :return: True if PTP PHY is brought DOWN, else False
    """
    return_val = False
    sp = open_com_port(com_port)

    if sp is not None:
        sp.write(b"ifconfig eth0 down\r")
        for i in range(0, 2):
            sp.read_until("{}@CSM-".format(csm_username).encode("UTF-8"))
            sp.read_until(b"#")
            sp.write(b"\r")

        return_val = True
        sp.close()

    return return_val


def get_ptp_phy_inet6_address(com_port, csm_username="root"):
    """
    Gets inet6 address for the PTP PHY, assumes logged in Linux terminal
    :param com_port: name of serial COM port to use :type: string
    :param csm_username: CSM username :type string
    :return: [0] True if inet6 address found, else False; [1] inet6 address as string
    """
    success = False
    inet6_address = ""
    sp = open_com_port(com_port)

    if sp is not None:
        sp.write(b"ifconfig eth1\r")
        resp_str = sp.read_until("{}@CSM-".format(csm_username).encode("UTF-8"))

        resp_str = resp_str.splitlines()
        log.debug(resp_str)
        for a_line in resp_str:
            if b"inet6 addr: " in a_line:
                inet6_address = a_line[a_line.find(b"inet6 addr: ")+len(b"inet6 addr: "):
                                       a_line.find(b"/")].decode("UTF-8")
                log.debug("inet6 address: " + inet6_address)
                success = True

        close_com_port(sp)

    return success, inet6_address


def run_test(com_port, csm_username="root", csm_password="root"):
    """
    Run the test
    :param com_port: name of serial port for CSM Master terminal interface :type string
    :param csm_username: CSM username :type string
    :param csm_password: CSM password :type string
    :return: True if
    """
    test_pass = check_at_root_cmd_line(com_port, csm_username, csm_password)
    test_pass = bring_up_ptp_phy(com_port) and test_pass
    success, inet6_address = get_ptp_phy_inet6_address(com_port)
    test_pass &= success
    test_pass = ping_ip(inet6_address, retries=20) and test_pass
    test_pass = bring_down_ptp_phy(com_port) and test_pass

    log.info("{} - PTP PHY Test".format("PASS" if test_pass else "FAIL"))
    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM PTP PHY Test")
    parser.add_argument("-c", "--csm_master_port", required=True, dest="csm_master_port", action="store",
                        help="Name of CSM Master COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run_test(args.csm_master_port)
