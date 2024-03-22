#!/usr/bin/env python3
"""
Utility module to set the display backlight.
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
import sys
from os import popen

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


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------

def set_display_backlight(brightness=20):
    # Get the systemctl environment variables
    system_vars_str = popen("systemctl show-environment").read()
    system_vars_dict = {}
    for line in system_vars_str.splitlines():
        system_vars_dict[line.split('=')[0]] = line.split('=')[1]

    f = open(system_vars_dict["DISPLAY_BRIGHTNESS"], "r+")
    f.write("{}\n".format(brightness))
    f.close()


def main(argv):
    """
    Sets the display backlight to the value based on the passed command line argument
    :param argv: argv[1]: range 0..255; display backlight brightness
    :return: None
    """
    if len(argv) == 1:
        set_display_backlight(int(sys.argv[1]))
        print("INFO - Set display backlight brightness to {}".format(sys.argv[1]))
    else:
        print("INFO - Invalid number of command line arguments!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    main(sys.argv[1:])
