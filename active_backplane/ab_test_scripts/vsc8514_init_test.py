#!/usr/bin/env python3
"""
Test script for Active Backplane VSC7512 to VSC8514 QSGMII link initialisation.

Suggested connections:
- Test PC GbE to KT-000-0164-00 RJ45 P23 (VSC7512 Port 1, CSM, ping target, -p argument)
- Raspberry Pi or second Test PC GbE to KT-000-0164-00 RJ45 P17 (VSC8514 Port 0, EMA3)
- KT-000-0164-00 STM32 NUCLEO board USB micro to test PC (COM port, -c argument)

Set the number of test iterations using the -t argument.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-t/--test_count required argument specifies number of times to repeat the test
-p/--ping_address required argument specifies the IP address to ping
-a/--ab_address optional argument specifies the IP address of the Active Backplane
-c/--com_port required argument specifies the COM port for test jig STM32
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
from ab_test_jig_intf import AbTestJigInterface
import argparse
import logging
import ipaddress
from os import popen
import platform
import time
from gbe_switch import TelnetGbeSwitch

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


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
def ping(ip_address, retries=1, timeout=3):
    """
    Calls the system ping command for the specified IP address
    :param ip_address: ip address/hostname to ping :type: string
    :param retries: number of times to retry failed ping before giving up :type: integer
    :param timeout: number of seconds to wait for ping response
    :return: True if the IP address is successfully pinged with retries attempts, else False
    """
    try:
        return_val = False

        # This will throw a ValueError exception if ip_address is NOT a valid IP address
        try:
            a = ipaddress.ip_address(ip_address)
        except Exception as ex:
            log.debug("Using hostname rather for ping rather than IP address".format(ex))
            a = ip_address

        ping_type = ""

        if platform.system().lower() == "windows":
            count_param = "n"
            if type(a) == ipaddress.IPv6Address:
                ping_type = "-6"
            timeout_param = "{}".format(timeout * 1000)
        else:
            count_param = "c"
            timeout_param = "{}".format(timeout)

        for i in range(0, retries):
            output = popen("ping {} -w {} -{} 1 {}".format(ping_type, timeout_param, count_param, a)).read()
            log.debug("Ping {}:".format(i))
            log.debug(output)

            if "unreachable" in output or "0 packets received" in output or "could not find" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

    except Exception as ex:
        log.critical("Something went wrong with the ping! - {}".format(ex))
        return False


def run_test(test_count, ping_address, ab_address, com_port):
    """
    Runtime procedure called when the the module is executed standalone or
    by a function call if the module is imported into another module.
    :param test_count: number of times to repeat the test :type integer
    :param ping_address: IPV4 or IPV6 address of ping target :type string
    :param ab_address: IPV4 or IPV6 address of the Active Backplane :type string
    :param com_port: COM port for test jig STM32 board :type string
    :return: None
    """
    atji = AbTestJigInterface(com_port)

    test_pass = 0
    test_times = []
    test_fail_times = []
    test_fail_steps = []

    for x in range(1, test_count + 1):
        atji.set_dcdc_enable(False)
        time.sleep(2)
        atji.set_dcdc_enable(True)

        start_time = time.perf_counter()
        ping_success = ping(ping_address, retries=30, timeout=1)
        end_time = time.perf_counter()

        # Pass if the ping was successful within 20-seconds.
        if ping_success and (end_time - start_time) < 20.0:
            log.info("{}\tTest Passed: {:3f} seconds".format(x, end_time - start_time))
            test_pass += 1
            test_times.append(end_time - start_time)
        else:
            log.info("Test Failed: {:3f} seconds".format(end_time - start_time))
            log.info("Ping Worked: {}".format(ping_success))
            test_fail_times.append(end_time - start_time)
            test_fail_steps.append(x)

            if ab_address is not None:
                # Try to ping the Active Backplane to confirm the switch is up and running
                # and get extra debug information
                if ping(ab_address, retries=3):
                    log.info("Ping Active Backplane Successful: {}".format(ab_address))

                    with TelnetGbeSwitch(ab_address, 31) as gs:
                        log.info("GbE Switch QSGMII Sync:{}".format(gs.get_sw_qsgmii_sync()))
                        log.info("GbE PHY QSGMII Sync:{}".format(gs.get_phy_qsgmii_sync()))

                else:
                    log.info("Ping Active Backplane Failed: {}".format(ab_address))

            exit()

    log.info("Total Pass Rate: {} out of {}".format(test_pass, test_count))
    log.info("Minimum time (s):\t{:.3f}".format(min(test_times)))
    log.info("Maximum time (s):\t{:.3f}".format(max(test_times)))
    log.info("Average time (s):\t{:.3f}".format(sum(test_times) / len(test_times)))
    if len(test_fail_times) > 0:
        log.info("Maximum FAIL time (s)\t{:.3f}".format(max(test_fail_times)))
    if len(test_fail_steps) > 0:
        log.info("Test FAIL steps: {}".format(test_fail_steps))

    atji.set_dcdc_enable(False)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="Active Backplane Telnet server test")
    parser.add_argument("-t", "--test_count", required=True, dest="test_count", action="store",
                        help="Number of times to repeat the test")
    parser.add_argument("-p", "--ping_address", required=True, dest="ping_address", action="store",
                        help="IPV4 or IPV6 address of target to ping")
    parser.add_argument("-a", "--ab_address", required=False, default=None, dest="ab_address", action="store",
                        help="IPV4 or IPV6 address of the Active Backplane")
    parser.add_argument("-c", "--com_port", required=True, dest="com_port", action="store",
                        help="COM port for test jig STM32")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")
    
    run_test(int(args.test_count), args.ping_address, args.ab_address, args.com_port)
