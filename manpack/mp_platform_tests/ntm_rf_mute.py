#!/usr/bin/env python3
"""
Utility module to set the NTM RF_MUTE signals
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
REG_GPIO_1_ADDRESS = 0x4000B000
REG_GPIO_1_RF_MUTE_MASTER_BIT = 0
REG_GPIO_1_RF_MUTE_SLAVE_BIT = 1

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def set_rf_mute(set_state=False):
    # Perform read-modify-write operation on the GPIO 0 register
    val = DevMem.read(REG_GPIO_1_ADDRESS)

    if set_state:
        val |= (1 << REG_GPIO_1_RF_MUTE_MASTER_BIT)
        val |= (1 << REG_GPIO_1_RF_MUTE_SLAVE_BIT)
    else:
        val &= (~(1 << REG_GPIO_1_RF_MUTE_MASTER_BIT))
        val &= (~(1 << REG_GPIO_1_RF_MUTE_SLAVE_BIT))

    DevMem.write(REG_GPIO_1_ADDRESS, val)


def main(argv):
    """
    Sets the CSM Motherboard GPIO1 register to assert/de-assert the
    RF_MUTE signals based on the passed command line argument
    :param argv: argv[1]: '0' = de-assert; non-zero assert
    :return: None
    """
    if len(argv) == 1:
        if int(sys.argv[1]):
            set_rf_mute(True)
            print("RF_MUTE - Asserted")
        else:
            set_rf_mute(False)
            print("RF_MUTE - De-asserted")
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
