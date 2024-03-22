#!/usr/bin/env python3
"""
Utility module to set the POWER_OFF_OVR signal
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
import sys

# Third-party imports -----------------------------------------------
from dev_mem import *

# Our own imports ---------------------------------------------------

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
REG_GPIO_0_ADDRESS = 0x4000A000
REG_GPIO_0_POWER_OFF_OVR_BIT = 1

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def set_power_off_ovr(set_state=False):
    # Perform read-modify-write operation on the GPIO 0 register
    val = DevMem.read(REG_GPIO_0_ADDRESS)

    if set_state:
        val |= (1 << REG_GPIO_0_POWER_OFF_OVR_BIT)
    else:
        val &= (~(1 << REG_GPIO_0_POWER_OFF_OVR_BIT))

    DevMem.write(REG_GPIO_0_ADDRESS, val)


def main(argv):
    """
    Sets the CSM Motherboard GPIO0 register to assert/de-assert the
    POWER_OFF_OVR signal based on the passed command line argument
    :param argv: one option is valid - '0' to de-assert else assert
    nPOWER_OFF_OVR signal
    :return: None
    """
    if len(argv) == 1:
        if int(sys.argv[1]):
            set_power_off_ovr(True)
            print("POWER_OFF_OVR - Asserted")
        else:
            set_power_off_ovr(False)
            print("POWER_OFF_OVR - De-asserted")
    else:
        print("*** Invalid number of command line arguments! ***")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    if __name__ == "__main__":
        main(sys.argv[1:])
