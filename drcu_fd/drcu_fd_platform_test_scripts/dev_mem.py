#!/usr/bin/env python3
"""
Wrapper for the devmem2 Linux utility, allows memory mapped registers to be
read and written.
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

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
DEVMEM_EXE_PATH = "/usr/bin/devmem2"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class DevMem:
    @staticmethod
    def read(address):
        """
        Read a 32-bit register
        :param address: register address to be read :type: Integer or String
        :return: 32-bit register data :type: Integer
        """
        cmd = "{} 0x{:x} w".format(DEVMEM_EXE_PATH, int(address))
        ret_str = os.popen(cmd).read()
        return int(ret_str.splitlines()[-1].split()[-1], base=16)

    @staticmethod
    def write(address, data):
        """
        Write a 32-bit register
        :param address: register address to be written :type: Integer or String
        :param data: data value to be written :type: Integer or String
        :return: N/A
        """
        cmd = "{} 0x{:x} w 0x{:x}".format(DEVMEM_EXE_PATH, int(address), int(data))
        # Read the output so that we block and wait for command to return
        os.popen(cmd).read()

    @staticmethod
    def set(address, mask):
        """
        Set bits in 32-bit register
        :param address: register address to be modified :type: Integer or String
        :param mask: bits set to '1' will be set :type Integer
        :return: N/A
        """
        val = DevMem.read(address)
        DevMem.write(address, val | mask)

    @staticmethod
    def clear(address, mask):
        """
        Clears bits in 32-bit register
        :param address: register address to be modified :type: Integer or String
        :param mask: bits set to '1' will be set :type Integer
        :return: N/A
        """
        val = DevMem.read(address)
        DevMem.write(address, val & ~mask)


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
