#!/usr/bin/env python3
"""
Utility module for monitoring keypad button status.
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
import argparse
import logging
from os import popen
import time

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


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Keypad Function Button Monitor")
    parser.add_argument("-o", "--once", action="store_true", help="Scan and print button state once")
    args = parser.parse_args()

    # Get the systemctl environment variables
    system_vars_str = popen("systemctl show-environment").read()
    system_vars_dict = {}
    for line in system_vars_str.splitlines():
        system_vars_dict[line.split('=')[0]] = line.split('=')[1]

    # Clear the terminal and move the cursor home
    while True:
        time.sleep(0.5)
        print("\x1b[2J", end="\n\x1b[HKeypad Button Monitor:\n")
        for fb in range(1, 9):
            print("KEYPAD_F{} - {}".format(fb, open(system_vars_dict["KEYPAD_F{}".format(fb)], "r").read().rstrip()))

        if args.once:
            break
