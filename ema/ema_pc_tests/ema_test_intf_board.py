#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0225-00 software running
on a KT-000-0151-00 EMA Test Interface Board NUCLEO-L432KC
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

# Third-party imports -----------------------------------------------
from serial import Serial
from serial import SerialException

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
class EmaTestInterfaceBoard:
    """
    Class for wrapping up the interface to the EMA Test Interface board
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT_DEFAULT = 2
    _TEST_STRING = b"The quick brown fox jumped over the lazy dog!"
    _POWER_OFF_RESPONSE_START = b"Toggling Power Off pin - "
    _POWER_OFF_RESPONSE_END = b"\r\n"
    _POWER_OFF_RESPONSE_OFF = b"OFF"
    _POWER_OFF_RESPONSE_ON = b"ON"
    _PPS_RESPONSE_START = b"1PPS Output "
    _PPS_RESPONSE_END = b"...\r\n"
    _PPS_RESPONSE_DISABLE = b"Disabled"
    _PPS_RESPONSE_ENABLE = b"Enabled"
    _RF_MUTE_RESPONSE_START = b"Toggling RF Mute pin - "
    _RF_MUTE_RESPONSE_END = b"\r\n"
    _RF_MUTE_RESPONSE_UNMUTE = b"UNMUTE"
    _RF_MUTE_RESPONSE_MUTE = b"MUTE"
    _UART_ECHO_RESPONSE_START = b"UART echo "
    _UART_ECHO_RESPONSE_END = b"...\r\n"
    _UART_ECHO_RESPONSE_ENABLE_END = b"u"
    _UART_ECHO_RESPONSE_DISABLE = b"Disabled"
    _UART_ECHO_RESPONSE_ENABLE = b"Enabled"

    def __init__(self, com_port, rx_timeout=_RX_TIMEOUT_DEFAULT):
        """
        Class constructor
        :param: COM port associated with the interface :type: string
        :return: None
        """
        self._com_port = com_port
        self._rx_timeout = rx_timeout

    def _open_com_port(self, com_port):
        """
        :param com_port: COM port to open :type: string
        :return: serial object if COM port opened, else None
        """
        try:
            sp = Serial(com_port, self._BAUD_RATE, timeout=self._rx_timeout,
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

    def set_rx_timeout(self, rx_timeout):
        '''
        :param rx_timeout: receive timeout in seconds to use when waiting for UART responses
        :return:
        '''
        self._rx_timeout = rx_timeout

    def set_power_off(self, power_off=False):
        """
        :param power_off: True to assert POWER_OFF_N signal, False to de-assert
        :return: True if operation successful, else False
        """
        ret_val = True
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            if power_off:
                wanted_resp = self._POWER_OFF_RESPONSE_START + \
                              self._POWER_OFF_RESPONSE_OFF + \
                              self._POWER_OFF_RESPONSE_END
                unwanted_resp = self._POWER_OFF_RESPONSE_START + \
                                self._POWER_OFF_RESPONSE_ON + \
                                self._POWER_OFF_RESPONSE_END
            else:
                wanted_resp = self._POWER_OFF_RESPONSE_START + \
                              self._POWER_OFF_RESPONSE_ON + \
                              self._POWER_OFF_RESPONSE_END
                unwanted_resp = self._POWER_OFF_RESPONSE_START + \
                                self._POWER_OFF_RESPONSE_OFF + \
                                self._POWER_OFF_RESPONSE_END

            resp_str = self._toggle_power_off(serial_port)

            if resp_str != wanted_resp and resp_str == unwanted_resp:
                # Need to toggle the signal again to get to the wanted state
                if self._toggle_power_off(serial_port) != wanted_resp:
                    ret_val = False
            elif resp_str != wanted_resp:
                ret_val = False

            self._close_com_port(serial_port)
        else:
            ret_val = False

        return ret_val

    def _toggle_power_off(self, serial_port):
        """
        :param serial_port: COM port to use :type Serial
        :return: response bytes from serial_port
        """
        serial_port.write(b"^o")
        resp_str = serial_port.read_until(self._POWER_OFF_RESPONSE_START)
        resp_str += serial_port.read_until(self._POWER_OFF_RESPONSE_END)
        return resp_str

    def set_pps(self, enable=False):
        """
        :param enable: True to enable PPS signal, False to disable
        :return: True if operation successful, else False
        """
        ret_val = True
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            if enable:
                wanted_resp = self._PPS_RESPONSE_START + \
                              self._PPS_RESPONSE_ENABLE + \
                              self._PPS_RESPONSE_END
                unwanted_resp = self._PPS_RESPONSE_START + \
                                self._PPS_RESPONSE_DISABLE + \
                                self._PPS_RESPONSE_END
            else:
                wanted_resp = self._PPS_RESPONSE_START + \
                              self._PPS_RESPONSE_DISABLE + \
                              self._PPS_RESPONSE_END
                unwanted_resp = self._PPS_RESPONSE_START + \
                                self._PPS_RESPONSE_ENABLE + \
                                self._PPS_RESPONSE_END

            resp_str = self._toggle_pps(serial_port)

            if resp_str != wanted_resp and resp_str == unwanted_resp:
                # Need to toggle the signal again to get to the wanted state
                if self._toggle_pps(serial_port) != wanted_resp:
                    ret_val = False
            elif resp_str != wanted_resp:
                ret_val = False

            self._close_com_port(serial_port)
        else:
            ret_val = False

        return ret_val

    def _toggle_pps(self, serial_port):
        """
        :param serial_port: COM port to use :type Serial
        :return: response bytes from serial_port
        """
        serial_port.write(b"^p")
        resp_str = serial_port.read_until(self._PPS_RESPONSE_START)
        resp_str += serial_port.read_until(self._PPS_RESPONSE_END)
        return resp_str

    def set_rf_mute(self, rf_mute=False):
        """
        :param rf_mute: True to assert RF_MUTE_N signal, False to de-assert
        :return: True if operation successful, else False
        """
        ret_val = True
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            if rf_mute:
                wanted_resp = self._RF_MUTE_RESPONSE_START + \
                              self._RF_MUTE_RESPONSE_MUTE + \
                              self._RF_MUTE_RESPONSE_END
                unwanted_resp = self._RF_MUTE_RESPONSE_START + \
                                self._RF_MUTE_RESPONSE_UNMUTE + \
                                self._RF_MUTE_RESPONSE_END
            else:
                wanted_resp = self._RF_MUTE_RESPONSE_START + \
                              self._RF_MUTE_RESPONSE_UNMUTE + \
                              self._RF_MUTE_RESPONSE_END
                unwanted_resp = self._RF_MUTE_RESPONSE_START + \
                                self._RF_MUTE_RESPONSE_MUTE + \
                                self._RF_MUTE_RESPONSE_END

            resp_str = self._toggle_rf_mute(serial_port)

            if resp_str != wanted_resp and resp_str == unwanted_resp:
                # Need to toggle the signal again to get to the wanted state
                if self._toggle_rf_mute(serial_port) != wanted_resp:
                    ret_val = False
            elif resp_str != wanted_resp:
                ret_val = False

            self._close_com_port(serial_port)
        else:
            ret_val = False

        return ret_val

    def _toggle_rf_mute(self, serial_port):
        """
        :param serial_port: COM port to use :type Serial
        :return: response bytes from serial_port
        """
        serial_port.write(b"^r")
        resp_str = serial_port.read_until(self._RF_MUTE_RESPONSE_START)
        resp_str += serial_port.read_until(self._RF_MUTE_RESPONSE_END)
        return resp_str

    def set_uart_echo(self, enable=False):
        """
        :param enable: True to enable UART echo, False to disable
        :return: True if operation successful, else False
        """
        ret_val = True
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            if enable:
                wanted_resp = self._UART_ECHO_RESPONSE_START + \
                              self._UART_ECHO_RESPONSE_ENABLE + \
                              self._UART_ECHO_RESPONSE_END
                unwanted_resp = self._UART_ECHO_RESPONSE_START + \
                                self._UART_ECHO_RESPONSE_DISABLE + \
                                self._UART_ECHO_RESPONSE_END
            else:
                wanted_resp = self._UART_ECHO_RESPONSE_START + \
                              self._UART_ECHO_RESPONSE_DISABLE + \
                              self._UART_ECHO_RESPONSE_END
                unwanted_resp = self._UART_ECHO_RESPONSE_START + \
                                self._UART_ECHO_RESPONSE_ENABLE + \
                                self._UART_ECHO_RESPONSE_END

            resp_str = self._toggle_uart_echo(serial_port)

            if resp_str[-len(wanted_resp):] != wanted_resp and \
                    resp_str[-len(unwanted_resp):] == unwanted_resp:
                # Need to toggle the signal again to get to the wanted state
                if self._toggle_uart_echo(serial_port)[-len(wanted_resp):] != wanted_resp:
                    ret_val = False

                # The command 'u' character will have been echoed so remove
                # it from the buffer
                if enable:
                    ret_val = (serial_port.read_until(self._UART_ECHO_RESPONSE_ENABLE_END) ==
                               self._UART_ECHO_RESPONSE_ENABLE_END)

            elif resp_str != wanted_resp:
                ret_val = False

            self._close_com_port(serial_port)
        else:
            ret_val = False

        return ret_val

    def _toggle_uart_echo(self, serial_port):
        """
        :param serial_port: COM port to use :type Serial
        :return: response bytes from serial_port
        """
        serial_port.write(b"^u")
        resp_str = serial_port.read_until(self._UART_ECHO_RESPONSE_START)
        resp_str += serial_port.read_until(self._UART_ECHO_RESPONSE_END)
        return resp_str

    def uart_echo_test(self):
        """
        :return: Return True if test passes, else False
        """
        test_pass = False
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._TEST_STRING)
            log.debug(b"Test string: " + self._TEST_STRING)
            resp_str = serial_port.read_until(self._TEST_STRING)
            log.debug(b"Echo response: " + resp_str)
            test_pass = (resp_str == self._TEST_STRING)

        return test_pass

    def uart_send_command(self, command, verbose=False):
        """
        :return: Return array of response lines if command succeeds, else an empty array
        """
        ret_val = []
        serial_port = self._open_com_port(self._com_port)
        command = command.rstrip().encode("utf-8") + b"\n"
        if serial_port is not None:
            serial_port.write(command)
            while True:
                r = serial_port.read_until(b"\n")
                if r:
                    r = r.decode("utf-8", errors="ignore")
                    ret_val.append(r)
                    if verbose:
                        print(r, end="", flush=True)
                else:
                    break
            self._close_com_port(serial_port)
        return ret_val


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
