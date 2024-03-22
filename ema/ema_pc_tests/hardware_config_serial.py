#!/usr/bin/env python3
"""
Implements the ASCII seria commands for setting Hardware Configuration
Information, a standard set of ASCII commands are used on a number of test
interface boards.
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
import logging
from enum import Enum

# Third-party imports -----------------------------------------------
from serial import Serial, SerialException

# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
PARAMETER_NAMES = ["Assembly Part No", "Assembly Revision No", "Assembly Serial No", "Assembly Build Batch No"]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class HardwareConfigParameters(Enum):
    """
    Enumeration class for hardware config information parameters
    """
    ASSEMBLY_PART_NO = 0
    ASSEMBLY_REVISION_NO = 1
    ASSEMBLY_SERIAL_NO = 2
    ASSEMBLY_BUILD_BATCH_NO = 3


class HardwareConfigSerial:
    """
    Class for wrapping up the ASCII set hardware configuration information serial
    interface commands
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _RESET_HCI_CMD = b'\r#RHCI\r'
    _RESET_HCI_RESPONSE_END = b">RHCI\r\n"
    _RESET_HCI_RESPONSE_SUCCESS = b"Successfully cleared HCI EEPROM"
    _SET_ASSEMBLY_PART_NO_CMD = b"\r#SHCI 0 "
    _SET_ASSEMBLY_PART_NO_SUCCESS = b"Successfully set parameter [Part No]"
    _SET_ASSEMBLY_REVISION_NO_CMD = b"\r#SHCI 1 "
    _SET_ASSEMBLY_REVISION_NO_SUCCESS = b"Successfully set parameter [Revision No]"
    _SET_ASSEMBLY_SERIAL_NO_CMD = b"\r#SHCI 2 "
    _SET_ASSEMBLY_SERIAL_NO_SUCCESS = b"Successfully set parameter [Serial No]"
    _SET_ASSEMBLY_BUILD_BATCH_NO_CMD = b"\r#SHCI 3 "
    _SET_ASSEMBLY_BUILD_BATCH_NO_SUCCESS = b"Successfully set parameter [Build Batch No]"
    _SET_CMD_END = b"\r"
    _SET_CMD_RESPONSE_END = b">SHCI\r\n"
    _GET_HCI_CMD = b"\r$HCI\r"
    _GET_HCI_RESPONSE_END = b"!HCI\r\n"

    def __init__(self, com_port):
        """
        Class constructor
        :param: COM port associated with the interface :type: string
        :return: None
        """
        self._com_port = com_port

    def _open_com_port(self, com_port):
        """
        :param com_port: COM port to open :type: string
        :return: serial object if COM port opened, else None
        """
        try:
            sp = Serial(com_port, self._BAUD_RATE, timeout=self._RX_TIMEOUT,
                        xonxoff=False, rtscts=False, dsrdtr=False)
            log.debug("Opened COM port {}".format(com_port))
            return sp

        except ValueError or SerialException:
            log.debug("Failed to open COM port {}".format(com_port))
            return None

    @staticmethod
    def _close_com_port(serial_port):
        """
        :param serial_port: COM port to close :type Serial
        :return:
        """
        log.debug("Closing COM port {}".format(serial_port.name))
        serial_port.close()

    def reset_hci(self):
        """
        Resets the HCI EEPROM
        :return: True if reset successful, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._RESET_HCI_CMD)
            resp_str = serial_port.read_until(self._RESET_HCI_RESPONSE_END)
            log.debug(b"#RHCI cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if self._RESET_HCI_RESPONSE_END in resp_str and self._RESET_HCI_RESPONSE_SUCCESS in resp_str:
                log.debug("Reset HCI")
                ret_val = True
            else:
                log.debug("*** Reset HCI Response Error! ***")
                ret_val = False
        else:
            log.critical("*** Reset HCI Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def _set_parameter(self, parameter, value=""):
        """
        Utility function to set a parameter
        :param: parameter: the parameter to set :type: HardwareConfigParameters
        :param value: text to set, 15-characters max :type: string
        :return: True if set command is successful, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            if parameter is HardwareConfigParameters.ASSEMBLY_PART_NO:
                cmd_str = self._SET_ASSEMBLY_PART_NO_CMD
                cmd_success = self._SET_ASSEMBLY_PART_NO_SUCCESS
            elif parameter is HardwareConfigParameters.ASSEMBLY_REVISION_NO:
                cmd_str = self._SET_ASSEMBLY_REVISION_NO_CMD
                cmd_success = self._SET_ASSEMBLY_REVISION_NO_SUCCESS
            elif parameter is HardwareConfigParameters.ASSEMBLY_SERIAL_NO:
                cmd_str = self._SET_ASSEMBLY_SERIAL_NO_CMD
                cmd_success = self._SET_ASSEMBLY_SERIAL_NO_SUCCESS
            elif parameter is HardwareConfigParameters.ASSEMBLY_BUILD_BATCH_NO:
                cmd_str = self._SET_ASSEMBLY_BUILD_BATCH_NO_CMD
                cmd_success = self._SET_ASSEMBLY_BUILD_BATCH_NO_SUCCESS
            else:
                log.critical("Set HCI Parameter - Invalid Parameter")
                return False

            cmd_str += value.encode("UTF-8")
            cmd_str += self._SET_CMD_END
            log.debug(b"#SHCI cmd: " + cmd_str)
            serial_port.write(bytes(cmd_str))

            resp_str = serial_port.read_until(self._SET_CMD_RESPONSE_END)
            log.debug(b"#SHCI cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if self._SET_CMD_RESPONSE_END in resp_str and cmd_success in resp_str:
                log.debug("Set {}: {}".format(PARAMETER_NAMES[parameter.value], value))
                ret_val = True
            else:
                log.debug("*** Set {} Response Error! ***".format(PARAMETER_NAMES[parameter.value]))
                ret_val = False
        else:
            log.critical("*** Set {} Failed to Open Serial Port {}! ***".format(PARAMETER_NAMES[parameter.value],
                                                                                self._com_port))
            raise SystemExit(-1)

        return ret_val

    def set_assembly_part_no(self, assembly_part_no):
        """
        Set the Assembly Part No field
        :param assembly_part_no: text to set, 15-characters max :type: string
        :return: True if set command is successful, else False
        """
        return self._set_parameter(HardwareConfigParameters.ASSEMBLY_PART_NO, assembly_part_no[:14])

    def set_assembly_revision_no(self, assembly_revision_no):
        """
        Set the Assembly Revision No field
        :param assembly_revision_no: text to set, 15-characters max :type: string
        :return: True if set command is successful, else False
        """
        return self._set_parameter(HardwareConfigParameters.ASSEMBLY_REVISION_NO, assembly_revision_no[:14])

    def set_assembly_serial_no(self, assembly_serial_no):
        """
        Set the Assembly Serial No field
        :param assembly_serial_no: text to set, 15-characters max :type: string
        :return: True if set command is successful, else False
        """
        return self._set_parameter(HardwareConfigParameters.ASSEMBLY_SERIAL_NO, assembly_serial_no[:14])

    def set_assembly_build_batch_no(self, assembly_build_batch_no):
        """
        Set the Assembly Build Batch No field
        :param assembly_build_batch_no: text to set, 15-characters max :type: string
        :return: True if set command is successful, else False
        """
        return self._set_parameter(HardwareConfigParameters.ASSEMBLY_BUILD_BATCH_NO, assembly_build_batch_no[:14])

    def get_hci(self):
        """
        Retrieves the HCI information
        :return: [0] True, if command successful, else False, [1] byte array of read HCI data
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_HCI_CMD)
            resp_str = serial_port.read_until(self._GET_HCI_RESPONSE_END)
            log.debug(b"HCI cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_HCI_RESPONSE_END in resp_str:
                hci_data = resp_str[resp_str.find(b"Hardware Configuration Information:"):resp_str.find(b"!HCI")]
                ret_val = True
            else:
                log.debug("*** Get HCI Response Error! ***")
                hci_data = b""
                ret_val = False
        else:
            log.critical("*** Get HCI Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val, hci_data

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
