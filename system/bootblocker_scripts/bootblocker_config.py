#!/usr/bin/env python3
"""
Utility class for BootBlocker Configuration Data structure
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Kirintec
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
from enum import Enum

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
class ConfigDataFlags(Enum):
    """
    Enumeration class for the bit fields in Configuration Data Flags
    """
    PERFORM_POST = 7
    TAMPER_DELAY = 6
    RESERVED00 = 5
    FORCE_TAMPER_EVENT = 4
    ENABLE_TAMPER_ACTIONS_CHAN1 = 3
    ENABLE_TAMPER_ACTIONS_CHAN0 = 2
    VERBOSE_BREAK_IN = 1
    VERBOSE = 0
    RESERVED12 = 15
    OSC_DISABLED = 14
    ENABLE_TAMPER_DETECTION_CHAN1 = 13
    ENABLE_TAMPER_DETECTION_CHAN0 = 12
    ENABLE_FALLBACK_CMD_MODE = 11
    ENABLE_BREAKIN = 10
    RESERVED11 = 9
    RESERVED10 = 8
    RESERVED22 = 23
    RESERVED21 = 22
    TAMPER_IRQ_BB = 21
    CLEAR_FW_ON_TAMPER = 20
    CLEAR_FW_FILE_ON_TAMPER = 19
    CLEAR_FPGA_FILE_ON_TAMPER = 18
    CLEAR_MISSION_FILE_ON_TAMPER = 17
    RESERVED20 = 16


class BootBlockerConfig:
    """
    Class to manage Configuration Data flags and build command strings
    """
    # Constants defining BootBlocker Configuration Data structure
    MAJOR_VERSION = 0
    MAJOR_VERSION_INDEX = 0x4
    MINOR_VERSION = 1
    MINOR_VERSION_INDEX = 0x5
    MAGIC = 0x4867
    MAGIC_INDEX = 0x0
    SIZE = 9
    SIZE_INDEX = 0x2
    FLAGS_INDEX = 0x6
    DEFAULT_CONFIG = [ConfigDataFlags.PERFORM_POST,
                      ConfigDataFlags.VERBOSE,
                      ConfigDataFlags.ENABLE_TAMPER_ACTIONS_CHAN1,
                      ConfigDataFlags.ENABLE_TAMPER_ACTIONS_CHAN0,
                      ConfigDataFlags.ENABLE_TAMPER_DETECTION_CHAN1,
                      ConfigDataFlags.ENABLE_TAMPER_DETECTION_CHAN0,
                      ConfigDataFlags.ENABLE_BREAKIN,
                      ConfigDataFlags.ENABLE_FALLBACK_CMD_MODE,
                      ConfigDataFlags.CLEAR_FW_ON_TAMPER,
                      ConfigDataFlags.CLEAR_FW_FILE_ON_TAMPER,
                      ConfigDataFlags.CLEAR_FPGA_FILE_ON_TAMPER,
                      ConfigDataFlags.CLEAR_MISSION_FILE_ON_TAMPER]

    def __init__(self):
        """
        Class constructor - creates a Configuration Data bytearray with all flags set to '0'
        """
        self._config_data = bytearray(self.SIZE)
        self._config_data[self.MAGIC_INDEX] = self.MAGIC & 0xFF
        self._config_data[self.MAGIC_INDEX + 1] = (self.MAGIC >> 8) & 0xFF
        self._config_data[self.SIZE_INDEX] = self.SIZE & 0xFF
        self._config_data[self.SIZE_INDEX + 1] = (self.SIZE >> 8) & 0xFF
        self._config_data[self.MAJOR_VERSION_INDEX] = self.MAJOR_VERSION & 0xFF
        self._config_data[self.MINOR_VERSION_INDEX] = self.MINOR_VERSION & 0xFF

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "BootBlockerConfig(x{})".format(" x".join(format(val, "02x") for val in self._config_data))

    def set_clear_flag(self, flag, val=False):
        """
        Set/clear the specified flag in the Configuration Data bytearray
        :param flag: flag to set/clear :type: ConfigDataFlags
        :param val: True to set flag, false to clear :type: Boolean
        :return:
        """
        if flag in ConfigDataFlags:
            flag_byte_index = flag.value // 8
            bit_mask = 1 << (flag.value - (flag_byte_index * 8))
            if val:
                self._config_data[self.FLAGS_INDEX + flag_byte_index] |= bit_mask
            else:
                self._config_data[self.FLAGS_INDEX + flag_byte_index] &= ~bit_mask
        return

    def get_flag(self, flag):
        """
        Return the set state of the specified flag in the Configuration Data bytearray
        :param flag:
        :return: True if flag set, else False
        """
        if flag in ConfigDataFlags:
            flag_byte_index = flag.value // 8
            bit_mask = 1 << (flag.value - (flag_byte_index * 8))
            if self._config_data[self.FLAGS_INDEX + flag_byte_index] & bit_mask:
                return True
            else:
                return False

    def get_write_command_string(self):
        return "cw {}\r".format(" ".join(format(val, "02X") for val in self._config_data))


class BootBlockerPassword:
    """
    Class to create unlock command codes and build command strings
    """
    PASSWORD_XOR = bytearray([0x1C, 0x91, 0x4D, 0x62])
    PASSCODE_HEX_SIZE = 4
    UNIT_SERIAL_NO_MAX_ASCII_SIZE = 8

    def __init__(self, unit_serial_no):
        """
        Class constructor, takes a single argument which is unit serial no.
        The serial no. is truncated to 8-characters, if it is less than
        8-characters padding will be applied
        :param unit_serial_no: up to 8-characters :type: string
        """
        if not str.isnumeric(unit_serial_no):
            raise TypeError("unit_serial_no must be a decimal number")

        # Truncate the unit serial no and pad the front end with zeroes if needed
        usn = unit_serial_no[:self.UNIT_SERIAL_NO_MAX_ASCII_SIZE]
        usn = usn.zfill(self.UNIT_SERIAL_NO_MAX_ASCII_SIZE)
        self._unit_serial_no_bytes = bytearray.fromhex(usn)
        self._password = bytearray()
        for i in range(0, self.PASSCODE_HEX_SIZE):
            self._password.append(self._unit_serial_no_bytes[i] ^ self.PASSWORD_XOR[i])

    def __repr__(self):
        """
        :return: string representing the class
        """
        astr = "BootBlockerPassword(unit_serial_no_bytes: x"
        astr += str.format(" x".join(format(val, "02x") for val in self._unit_serial_no_bytes))
        astr += "; password: x"
        astr += str.format(" x".join(format(val, "02x") for val in self._password))
        astr += ")"
        return astr

    def get_unlock_command_string(self):
        return "u {}\r".format("".join(format(val, "02X") for val in self._password))

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Module is not intended to be executed stand-alone, print warning message
    """
    print("Module is not intended to be executed stand-alone")
