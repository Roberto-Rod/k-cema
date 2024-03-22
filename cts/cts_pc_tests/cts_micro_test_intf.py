#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0xx-00 Integrated CTS
Digital Board Test Utility software running on the KT-000-0206-00 Integrated
CTS Digital Board STM32 microcontroller.

Software compatibility:
- KT-956-0xxx-00 K-CEMA Integrated CTS Digital Board Test Utility V1.0.0 onwards
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
class CtsMicroGpoSignals(Enum):
    """ Enumeration class for GPO signals """
    ETH_PHY_LED_EN = 0
    RX_PATH_3V3_IF_EN = 1
    TX_PATH_3V3_TX_EN = 2
    TX_PATH_5V0_TX_EN = 3
    ETH_PHY_RESET_N = 4


class CtsMicroIfPaths(Enum):
    """ Enumeration class for IF paths"""
    IF0_916_917_MHZ = 0
    IF1_910_920_MHZ = 1
    IF2_2305_2315_MHZ = 2
    IF3_2350_2360_MHZ = 3


class CtsMicroAdcSampleTime(Enum):
    """ Enumeration class for ADC Sample Times """
    ADC_3_CYCLES = 0
    ADC_15_CYCLES = 1
    ADC_28_CYCLES = 2
    ADC_56_CYCLES = 3
    ADC_84_CYCLES = 4
    ADC_112_CYCLES = 5
    ADC_144_CYCLES = 6
    ADC_480_CYCLES = 7


