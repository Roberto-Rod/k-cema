#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0262-00 DRCU & Fill Device
Test Jig Utility software running on the KT-000-0207-00 DRCU & Fill Device Test
Jig STM32 microcontroller.

Software compatibility:
- KT-956-0262-00 K-CEMA DRCU & Fill Device Test Jig Utility V1.0.0 onwards
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
from collections import OrderedDict
from enum import Enum
import logging

# Third-party imports -----------------------------------------------
from serial import Serial

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
class DrcuFdTestJigGpoSignals(Enum):
    """ Enumeration class for GPO signals """
    CSM_1PPS_DIRECTION = 0
    SOM_SYS_RESET = 1
    SOM_SD_BOOT_ENABLE = 2


class DrcuFdTestJigInterface:
    """
    Class for wrapping up the interface to the CSM Microcontroller Test Jig Utility Interface
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _GET_ADC_CMD = b"$ADC"
    _GET_ADC_CMD_SUCCESS = b"!ADC\r\n"
    _SET_GPO_CMD = b"#GPO"
    _SET_GPO_CMD_SUCCESS = b">GPO\r\n"
    _SET_GPO_ASSERT_SIGNAL_RESP = b" set to: "
    _GET_GPI_CMD = b"$GPI"
    _GET_GPI_CMD_SUCCESS = b"!GPI\r\n"
    _GET_PPS_INPUT_DETECTED_CMD = b"$PPSD"
    _GET_PPS_INPUT_DETECTED_CMD_SUCCESS = b"!PPSD"
    _GET_PPS_INPUT_DETECTED_RESP = b"1PPS detected"
    _SET_PPS_OUTPUT_ENABLE_CMD = b"#PPSE"
    _SET_PPS_OUTPUT_ENABLE_CMD_SUCCESS = b">PPSE"
    _SET_PPS_OUTPUT_ENABLE_RESP = b"1PPS Enabled"
    _SET_PPS_OUTPUT_DISABLE_RESP = b"1PPS Disabled"

    def __init__(self, com_port=None):
        """
        Class constructor
        :param: optional parameter COM port associated with the interface :type string
        :return: N/A
        """
        self._serial_port = None
        self._com_port = com_port
        if com_port is not None:
            self.open_com_port(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "DrcuFdTestJigInterface({!r})".format(self._com_port)

    def __del__(self):
        """ Class destructor - close the serial port """
        self.close_com_port()

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the serial port"""
        self.close_com_port()

    def open_com_port(self, com_port):
        """
        Opens the specified serial port
        :param com_port: COM port to open :type string
        :return: N/A
        """
        self._serial_port = Serial(com_port, self._BAUD_RATE, timeout=self._RX_TIMEOUT,
                                   xonxoff=False, rtscts=False, dsrdtr=False)
        log.debug("Opened COM port {}".format(com_port))
        self._com_port = com_port

    def close_com_port(self):
        """ Closes _serial_port COM port if it is open """
        if self._serial_port is not None:
            log.debug("Closing COM port {}".format(self._serial_port.name))
            self._serial_port.close()
        self._serial_port = None
        self._com_port = ""

    def _synchronise_cmd_prompt(self):
        """
        Send dummy command string "\r" and read until a "?\r\n"
        string is returned, unknown command.
        :return: N/A
        """
        self._serial_port.write(b"\r")
        self._serial_port.read_until(self._CMD_UNKNOWN, self._RX_TIMEOUT)

    def get_adc_data(self):
        """
        Read the test jig's ADC data
        :return [0]: True if ADC read, else False
        :return [1]: Dictionary of ADC data {"channel name": channel value, ...} :type OrderedDict
        """
        ret_val = False
        adc_data = OrderedDict()

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_ADC_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_ADC_CMD_SUCCESS)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_ADC_CMD_SUCCESS) != -1:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 3:
                        adc_data[" ".join(split_line[2:])] = int(split_line[0])
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, adc_data

    def assert_gpo_signal(self, gpo_signal,  assert_value):
        """
        Assert/de-assert the specified GPO signal
        :param gpo_signal: GPO signal to assert/de-assert :type DrcuFdTestJigGpoSignals
        :param assert_value: Set to True to assert signal, False to de-assert
        :return: True if successful, else False
        """
        if gpo_signal not in DrcuFdTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_GPO_CMD + " {} {}".format(gpo_signal.value,
                                                          1 if assert_value else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_GPO_CMD_SUCCESS)
            ret_val = resp_str.find(self._SET_GPO_CMD_SUCCESS) != -1 and \
                resp_str.find(self._SET_GPO_ASSERT_SIGNAL_RESP) != -1
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_gpi_state(self):
        """
        Read the state of the test jig's general purpose inputs
        :return [0]: True if GPI read, else False
        :return [1]: Dictionary of GPI data {"signal name": signal value, ...} :type OrderedDict
        """
        ret_val = False
        gpi_data = OrderedDict()

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_CMD_SUCCESS)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_GPI_CMD_SUCCESS) != -1:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 2:
                        gpi_data[" ".join(split_line[2:])] = int(split_line[0])
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, gpi_data

    def get_pps_detected(self):
        """
        Check if a PPS input is being detected on the selected source
        :return: [0] True if PPS detected, else False
                 [1] PPS delta in ms, -1 if no PPS detected
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_PPS_INPUT_DETECTED_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_PPS_INPUT_DETECTED_CMD_SUCCESS)

            # Was the command response terminator found or did it timeout?
            ret_val = resp_str.find(self._GET_PPS_INPUT_DETECTED_CMD_SUCCESS) != -1 and \
                resp_str.find(self._GET_PPS_INPUT_DETECTED_RESP) != -1

            pps_delta_ms = -1
            if ret_val:
                for a_line in resp_str.splitlines():
                    if a_line.find(self._GET_PPS_INPUT_DETECTED_RESP) != -1:
                        pps_delta_ms = int(a_line.decode("UTF-8").split()[-2])
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, pps_delta_ms

    def enable_pps_output(self, enable):
        """
        Enable/disable the PPS output from the test jig NUCLEO board to the CSM Slave interface
        :param enable: Set to True to enable PPS output, False to disable :type Boolean
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_PPS_OUTPUT_ENABLE_CMD + "{}".format(1 if enable else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_PPS_OUTPUT_ENABLE_CMD_SUCCESS)
            ret_val = resp_str.find(self._SET_PPS_OUTPUT_ENABLE_CMD_SUCCESS) != -1 and \
                ((resp_str.find(self._SET_PPS_OUTPUT_ENABLE_RESP) != -1 and enable) or
                 (resp_str.find(self._SET_PPS_OUTPUT_DISABLE_RESP) != -1 and not enable))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
