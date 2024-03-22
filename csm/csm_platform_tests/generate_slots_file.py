#!/usr/bin/python3
"""
This module is intended to generate a slots.sh file for the K-CEMA system
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
-t/--ab_ip_address required argument specifies Active Backplane IP address (default "", auto-detect)
-p/--port specifies Telnet Server Port No. (default 31, AB GbE switch SMI)
-o/--output_file specifies the output filename (default '/run/media/mmcblk1p2/slots.sh')

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

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from gbe_switch import SerialGbeSwitch, TelnetGbeSwitch

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
EMA_PORT_TO_SLOT_MAP = [['7', '1'],
                        ['8', '2'],
                        ['1', '3'],
                        ['2', '4'],
                        ['3', '5']]

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
    try:
        log.info("Connecting to " + ab_ip_address + ":" + str(telnet_port))
        retries = 3
        mac_address_to_slot_map.clear()
        while retries:
            gs = TelnetGbeSwitch(ab_ip_address, telnet_port)
            mac_addresses = gs.get_mac_addresses()

            for mac_entry in mac_addresses:
                mac_entry[0] = mac_entry[0].upper()
                mac_entry[0] = mac_entry[0].replace("-", ":")

                for p2s_entry in EMA_PORT_TO_SLOT_MAP:
                    # If the MAC address entry port has a corresponding entry in the
                    # EMA_PORT_TO_SLOT_MAP add it to the mac_address_to_slot_map
                    if p2s_entry[0] == str(mac_entry[1]):
                        # Change mac_entry port number to slot number
                        mac_entry[1] = p2s_entry[1]
                        mac_address_to_slot_map.append(mac_entry)
                        log.debug("MAC address: {}".format(mac_entry))
                        break

            # Expecting to get 5x EMA MAC addresses
            if len(mac_address_to_slot_map) == 5:
                # Sort the list by slot number
                mac_address_to_slot_map.sort(key=operator.itemgetter(1))
                break
            else:
                retries = retries - 1
                # Clear out the map read to try again
                mac_address_to_slot_map.clear()

        if len(mac_address_to_slot_map) == 0:
            log.info("FAIL: did not find EMA MAC addresses")
            ret_val = False
        else:
            log.info("OK: found EMA MAC addresses: {}".format(mac_address_to_slot_map))
            ret_val = True

    except Exception as err:
        log.critical("*** Something went wrong reading MAC Addresses *** - {}".format(err))
        ret_val = False

    return ret_val


def write_file(output_file):
    """
    Writes the output file to disc
    :param output_file: output filename :type string
    :return: True if file successfully written, else False
    """
    try:
        f = open(output_file, "w")

        f.write("#!/bin/bash\n\n")

        for entry in mac_address_to_slot_map:
            string = "export SLOT_" + entry[1] + "_MAC=" + entry[0] + "\n"
            f.write(string)

        f.close()

        # Finally change the file permissions to o755
        os.chmod(output_file, 0o755)
        return True

    except OSError:
        log.critical("*** Unable to open file: {} ***".format(output_file))
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


def generate_slots_file(ab_ip_address, telnet_port, output_file, serial_port):
    """
    Performs the steps necessary to generate the slots file
    - Get MAC address list from the Active Backplane GbE Switch
    - Generate physical slot to MAC address map
    - Write output file
    :param ab_ip_address: Active Backplane IP address, set to "" for auto-detection :type string
    :param telnet_port: Active Backplane GbE Switch SMI Telnet port :type string
    :param output_file: output filename :type string
    :param serial_port: serial port for communicating with CSM Gbe Switch :type string
    :return: True if process is successful else False
    """
    ret_val = False

    if ab_ip_address == "":
        detect_active_backplane_ip_address(serial_port)
        if len(ab_ip_addresses_to_try) == 1:
            log.info("Auto-detected Active Backplane IP address: {}".format(ab_ip_addresses_to_try[0]))
            ab_ip_address = ab_ip_addresses_to_try[0]
        else:
            log.info("Failed to auto-detect Active Backplane IP address!")

    if get_ema_mac_address_list(ab_ip_address, telnet_port):
        ret_val = write_file(output_file)

    return ret_val


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Generate a slots.sh file")
    parser.add_argument("-o", "--output_file", default="/run/media/mmcblk1p2/slots.sh",
                        help="Output file. Default is /run/media/mmcblk1p2/slots.sh")
    parser.add_argument("-s", "--serial_port", default=None,
                        help="CSM GbE Switch Serial Port")
    parser.add_argument("-t", "--ab_ip_address", default="",
                        help="Telnet IP address, for auto-detection leave this argument blank")
    parser.add_argument("-p", "--telnet_port", default=31, help="Telnet port number. Default is 31")
    args = parser.parse_args()

    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    # If a serial port argument has been passed then use that, otherwise test whether the UART symlink exists
    # and if not then use the original absolute UART device node
    if args.serial_port:
        ser_port = args.serial_port
    elif os.path.exists(CSM_GBE_SWITCH_SMI_UART_LINK):
        ser_port = CSM_GBE_SWITCH_SMI_UART_LINK
    else:
        ser_port = CSM_GBE_SWITCH_SMI_UART_ORIG

    if generate_slots_file(args.ab_ip_address, args.telnet_port, args.output_file, ser_port):
        log.info("OK: Generate Slots File")
    else:
        log.info("FAIL: Generate Slots File")
