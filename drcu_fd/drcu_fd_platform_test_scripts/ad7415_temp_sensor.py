#!/usr/bin/env python3
"""
Module for accessing an Analog Devices AD7415 I2C bus temperature sensor.
Relies on the I2C module that uses I2C tools to access the I2C bus.
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
import sys

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from i2c import I2C

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
DEBUG = False

# TMP442 device constants
AD7415_I2C_ADDRESS = 0x48
AD7415_TEMP_VAL_REG_ADDRESS = 0x00

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class AD7415TempSensor:
    def __init__(self, bus):
        """
        Class constructor, creates an I2C object used to access the device,
        the I2C object uses I2C Tools to interact with the bus
        :param bus: I2C bus that the device resides on, integer value
        :return: None
        """
        self.i2c = I2C(bus, AD7415_I2C_ADDRESS)

    def read_temp(self):
        """
        Reads the specified temperature value register, returned temperature
        has resolution of 0.25 deg C
        :return: channel temperature with 0.25 deg C resolution, -128 for invalid temperature
        """
        ret_val = int(self.i2c.read_word(AD7415_TEMP_VAL_REG_ADDRESS))

        # Swap the bytes and shift the data into the right place
        ret_val = (((ret_val >> 8) & 0xFF) | ((ret_val << 8) & 0xFF00)) >> 6

        if ret_val >= 512:
            # Negative temperature
            ret_val = (float(ret_val) - 1024.0) / 4.0
        else:
            # Positive temperature
            ret_val = float(ret_val) / 4.0

        return ret_val


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates an instance of AD7415TempSensor on I2C bus 1 then reads and displays the temperature.
    :param argv: system command line options and arguments - currently not used
    :return: None
    """
    temp_sensor = AD7415TempSensor(1)
    log.info("Temperature: {} deg C".format(temp_sensor.read_temp()))


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
