"""Script to generate Hardware Config Information Intel Hex file

Generates an Intel Hex file containing hardware configuration information that can be loaded in to an EEPROM.
Originally intended for hardware configuration information stored in NXP PCA9500 devices on K-CEMA PCBs.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec & Davies Systems Ltd
#
# -----------------------------------------------------------------------------
'''
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
None
'''

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import json
import sys

# Third-party imports -----------------------------------------------
from intelhex import IntelHex
from PyCRC.CRCCCITT import CRCCCITT

# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
debug = False
hw_config_format_filename = "hw_config_format.json"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def main(argv):
    '''
    Complete description of the method, what it does and how it should be used
    :param argv: system command line options and arguments - currently not used
    :return: None
    '''

    # Import the version information format JSON data
    try:
        print("Importing Hw Config Format JSON Data from: %s" % hw_config_format_filename)

        with open(hw_config_format_filename, 'r') as f:
            hw_config_format_data = json.load(f)
    except:
        print("ERROR: failed to import Hw Config Format JSON Data from: %s" % hw_config_format_filename)

    if debug:
        print(json.dumps(hw_config_format_data, indent=4))
        pass

    # Ask the user which version they want to use
    query_str = "Select required Hw Config Version (no. followed by Enter):\n\n"
    x = 1
    option_list = []
    for key in hw_config_format_data.keys():
        query_str += (str(x) + " - " + key + "\n")
        option_list.append(key)
        x += 1

    while 1:
        option = input(query_str)
        if option.isdigit():
            option = int(option)
            if 0 < option <= len(option_list):
                break

        go_again = input("Invalid option! - %s - Try again (Enter) or quit (Q + Enter)?\n" % option)
        if go_again == "Q" or go_again == "q":
            print("Quitting application")
            return

    if debug:
        print(option_list[option-1])
        pass

    # Ask the user for input data and create Intel Hex file
    # Create Intel Hex file and initialise all date values to '\0'
    ih = IntelHex()
    for x in range(0, 255):
        ih.puts(x, '\0')

    version_info = hw_config_format_data.get(option_list[option-1])

    for item in version_info.keys():
        detail = version_info.get(item)
        # For information items, ask user for input and add to Intel Hex file as ASCII data
        # For string information truncate length by 1-byte to allow for '\0' termination
        if detail.get("type") == "information":
            detail_val = input("Enter %s (ASCII string, max length %d characters): \n" %
                               (detail.get("name"), detail.get("length_bytes")-1))[:(detail.get("length_bytes")-1)]
            print("%s will be set to \"%s\" at address offset 0x%x" %
                  (detail.get("name"), detail_val, detail.get("addr_offset")))
            ih.putsz(detail.get("addr_offset"), detail_val)

        # For version item, add the selected option directly to the file
        elif detail.get("type") == "version":
            print("%s will be set to \"%d\" at address offset 0x%x" %
                  (detail.get("name"), option, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), option.to_bytes(1, "little"))

        # For CRC16-CCITT item calculate checksum add directly to Intel Hex file
        elif detail.get("type") == "CRC16-CCITT":
            # Add a dummy byte to set length of memory
            # print(type(detail.get("addr_offset")))
            crc = CRCCCITT(version="FFFF").calculate(ih.gets(0, detail.get("addr_offset")))
            print("%s will be set to \"0x%x\" at address offset 0x%x" %
                  (detail.get("name"), crc, detail.get("addr_offset")))
            ih.puts(detail.get("addr_offset"), crc.to_bytes(2,"little") )

        else:
            print("Unable to process detail type: %s" % detail.get("type"))

    # Ask the user for output filename
    filename = input("Enter output filename (*.hex and .bin extension will be added): ")
    filename_hex = filename + ".hex"
    filename_bin = filename + ".bin."

    # Create output file
    try:
        ih.write_hex_file(filename_hex)
        print("Output file created: \"%s\"" % filename_hex)
        ih.tobinfile(filename_bin)
        print("Output file created: \"%s\"" % filename_bin)
    except:
        print("Unable to create output file: \"%s\" & \"%s\"" % (filename_hex, filename_bin))

    return None


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    '''
    Complete description of the runtime of the script, what it does and how it
    should be used
    '''
    if __name__ == "__main__":
        main(sys.argv[1:])

# ih = IntelHex()
# ih.putsz(0x0, "My string\0")
# ih.write_hex_file("HwConfigInfo1.hex")
#
#
# ih = IntelHex()
# ih.putsz(0x20, "Another string\0")
# ih.write_hex_file("HwConfigInfo2.hex")
