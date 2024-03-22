#!/usr/bin/env python3
"""
Module for setting and getting the
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
from enum import Enum
import json

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT
from intelhex import IntelHex

# Our own imports ---------------------------------------------------
from i2c import I2C


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class AssemblyType(Enum):
    NTM_DIGITAL_LB = 0
    NTM_DIGITAL_MB_HB = 1
    NTM_RF_LB = 2
    NTM_RF_MB_HB = 3
    NTM_RF_MB_HB_A = 4
    NTM_RF_MB_EHB_8GHZ = 5
    NTM_RF_MB_EHB_6GHZ = 6
    PCM = 7
    NTM_TEST_JIG = 8
    EMA_LB_R = 9
    EMA_LB_A = 10
    EMA_MB_R = 11
    EMA_MB_A = 12
    EMA_HB_R = 13
    EMA_HB_A = 14
    EMA_EHB_6GHZ_R = 15
    EMA_EHB_8GHZ_R = 16
    def __str__(self):
        return self.name
    @staticmethod
    def from_string(s):
        try:
            return AssemblyType[s]
        except KeyError:
            raise ValueError()

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
ASSEMBLY_NUMBER = {AssemblyType.NTM_DIGITAL_LB: "KT-000-0134-00",
                   AssemblyType.NTM_DIGITAL_MB_HB: "KT-000-0135-00",
                   AssemblyType.NTM_RF_LB: "KT-000-0136-00",
                   AssemblyType.NTM_RF_MB_HB: "KT-000-0137-00",
                   AssemblyType.NTM_RF_MB_HB_A: "KT-000-0137-01",
                   AssemblyType.NTM_RF_MB_EHB_8GHZ: "KT-000-0202-00",
                   AssemblyType.NTM_RF_MB_EHB_6GHZ: "KT-000-0202-01",
                   AssemblyType.PCM: "KT-000-0143-00",
                   AssemblyType.NTM_TEST_JIG: "KT-000-0161-00",
                   AssemblyType.EMA_LB_A: "KT-950-xxxx-00",
                   AssemblyType.EMA_LB_R: "KT-950-0331-00",
                   AssemblyType.EMA_MB_A: "KT-950-xxxx-00",
                   AssemblyType.EMA_MB_R: "KT-950-0332-00",
                   AssemblyType.EMA_HB_A: "KT-950-0409-00",
                   AssemblyType.EMA_HB_R: "KT-950-0333-00",
                   AssemblyType.EMA_EHB_6GHZ_R: "KT-950-0505-01",
                   AssemblyType.EMA_EHB_8GHZ_R: "KT-950-0505-00",
                   }

ASSEMBLY_TYPE = {AssemblyType.NTM_DIGITAL_LB: "NTM Digital Board",
                 AssemblyType.NTM_DIGITAL_MB_HB: "NTM Digital Board",
                 AssemblyType.NTM_RF_LB: "NTM RF Board",
                 AssemblyType.NTM_RF_MB_HB: "NTM RF Board",
                 AssemblyType.NTM_RF_MB_HB_A: "NTM RF Board",
                 AssemblyType.NTM_RF_MB_EHB_8GHZ: "NTM RF Board",
                 AssemblyType.NTM_RF_MB_EHB_6GHZ: "NTM RF Board",
                 AssemblyType.PCM: "Power Conditioning Module",
                 AssemblyType.NTM_TEST_JIG: "NTM Digital Board Test Jig",
                 AssemblyType.EMA_LB_A: "EMA Module",
                 AssemblyType.EMA_LB_R: "EMA Module",
                 AssemblyType.EMA_MB_A: "EMA Module",
                 AssemblyType.EMA_MB_R: "EMA Module",
                 AssemblyType.EMA_HB_A: "EMA Module",
                 AssemblyType.EMA_HB_R: "EMA Module",
                 AssemblyType.EMA_EHB_6GHZ_R: "EMA Module",
                 AssemblyType.EMA_EHB_8GHZ_R: "EMA Module"}

FORMAT_FILE = {AssemblyType.NTM_DIGITAL_LB: "hw_config_format_256.json",
               AssemblyType.NTM_DIGITAL_MB_HB: "hw_config_format_256.json",
               AssemblyType.NTM_RF_LB: "hw_config_format_256.json",
               AssemblyType.NTM_RF_MB_HB: "hw_config_format_256.json",
               AssemblyType.NTM_RF_MB_HB_A: "hw_config_format_256.json",
               AssemblyType.NTM_RF_MB_EHB_8GHZ: "hw_config_format_256.json",
               AssemblyType.NTM_RF_MB_EHB_6GHZ: "hw_config_format_256.json",
               AssemblyType.PCM: "hw_config_format_256.json",
               AssemblyType.NTM_TEST_JIG: "hw_config_format_256.json",
               AssemblyType.EMA_LB_A: "hw_config_format_128.json",
               AssemblyType.EMA_LB_R: "hw_config_format_128.json",
               AssemblyType.EMA_MB_A: "hw_config_format_128.json",
               AssemblyType.EMA_MB_R: "hw_config_format_128.json",
               AssemblyType.EMA_HB_A: "hw_config_format_128.json",
               AssemblyType.EMA_HB_R: "hw_config_format_128.json",
               AssemblyType.EMA_EHB_6GHZ_R: "hw_config_format_128.json",
               AssemblyType.EMA_EHB_8GHZ_R: "hw_config_format_128.json"}

OUTPUT_FILE = {AssemblyType.NTM_DIGITAL_LB: "/sys/bus/i2c/devices/0-0051/eeprom",
               AssemblyType.NTM_DIGITAL_MB_HB: "/sys/bus/i2c/devices/0-0051/eeprom",
               AssemblyType.NTM_RF_LB: "/sys/bus/i2c/devices/1-0050/eeprom",
               AssemblyType.NTM_RF_MB_HB: "/sys/bus/i2c/devices/1-0050/eeprom",
               AssemblyType.NTM_RF_MB_HB_A: "/sys/bus/i2c/devices/1-0050/eeprom",
               AssemblyType.NTM_RF_MB_EHB_8GHZ: "/sys/bus/i2c/devices/1-0050/eeprom",
               AssemblyType.NTM_RF_MB_EHB_6GHZ: "/sys/bus/i2c/devices/1-0050/eeprom",
               AssemblyType.PCM: "/sys/bus/i2c/devices/0-0057/eeprom",
               AssemblyType.NTM_TEST_JIG: "/sys/bus/i2c/devices/0-0057/eeprom",
               AssemblyType.EMA_LB_A: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_LB_R: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_MB_A: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_MB_R: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_HB_A: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_HB_R: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_EHB_6GHZ_R: "/sys/bus/i2c/devices/0-0050/eeprom",
               AssemblyType.EMA_EHB_8GHZ_R: "/sys/bus/i2c/devices/0-0050/eeprom"}

GPIO_I2C_BUS_ADDRESS = {AssemblyType.NTM_DIGITAL_LB: 0x21,
                        AssemblyType.NTM_DIGITAL_MB_HB: 0x21,
                        AssemblyType.NTM_RF_LB: 0x20,
                        AssemblyType.NTM_RF_MB_HB: 0x20,
                        AssemblyType.NTM_RF_MB_HB_A: 0x20,
                        AssemblyType.NTM_RF_MB_EHB_8GHZ: 0x20,
                        AssemblyType.NTM_RF_MB_EHB_6GHZ: 0x20,
                        AssemblyType.PCM: 0x27,
                        AssemblyType.NTM_TEST_JIG: 0x27}

GPIO_I2C_BUS_NUMBER = {AssemblyType.NTM_DIGITAL_LB: 0,
                       AssemblyType.NTM_DIGITAL_MB_HB: 0,
                       AssemblyType.NTM_RF_LB: 1,
                       AssemblyType.NTM_RF_MB_HB: 1,
                       AssemblyType.NTM_RF_MB_HB_A: 1,
                       AssemblyType.NTM_RF_MB_EHB_8GHZ: 1,
                       AssemblyType.NTM_RF_MB_EHB_6GHZ: 1,
                       AssemblyType.PCM: 0,
                       AssemblyType.NTM_TEST_JIG: 0}

DEFAULT_CONFIG_DATA = "\x67\x48\x09\x00\x00\x01\xCD\x2C\x1E"

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
    # Create Intel Hex file and initialise all data values to '\0'
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
                detail_val = input("Enter %s (ASCII string, max length %d characters): \n" %
                                   (detail.get("name"), detail.get("length_bytes")-1))[:(detail.get("length_bytes")-1)]
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
    log.debug("{} Configuration Information:".format(ASSEMBLY_TYPE[assembly_type]))

    # Read the GPIO expander part of the config data
    if assembly_type in GPIO_I2C_BUS_ADDRESS:
        i2c = I2C(GPIO_I2C_BUS_NUMBER[assembly_type], GPIO_I2C_BUS_ADDRESS[assembly_type])
        # PCA9500 has quasi-directional I/O's which must be set HIGH before they can be read
        # This is achieved by doing a memory read of address 0xFF
        hardware_config = i2c.read_byte(0xFF)
        log.debug("Hardware Version: {}".format(hardware_config & 0x1F))
        return_dict["Hardware Version"] = str(hardware_config & 0x1F)
        log.debug("Hardware Mod revision: {}".format((hardware_config & 0xE0) >> 5))
        return_dict["Hardware Mod Version"] = str((hardware_config & 0xE0) >> 5)

    # Process the data read from EEPROM
    for detail in version_info:
        detail_str = ""
        if detail.get("name") == "Hw Config Version":
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


def clear_unused_memory(assembly_type, config_version=1):
    """
    Read config information for specified assembly type, clear unused
    memory area to 0x00 and set config version number
    :param assembly_type: :type: one of AssemblyType enumerated values
    :param config_version: which version to use from the JSON config format template data :type: integer
    :return True/False based on success :type: boolean
    """
    # Import the version information format JSON data
    try:
        log.debug("Importing Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))

        with open(FORMAT_FILE[assembly_type], 'r') as f:
            hw_config_format_data = json.load(f)

    except OSError:
        log.critical("ERROR: failed to import Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))
        return False

    # Read the hardware config in (all versions that are in file)
    option_list = []
    for key in hw_config_format_data.keys():
        option_list.append(key)

    # Check that the requested config version is valid
    if not "Version {}".format(config_version) in option_list:
        log.critical("ERROR: Invalid hardware config version requested "
                     "(requested {}, max available is {})".format(config_version, len(option_list)))
        return False

    filename = OUTPUT_FILE[assembly_type]
    try:
        with open(filename, mode="rb") as f:
            file_contents = f.read()
            file_contents = bytearray(file_contents)

    except OSError:
        log.critical("ERROR: Unable to read I2C EEPROM")
        return False

    version_info = hw_config_format_data.get(option_list[config_version-1])
    log.info("{} Configuration Information:".format(ASSEMBLY_TYPE[assembly_type]))

    end_used_memory = 0
    end_unused_memory = 0
    hcv_index = 0
    crc_offset = 0

    for detail in version_info:
        if detail.get("type") == "information":
            # Find the information item with highest memory offset
            detail_end_address = detail.get("addr_offset") + detail.get("length_bytes")
            if detail_end_address > end_used_memory:
                end_used_memory = detail_end_address

        elif detail.get("type") == "version":
            end_unused_memory = detail.get("addr_offset") + detail.get("length_bytes")
            hcv_index = detail.get("addr_offset")

        elif detail.get("type") == "CRC16-CCITT":
            crc_offset = detail.get("addr_offset")

    # Required memory indexes haven't been found
    if end_unused_memory == end_used_memory == hcv_index == crc_offset == 0:
        return False

    for i in range(end_used_memory, end_unused_memory+1):
        file_contents[i] = 0
    file_contents[hcv_index] = config_version

    # Regenerate CRC
    crc = CRCCCITT(version="FFFF").calculate(file_contents[0:hcv_index+1])
    file_contents[crc_offset], file_contents[crc_offset + 1] = crc.to_bytes(2, "little")

    filename = OUTPUT_FILE[assembly_type]
    try:
        with open(filename, mode="wb") as f:
            f.write(file_contents)

    except OSError:
        log.critical("ERROR: Unable to write I2C EEPROM")
        return False

    log.info("Successfully cleared unused memory and set config version number")
    return True


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


def refresh_config_info():
    """
    Read hardware and unit config info then reset Assembly Serial No,
    Rev No, Build Date/Batch no and Part No.  All other data in EEPROM
    is written to default values
    """
    for at in AssemblyType:
        success, return_dict = get_config_info(at)
        if success and (return_dict.get("Assembly Part Number") == ASSEMBLY_NUMBER.get(at)):
            if set_config_info(return_dict.get("Assembly Serial Number"),
                               return_dict.get("Assembly Revision Number"),
                               return_dict.get("Assembly Build Date/Batch Number"),
                               at):
                log.info("{} config info successfully refreshed".format(at.name))
            else:
                log.critical("Set {} config info failed!".format(at.name))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Print out the configuration information, refresh if required
    """
    parser = argparse.ArgumentParser(description="Unit and Hardware Config Info")
    parser.add_argument("-r", "--refresh", dest="refresh", action="store_true",
                        help="Config info is read, serial no, revision no, batch no,"
                             "and assembly type value are re-written, all other values"
                             "are returned to default values")
    parser.add_argument("-p", "--print_info", dest="print_info", action="store_true",
                        help="PCB and unit config info is printed")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    if args.refresh:
        refresh_config_info()

    if args.print_info:
        print_config_info()

    clear_unused_memory(AssemblyType.NTM_RF_LB)
