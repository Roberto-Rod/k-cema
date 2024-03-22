#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0226-00 software running
on a KT-000-0150-00 EMA PCM NTM Test Interface Board NUCLEO-L432KC
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
import re

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
class PcmNtmTestInterfaceBoard:
    """
    Class for wrapping up the interface to the EMA Test Interface board
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _GET_DOP_CMD = b"\r$DOP\r"
    _GET_DOP_RESPONSE_END = b"!DOP\r\n"
    _GET_DOP_RF_MUTE_ASSERTED = b"RF_MUTE_N:\t0"
    _GET_DOP_RF_MUTE_NOT_ASSERTED = b"RF_MUTE_N:\t1"
    _GET_DOP_FAN_ALERT_ASSERTED = b"FAN_ALERT_N:\t0"
    _GET_DOP_FAN_ALERT_NOT_ASSERTED = b"FAN_ALERT_N:\t1"
    _GET_DOP_POWER_FAIL_ASSERTED = b"PFI_N:\t\t0"
    _GET_DOP_POWER_FAIL_NOT_ASSERTED = b"PFI_N:\t\t1"
    _GET_PPS_CMD = b"\r$PPS\r"
    _GET_PPS_RESPONSE_END = b"!PPS\r\n"
    _GET_PPS_DETECTED = b"1PPS detected"
    _GET_PPS_NOT_DETECTED = b"1PPS NOT detected"
    _INITIALISE_FAN_CONTROLLER_CMD = b"\r#INIFAN\r"
    _INITIALISE_FAN_CONTROLLER_RESPONSE_END = b">INIFAN\r\n"
    _INITIALISE_FAN_CONTROLLER_SUCCESS = b"EMC2104 fan controller successfully initialised"
    _GET_FAN_CONTROLLER_TEMP_CMD = b"\r$TMP\r"
    _GET_FAN_CONTROLLER_TEMP_RESPONSE_END = b"!TMP\r\n"
    _PUSH_FAN_CONTROLLER_TEMP_CMD = b"\r#FPT"
    _PUSH_FAN_CONTROLLER_TEMP_CMD_END = b"\r"
    _PUSH_FAN_CONTROLLER_TEMP_RESPONSE_END = b">FPT\r\n"
    _PUSH_FAN_CONTROLLER_TEMP_RESPONSE_SUCCESS = b"Pushed temperature to fan controller"
    _GET_FAN_SPEEDS_CMD = b"\r$FSP\r"
    _GET_FAN_SPEEDS_RESPONSE_END = b"!FSP\r\n"
    _GET_AOP_CMD = b"\r$AOP\r"
    _GET_AOP_RESPONSE_END = b"!AOP\r\n"
    _GET_AOP_3V4_STBY = b"+3V4_STBY\t"
    _GET_AOP_28V = b"+28V_STBY\t"
    _SET_RDAC_CMD = b"\r#RDAC"
    _SET_RDAC_CMD_END = b"\r"
    _SET_RDAC_RESPONSE_END = b">RDAC\r\n"
    _SET_RDAC_RESPONSE_SUCCESS = b"RDAC value set:"
    _SET_50TP_CMD = b"\r#50TP\r"
    _SET_50TP_RESPONSE_END = b">50TP\r\n"
    _SET_50TP_RESPONSE_SUCCESS = b"AD5272 50TP value successfully programmed"

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

    def get_pps_detected(self):
        """
        Query if a 1PPS signal is being detected
        :return: True, if 1PPS detected, else False
        """
        ret_val = False
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_PPS_CMD)
            resp_str = serial_port.read_until(self._GET_PPS_RESPONSE_END)
            log.debug(b"$PPS cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_PPS_RESPONSE_END in resp_str:
                if self._GET_PPS_DETECTED in resp_str:
                    log.debug("PPS detected")
                    ret_val = True
                elif self._GET_PPS_NOT_DETECTED in resp_str:
                    log.debug("PPS NOT detected")
                    ret_val = False
                elif self._GET_PPS_NOT_DETECTED not in resp_str and self._GET_PPS_DETECTED not in resp_str:
                    log.critical("*** Get PPS Response Failed! ***")
                    raise SystemExit(-1)

            else:
                log.critical("*** Get PPS Detected Command Failed! ***")
                raise SystemExit(-1)

        else:
            log.critical("*** Get PPS Detected Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def get_rf_mute_asserted(self):
        """
        Query if the RF_MUTE_N signal is asserted
        :return: True, if signal is asserted, else False
        """
        ret_val = False
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_DOP_CMD)
            resp_str = serial_port.read_until(self._GET_DOP_RESPONSE_END)
            log.debug(b"$DOP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_DOP_RESPONSE_END in resp_str:
                if self._GET_DOP_RF_MUTE_ASSERTED in resp_str:
                    log.debug("RF Mute asserted")
                    ret_val = True
                elif self._GET_DOP_RF_MUTE_NOT_ASSERTED in resp_str:
                    log.debug("RF Mute NOT asserted")
                    ret_val = False
                elif self._GET_DOP_RF_MUTE_ASSERTED not in resp_str and \
                        self._GET_DOP_RF_MUTE_NOT_ASSERTED not in resp_str:
                    log.critical("*** Get RF Mute Asserted Response Failed! ***")
                    raise SystemExit(-1)

            else:
                log.critical("*** Get RF Mute Asserted Command Failed! ***")
                raise SystemExit(-1)

        else:
            log.critical("*** Get FR Mute Asserted Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def get_fan_alert_asserted(self):
        """
        Query if the FAN_ALERT_N signal is asserted
        :return: True, if signal is asserted, else False
        """
        ret_val = False
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_DOP_CMD)
            resp_str = serial_port.read_until(self._GET_DOP_RESPONSE_END)
            log.debug(b"$DOP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_DOP_RESPONSE_END in resp_str:
                if self._GET_DOP_FAN_ALERT_ASSERTED in resp_str:
                    log.debug("Fan Alert asserted")
                    ret_val = True
                elif self._GET_DOP_FAN_ALERT_NOT_ASSERTED in resp_str:
                    log.debug("Fan Alert NOT asserted")
                    ret_val = False
                elif self._GET_DOP_RF_MUTE_ASSERTED not in resp_str and \
                        self._GET_DOP_FAN_ALERT_NOT_ASSERTED not in resp_str:
                    log.critical("*** Get Fan Alert Asserted Response Failed! ***")
                    raise SystemExit(-1)

            else:
                log.critical("*** Get Fan Alert Asserted Command Failed! ***")
                raise SystemExit(-1)

        else:
            log.critical("*** Get FR Mute Asserted Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def get_power_fail_asserted(self):
        """
        Query if the PFI_N signal is asserted
        :return: [0] if command was successful, else False [1] True, if signal is asserted, else False
        """
        ret_val = False
        asserted = False
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_DOP_CMD)
            resp_str = serial_port.read_until(self._GET_DOP_RESPONSE_END)
            log.debug(b"$DOP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_DOP_RESPONSE_END in resp_str:
                if self._GET_DOP_POWER_FAIL_ASSERTED in resp_str:
                    log.debug("Power Fail asserted")
                    asserted = True
                    ret_val = True
                elif self._GET_DOP_POWER_FAIL_NOT_ASSERTED in resp_str:
                    log.debug("Power Fail NOT asserted")
                    asserted = False
                    ret_val = True
                elif self._GET_DOP_POWER_FAIL_ASSERTED not in resp_str and \
                        self._GET_DOP_POWER_FAIL_NOT_ASSERTED not in resp_str:
                    log.critical("*** Get Power Fail Asserted Response Failed! ***")

            else:
                log.critical("*** Get Power Fail Asserted Command Failed! ***")

        else:
            log.critical("*** Get FR Mute Asserted Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val, asserted

    def fan_controller_init(self):
        """
        Send the command to initialise the fan controller
        :return: True if fan controller initialised, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._INITIALISE_FAN_CONTROLLER_CMD)
            resp_str = serial_port.read_until(self._INITIALISE_FAN_CONTROLLER_RESPONSE_END)
            log.debug(b"#INIFAN cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._INITIALISE_FAN_CONTROLLER_RESPONSE_END in resp_str:
                if self._INITIALISE_FAN_CONTROLLER_SUCCESS in resp_str:
                    log.debug("Fan controller successfully initialised")
                    ret_val = True
                else:
                    log.debug("Fan controller NOT initialised")
                    ret_val = False
            else:
                log.critical("*** Initialise Fan Controller Command Failed! ***")
                ret_val = False

        else:
            log.critical("*** Initialise Fan Controller Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def get_fan_controller_temp(self):
        """
        Get the fan controller IC temperature
        :return: temperature if successfully read, else -128
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_FAN_CONTROLLER_TEMP_CMD)
            resp_str = serial_port.read_until(self._GET_FAN_CONTROLLER_TEMP_RESPONSE_END)
            log.debug(b"$TMP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_FAN_CONTROLLER_TEMP_RESPONSE_END) != -1:
                part_str = resp_str[resp_str.find(b"Temperature:"):resp_str.find(b"!TMP")]
                if len(part_str) > 0:
                    temp_str = re.findall(r"\d+", str(part_str))
                    ret_val = int(temp_str[0])
                    log.debug("Fan Controller Temperature: {}".format(ret_val))
                else:
                    log.debug("*** Get Fan Controller Temperature Response Error! ***")
                    ret_val = -128
            else:
                log.debug("*** Get Fan Controller Temperature Response Error! ***")
                ret_val = -128
        else:
            log.critical("*** Get Fan Controller Temperature Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def fan_controller_push_temperature(self, temperature=20):
        """
        Get the fan controller IC temperature
        :param: temperature :type: int
        :return: True if temperature successfully pushed, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            cmd_str = self._PUSH_FAN_CONTROLLER_TEMP_CMD
            cmd_str += str(temperature).encode("Utf-8")
            cmd_str += self._PUSH_FAN_CONTROLLER_TEMP_CMD_END
            log.debug(b"#FPT cmd: " + cmd_str)

            serial_port.write(bytes(cmd_str))
            resp_str = serial_port.read_until(self._PUSH_FAN_CONTROLLER_TEMP_RESPONSE_END)
            log.debug(b"#FPT cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if self._PUSH_FAN_CONTROLLER_TEMP_RESPONSE_END in resp_str and \
                    self._PUSH_FAN_CONTROLLER_TEMP_RESPONSE_SUCCESS in resp_str:
                log.debug("Pushed Fan Controller Temperature: {}".format(temperature))
                ret_val = True
            else:
                log.debug("*** Push Fan Controller Temperature Response Error! ***")
                ret_val = False
        else:
            log.critical("*** Push Fan Controller Temperature Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def get_fan_speeds(self):
        """
        Get the fan speeds from the fan controller
        :return: Tuple containing fan speeds, [0] fan 1, [1] fan 2, values = -1 if read fails
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_FAN_SPEEDS_CMD)
            resp_str = serial_port.read_until(self._GET_FAN_SPEEDS_RESPONSE_END)
            log.debug(b"$FSP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_FAN_SPEEDS_RESPONSE_END in resp_str:
                # Extract Fan Speed 1
                part_str = resp_str[resp_str.find(b"Fan 1 Speed RPM:")+6:resp_str.find(b"Fan 2 Speed RPM:")]
                if len(part_str) > 0:
                    temp_str = re.findall(r"\d+", str(part_str))
                    fan1_spd = int(temp_str[0])
                    log.debug("Fan : {}".format(fan1_spd))
                else:
                    log.debug("*** Get Fan Speeds Response Error! ***")
                    fan1_spd = -1

                # Extract Fan Speed 2
                part_str = resp_str[resp_str.find(b"Fan 2 Speed RPM:")+6:resp_str.find(b"Fan 1 PWM Drive:")]
                if len(part_str) > 0:
                    temp_str = re.findall(r"\d+", str(part_str))
                    fan2_spd = int(temp_str[0])
                    log.debug("Fan 2 Speed: {}".format(fan2_spd))
                else:
                    log.debug("*** Get Fan Speeds Response Error! ***")
                    fan2_spd = -1

            else:
                log.debug("*** Get Fan Speeds Response Error! ***")
                fan1_spd = -1
                fan2_spd = -1
        else:
            log.critical("*** Get Fan Speeds Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return fan1_spd, fan2_spd

    def get_analog_op(self):
        """
        Read the analog outputs
        :return: Tuple containing analogue outputs in mV, [0] +3V4_STBY, [1] +28, values = -1 if read fails
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._GET_AOP_CMD)
            resp_str = serial_port.read_until(self._GET_AOP_RESPONSE_END)
            log.debug(b"$AOP cmd resp: " + resp_str)
            # Was the command response terminator found or did it timeout?
            if self._GET_AOP_RESPONSE_END in resp_str:
                resp_str = resp_str.decode("UTF-8")
                resp_str = resp_str.split("\n")

                # Extract +3V4_STBY value
                rail_3v4_stby = -1
                for astr in resp_str:
                    if "+3V4_STBY" in astr:
                        rail_3v4_stby = int(re.findall(r"\d+", astr.split(":")[1])[0])
                        break

                # Extract +28V value
                rail_28v = -1
                for astr in resp_str:
                    if "+28V" in astr:
                        rail_28v = int(re.findall(r"\d+", astr.split(":")[1])[0])
                        break

            else:
                log.debug("*** Get Analog Outputs Response Error! ***")
                rail_3v4_stby = -1
                rail_28v = -1
        else:
            log.critical("*** Get Analog Outputs Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return rail_3v4_stby, rail_28v

    def set_rdac(self, rdac_val):
        """
        Set the AD7252 digital-pot wiper to the specified RDAC value
        :param rdac_val:
        :return: True if set command is successful, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            cmd_str = self._SET_RDAC_CMD
            cmd_str += str(rdac_val).encode("Utf-8")
            cmd_str += self._SET_RDAC_CMD_END
            log.debug(b"#RDAC cmd: " + cmd_str)

            serial_port.write(bytes(cmd_str))
            resp_str = serial_port.read_until(self._SET_RDAC_RESPONSE_END)
            log.debug(b"#RDAC cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if self._SET_RDAC_RESPONSE_END in resp_str and \
                    self._SET_RDAC_RESPONSE_SUCCESS in resp_str:
                log.debug("Set RDAC: {}".format(rdac_val))
                ret_val = True
            else:
                log.debug("*** Set RDAC Response Error! ***")
                ret_val = False
        else:
            log.critical("*** Set RDAC Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

        return ret_val

    def set_50tp(self):
        """
        Set the AD7252 50TP memory with current digital-pot wiper value
        :return: True if set command is successful, else False
        """
        serial_port = self._open_com_port(self._com_port)

        if serial_port is not None:
            serial_port.write(self._SET_50TP_CMD)
            resp_str = serial_port.read_until(self._SET_50TP_RESPONSE_END)
            log.debug(b"#50TP cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if self._SET_50TP_RESPONSE_END in resp_str and \
                    self._SET_50TP_RESPONSE_SUCCESS in resp_str:
                log.debug("Set 50TP")
                ret_val = True
            else:
                log.debug("*** Set 50TP Response Error! ***")
                ret_val = False
        else:
            log.critical("*** Set 50TP Failed to Open Serial Port {}! ***".format(self._com_port))
            raise SystemExit(-1)

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
