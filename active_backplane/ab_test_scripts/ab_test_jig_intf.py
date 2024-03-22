#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0223-00 Active Backplane Test
Jig Utility software running on the KT-000-0164-00 Active Backplane Test Jig STM32
microcontroller.

Software compatibility:
- KT-956-0223-00 Active Backplane Test Jig Utility V3.0.0
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


class HwConfigInfo:
    """
    Class for encapsulating Hardware Config Information
    """
    hw_version_no = ""
    hw_mod_version_no = ""
    assy_part_no = ""
    assy_rev_no = ""
    assy_serial_no = ""
    assy_build_batch_no = ""
    hw_info_valid = False

    def __init__(self, hw_version_no="", hw_mod_version_no="", assy_part_no="",
                 assy_rev_no="", assy_serial_no="", assy_build_batch_no=""):
        self.hw_version_no = hw_version_no
        self.hw_mod_version_no = hw_mod_version_no
        self.assy_part_no = assy_part_no
        self.assy_rev_no = assy_rev_no
        self.assy_serial_no = assy_serial_no
        self.assy_build_batch_no = assy_build_batch_no

        # If some information was passed assume it's value
        if hw_version_no == hw_mod_version_no == assy_part_no == assy_serial_no == assy_build_batch_no == "":
            self.hw_info_valid = False
        else:
            self.hw_info_valid = True

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "HwConfigInfo({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
                self.hw_version_no, self.hw_mod_version_no, self.assy_part_no, self.assy_rev_no,
                self.assy_serial_no, self.assy_build_batch_no, self.hw_info_valid)


