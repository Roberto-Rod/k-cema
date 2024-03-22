#!/usr/bin/python3
"""
This module is intended to generate a run.sh file for the K-CEMA system
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
-t/--ab_ip_address required argument specifies Active Backplane IP address (default "", auto-detect)
-p/--port specifies Telnet Server Port No. (default 31, AB GbE switch SMI)
-o/--output_file specifies the output filename (default '/run/media/mmcblk1p2/run.sh')

ARGUMENTS -------------------------------------------------------------
None
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
import operator
import os
import serial
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from gbe_switch import SerialGbeSwitch, TelnetGbeSwitch
from hardware_unit_config import *

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
mac_address_to_slot_map = []
ab_ip_addresses_to_try = []

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
CSM_GBE_SWITCH_SMI_UART_LINK = "/dev/ttyEthSw"
CSM_GBE_SWITCH_SMI_UART_ORIG = "/dev/ttyUL6"
CSM_GBE_SWITCH_SMI_BAUD_RATE = 115200

# Table of applications; run script directory, executable name, include mission roots,
# include EMA MACs, include DCPS switch (for DDS apps), include poweroff directive
APPS = [{"run_dir": "/run/media/mmcblk1p2/app_launchers/01_csm_app",
         "exec": "csm_app.bin", "inc_miss": True, "inc_mac": True, "inc_dcps": True, "inc_pwroff": True},
        {"run_dir": "/run/media/mmcblk1p2/app_launchers/02_mora_bridge",
         "exec": "mora_brdg.bin", "inc_miss": False, "inc_mac": False, "inc_dcps": True, "inc_pwroff": False},
        {"run_dir": "/run/media/mmcblk1p2/app_launchers/03_sapient_bridge",
         "exec": "sapnt_brdg.bin", "inc_miss": False, "inc_mac": False, "inc_dcps": True, "inc_pwroff": False},
        {"run_dir": "/run/media/mmcblk1p2/app_launchers/04_kfmt_bridge",
         "exec": "kfmt_brdg.bin", "inc_miss": False, "inc_mac": False, "inc_dcps": True, "inc_pwroff": False}]

EMA_PORT_TO_SLOT_MAP = [['7', '1'],
                        ['8', '2'],
                        ['1', '3'],
                        ['2', '4'],
                        ['3', '5']]

MP_PORT_TO_SLOT_MAP = [['5', '1'],
                       ['6', '2'],
                       ['7', '3']]

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

def get_ema_mac_address_list(ab_ip_address, telnet_port):
    """
    Connects to the Active Backplane and retrieves the list of MAC addresses
    connected to each GbE Switch port.
    Assumes a single MAC address is present on each Active Backplane EMA slot
    :param ab_ip_address: Active Backplane IP address :type string
    :param telnet_port: Active Backplane GbE Switch SMI Telnet port :type string
    :return: True if MAC address list retrieved, else False
    """
    expected_nr_emas = 5
    try:
        log.info("Connecting to " + ab_ip_address + ":" + str(telnet_port))
        retries = 20
        mac_address_to_slot_map.clear()
        while retries:
            gs = TelnetGbeSwitch(ab_ip_address, telnet_port)
            mac_addresses = gs.get_mac_addresses()
            # Expecting to get 5x EMA MAC addresses
            if parse_mac_addresses(mac_addresses, EMA_PORT_TO_SLOT_MAP, expected_nr_emas):
                break
            else:
                retries -= 1
                log.info("Found fewer than {} EMAs, retrying...".format(expected_nr_emas))
                time.sleep(1)
                # Clear out the map read to try again
                mac_address_to_slot_map.clear()
    except Exception as err:
        log.critical("*** Something went wrong reading MAC Addresses *** - {}".format(err))
        return False

    if len(mac_address_to_slot_map) == 0:
        log.info("FAIL: did not find EMA MAC addresses")
        return False
    else:
        log.info("OK: found EMA MAC addresses: {}".format(mac_address_to_slot_map))
        return True


def get_ema_mac_address_list_mp(serial_port):
    """
    Connects to the GbE switch and retrieves the list of MAC addresses
    connected to each port.
    :param serial_port: GbE Switch serial port :type string
    :return: True if MAC address list retrieved, else False
    """
    expected_nr_emas = 3
    try:
        retries = 20
        mac_address_to_slot_map.clear()
        while retries:
            mac_address_to_slot_map.clear()
            gs = SerialGbeSwitch(serial_port, CSM_GBE_SWITCH_SMI_BAUD_RATE)
            mac_addresses = gs.get_mac_addresses()

            # Expecting to get 3x EMA MAC addresses
            if parse_mac_addresses(mac_addresses, MP_PORT_TO_SLOT_MAP, expected_nr_emas):
                break
            else:
                retries -= 1
                log.info("Found fewer than {} EMAs, retrying...".format(expected_nr_emas))
                time.sleep(1)
                # Clear out the map read to try again
                mac_address_to_slot_map.clear()
    except Exception as err:
        log.critical("*** Something went wrong reading MAC Addresses *** - {}".format(err))
        return False

    if len(mac_address_to_slot_map) == 0:
        log.info("FAIL: did not find EMA MAC addresses")
        return False
    else:
        log.info("OK: found EMA MAC addresses: {}".format(mac_address_to_slot_map))
        return True


def parse_mac_addresses(mac_addresses, mac_map, expected_nr):
    for mac_entry in mac_addresses:
        mac_entry[0] = mac_entry[0].upper()
        mac_entry[0] = mac_entry[0].replace("-", ":")

        for p2s_entry in mac_map:
            # If the MAC address entry port has a corresponding entry in the
            # mac_map add it to the mac_address_to_slot_map
            if p2s_entry[0] == str(mac_entry[1]):
                # Skip this entry if it is a Xilinx pre-configuration MAC
                if not str(mac_entry[0]).startswith("00:0A:35"):
                    # Store this entry
                    this_entry = [mac_entry[0], p2s_entry[1]]
                    mac_address_to_slot_map.append(this_entry)
                    log.debug("MAC address: {}".format(this_entry))

            if len(mac_address_to_slot_map) == expected_nr:
                # Sort the list by slot number
                mac_address_to_slot_map.sort(key=operator.itemgetter(1))
                return True

    return False


def detect_active_backplane_ip_address(serial_port):
    """
    Build a list of LWIP AUTOIP addresses for nodes connected to the CSM GbE Switch,
    in a K-CEMA system there should be a single address which is for the Active Backplane
    :param serial_port: CSM GbE Switch serial port :type string
    :return:
    """
    gs = SerialGbeSwitch(serial_port, CSM_GBE_SWITCH_SMI_BAUD_RATE)
    global ab_ip_addresses_to_try
    ab_ip_addresses_to_try = gs.find_lwip_autoip_addresses()


def generate_run_file(app, ab_ip_address="", telnet_port="", serial_port=""):
    """
    Performs the steps necessary to generate the run file, where required:
    - Get MAC address list from the Active Backplane GbE Switch
    - Generate physical slot to MAC address map
    - Write output file
    :param app: App details, see APPS constant
    :param ab_ip_address: Active Backplane IP address, set to "" for auto-detection :type string
    :param telnet_port: Active Backplane GbE Switch SMI Telnet port :type string
    :param output_file: output filename :type string
    :param serial_port: serial port for communicating with CSM Gbe Switch :type string
    :return: True if process is successful else False
    """
    run_dir = app["run_dir"]
    executable = app["exec"]
    inc_miss = app["inc_miss"]
    inc_mac = app["inc_mac"]
    inc_dcps = app["inc_dcps"]
    inc_pwroff = app["inc_pwroff"]

    # If MAC addresses are required then get them before continuing to write file
    if inc_mac:
        ok, config = get_config_info(AssemblyType.CSM_MOTHERBOARD)
        if ok:
            running_on_manpack = False
            if "Assembly Part Number" in config.keys():
                if config["Assembly Part Number"].startswith("KT-000-0180-"):
                    running_on_manpack = True

            if running_on_manpack:
                ok = get_ema_mac_address_list_mp(serial_port)
            else:
                if ab_ip_address == "":
                    detect_active_backplane_ip_address(serial_port)
                    if len(ab_ip_addresses_to_try) == 1:
                        log.info("Auto-detected Active Backplane IP address: {}".format(ab_ip_addresses_to_try[0]))
                        ab_ip_address = ab_ip_addresses_to_try[0]
                    else:
                        log.info("Failed to auto-detect Active Backplane IP address!")
                ok = get_ema_mac_address_list(ab_ip_address, telnet_port)
    else:
        ok = True

    if ok:
        # Create run script directory if it doesn't exist
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
        # Create run script
        output_file = os.path.join(run_dir, "run.sh")
        try:
            f = open(output_file, "w")

            # Main exports, always include
            f.write("#!/bin/bash\n")
            f.write("LIB_ROOT=/usr/local/lib\n")
            f.write("export APP_ROOT=/run/media/mmcblk1p1\n")
            f.write("export FILE_ROOT=/run/media/mmcblk1p2\n")

            # Mission exports if required
            if inc_miss:
                f.write("export MISSION_ROOT_1=/run/media/mmcblk1p2\n")
                f.write("export MISSION_ROOT_2=/run/media/mmcblk1p2\n")
                f.write("export MISSION_ROOT_3=/run/media/mmcblk1p2\n")
                f.write("export MISSION_ROOT_4=/run/media/mmcblk1p2\n")
                f.write("export MISSION_ROOT_5=/run/media/mmcblk1p2\n")
                f.write("export TEMP_MISSION_ROOT=/tmp\n")

            # Library path, always included
            f.write(
                "export LD_LIBRARY_PATH=${LIB_ROOT}/Boost:${LIB_ROOT}/CryptoPP:${LIB_ROOT}/OpenSSL:${LIB_ROOT}/OpenDDS\n")

            # EMA (slot) MAC addresses, if required
            if inc_mac:
                for entry in mac_address_to_slot_map:
                    string = "export SLOT_" + entry[1] + "_MAC=" + entry[0] + "\n"
                    f.write(string)

            # Executable line, always included, DCPS switch optional
            f.write("${{APP_ROOT}}/{}{}\n".format(executable, " -DCPSConfigFile ${FILE_ROOT}/rtps.ini" if inc_dcps else ""))

            # Power off directive, if required
            if inc_pwroff:
                f.write("if [ $? == 0 ]; then\n")
                f.write("    poweroff\n")
                f.write("fi\n")

            f.close()

            # Finally change the file permissions to o755
            os.chmod(output_file, 0o755)

        except OSError:
            log.critical("*** Unable to open file: {} ***".format(output_file))
            ok = False

    return ok


def generate_parent_run_file(output_file):
    """
    Writes the parent run file to file system
    :param output_file: output filename :type string
    :return: True if file successfully written, else False
    """
    try:
        f = open(output_file, "w")
        f.write("#!/bin/bash\n")
        f.write("LAUNCH_ROOT=/run/media/mmcblk1p2\n")
        f.write("for DIR in $LAUNCH_ROOT/app_launchers/*; do\n")
        f.write("    if [ -f \"$DIR/run.sh\" ]; then\n")
        f.write("        nohup $DIR/run.sh &>/dev/null &\n")
        f.write("    fi\n")
        f.write("done\n")
        f.close()

        # Finally change the file permissions to o755
        os.chmod(output_file, 0o755)
        return True
    except Exception as e:
        print(e)
        return False


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Generate a run.sh file")
    parser.add_argument("-o", "--output_file", default="/run/media/mmcblk1p2/run.sh",
                        help="Output file. Default is /run/media/mmcblk1p2/run.sh")
    parser.add_argument("-s", "--serial_port", default=None,
                        help="CSM GbE Switch Serial Port")
    parser.add_argument("-t", "--ab_ip_address", default="",
                        help="Telnet IP address, for auto-detection leave this argument blank")
    parser.add_argument("-p", "--telnet_port", default=31, help="Telnet port number. Default is 31")
    parser.add_argument("-c", "--csm_app_only", action="store_true", help="Only generate CSM app launcher")
    args = parser.parse_args()

    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    # If a serial port argument has been passed then use that, otherwise test whether the UART symlink exists
    # and if not then use the original absolute UART device node
    if args.serial_port:
        serial_port = args.serial_port
    elif os.path.exists(CSM_GBE_SWITCH_SMI_UART_LINK):
        serial_port = CSM_GBE_SWITCH_SMI_UART_LINK
    else:
        serial_port = CSM_GBE_SWITCH_SMI_UART_ORIG

    ok = False
    if args.csm_app_only:
        ok = generate_run_file(APPS[0], args.ab_ip_address, args.telnet_port, serial_port)
    elif generate_parent_run_file(args.output_file):
        ok = True
        for app in APPS:
            ok = generate_run_file(app, args.ab_ip_address, args.telnet_port, serial_port) and ok

    if ok:
        log.info("OK: Generate Run File")
    else:
        log.info("FAIL: Generate Run File")
