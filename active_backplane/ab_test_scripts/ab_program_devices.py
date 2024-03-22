#!/usr/bin/env python3
"""
This file contains utility functions to program/erase the Active Backplane
microcontroller using a Segger J-Link and the GbE Switch SPI Flash device
using an ASIX PRESTO programmer.
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

JLINK_SCRIPT_PROGRAM_DEVICE = "si JTAG\nspeed 4000\nr\nh\nloadbin \"{}\",0\nr\ng\nexit\n"
JLINK_SCRIPT_ERASE_DEVICE = "si JTAG\nspeed 4000\nr\nh\nerase\nexit\n"
JLINK_SCRIPT_FILENAME = "command.jlink"
JLINK_PATH_WIN32 = "C:\\Program Files (x86)\\SEGGER\\JLink\\JLink.exe"
JLINK_PATH_WIN64 = "C:\\Program Files\\SEGGER\\JLink\\JLink.exe"
JLINK_PROGRAM_CMD = "\"{}\" -Device TM4C1294NCPDT -If JTAG -JTAGConf \"-1,-1\" -CommandFile \"{}\""

ASIX_UP_PATH_WIN32 = "C:\\Program Files (x86)\\ASIX\\UP\\up.exe"
ASIX_UP_PATH_WIN64 = "C:\\Program Files\\ASIX\\UP\\up.exe"
ASIX_UP_PROGRAM_CMD = "\"{}\" /part MX25L2006E /q1 /p \"{}\""
ASIX_UP_ERASE_CMD = "\"{}\" /part MX25L2006E /q1 /erase"

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
    Uses Segger J-Link to program the TM4C1294NCPDT microcontroller using the
    specified file.  A temporary J-Link script file is created for performing
    the programming operation, this file is removed once the programming
    operation is complete.
    :param bin_file_path: path of binary file that will be programmed into the microcontroller :type: string
    :return: True if the device is successfully programmed, else False
    """
    ret_val = False

    if os.path.isfile(bin_file_path):
        # Check that J-Link is installed
        jlink_exe_path = get_jlink_exe_path_win()

        if jlink_exe_path is not None:
            # Create a J-Link script file for device programming
            with open(JLINK_SCRIPT_FILENAME, 'w') as f:
                f.write(JLINK_SCRIPT_PROGRAM_DEVICE.format(bin_file_path))

            # Execute command to program device
            output = os.popen(JLINK_PROGRAM_CMD.format(jlink_exe_path, JLINK_SCRIPT_FILENAME)).read()
            log.debug(output)

            if output.count("O.K.") == 2 and output.find("Script processing completed.") != -1:
                ret_val = True

            # Clean up the J-Link script file
            if os.path.isfile(JLINK_SCRIPT_FILENAME):
                os.remove(JLINK_SCRIPT_FILENAME)

    return ret_val


def erase_micro_device():
    """
    Uses Segger J-Link to erase the TM4C1294NCPDT microcontroller.  A temporary
    J-Link script file is created for performing the erase operation, this file
    is removed once the erase operation is complete.
    :return: True if the device is successfully erased, else False
    """
    ret_val = False

    # Check that J-Link is installed
    jlink_exe_path = get_jlink_exe_path_win()

    if jlink_exe_path is not None:
        # Create a J-Link script file for device programming
        with open(JLINK_SCRIPT_FILENAME, 'w') as f:
            f.write(JLINK_SCRIPT_ERASE_DEVICE)

        # Execute command to program device
        output = os.popen(JLINK_PROGRAM_CMD.format(jlink_exe_path, JLINK_SCRIPT_FILENAME)).read()
        log.debug(output)

        if output.find("Erasing done.") != -1 and output.find("Script processing completed.") != -1:
            ret_val = True

        # Clean up the J-Link script file
        if os.path.isfile(JLINK_SCRIPT_FILENAME):
            os.remove(JLINK_SCRIPT_FILENAME)

    return ret_val


def get_jlink_exe_path_win():
    """
    Checks for Segger J-Link executable in standard 32/64-bit installation
    folders on Windows OS
    :return: jlink.exe path as string, None if not found
    """
    ret_val = None

    if platform.system().lower() == "windows":
        if os.path.isfile(JLINK_PATH_WIN64):
            ret_val = JLINK_PATH_WIN64
        elif os.path.isfile(JLINK_PATH_WIN32):
            ret_val = JLINK_PATH_WIN32

    return ret_val


def program_gbe_sw_spi_flash(bin_file_path):
    """
    Uses the ASIX PRESTO programmer via UP software to program the GbE Switch Macronix MX25V2033FM1I
    SPI Flash device with the specified file.
    :param bin_file_path: path of binary file that will be programmed into the SPI Flash device :type: string
    :return: True if the device is successfully erased, else False
    """
    ret_val = False

    if os.path.isfile(bin_file_path):
        # Check that ASIX UP is installed
        up_exe_path = get_asix_up_exe_path_win()

        if up_exe_path is not None:
            # Execute command to program device
            cmd_prompt = os.popen(ASIX_UP_PROGRAM_CMD.format(up_exe_path, bin_file_path))

            if cmd_prompt.close() is None:
                ret_val = True

    return ret_val


def erase_gbe_sw_spi_flash():
    """
    Uses the ASIX PRESTO programmer via UP software to erase the Macronix MX25V2033FM1I GbE Switch SPI Flash device.
    :return: True if the device is successfully erased, else False
    """
    ret_val = False

    # Check that ASIX UP is installed
    up_exe_path = get_asix_up_exe_path_win()

    if up_exe_path is not None:
        # Execute command to program device
        cmd_prompt = os.popen(ASIX_UP_ERASE_CMD.format(up_exe_path))

        if cmd_prompt.close() is None:
            ret_val = True

    return ret_val


def get_asix_up_exe_path_win():
    """
    Checks for the ASIX UP executable in standard 32/64-bit installation
    folders on Windows OS
    :return: up.exe path as string, None if not found
    """
    ret_val = None

    if platform.system().lower() == "windows":
        if os.path.isfile(ASIX_UP_PATH_WIN64):
            ret_val = ASIX_UP_PATH_WIN64
        elif os.path.isfile(ASIX_UP_PATH_WIN32):
            ret_val = ASIX_UP_PATH_WIN32

    return ret_val


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
