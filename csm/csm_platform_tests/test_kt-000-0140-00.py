#!/usr/bin/env python3
"""
KT-000-0140-00 CSM Motherboard Platform Test Script
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import logging
from os import popen
import time

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from eui48_ic import Eui48Ic
import test_power_supplies
from tmp442_temp_sensor import Tmp442TempSensor
from uart_test import UartTest
from gps_nmea_decode import GpsNmeaDecode
from dev_mem import DevMem
import hardware_unit_config
from hardware_unit_config import AssemblyType
from tcxo_adjust import TcxoAdjust

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
MOUNTED_SUPERFLASH_DEVICES = {
    "mtd0 on /mnt/sf0 type jffs2 (rw,noatime,sync)",
    "mtd1 on /mnt/sf1 type jffs2 (rw,noatime,sync)",
    "mtd2 on /mnt/sf2 type jffs2 (rw,noatime,sync)",
    "mtd3 on /mnt/sf3 type jffs2 (rw,noatime,sync)",
    "mtd4 on /mnt/sf4 type jffs2 (rw,noatime,sync)",
    "mtd5 on /mnt/sf5 type jffs2 (rw,noatime,sync)",
    "mtd6 on /mnt/sf6 type jffs2 (rw,noatime,sync)",
    "mtd7 on /mnt/sf7 type jffs2 (rw,noatime,sync)"
}

SOM_I2C_DEVICE_ADDRESS_LIST = {
    "20: -- -- 22",
    "40: -- -- -- -- -- -- -- -- -- 49 -- -- 4c ",
    "50: UU UU UU ",
    "60: -- -- -- -- -- -- -- -- UU "
}

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
def print_som_mac_ip_address():
    ifconfig_string = popen("ifconfig").read()

    # Split the input into lines
    ifconfig_string_split = ifconfig_string.split("\n")

    # Find the line with the eth0 MAC address and extract it
    for astr in ifconfig_string_split:
        if astr.find("eth0:avahi Link encap:Ethernet  HWaddr ") != -1:
            log.info("SoM MAC Address:\t" + astr[astr.find("HWaddr ")+len("HWaddr "):])
            break

    # Find the line with the eth0 IP address and extract it
    found_avahi = False
    for astr in ifconfig_string_split:
        if found_avahi:
            log.info("SoM IP Address:\t" + astr[astr.find("inet addr:")+len("inet addr:"):astr.find(" Bcast:")])
            break

        if astr.find("eth0:avahi Link encap:Ethernet  HWaddr ") != -1:
            found_avahi = True


def check_som_i2c_device_detection():
    """

    :return: True if the test passes, else False :type boolean
    """
    test_pass = True

    i2c_detect_string = popen("i2cdetect -y -r 1").read()

    for i2c_device in SOM_I2C_DEVICE_ADDRESS_LIST:
        if i2c_detect_string.find(i2c_device) == -1:
            test_pass = False

    return test_pass


def som_pps_input_tcxo_test():
    """
    Attempt to trim the TCXO to 10 MHz, GPS 1PPS signal must be present for successful trim
    :return: True if the test passes, else False :type boolean
    """
    return TcxoAdjust().trim_dac(10000000, set_eeprom=True)


def _super_flash_test():
    """
    Uses the Linux mount command to check if the SuperFlash devices are 
    mounted
    :return: True if the SuperFlash devices are mounted, else False 
    """
    test_pass = True
    mount_string = popen("mount").read()

    for device in MOUNTED_SUPERFLASH_DEVICES:
        test_pass &= (mount_string.find(device) != -1)

    if test_pass:
        log.info("PASS - SuperFlash Mount Test")
    else:
        log.info("FAIL - SuperFlash Mount Test")

    return test_pass


def run_test(serial_no, rev_no, batch_no):
    """
    Executes tests and determines overall test script result
    :param serial_no: serial number of board under test :type: string
    :param rev_no: revision number of board under test :type: string
    :param batch_no: batch number of board under test :type: string
    :return: None
    """
    log.info("KT-000-0140-00 CSM Motherboard Platform Test Script:")
    input("Make wire link from P12 Pin 2 to Pin 3 on the board under test and connect active GPS antenna to case TNC J8, then press <Enter>")

    ut = UartTest()
    overall_pass = ut.run_test()

    ts = Tmp442TempSensor(1)
    overall_pass = ts.run_test() and overall_pass

    dev1 = Eui48Ic(1, 0x50)
    dev2 = Eui48Ic(1, 0x51)

    log.debug("Dev1 EUI48 = {}".format(hex(dev1.read_eui48())))
    if dev1.read_verify_oui():
        overall_pass &= True
        log.info("PASS - Dev1 OUI valid")
    else:
        overall_pass &= False
        log.info("FAIL - Dev1 OUI NOT valid")

    log.debug("dev2 EUI48 = {}".format(hex(dev2.read_eui48())))
    if dev2.read_verify_oui():
        overall_pass &= True
        log.info("PASS - Dev2 EUI48 OUI valid")
    else:
        overall_pass &= False
        log.info("FAIL - Dev2 OUI NOT valid")

    if test_power_supplies.run_test():
        overall_pass &= True
    else:
        overall_pass &= False

    if _super_flash_test():
        overall_pass &= True
    else:
        overall_pass &= False

    gps = GpsNmeaDecode()
    if gps.wait_for_lock(timeout=300):
        log.info("PASS - GPS Lock Test")
        overall_pass &= True
    else:
        log.info("FAIL - GPS Lock Test")
        overall_pass &= False

    if som_pps_input_tcxo_test():
        log.info("PASS - SoM 1PPS & TCXO Input Test")
        overall_pass &= True
    else:
        log.info("FAIL - SoM 1PPS & TCXO Input Test")
        overall_pass &= False

    if check_som_i2c_device_detection():
        log.info("PASS - SoM I2C Device Detect Test")
        overall_pass &= True
    else:
        log.info("FAIL - SoM I2C Device Detect Test")
        overall_pass &= False

    if hardware_unit_config.set_config_info(serial_no, rev_no, batch_no, AssemblyType.CSM_MOTHERBOARD):
        log.info("PASS - Written Hardware Config Info")
    else:
        log.info("FAIL - Written Hardware Config Info")

    print_som_mac_ip_address()

    if overall_pass:
        log.info("PASS - Overall Test Result")
    else:
        log.info("FAIL - Overall Test Result")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM Motherboard Production Test")
    parser.add_argument("-s", "--serial_no", required=True, dest="serial_no", action="store",
                        help="Serial number of board under test, max length 15 characters")
    parser.add_argument("-r", "--rev_no", required=True, dest="rev_no", action="store",
                        help="Revision number of board under test, max length 15 characters")
    parser.add_argument("-b", "--batch_no", required=True, dest="batch_no", action="store",
                        help="Batch number of board under test, max length 15 characters")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run_test(args.serial_no, args.rev_no, args.batch_no)
