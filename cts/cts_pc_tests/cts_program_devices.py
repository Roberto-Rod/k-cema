#!/usr/bin/env python3
"""
This file contains utility functions to program/erase the K-CEMA Integrated CTS
Digital Board microcontroller using a Segger J-Link.
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
import platform

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

JLINK_SCRIPT_PROGRAM_DEVICE = "device STM32F439VG\nsi SWD\nspeed auto\nr\nh\nloadfile \"{}\",0\nr\ng\nexit\n"
JLINK_SCRIPT_ERASE_DEVICE = "device STM32F439VG\nsi SWD\nspeed auto\nr\nh\nerase\nexit\n"
JLINK_SCRIPT_FILENAME = "command.jlink"
JLINK_PATH_WIN32 = "C:\\Program Files (x86)\\SEGGER\\JLink\\JLink.exe"
JLINK_PATH_WIN64 = "C:\\Program Files\\SEGGER\\JLink\\JLink.exe"
JLINK_PROGRAM_CMD = "\"{}\" -CommandFile \"{}\" -ExitOnError 1 -NoGui 1 -Log j-link_log.txt"

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
def program_micro_device(bin_file_path):
    """
    Uses Segger J-Link to program the STM32L071CZ microcontroller using the specified file.
    A temporary J-Link script file is created for performing the programming operation, this file
    is removed once the programming operation is complete.
    :param bin_file_path: path of binary file that will be programmed into the microcontroller :type: string
    :return: True if the device is successfully programmed, else False
    """
    if not os.path.isfile(bin_file_path):
        raise RuntimeError("Invalid binary file path!")

    # Create a J-Link script file for device programming
    with open(JLINK_SCRIPT_FILENAME, 'w') as f:
        f.write(JLINK_SCRIPT_PROGRAM_DEVICE.format(bin_file_path))

    # Execute command to program device
    cmd_prompt = os.popen(JLINK_PROGRAM_CMD.format(get_jlink_exe_path_win(), JLINK_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the J-Link script file
    if os.path.isfile(JLINK_SCRIPT_FILENAME):
        os.remove(JLINK_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


def erase_micro_device():
    """
    Uses Segger J-Link to erase the STM32L071CZ microcontroller.  A temporary J-Link script file is
    created for performing the erase operation, this file is removed once the erase operation is complete.
    :return: True if the device is successfully erased, else False
    """
    # Create a J-Link script file for device programming
    with open(JLINK_SCRIPT_FILENAME, 'w') as f:
        f.write(JLINK_SCRIPT_ERASE_DEVICE)

    # Execute command to erase device
    cmd_prompt = os.popen(JLINK_PROGRAM_CMD.format(get_jlink_exe_path_win(), JLINK_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the J-Link script file
    if os.path.isfile(JLINK_SCRIPT_FILENAME):
        os.remove(JLINK_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


def get_jlink_exe_path_win():
    """
    Checks for Segger J-Link executable in standard 32/64-bit installation folders on Windows OS
    :return: jlink.exe path as string, None if not found
    """
    if platform.system().lower() == "windows":
        if os.path.isfile(JLINK_PATH_WIN64):
            return JLINK_PATH_WIN64
        elif os.path.isfile(JLINK_PATH_WIN32):
            return JLINK_PATH_WIN32
        else:
            raise RuntimeError("Segger J-Link executable not found!")
    else:
        raise RuntimeError("Unsupported platform!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
