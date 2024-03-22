#!/usr/bin/env python3
"""
Module for accessing the NVMe SSD temperature sensor using the
Linux nvme  utility.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
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
import logging
import os
import sys

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
class NvmeTempSensor:
    NVME_TEMP_SENSOR_CMD = "/usr/sbin/nvme smart-log {} | grep -i '^temperature'"

    def __init__(self):
        """ Class constructor """
        pass

    def read_temp(self, drive):
        """
        Reads the specified temperature sensor, returned temperature has resolution of 1 deg C
        :param drive: name of NVMe drive to query temperature of :type String
        :return: channel temperature with 1 deg C resolution, -128 for invalid temperature read
        """
        ret_val = -128
        resp_str = os.popen(self.NVME_TEMP_SENSOR_CMD.format(drive)).read()

        for a_line in resp_str.splitlines():
            if "temperature" in a_line:
                ret_val = int(a_line.split()[-2])

        return ret_val


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates an instance of NVMe Temp Sensor then reads and displays the temperature.
    :param argv: system command line options and arguments - currently not used
    :return: N/A
    """
    nt = NvmeTempSensor()
    for drive in ["/dev/nvme0"]:
        log.info("{:<4}\t: {} Temperature (deg C)".format(nt.read_temp(drive), drive))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Creates an instance of the class and reads temperatures from device 
    """
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(sys.argv[1:])