class CtsMicroTestInterface:
    """
    Class for wrapping up the interface to the Integrated CTS Test Jig Utility Interface
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _GET_ADC_CMD = b"$ADC"
    _GET_ADC_CMD_RESP_END = b"!ADC\r\n"
    _GET_TEMP_CMD = b"$TMP"
    _GET_TEMP_RESP_END = b"!TMP\r\n"
    _GET_LOOP_BACK_TEST_CMD = b"$LBT"
    _GET_LOOP_BACK_TEST_RESP_END = b"!LBT"
    _GET_LOOP_BACK_TEST_PASS_RESULT = b"PASS - Overall Test Result"
    _SET_GPO_CMD = b"#GPO"
    _SET_GPO_RESP_END = b">GPO\r\n"
    _SET_GPO_ASSERT_SIGNAL_SUCCESS = b" set to: "
    _GET_PPS_INPUT_DETECTED_CMD = b"$PPSD"
    _GET_PPS_INPUT_DETECTED_RESP_END = b"!PPSD"
    _GET_PPS_INPUT_DETECTED_RESPONSE = b"1PPS detected"
    _SET_IF_PATH_CMD = b"#IFP"
    _SET_IF_PATH_RESP_END = b">IFP"
    _SET_IF_PATH_SUCCESS = b"Set IF path to "
    _GET_RF_DETECTOR_CMD = b"$RFDT"
    _GET_RF_DETECTOR_RESP_END = b"!RFDT"
    _GET_MAC_ADDRESS_CMD = b"$MAC"
    _GET_MAC_ADDRESS_RESP_END = b"!MAC\r\n"
    _GET_MAC_ADDRESS_RESPONSE = b"MAC address: "

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
        return "CtsTestJigInterface({!r})".format(self._com_port)

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
        Read the STM32s ADC data
        :return [0]: True if ADC read, else False
        :return [1]: Dictionary of ADC data {"channel name": channel value, ...} :type OrderedDict
        """
        ret_val = False
        adc_data = OrderedDict()

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_ADC_CMD + self._CMD_END)
            resp_str = self._serial_port.read_until(self._GET_ADC_CMD_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_ADC_CMD_RESP_END in resp_str:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 3:
                        adc_data[" ".join(split_line[2:])] = int(split_line[0])
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, adc_data

    def get_temperature(self):
        """
        Query STM32 temperature
        :return: battery temperature, -255 if read fails :type integer
        """
        temperature = -255

        if self._serial_port is not None:
            self._serial_port.write(self._GET_TEMP_CMD + self._CMD_END)
            resp_str = self._serial_port.read_until(self._GET_TEMP_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_TEMP_RESP_END in resp_str:
                for a_line in resp_str.splitlines():
                    if b"Temperature:" in a_line:
                        temperature = int(a_line.split()[-1])
        else:
            raise RuntimeError("Serial port is not open!")

        return temperature

    def get_loop_back_test(self):
        """
        Command a loop back test and return the result
        :return: True if the loop back test passes, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_LOOP_BACK_TEST_CMD + self._CMD_END)
            resp_str = self._serial_port.read_until(self._GET_LOOP_BACK_TEST_RESP_END)

            # Was the command response terminator found or did it timeout, did the loop back test pass?
            ret_val = self._GET_LOOP_BACK_TEST_RESP_END in resp_str and self._GET_LOOP_BACK_TEST_PASS_RESULT in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_gpo_signal(self, gpo_signal,  set_value):
        """
        Assert/de-assert the specified GPO signal
        :param gpo_signal: GPO signal to assert/de-assert :type CtsMicroGpoSignals
        :param set_value: True to set signal high, False to set signal low
        :return: True if successful, else False
        """
        if gpo_signal not in CtsMicroGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_GPO_CMD + " {} {}".format(gpo_signal.value, 1 if set_value else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._CMD_END)
            resp_str = self._serial_port.read_until(self._SET_GPO_RESP_END)

            ret_val = (self._SET_GPO_RESP_END in resp_str and self._SET_GPO_ASSERT_SIGNAL_SUCCESS in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_pps_detected(self):
        """
        Check if a PPS input is being detected
        :return: [0] True if PPS detected, else False
        :return: [1] PPS delta in ms, -1 if no PPS detected
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_PPS_INPUT_DETECTED_CMD + self._CMD_END)
            resp_str = self._serial_port.read_until(self._GET_PPS_INPUT_DETECTED_RESP_END)

            # Was the command response terminator found or did it timeout?
            ret_val = resp_str.find(self._GET_PPS_INPUT_DETECTED_RESP_END) != -1 and \
                      resp_str.find(self._GET_PPS_INPUT_DETECTED_RESPONSE) != -1

            pps_delta_ms = -1
            if ret_val:
                for a_line in resp_str.splitlines():
                    if a_line.find(self._GET_PPS_INPUT_DETECTED_RESPONSE) != -1:
                        pps_delta_ms = int(a_line.decode("UTF-8").split()[-2])
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, pps_delta_ms

    def set_if_path(self, if_path):
        """
        Setthe IF path to the specfified value.  The RX +3V3 IF supply rail must be set separately.
        :param if_path: GPO signal to assert/de-assert :type CtsMicroIfPaths
        :return: True if successful, else False
        """
        if if_path not in CtsMicroIfPaths:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_IF_PATH_CMD + " {}".format(if_path.value).encode("UTF-8") + self._CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_IF_PATH_RESP_END)

            ret_val = (self._SET_IF_PATH_RESP_END in resp_str and self._SET_IF_PATH_SUCCESS in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_rf_detector(self, dwell_time_100_us, sample_time=None):
        """
        Reads the RF detector voltage
        :param dwell_time_100_us: dwell time before reading the RF detector, resolution 0100 us :type Integer
        :return: [0] raw ADC value :type Integer
        :return: [1] voltage, resolution mV :type Integer
        """
        dwell_time_100_us = int(dwell_time_100_us)
        raw_adc_value = -4095
        voltage_mv = -3300

        if sample_time is not None:
            if type(sample_time) is not CtsMicroAdcSampleTime:
                raise TypeError("sample_time must be type CtsMicroAdcSampleTime")

        if self._serial_port is not None:
            if sample_time is not None:
                cmd_str = self._GET_RF_DETECTOR_CMD + \
                          " {}".format(dwell_time_100_us).encode("UTF-8") + \
                          " {}".format(sample_time.value).encode("UTF-8") + \
                          self._CMD_END
            else:
                cmd_str = self._GET_RF_DETECTOR_CMD + " {}".format(dwell_time_100_us).encode("UTF-8") + self._CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._GET_RF_DETECTOR_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_RF_DETECTOR_RESP_END in resp_str:
                for a_line in resp_str.splitlines():
                    if b"Raw ADC value" in a_line:
                        raw_adc_value = int(a_line.split()[0])
                    if b"Voltage (mV)" in a_line:
                        voltage_mv = int(a_line.split()[0])
        else:
            raise RuntimeError("Serial port is not open!")

        return raw_adc_value, voltage_mv

    def get_mac_address(self):
        """
        Check if a PPS input is being detected
        :return: string representing the MAC address :type String
        """
        mac_address = ""

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_MAC_ADDRESS_CMD + self._CMD_END)
            resp_str = self._serial_port.read_until(self._GET_MAC_ADDRESS_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_MAC_ADDRESS_RESP_END in resp_str:
                for a_line in resp_str.splitlines():
                    if self._GET_MAC_ADDRESS_RESPONSE in a_line:
                        mac_address = a_line.decode("UTF-8").split()[-1]
        else:
            raise RuntimeError("Serial port is not open!")

        return mac_address


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
