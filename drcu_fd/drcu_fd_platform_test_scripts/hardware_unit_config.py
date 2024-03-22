#!/usr/bin/env python3
"""
Module for setting and getting the Unit Configuration Information
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
See argparse definition in the Runtime Procedure

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
from enum import Enum
import json
import os
import sys

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT
from intelhex import IntelHex

# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class AssemblyType(Enum):
    DRCU_ASSEMBLY = 1
    FD_ASSEMBLY = 2

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
ASSEMBLY_NUMBER = {AssemblyType.DRCU_ASSEMBLY: "KT-950-0429-00",
                   AssemblyType.FD_ASSEMBLY: "KT-950-0431-00"}

FORMAT_FILE = {AssemblyType.DRCU_ASSEMBLY: r"{}/hw_config_format_128.json"
                                           r"".format(os.path.dirname(os.path.realpath(__file__))),
               AssemblyType.FD_ASSEMBLY: r"{}/hw_config_format_128.json"
                                         r"".format(os.path.dirname(os.path.realpath(__file__)))}

OUTPUT_FILE = {AssemblyType.DRCU_ASSEMBLY: "/sys/bus/i2c/devices/1-0051/eeprom",
               AssemblyType.FD_ASSEMBLY: "/sys/bus/i2c/devices/1-0051/eeprom"}

DEFAULT_CONFIG_DATA = "\x67\x48\x09\x00\x00\x00\x00\x00\x00"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def set_config_info(serial_no, rev_no, batch_no, assembly_type, config_version=1):
    """
    Set config information for specified assembly type
    :param serial_no: value to set :type: string
    :param rev_no: value to set :type: string
    :param batch_no: value to set :type: string
    :param assembly_type: :type: one of AssemblyType enumerated values
    :param config_version: which version to use from the JSON config format template data :type: integer
    :return True/False based on success :type: boolean
    """
    if not isinstance(assembly_type, AssemblyType):
        raise TypeError("assembly_type must be an instance of AssemblyType Enum")

    # Import the version information format JSON data
    try:
        log.debug("Importing Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))

        with open(FORMAT_FILE[assembly_type], 'r') as f:
            hw_config_format_data = json.load(f)

    except OSError:
        log.critical("ERROR: failed to import Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))
        return False

    log.debug(json.dumps(hw_config_format_data, indent=4))

    # Read the hardware config in (all versions that are in file)
    option_list = []
    for key in hw_config_format_data.keys():
        option_list.append(key)

    log.debug(option_list)

    # Check that the requested config version is valid
    if not "Version {}".format(config_version) in option_list:
        log.critical("ERROR: Invalid hardware config version requested "
                     "(requested {}, max available is {})".format(config_version, len(option_list)))
        return False

    # Ask the user for input data and create Intel Hex file
    # Create Intel Hex file and initialise all date values to '\0'
    ih = IntelHex()
    for x in range(0, 255):
        ih.puts(x, "\0")

    version_info = hw_config_format_data.get(option_list[config_version-1])

    for detail in version_info:
        # For information items, ask user for input and add to Intel Hex file as ASCII data
        # For string information truncate length by 1-byte to allow for '\0' termination
        if detail.get("type") == "information":
            # Set the Assembly Part Number automatically as we know which assembly we are testing
            if detail.get("name") == "Assembly Part Number":
                detail_val = ASSEMBLY_NUMBER[assembly_type]
            elif detail.get("name") == "Assembly Revision Number":
                detail_val = rev_no[:(detail.get("length_bytes")-1)]
            elif detail.get("name") == "Assembly Serial Number":
                detail_val = serial_no[:(detail.get("length_bytes")-1)]
            elif detail.get("name") == "Assembly Build Date/Batch Number":
                detail_val = batch_no[:(detail.get("length_bytes")-1)]
            elif detail.get("name") == "BootBlocker Config":
                detail_val = DEFAULT_CONFIG_DATA
            elif detail.get("name") == "BootBlocker Version Number":
                detail_val = ""
            else:
                detail_val = ""

            log.debug("%s will be set to \"%s\" at address offset 0x%x" %
                      (detail.get("name"), detail_val, detail.get("addr_offset")))
            ih.putsz(detail.get("addr_offset"), detail_val)

        # For version item, add the selected option directly to the file
        elif detail.get("type") == "version":
            log.debug("%s will be set to \"%d\" at address offset 0x%x" %
                      (detail.get("name"), config_version, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), config_version.to_bytes(1, "little"))

        # For CRC16-CCITT item calculate checksum add directly to Intel Hex file
        elif detail.get("type") == "CRC16-CCITT":
            # Add a dummy byte to set length of memory
            data = ih.gets(0, detail.get("addr_offset"))
            crc = CRCCCITT(version="FFFF").calculate(data)
            log.debug("%s will be set to \"0x%x\" at address offset 0x%x" %
                      (detail.get("name"), crc, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), crc.to_bytes(2, "little"))

        else:
            log.critical("ERROR: Unable to process detail type: %s" % detail.get("type"))

    # Write output data as a binary file directly to the EEPROM device driver node
    filename = OUTPUT_FILE[assembly_type]
    try:
        ih.tobinfile(filename)
        log.debug("Wrote binary data to {}".format(filename))
        return True
    except OSError:
        log.critical("ERROR: Unable to write to {}".format(filename))
        return False


def get_config_info(assembly_type, config_version=1):
    """
    Read and return config information for specified assembly type
    :param assembly_type: :type: one of AssemblyType enumerated values
    :param config_version: which version to use from the JSON config format template data :type: integer
    :return[0] True/False based on success :type: boolean
    :return[1] dictionary containing read data, keys re-ues "name" parameter from JSON config
     format template data :type: dictionary
    """
    return_dict = dict()

    # Import the version information format JSON data
    try:
        log.debug("Importing Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))

        with open(FORMAT_FILE[assembly_type], 'r') as f:
            hw_config_format_data = json.load(f)

    except OSError:
        log.critical("ERROR: failed to import Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))
        return False, return_dict

    # Read the hardware config in (all versions that are in file)
    option_list = []
    for key in hw_config_format_data.keys():
        option_list.append(key)

    # Check that the requested config version is valid
    if not "Version {}".format(config_version) in option_list:
        log.critical("ERROR: Invalid hardware config version requested "
                     "(requested {}, max available is {})".format(config_version, len(option_list)))
        return False, return_dict

    filename = OUTPUT_FILE[assembly_type]
    try:
        with open(filename, mode="rb") as f:
            file_contents = f.read()

    except OSError:
        log.critical("ERROR: Unable to read I2C EEPROM")
        return False, return_dict

    version_info = hw_config_format_data.get(option_list[config_version-1])
    log.debug("{} Configuration Information:".format(ASSEMBLY_NUMBER[assembly_type]))

    # Process the data read from EEPROM
    for detail in version_info:
        detail_str = ""
        if detail.get("name") == "Config Version":
            detail_str = "{}".format(str(file_contents[detail.get("addr_offset")]))

        elif detail.get("type") == "CRC16-CCITT":
            data = file_contents[0:detail.get("addr_offset")]
            calc_crc = CRCCCITT(version="FFFF").calculate(data)
            read_crc = (file_contents[detail.get("addr_offset")+1] << 8) | file_contents[detail.get("addr_offset")]
            detail_str = "{} read: 0x{} calculated: 0x{}".format(detail.get("type"), hex(read_crc), hex(calc_crc))
            if calc_crc == read_crc:
                detail_str += ": VALID"
            else:
                detail_str += ": INVALID"

        elif detail.get("name") == "BootBlocker Version Number":
            major_version = (file_contents[detail.get("addr_offset")+3] << 8) | \
                             file_contents[detail.get("addr_offset")+2]
            minor_version = (file_contents[detail.get("addr_offset")+5] << 8) | \
                             file_contents[detail.get("addr_offset")+4]
            build_version = (file_contents[detail.get("addr_offset")+7] << 8) | \
                             file_contents[detail.get("addr_offset")+6]
            detail_str = "{}.{}.{}".format(major_version, minor_version, build_version)

        elif detail.get("name") == "BootBlocker Config":
            for i in range(0, detail.get("length_bytes")):
                detail_str += " 0x{}".format(format(file_contents[detail.get("addr_offset")+i], "02x"))

        else:
            detail_str = "{}".format(file_contents[detail.get("addr_offset"): detail.get("addr_offset") +
                                     detail.get("length_bytes")].decode("UTF-8").rstrip("\x00"))

        log.debug("{}: {}".format(detail.get("name"), detail_str))
        return_dict[detail.get("name")] = detail_str

    return True, return_dict


def print_config_info():
    """
    Read and print hardware and unit config info
    """
    for at in AssemblyType:
        success, return_dict = get_config_info(at)
        if success and (return_dict.get("Assembly Part Number") == ASSEMBLY_NUMBER.get(at)):
            log.info("{} Configuration Information:".format(at.name))
            log.info("Info read success: {}".format(success))
            for key in return_dict:
                log.info("{}: {}".format(key, return_dict.get(key)))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Print out the configuration information, refresh if required
    """
    parser = argparse.ArgumentParser(description="Unit Config Info")
    parser.add_argument("-p", "--print_info", action="store_true", help="Unit config info is printed")
    parser.add_argument("-sb", "--set_batch_build_no", default="", help="Set assembly build data/batch number")
    parser.add_argument("-sn", "--set_serial_no", default="", help="Set assembly serial number")
    parser.add_argument("-sr", "--set_rev_no", default="", help="Set assembly revision number")
    parser.add_argument("-st", "--set_assy_type", default="",
                        help="Set assembly type: DRCU_ASSEMBLY; FD_ASSEMBLY")
    parser.add_argument("-u", "--unit_info", action="store_true", help="Print unit info as JSON string")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S", stream=sys.stdout)

    if args.print_info:
        print_config_info()

    if args.set_batch_build_no != "" and args.set_serial_no != "" and \
            args.set_rev_no != "" and args.set_assy_type != "":
        if args.set_assy_type == "DRCU_ASSEMBLY" or args.set_assy_type == "FD_ASSEMBLY":
            if set_config_info(args.set_serial_no, args.set_rev_no, args.set_batch_build_no,
                               getattr(AssemblyType, args.set_assy_type)):
                log.info("INFO - Programmed config info {}".format(args.set_assy_type))
            else:
                log.info("INFO - Failed to program config info {}!".format(args.set_assy_type))
        else:
            log.info("INFO - Invalid assembly type {}, must be DRCU_ASSEMBLY"
                     "".format(args.set_assy_type))

    if args.unit_info:
        read_success, config_info = get_config_info(AssemblyType.DRCU_ASSEMBLY)
        print(json.dumps(config_info))
