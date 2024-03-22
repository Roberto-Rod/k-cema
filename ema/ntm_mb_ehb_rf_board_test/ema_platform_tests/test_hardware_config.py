#!/usr/bin/env python3
from PyCRC.CRCModules.CRCCCITT import CRCCCITT
from enum import Enum
from intelhex import IntelHex
from hardware_unit_config import *

import json
import argparse

DEBUG = False

DEFAULT_CONFIG_DATA = "\x67\x48\x09\x00\x00\x01\xCD\x0C\x1E"


def run_test(assembly_type, zero_serial_number=False, config_version=1, revision=None, serial_number=None, date=None):
    print("")
    print("test_hardware_config")
    print("--------------------")
    print("")

    # Import the version information format JSON data
    try:
        print("Importing Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))

        with open(FORMAT_FILE[assembly_type], 'r') as f:
            hw_config_format_data = json.load(f)
    except:
        print("ERROR: failed to import Hw Config Format JSON Data from: {}".format(FORMAT_FILE[assembly_type]))

    if DEBUG:
        print(json.dumps(hw_config_format_data, indent=4))
        pass

    # Read the hardware config in (all versions that are in file)
    option_list = []
    for key in hw_config_format_data.keys():
        option_list.append(key)

    if DEBUG:
        print(option_list)
        pass

    # Check that the requested config version is valid
    if not 0 < config_version <= len(option_list):
        print("Invalid hardware config version requested (requested {}, max available is {})".format(config_version, len(option_list)))
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
            detail_val = ""
            # Set the Assembly Part Number automatically as we know which assembly we are testing
            if detail.get("name") == "Assembly Part Number":
                detail_val = ASSEMBLY_NUMBER[assembly_type]
            elif detail.get("name") == "Assembly Serial Number" and serial_number is not None:
                detail_val = serial_number
            elif detail.get("name") == "Assembly Revision Number" and revision is not None:
                detail_val = revision
            elif detail.get("name") == "Assembly Build Date/Batch Number" and date is not None:
                detail_val = date
            elif detail.get("name") == "BootBlocker Config":
                detail_val = DEFAULT_CONFIG_DATA
            elif detail.get("name") == "BootBlocker Version Number":
                detail_val = "?"
            else:
                # If zero_serial_number is set then use a serial number of 000000 and set other fields as N/A
                if zero_serial_number:
                    if detail.get("name") == "Assembly Serial Number":
                        detail_val = "000000"
                    else:
                        detail_val = "N/A"
            if not detail_val:
                detail_val = input("Enter %s (ASCII string, max length %d characters): \n" %
                                (detail.get("name"), detail.get("length_bytes")-1))[:(detail.get("length_bytes")-1)]
            try:
                print("{} will be set to \"{}\" at address offset 0x{}\n".format(detail.get("name"), detail_val,
                                                                                 detail.get("addr_offset")))
            except UnicodeEncodeError:
                print("{} will be set to \"{}\" at address offset 0x{}\n".format(detail.get("name"), bytes(detail_val, "utf-8"),
                                                                                 detail.get("addr_offset")))
            ih.putsz(detail.get("addr_offset"), detail_val)

        # For version item, add the selected option directly to the file
        elif detail.get("type") == "version":
            print("%s will be set to \"%d\" at address offset 0x%x" %
                  (detail.get("name"), config_version, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), config_version.to_bytes(1, "little"))

        # For CRC16-CCITT item calculate checksum add directly to Intel Hex file
        elif detail.get("type") == "CRC16-CCITT":
            # Add a dummy byte to set length of memory
            data = ih.gets(0, detail.get("addr_offset"))
            crc = CRCCCITT(version="FFFF").calculate(data)
            print("%s will be set to \"0x%x\" at address offset 0x%x" %
                  (detail.get("name"), crc, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), crc.to_bytes(2,"little"))

        else:
            print("Unable to process detail type: %s" % detail.get("type"))

    # Write output data as a binary file directly to the EEPROM device driver node
    filename = OUTPUT_FILE[assembly_type]
    try:
        ih.tobinfile(filename)
        print("Wrote binary data to {}".format(filename))
        return True
    except:
        print("Unable to write to {}".format(filename))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the hardware configuration information")
    parser.add_argument("assembly_type", nargs='?', default=AssemblyType.EMA_HB_R, type=AssemblyType.from_string, choices=list(AssemblyType), help="Enumerated AssemblyType found in hardware_unit_config.py")
    args = parser.parse_args()

    if run_test(args.assembly_type):
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")