class AbTestJigInterface:
    """
    Class for wrapping up the interface to the Active Backplane Test Jig Utility Interface
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _SET_DCDC_ENABLE_CMD = b"#DCDC"
    _SET_DCDC_ENABLE_END = b">DCDC\r\n"
    _SET_DCDC_ENABLE_ENABLED_SUCCESS = b"Set DCDC to: ON"
    _SET_DCDC_ENABLE_DISABLED_SUCCESS = b"Set DCDC to: OFF"
    _SET_RACK_ADDRESS_CMD = b"#RADR"
    _SET_RACK_ADDRESS_END = b">RADR\r\n"
    _SET_RACK_ADDRESS_HIGH_SUCCESS = b"Set Rack Address to: 1"
    _SET_RACK_ADDRESS_LOW_SUCCESS = b"Set Rack Address to: 0"
    _ASSERT_SYSTEM_RESET_CMD = b"#SRST"
    _ASSERT_SYSTEM_RESET_END = b">SRST\r\n"
    _ASSERT_SYSTEM_RESET_SUCCESS = b"Set System Reset to: TRUE"
    _DEASSERT_SYSTEM_RESET_SUCCESS = b"Set System Reset to: FALSE"
    _SET_PPS_ENABLE_CMD = b"#PPS"
    _SET_PPS_ENABLE_END = b">PPS\r\n"
    _SET_PPS_ENABLE_ENABLED_SUCCESS = b"1PPS Enabled"
    _SET_PPS_ENABLE_DISABLED_SUCCESS = b"1PPS Disabled"
    _GET_HW_CONFIG_INFO_CMD = b"$HCI"
    _GET_HW_CONFIG_INFO_END = b"!HCI\r\n"
    _RESET_HW_CONFIG_INFO_CMD = b"#RHCI"
    _RESET_HW_CONFIG_INFO_END = b">RHCI\r\n"
    _RESET_HW_CONFIG_INFO_SUCCESS = b"Successfully cleared HCI EEPROM"
    _SET_HW_CONFIG_INFO_CMD = b"#SHCI"
    _SET_HW_CONFIG_INFO_END = b">SHCI\r\n"
    _SET_HW_CONFIG_INF_PART_NO_SUCCESS = b"Successfully set parameter [Part No] to"
    _SET_HW_CONFIG_INF_REV_NO_SUCCESS = b"Successfully set parameter [Revision No] to"
    _SET_HW_CONFIG_INF_SERIAL_NO_SUCCESS = b"Successfully set parameter [Serial No] to"
    _SET_HW_CONFIG_INF_BUILD_BATCH_NO_SUCCESS = b"Successfully set parameter [Build Batch No] to"
    _GET_ADC_CMD = b"$ADC"
    _GET_ADC_CMD_SUCCESS = b"!ADC\r\n"
    _GET_ADC_VREFINT_RESP_LINE = b"VREFINT (mV)"
    _GET_ADC_BUT_3V3_RESP_LINE = b"BUT +3V3 (mV)"
    _GET_MAC_ADDRESS_CMD = b"$MAC"
    _GET_MAC_ADDRESS_SUCCESS = b"!MAC\r\n"
    _GET_MAC_ADDRESS_MICRO_RESP_LINE = b"Micro MAC Address:"
    _GET_MAC_ADDRESS_SWITCH_RESP_LINE = b"Switch MAC Address:"

    def __init__(self, com_port=None):
        """
        Class constructor
        :param: optional parameter COM port associated with the interface :type string
        :return: None
        """
        self._serial_port = None
        self._com_port = com_port
        if com_port is not None:
            self.open_com_port(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "AbTestJigInterface({!r})".format(self._com_port)

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
        :return: serial object if COM port opened, a SerialException will be raised if the port cannot be opened
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
        Send dummy command string "DEFINITELY_NOT_A_CMD\r" and read until a "?\r\n"
        string is returned, unknown command.
        :return: None
        """
        self._serial_port.write(b"\r")
        self._serial_port.read_until(self._CMD_UNKNOWN, self._RX_TIMEOUT)

    def set_dcdc_enable(self, enable):
        """
        Enable the board under test DC-DC converter
        :param: enable, True to enable, False to disable :type: boolean
        :return: True if DC-DC converter enable set, else False
        """
        ret_val = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._SET_DCDC_ENABLE_CMD
            if enable:
                cmd_str += "1".encode("Utf-8")
            else:
                cmd_str += "0".encode("Utf-8")
            cmd_str += self._SET_CMD_END
            log.debug(b"#DCDC cmd: " + cmd_str)
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._SET_DCDC_ENABLE_END)
            log.debug(b"#DCDC cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._SET_DCDC_ENABLE_END) != -1 and \
                    (resp_str.find(self._SET_DCDC_ENABLE_ENABLED_SUCCESS) != -1 or
                        resp_str.find(self._SET_DCDC_ENABLE_DISABLED_SUCCESS) != -1):
                log.debug("DC-DC enable state set to: {}".format(enable))
                ret_val = True
            else:
                log.debug("*** Set DC-DC Converter Enable State Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_rack_address(self, high):
        """
        Set the Rack Address input to the board under test
        :param: high, True to set signal high False to set signal low :type: boolean
        :return: True if Rack Address signal set, else False
        """
        ret_val = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._SET_RACK_ADDRESS_CMD
            if high:
                cmd_str += "1".encode("Utf-8")
            else:
                cmd_str += "0".encode("Utf-8")
            cmd_str += self._SET_CMD_END
            log.debug(b"#RADR cmd: " + cmd_str)
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._SET_RACK_ADDRESS_END)
            log.debug(b"#RADR cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._SET_RACK_ADDRESS_END) != -1 and \
                    (resp_str.find(self._SET_RACK_ADDRESS_HIGH_SUCCESS) != -1 or
                        resp_str.find(self._SET_RACK_ADDRESS_LOW_SUCCESS) != -1):
                log.debug("Rack Address set to: {}".format(int(high)))
                ret_val = True
            else:
                log.debug("*** Set Rack Address Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def assert_system_reset(self, reset):
        """
        Assert/deassert the system reset signal to the board under test
        :param: reset, True to assert rest, False to de-assert reset :type: boolean
        :return: True if Rack Address signal set, else False
        """
        ret_val = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._ASSERT_SYSTEM_RESET_CMD
            if reset:
                cmd_str += "1".encode("Utf-8")
            else:
                cmd_str += "0".encode("Utf-8")
            cmd_str += self._SET_CMD_END
            log.debug(b"#SRST cmd: " + cmd_str)
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._ASSERT_SYSTEM_RESET_END)
            log.debug(b"#SRST cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._ASSERT_SYSTEM_RESET_END) != -1 and \
                    (resp_str.find(self._ASSERT_SYSTEM_RESET_SUCCESS) != -1 or
                        resp_str.find(self._DEASSERT_SYSTEM_RESET_SUCCESS) != -1):
                log.debug("Assert System Reset set to: {}".format(reset))
                ret_val = True
            else:
                log.debug("*** Assert System Reset Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_pps_enable(self, enable):
        """
        Enable the test jig 1PPS output to the board under test
        :param: enable, True to enable, False to disable :type: boolean
        :return: True if 1PPS state set, else False
        """
        ret_val = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._SET_PPS_ENABLE_CMD
            if enable:
                cmd_str += "1".encode("Utf-8")
            else:
                cmd_str += "0".encode("Utf-8")
            cmd_str += self._SET_CMD_END
            log.debug(b"#PPS cmd: " + cmd_str)
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._SET_PPS_ENABLE_END)
            log.debug(b"#PPS cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._SET_PPS_ENABLE_END) != -1 and \
                    (resp_str.find(self._SET_PPS_ENABLE_ENABLED_SUCCESS) != -1 or
                        resp_str.find(self._SET_PPS_ENABLE_DISABLED_SUCCESS) != -1):
                log.debug("1PPS enable state set to: {}".format(enable))
                ret_val = True
            else:
                log.debug("*** Set 1PPS Enable State Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_hw_config_info(self):
        """
        Read the board under test's hardware config information, this command exercises the
        board under test's I2C bus so it is advisable to assert the system reset before
        calling this method.
        :return [0]: True if Rack Address signal set, else False
        :return [1]: HwConfigInfo object containing read data, None if the read fails
        """
        ret_val = False
        hci = None

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            log.debug(b"$HCI cmd: " + self._GET_HW_CONFIG_INFO_CMD)
            self._serial_port.write(self._GET_HW_CONFIG_INFO_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._GET_HW_CONFIG_INFO_END)
            log.debug(b"$HCI cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_HW_CONFIG_INFO_END) != -1:
                # Split response by lines then process to extract data
                hci = HwConfigInfo()
                hci_details = [
                    # (search string in response, HwConfigInfo attribute)
                    (b"Hardware Version No: ", "hw_version_no"),
                    (b"Hardware Mod Version No: ", "hw_mod_version_no"),
                    (b"Assembly Part No: ", "assy_part_no"),
                    (b"Assembly Revision No: ", "assy_rev_no"),
                    (b"Assembly Serial No: ", "assy_serial_no"),
                    (b"Assembly Build Date or Batch No: ", "assy_build_batch_no"),
                    (b"Hardware Configuration Information CRC Valid: ", "hw_info_valid")
                ]

                for hci_detail, hci_attr in hci_details:
                    for resp_line in resp_str.splitlines():
                        if hci_detail in resp_line:
                            setattr(hci, hci_attr, str(resp_line.split(b": ")[1], "UTF-8").strip())

                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, hci

    def reset_hw_config_info(self):
        """
        Reset the Hardware Configuration Information
        :return: True if Hardware Configuration Information reset, else False
        """
        ret_val = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._RESET_HW_CONFIG_INFO_CMD + self._SET_CMD_END
            log.debug(b"#RHCI cmd: " + cmd_str)
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._RESET_HW_CONFIG_INFO_END)
            log.debug(b"#RHCI cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._RESET_HW_CONFIG_INFO_END) != -1 and \
                    resp_str.find(self._RESET_HW_CONFIG_INFO_SUCCESS) != -1:
                log.debug("Hardware Configuration Information Reset")
                ret_val = True
            else:
                log.debug("*** Hardware Configuration Information Reset Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_hw_config_info(self, assy_part_no, assy_rev_no, assy_serial_no, assy_build_batch_no):
        """
        Reset the Hardware Configuration Information, strings are truncated to 15 characters
        plus Null termination
        :param assy_build_batch_no: :type string
        :param assy_serial_no: :type string
        :param assy_rev_no: :type string
        :param assy_part_no: :type string
        :return: True if Hardware Configuration Information set, else False
        """
        ret_val = False

        if type(assy_part_no) is not str or type(assy_rev_no) is not str or \
           type(assy_serial_no) is not str or type(assy_build_batch_no) is not str:
            log.critical("One of the parameters is not of type str!")
            return ret_val

        id_val = [(0, assy_part_no, self._SET_HW_CONFIG_INF_PART_NO_SUCCESS),
                  (1, assy_rev_no, self._SET_HW_CONFIG_INF_REV_NO_SUCCESS),
                  (2, assy_serial_no, self._SET_HW_CONFIG_INF_SERIAL_NO_SUCCESS),
                  (3, assy_build_batch_no, self._SET_HW_CONFIG_INF_BUILD_BATCH_NO_SUCCESS)]

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            for param_id, param_val, param_success in id_val:
                cmd_str = "{} {} {}{}".format(self._SET_HW_CONFIG_INFO_CMD.decode("UTF-8"),
                                              param_id, param_val[0:15],
                                              self._SET_CMD_END.decode("UTF-8"))
                log.debug(b"#SHCI cmd: " + bytes(cmd_str.encode("UTF-8")))
                self._serial_port.write(bytes(cmd_str.encode("UTF-8")))

                resp_str = self._serial_port.read_until(self._SET_HW_CONFIG_INFO_END)
                log.debug(b"#SHCI cmd resp: " + resp_str)

                # Was the command response terminator found or did it timeout?
                if resp_str.find(self._SET_HW_CONFIG_INFO_END) != -1 and resp_str.find(param_success) != -1:
                    log.debug("Set Hw Config Info {} to: {}".format(param_id, param_val))
                    ret_val = True
                else:
                    log.debug("*** Set Hw Config Info  Response Error! ***")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_adc_data(self):
        """
        Read the test jig's NUCLEO board ADC channels.
        :return [0]: True if ADC read, else False
        :return [1]: NUCLEO Internal VRef, unit mV, -1 if the read fails
        :return [2]: Board Under Test +3V3, unit mV, -1 if the read fails
        """
        ret_val = False
        vref_int_mv = -1
        but_3v3_mv = -1

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            log.debug(b"$ADC cmd: " + self._GET_ADC_CMD)
            self._serial_port.write(self._GET_ADC_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._GET_ADC_CMD_SUCCESS)
            log.debug(b"$ADC cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_ADC_CMD_SUCCESS) != -1:
                for a_line in resp_str.splitlines():
                    if self._GET_ADC_VREFINT_RESP_LINE in a_line:
                        vref_int_mv = int(a_line.split()[-1])
                    elif self._GET_ADC_BUT_3V3_RESP_LINE in a_line:
                        but_3v3_mv = int(a_line.split()[-1])

                if vref_int_mv != -1 and but_3v3_mv != -1:
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, vref_int_mv, but_3v3_mv

    def get_mac_addresses(self):
        """
        Read the board under test's Micro and Switch MAC address EUI48 ICs.
        :return [0]: True if MAC addresses read, else False :type Boolean
        :return [1]: Micro MAC address :type String
        :return [2]: Switch MAC address :type String
        """
        micro_mac_address = ""
        switch_mac_address = ""

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            log.debug(b"$MAC cmd: " + self._GET_MAC_ADDRESS_CMD)
            self._serial_port.write(self._GET_MAC_ADDRESS_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._GET_MAC_ADDRESS_SUCCESS)
            log.debug(b"$MAC cmd resp: " + resp_str)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_MAC_ADDRESS_SUCCESS) != -1:
                for a_line in resp_str.splitlines():
                    if self._GET_MAC_ADDRESS_MICRO_RESP_LINE in a_line:
                        micro_mac_address = a_line.split()[-1].decode("UTF-8")
                    elif self._GET_MAC_ADDRESS_SWITCH_RESP_LINE in a_line:
                        switch_mac_address = a_line.split()[-1].decode("UTF-8")

        else:
            raise RuntimeError("Serial port is not open!")

        return micro_mac_address, switch_mac_address

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
