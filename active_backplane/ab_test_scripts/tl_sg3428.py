#!/usr/bin/env python3
"""
Class that encapsulates the serial command line interface to the tp-link TL-SG3428 managed switch.
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
from time import sleep

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
class TLSG3428:
    """
    Class for wrapping up the serial command line interface to the tp-link TL-SG3428 managed switch
    """
    MAX_PORT_NO = 28

    _BAUD_RATE = 38400
    _RX_TIMEOUT = 1.0
    _CMD_END = b"\r"
    _CMD_PROMPT = b"TL-SG3428#"
    _BAD_CMD = b"Error: Bad command"

    _LOGOUT_CMD = b"logout"
    _LOGOUT_SUCCESS = b"User:"
    _LOGIN_USER = b"admin"
    _LOGIN_USER_SUCCESS = b"Password:"
    _LOGIN_PWD = b"kcematest"
    _LOGIN_PWD_SUCCESS = b"TL-SG3428>"

    _CONFIG_ENABLE_CMD = b"enable"
    _CONFIG_ENABLE_SUCCESS = _CMD_PROMPT

    _CONFIG_CMD = b"configure"
    _CONFIG_PROMPT = b"TL-SG3428(config)#"
    _IF_CONFIG_SELECT_CMD = b"interface gigabitEthernet 1/0/"
    _IF_CONFIG_ENABLE_CMD = b"no shutdown"
    _IF_CONFIG_DISABLE_CMD = b"shutdown"
    _IF_CONFIG_EXIT_CMD = b"end"
    _IF_CONFIG_PROMPT = b"TL-SG3428(config-if)#"

    def __init__(self, com_port=None):
        """
        Class constructor
        :param com_port: optional parameter COM port associated with the interface :type string
        :return N/A
        """
        self._serial_port = None
        self._com_port = com_port
        if com_port is not None:
            self.open_com_port(com_port)

    def __repr__(self):
        """ :return string representing the class :type string """
        return "TLSG3428({!r})".format(self._com_port)

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

    def port_enable(self, port, enable, sync_cmd_prompt=True):
        """
        Enable or disable the specified port
        :param port: port number in range 1..self.MAX_PORT_NO :type integer
        :param enable: True to enable, False to disable :type boolean
        :param sync_cmd_prompt: if set to True call to synchronise with switch CLI will be made :type boolean
        """
        if not isinstance(port, int) or not isinstance(enable, bool) or not isinstance(sync_cmd_prompt, bool):
            raise ValueError("Invalid parameter type!")

        if port < 1 or port > self.MAX_PORT_NO:
            raise ValueError("Invalid port number! - valid range 1 to {}".format(self.MAX_PORT_NO))

        if self._serial_port is not None:
            # Logout/synchronise command prompt
            if sync_cmd_prompt:
                self._synchronise_cmd_prompt()

            # Login
            self._send_cmd(self._LOGIN_USER, self._LOGIN_USER_SUCCESS)
            self._send_cmd(self._LOGIN_PWD, self._LOGIN_PWD_SUCCESS)

            # Enable Configuration Mode
            self._send_cmd(self._CONFIG_ENABLE_CMD, self._CONFIG_ENABLE_SUCCESS)
            self._send_cmd(self._CONFIG_CMD, self._CONFIG_PROMPT)

            # Enable/disable the specified port
            self._send_cmd(self._IF_CONFIG_SELECT_CMD + bytes(str(port), "UTF-8"), self._IF_CONFIG_PROMPT)

            if enable:
                self._send_cmd(self._IF_CONFIG_ENABLE_CMD, self._IF_CONFIG_PROMPT)
            else:
                self._send_cmd(self._IF_CONFIG_DISABLE_CMD, self._IF_CONFIG_PROMPT)

            # Exit Configuration Mode and Logout
            self._send_cmd(self._IF_CONFIG_EXIT_CMD, self._CMD_PROMPT)
            self._send_cmd(self._LOGOUT_CMD, self._LOGOUT_SUCCESS)
        else:
            raise RuntimeError("Serial port is not open!")

    def _synchronise_cmd_prompt(self):
        """
        Attempt to synchronise the command prompt at the user login prompt.

        Note, this method isn't completely exhaustive of all potential scenarios, it covers
        getting back to the login prompt from scenarios associated with using this driver.

        As a fail-safe the serial command line logs out after 3-minutes of inactivity
        @return: None
        """
        # Send <Enter> then take appropriate synchronisation action based on the response
        self._serial_port.read_all()
        self._serial_port.write(b"\r")
        sleep(1.0)
        resp_str = self._serial_port.read_all()

        if resp_str.find(self._LOGOUT_SUCCESS) != -1:
            # Already synchronised
            pass
        elif resp_str.find(self._LOGIN_USER_SUCCESS) != -1:
            # At password entry prompt, enter dummy password to return to user entry prompt
            self._serial_port.write(b"r")
            self._serial_port.read_until(self._LOGOUT_SUCCESS)
        elif resp_str.find(self._LOGIN_PWD_SUCCESS) != -1:
            # Logged in, configuration mode not enabled, enabled configuration mode then logout
            self._serial_port.write(b"enable\rlogout\r")
            self._serial_port.read_until(self._LOGOUT_SUCCESS)
        elif resp_str.find(self._CMD_PROMPT) != -1:
            # Logged in, configuration mode enabled, logout to return to user entry prompt
            self._serial_port.write(b"logout\r")
            self._serial_port.read_until(self._LOGOUT_SUCCESS)
        elif resp_str.find(self._CONFIG_PROMPT) != -1 or resp_str.find(self._IF_CONFIG_PROMPT) != -1:
            # Logged in at configuration menu, end configuration and logout
            self._serial_port.write(b"end\rlogout\r")
            self._serial_port.read_until(self._LOGOUT_SUCCESS)

    def _send_cmd(self, cmd, resp):
        """
        Send a serial command and check for expected response
        @param cmd: command to send @type: bytes
        @param resp:
        @return: None, a RuntimeError is raised if the expected response isn't found
        """
        cmd_str = cmd + self._CMD_END
        self._serial_port.write(cmd_str)

        resp_str = self._serial_port.read_until(resp)
        log.debug(b"TL-SG3428 cmd Expected: " + resp + b"; Received: " + resp_str)

        if resp_str.find(resp) == -1 or resp_str.find(self._BAD_CMD) != -1:
            raise RuntimeError(b"TL-SG3428 Command Failed: " + cmd + b"; Response: " + resp_str)


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
