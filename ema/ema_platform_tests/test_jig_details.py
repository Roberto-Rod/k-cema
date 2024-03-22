#!/usr/bin/env python3
import os
from test_hardware_config import *


def run_test():
    '''
    This test serves two purposes: (a) log the test jig details, (b) test the NTM I2C bus on the PCM connector
    The test jig part number is tested against the expected part number to validate the I2C bus transactions
    :return: True if the test passes
    '''
    print("")
    print("test_jig_details")
    print("----------------")
    # Read ID data as a binary file directly from the EEPROM device driver node
    filename = OUTPUT_FILE[AssemblyType.NTM_TEST_JIG]
    try:
        details = open(filename, "rb").read()
        if len(details) == 256:
            test_jig_part_number = details[0:15].decode("utf-8").rstrip("\x00")
            test_jig_revision = details[16:31].decode("utf-8").rstrip("\x00")
            test_jig_serial_number = details[32:47].decode("utf-8").rstrip("\x00")
            print("Test Jig Part Number: {}".format(test_jig_part_number))
            print("Test Jig Revision: {}".format(test_jig_revision))
            print("Test Jig Serial Number: {}".format(test_jig_serial_number))
            if test_jig_part_number != "KT-000-0161-00":
                print("FAIL - unexpected Test Jig Part Number")
                return False
        else:
            print("FAIL - unexpected length ({} bytes) {}".format(len(details), filename))
            return False
    except:
        print("FAIL - could not read {}".format(filename))
        return False

    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
