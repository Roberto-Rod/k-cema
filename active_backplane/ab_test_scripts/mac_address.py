import re#!/usr/bin/env python3
"""
Utility functions for handling MAC addresses
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
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
import re

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
MAC_ADDRESS_REG_EX = re.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def check_str_format(mac_addr):
    """
    Checks a string to see if it matches the format expected for a MAC address,
    "00-00-00-00-00-00" or "00:00:00:00:00:00".  Note, '-' and ':'  can be mixed
    in the stint
    @param mac_addr: string to check :type string
    @return: True if string is expected format for MAC address, else False
    """
    if type(mac_addr) is str and re.match(MAC_ADDRESS_REG_EX, mac_addr):
        return True
    else:
        return False


def str_to_vals(mac_addr):
    """
    Splits MAC address string and returns 6x values as a tuple of integers.
    Raises ValueError if MAC address is not of the expected type and format.
    @param mac_addr: string to split :type string
    @return: tuple of 6x integer values
    """
    if not check_str_format(mac_addr):
        raise ValueError("MAC address is not expected type and/or format!")

    # Ensure that a common separator is being used
    mac_addr = mac_addr.replace(':', '-')
    return tuple(int(val, 16) for val in mac_addr.split('-'))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Module is NOT intended to be executed stand-alone, print warning message
    """
    print("Module is NOT intended to be executed stand-alone")
