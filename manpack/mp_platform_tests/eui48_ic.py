#!/usr/bin/env python3
"""
Module for accessing a Microchip 24AA025E48T
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

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from i2c import I2C

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
# http://ww1.microchip.com/downloads/en/AppNotes/TB3187-Organizationally-Unique-Identifiers-Tech-Brief-90003187A.pdf
MICROCHIP_OUI = {0x0004A3, 0x001EC0, 0xD88039, 0x5410EC, 0xFCC23D, 0x801F12, 0x049162, 0x682719, 0xE8EB1B, 0x803428}

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
DEBUG = False

# 24AA025E48T device constants
EUI48IC_OUI_START_ADDRESS = 0xFA

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class Eui48Ic:
    def __init__(self, bus, address):
        """
        Class constructor, creates an I2C object used to access the device,
        the I2C object uses I2C Tools to interact with the bus
        :param bus: I2C bus that the device resides on, integer value
        :param address: I2C address of device
        :return: None
        """
        self._i2c = I2C(bus, address)

    def read_eui48(self):
        """
        Reads the EUI-48 from the device
        :return: channel temperature with 1 deg C resolution, -128 for invalid channel
        """
        b1 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 0))
        b2 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 1))
        b3 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 2))
        b4 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 3))
        b5 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 4))
        b6 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 5))

        return (b1 << 40) | (b2 << 32) | (b3 << 24)| (b4 << 16)| (b5 << 8)| b6

    def read_verify_oui(self):
        """
        Reads the OUI from the device and verifies it is a valid Microchip ID
        :return: True if OUI is valid, else false
        """
        b1 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 0))
        b2 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 1))
        b3 = int(self._i2c.read_byte(EUI48IC_OUI_START_ADDRESS + 2))

        if ((b1 << 16) | (b2 << 8) | b3) in MICROCHIP_OUI:
            return True
        else:
            return False


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(argv):
    """
    Creates 2x instances of Eui48Ic class, reads and displays EUI48 and verifies
    OUI is valid Microchip ID
    :param argv: system command line options and arguments - currently not used
    :return: None
    """
    dev1 = Eui48Ic(1, 0x50)
    dev2 = Eui48Ic(1, 0x51)

    log.info("dev1 EUI48 = {}".format(hex(dev1.read_eui48())))
    if dev1.read_verify_oui():
        log.info("dev1 OUI valid")
    else:
        log.info("dev1 OUI NOT valid")

    log.info("dev2 EUI48 = {}".format(hex(dev2.read_eui48())))
    if dev2.read_verify_oui():
        log.info("dev2 OUI valid")
    else:
        log.info("dev2 OUI NOT valid")

    return None


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Creates an instance of the class and reads temperatures from device 
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(sys.argv[1:])
