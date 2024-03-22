#!/usr/bin/env python3
"""
Module for accessing a Texas Instruments TMP442 I2C bus temperature sensor.
Relies on the I2C module that uses I2C tools to access the I2C bus.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import time
from enum import Enum

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
TMP422_I2C_ADDRESS = 0x4C
TMP442_RESET_REG_ADDRESS = 0xFC
TMP442_CONFIG2_REG_ADDRESS = 0x0A
TMP442_CONFIG2_LEN_BIT = 0x08
TMP442_CONFIG2_REN1_BIT = 0x10
TMP442_CONFIG2_REN2_BIT = 0x20
TS_TMP442_ETA_CORRECTION1 = 0x21
TS_TMP442_ETA_CORRECTION2 = 0x22
TMP442_MANUFACTURER_ID_REG_ADDRESS = 0xFE
TMP442_MANUFACTURER_ID = 0x55
TMP442_DEVICE_ID_REG_ADDRESS = 0xFF
TMP442_DEVICE_ID = 0x42
TMP442_INT_TEMP = 0x00
TMP442_REMOTE1_TEMP = 0x01
TMP442_REMOTE2_TEMP = 0x02

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class TempChannels(Enum):
    """
    Enumeration class for temperature sensor channels
    """
    INTERNAL = TMP442_INT_TEMP
    REMOTE1 = TMP442_REMOTE1_TEMP
    REMOTE2 = TMP442_REMOTE2_TEMP


class Tmp442TempSensor:
    _AMBIENT_TEMP_MIN = 20
    _AMBIENT_TEMP_MAX = 60
    _REMOTE1_TEMP_MIN = 35
    _REMOTE1_TEMP_MAX = 75
    _REMOTE2_TEMP_MIN = 35
    _REMOTE2_TEMP_MAX = 75

    def __init__(self, bus):
        """
        Class constructor, creates an I2C object used to access the device,
        the I2C object uses I2C Tools to interact with the bus
        :param bus: I2C bus that the device resides on, integer value
        :return: None
        """
        self.i2c = I2C(bus, TMP422_I2C_ADDRESS)

    def init_device(self):
        """
        Resets the TMP442 device clearing any previous configuration data and
        reconfigures device as follows:
        - Local, Remote 1 & Remote 2 sensors enabled
        - Automatic beta compensation enabled for Remote 1 & Remote 2 sensors,
          POR default
        - ETA correction set to 3 for remote diodes with ideality factor 1.008
        - Remote 1 & Remote 2 sensor eta correction = 0, POR default
        - Resistance correction disabled
        - Maximum possible conversion rate, POR default
        :return: True if device identified and initialised, else False
        """
        ret_val = False

        if ((int(self.i2c.read_byte(TMP442_MANUFACTURER_ID_REG_ADDRESS)) == TMP442_MANUFACTURER_ID) and
                int((self.i2c.read_byte(TMP442_DEVICE_ID_REG_ADDRESS)) == TMP442_DEVICE_ID)):
            self.i2c.write_byte(TMP442_RESET_REG_ADDRESS, 0x00)
            self.i2c.write_byte(TS_TMP442_ETA_CORRECTION1, 0x03)
            self.i2c.write_byte(TS_TMP442_ETA_CORRECTION2, 0x03)
            self.i2c.write_byte(TMP442_CONFIG2_REG_ADDRESS,
                                (TMP442_CONFIG2_LEN_BIT | TMP442_CONFIG2_REN1_BIT | TMP442_CONFIG2_REN2_BIT))
            # Pause for 1-second to allow device to sample all the channels
            time.sleep(1)
            ret_val = True

        return ret_val

    def read_temp(self, channel):
        """
        Reads the specified temperature channel, only reads the device high
        register so the returned value has resolution of 1 deg C
        :param: channel one of TempChannels enumerated values :type TempChannels
        :return: channel temperature with 1 deg C resolution, -128 for invalid channel
        """
        ret_val = -128

        if isinstance(channel, TempChannels):
            ret_val = int(self.i2c.read_byte(channel.value))

        return ret_val

    def run_test(self):
        """
        Read all three temperature channels and check against expected values
        at room temperature
        :return: True if test passes, else False
        """
        test_pass = True
        self.init_device()

        temp = self.read_temp(TempChannels.INTERNAL)
        if self._AMBIENT_TEMP_MIN <= temp <= self._AMBIENT_TEMP_MAX:
            log.info("PASS - TMP442 Ambient [{} deg C]".format(temp))
            test_pass &= True
        else:
            log.info("FAIL - TMP442 Ambient [{} deg C]".format(temp))
            test_pass &= False

        temp = self.read_temp(TempChannels.REMOTE1)
        if self._REMOTE1_TEMP_MIN <= temp <= self._REMOTE1_TEMP_MAX:
            log.info("PASS - TMP442 Remote 1 [{} deg C]".format(temp))
            test_pass &= True
        else:
            log.info("FAIL - TMP442 Remote 1 [{} deg C]".format(temp))
            test_pass &= False

        temp = self.read_temp(TempChannels.REMOTE2)
        if self._REMOTE2_TEMP_MIN <= temp <= self._REMOTE2_TEMP_MAX:
            log.info("PASS - TMP442 Remote 2 [{} deg C]".format(temp))
            test_pass &= True
        else:
            log.info("FAIL - TMP442 Remote 2 [{} deg C]".format(temp))
            test_pass &= False

        return test_pass


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates an instance of Tmp442TempSensor on I2C bus 1, initialises device
    then reads and displays each temperature channel
    :param argv: system command line options and arguments - currently not used
    :return: None
    """
    temp_sensor = Tmp442TempSensor(1)

    if temp_sensor.init_device():
        log.info("Internal: {} deg C".format(temp_sensor.read_temp(TempChannels.INTERNAL)))
        log.info("Remote 1: {} deg C".format(temp_sensor.read_temp(TempChannels.REMOTE1)))
        log.info("Remote 2: {} deg C".format(temp_sensor.read_temp(TempChannels.REMOTE2)))
        log.info("Bad Chan: {} deg C".format(temp_sensor.read_temp(0xFF)))
    else:
        log.info("*** Failed to initialise device! ***")

    return None


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
