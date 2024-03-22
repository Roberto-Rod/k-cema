#!/usr/bin/env python3
"""
Utility module to set the RF_MUTE signals
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
REG_GPIO_0_ADDRESS      = 0x4000A000
EXP_PWR_DISABLE_0_BIT   = 16
EXP_PWR_DISABLE_1_BIT   = 17

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def expansion_slot_power_disable(slot, disable=False):
    # Perform read-modify-write operation on the GPIO 0 register
    reg_val = DevMem.read(REG_GPIO_0_ADDRESS)

    if disable:
        reg_val |= (1 << (EXP_PWR_DISABLE_0_BIT if slot == 0 else EXP_PWR_DISABLE_1_BIT))
    else:
        reg_val &= (~(1 << (EXP_PWR_DISABLE_0_BIT if slot == 0 else EXP_PWR_DISABLE_1_BIT)))

    DevMem.write(REG_GPIO_0_ADDRESS, reg_val)


def main(argv):
    """
    Sets the CSM Motherboard GPIO1 register to assert/de-assert the
    RF_MUTE signals based on the passed command line argument
    :param argv: argv[1]: '0' = de-assert; non-zero assert
    :return: None
    """
    if len(argv) == 2:
        if int(argv[0]) in [0, 1]:
            if int(argv[1]):
                expansion_slot_power_disable(int(argv[0]), True)
                print("Expansion Slot {} Power Disable - Asserted".format(argv[0]))
            else:
                expansion_slot_power_disable(int(argv[0]), False)
                print("Expansion Slot {} Power Disable - De-asserted".format(argv[0]))
        else:
            print("Invalid expansion slot!")
    else:
        print("Invalid number of command line arguments!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    main(sys.argv[1:])
