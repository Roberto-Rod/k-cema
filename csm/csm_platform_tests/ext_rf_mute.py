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
See arparse processing in main runtime procedure.

ARGUMENTS -------------------------------------------------------------
See arparse processing in main runtime procedure.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
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
REG_GPIO_1_RF_MUTE_DIR_BIT = 2
REG_GPIO_1_RF_MUTE_IN_BIT = 3

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def set_master_rf_mute(set_state=False):
    # Perform read-modify-write operation on the GPIO 1 register
    val = DevMem.read(REG_GPIO_1_ADDRESS)

    if set_state:
        val |= (1 << REG_GPIO_1_RF_MUTE_MASTER_BIT)
    else:
        val &= (~(1 << REG_GPIO_1_RF_MUTE_MASTER_BIT))

    DevMem.write(REG_GPIO_1_ADDRESS, val)


def set_slave_rf_mute(set_state=False):
    # Perform read-modify-write operation on the GPIO 1 register
    val = DevMem.read(REG_GPIO_1_ADDRESS)

    if set_state:
        val |= (1 << REG_GPIO_1_RF_MUTE_SLAVE_BIT)
    else:
        val &= (~(1 << REG_GPIO_1_RF_MUTE_SLAVE_BIT))

    DevMem.write(REG_GPIO_1_ADDRESS, val)


def set_rf_mute_dir(set_state=False):
    # Perform read-modify-write operation on the GPIO 1 register
    val = DevMem.read(REG_GPIO_1_ADDRESS)

    if set_state:
        val |= (1 << REG_GPIO_1_RF_MUTE_DIR_BIT)
    else:
        val &= (~(1 << REG_GPIO_1_RF_MUTE_DIR_BIT))

    DevMem.write(REG_GPIO_1_ADDRESS, val)


def get_rf_mute_in():
    # Read and return the RF Mute input signal
    val = DevMem.read(REG_GPIO_1_ADDRESS)
    return True if val & (1 << REG_GPIO_1_RF_MUTE_IN_BIT) else False


def main(kw_args):
    """
    Process the command line arguments and set/get the RF Mute signals accordingly
    """
    if kw_args.both is not None:
        if int(kw_args.both):
            set_master_rf_mute(True)
            set_slave_rf_mute(True)
            print("Both RF_MUTE - Asserted")
        else:
            set_master_rf_mute(False)
            set_slave_rf_mute(False)
            print("Both RF_MUTE - De-asserted")
    elif kw_args.master is not None:
        if int(kw_args.master):
            set_master_rf_mute(True)
            print("Master RF_MUTE - Asserted")
        else:
            set_master_rf_mute(False)
            print("Master RF_MUTE - De-asserted")
    elif kw_args.slave is not None:
        if int(kw_args.slave):
            set_slave_rf_mute(True)
            print("Slave RF_MUTE - Asserted")
        else:
            set_slave_rf_mute(False)
            print("Slave RF_MUTE - De-asserted")

    if kw_args.direction is not None:
        if int(kw_args.direction):
            set_rf_mute_dir(True)
            print("RF_MUTE_DIR - Output")
        else:
            set_rf_mute_dir(False)
            print("RF_MUTE_DIR - Input")

    if kw_args.get:
        print("RF_MUTE_IN - {}".format("Asserted" if get_rf_mute_in() else "De-asserted"))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    parser = argparse.ArgumentParser(description="Set RF Mute Signals")
    parser.add_argument("-b", "--both", default=None, help="Set both signals to specified state.")
    parser.add_argument("-m", "--master", default=None, help="Set master/control signal to specified state.")
    parser.add_argument("-s", "--slave", default=None, help="Set slave/NTM signal to specified state.")
    parser.add_argument("-d", "--direction", default=None, help="Set NEO control direction signal to specified state.")
    parser.add_argument("-g", "--get", action="store_true", default=False,
                        help="Get NEO control RF Mute signal state.")
    args = parser.parse_args()
    main(args)
