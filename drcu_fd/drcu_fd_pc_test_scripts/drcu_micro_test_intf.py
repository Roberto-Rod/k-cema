#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0256-00 software running
on the KT-000-0198-00 Display RCU Motherboard STM32 microcontroller.

Software compatibility:
- KT-956-0256-00 K-CEMA DRCU Micro Test Utility - v1.2.0 onwards

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
from dataclasses import dataclass
import logging
from enum import Enum

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
class DrcuGpoSignals(Enum):
    ZER_PWR_HOLD = 0
    XCHANGE_RESET = 1
    SOM_PWR_BTN_N = 2
    SOM_SYS_RST_PMIC_N = 3
    KEYPAD_LED_OE_N = 4
    BATT_CHRG_LOW = 5
    BATT_CHRG_EN_N = 6
    MICRO_I2C_EN = 7
    SOM_I2C_RESET = 8


class DrcuGpiSignals(Enum):
    IRQ_TAMPER_N = 0
    BATT_CHRG_STAT_N = 1
    KEYPAD_BTN0_N = 5
    KEYPAD_BTN1_N = 6
    KEYPAD_BTN2_N = 7


class DrcuPoEPseType(Enum):
    INVALID_0 = 0
    INVALID_1 = 1
    INVALID_2 = 2
    IEEE802_3_BT_TYPE4 = 3
    INVALID_4 = 4
    IEEE802_3_BT_TYPE3 = 5
    IEEE802_3_AT = 6
    IEEE802_3_AF = 7


class DrcuTamperChannels(Enum):
    CHANNEL_0 = 0
    CHANNEL_1 = 1


class DrcuTamperChannelStatus(Enum):
    DISABLED = 0
    ARMED_READY = 1
    TAMPERED = 2
    UNKNOWN = 3


class DrcuHwConfigInfo:
    """ Class for encapsulating Hardware Config Information """
    hw_version_no = ""
    hw_mod_version_no = ""
    assy_part_no = ""
    assy_rev_no = ""
    assy_serial_no = ""
    assy_build_batch_no = ""
    hw_info_valid = False

    def __init__(self, hw_version_no="", hw_mod_version_no="", assy_part_no="",
                 assy_rev_no="", assy_serial_no="", assy_build_batch_no=""):
        """ Class constructor """
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
        """ :return: string representing the class """
        return "HwConfigInfo({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.hw_version_no, self.hw_mod_version_no, self.assy_part_no, self.assy_rev_no,
            self.assy_serial_no, self.assy_build_batch_no, self.hw_info_valid)


class DrcuMircoTestInterface:
    """
    Class for wrapping up the interface to the CSM Zeroise Microcontroller Test Utility Interface
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _GET_BATT_TEMP_CMD = b"$BTMP"
    _GET_BATT_TEMP_RESPONSE_END = b"!BTMP\r\n"
    _GET_STM32_TEMP_CMD = b"$TMP"
    _GET_STM32_TEMP_RESPONSE_END = b"!TMP\r\n"
    _SET_GPO_CMD = b"#GPO"
    _SET_GPO_RESPONSE_END = b">GPO\r\n"
    _SET_GPO_ASSERT_SIGNAL_RESP = b" set to: "
    _GET_GPI_CMD = b"$GPI"
    _GET_GPI_RESPONSE_END = b"!GPI\r\n"
    _GET_HW_CONFIG_INFO_CMD = b"$HCI"
    _GET_HW_CONFIG_INFO_RESPONSE_END = b"!HCI\r\n"
    _RESET_HW_CONFIG_INFO_CMD = b"#RHCI"
    _RESET_HW_CONFIG_INFO_RESPONSE_END = b">RHCI\r\n"
    _RESET_HW_CONFIG_INFO_SUCCESS = b"Successfully cleared HCI EEPROM"
    _SET_HW_CONFIG_INFO_CMD = b"#SHCI"
    _SET_HW_CONFIG_INFO_RESPONSE_END = b">SHCI\r\n"
    _SET_HW_CONFIG_INFO_PART_NO_SUCCESS = b"Successfully set parameter [Part No] to"
    _SET_HW_CONFIG_INFO_REV_NO_SUCCESS = b"Successfully set parameter [Revision No] to"
    _SET_HW_CONFIG_INFO_SERIAL_NO_SUCCESS = b"Successfully set parameter [Serial No] to"
    _SET_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS = b"Successfully set parameter [Build Batch No] to"
    _GET_PPS_INPUT_DETECTED_CMD = b"$PPS"
    _GET_PPS_INPUT_DETECTED_RESPONSE_END = b"!PPS"
    _GET_PPS_INPUT_DETECTED_RESPONSE = b"1PPS detected"
    _SET_TAMPER_CHANNEL_CMD = b"#SAT"
    _SET_TAMPER_CHANNEL_RESPONSE_END = b">SAT\r\n"
    _SET_TAMPER_CHANNEL_ENABLED_SUCCESS = b"ENABLED"
    _SET_TAMPER_CHANNEL_DISABLED_SUCCESS = b"DISABLED"
    _GET_TAMPER_REGISTERS_CMD = b"$RAT"
    _GET_TAMPER_RESPONSE_END = b"!RAT\r\n"

    def __init__(self, com_port=None):
        """
        Class constructor
        :param: COM port associated with the interface :type: string
        :return: None
        """
        self._serial_port = None
        self._com_port = com_port
        if com_port is not None:
            self.open_com_port(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "CsmTestJigInterface({!r})".format(self._com_port)

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
        Send dummy command string "DEFINITELY_NOT_A_CMD\r" and read until a "?\r\n"
        string is returned, unknown command.
        :return: N/A
        """
        self._serial_port.write(b"\r")
        self._serial_port.read_until(self._CMD_UNKNOWN, self._RX_TIMEOUT)

    def get_battery_temperature(self):
        """
        Query battery temperature
        :return: battery temperature, -255 if read fails :type integer
        """
        batt_temp = -255

        if self._serial_port is not None:
            self._serial_port.write(self._GET_BATT_TEMP_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_BATT_TEMP_RESPONSE_END)
            log.debug(resp_str)

            # Was the command response terminator found or did it timeout?
            if self._GET_BATT_TEMP_RESPONSE_END in resp_str:
                for a_line in resp_str.splitlines():
                    if b"Battery Temperature:" in a_line:
                        batt_temp = int(a_line.split()[-1])
        else:
            raise RuntimeError("Serial port is not open!")

        return batt_temp

    def get_stm32_temperature(self):
        """
        Query STM32 temperature
        :return: battery temperature, -255 if read fails :type integer
        """
        stm32_temp = -255

        if self._serial_port is not None:
            self._serial_port.write(self._GET_STM32_TEMP_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_STM32_TEMP_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_STM32_TEMP_RESPONSE_END in resp_str:
                for a_line in resp_str.splitlines():
                    if b"Temperature:" in a_line:
                        stm32_temp = int(a_line.split()[-1])
        else:
            raise RuntimeError("Serial port is not open!")

        return stm32_temp

    def get_poe_pd_pse_type(self):
        """
        Read the PoE Power Device Power Supply Equipment detected state.
        :return: ret_val True if command successful, else False; pse_type DrcuPoEPseType enumerated value
        """
        ret_val = False
        pse_type = DrcuPoEPseType.INVALID_0

        if self._serial_port is not None:
            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_RESPONSE_END)

            # Was the command response terminator found or did we timeout?
            if self._GET_GPI_RESPONSE_END in resp_str:
                # Build a 3-bit integer value representing to map on to the DrcuPoEPseType enumeration
                int_val = 0
                for a_line in resp_str.splitlines():
                    if bytes("POE_PD_AT_DET", encoding="UTF-8") in a_line:
                        int_val |= int(a_line[0:1].decode("UTF-8"))
                    elif bytes("POE_PD_TYP3_DET_N", encoding="UTF-8") in a_line:
                        int_val |= (int(a_line[0:1].decode("UTF-8")) << 1)
                    elif bytes("POE_PD_TYP4_DET_N", encoding="UTF-8") in a_line:
                        int_val |= (int(a_line[0:1].decode("UTF-8")) << 2)
                    else:
                        pass

                pse_type = DrcuPoEPseType(int_val)
                ret_val = True

        return ret_val, pse_type

    def set_gpo_signal(self, gpo_signal, state):
        """
        Set the specified GPO signal
        :param gpo_signal: GPO signal to assert/de-assert :type DrcuFdTestJigGpoSignals
        :param state: True set signal to '1', False set signal to '0'
        :return: True if successful, else False
        """
        if gpo_signal not in DrcuGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            cmd_str = self._SET_GPO_CMD + " {} {}".format(gpo_signal.value, 1 if state else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._SET_GPO_RESPONSE_END)

            ret_val = (self._SET_GPO_RESPONSE_END in resp_str) and (self._SET_GPO_ASSERT_SIGNAL_RESP in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_gpi_signal_asserted(self, signal):
        """
        Check if a GPI signal is asserted.
        Note, all the GPI signals covered by this method are active-low.
        :param signal: signal to check :type: CsmGpiSignals
        :return: ret_val True if command successful, else False; signal_asserted True if asserted, else False
        """
        if signal not in DrcuGpiSignals:
            raise ValueError("Get GPI Invalid Signal!")

        ret_val = False
        signal_asserted = False

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_RESPONSE_END)

            # Was the command response terminator found or did we timeout?
            if self._GET_GPI_RESPONSE_END in resp_str:
                for a_line in resp_str.splitlines():
                    if bytes(signal.name, encoding="UTF-8") in a_line:
                        if int(a_line[0]) == ord("0"):
                            log.debug("{} ASSERTED".format(signal.name))
                            signal_asserted = True
                        else:
                            log.debug("{} NOT ASSERTED".format(signal.name))
                            signal_asserted = False

                        ret_val = True
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, signal_asserted

    def get_hw_config_info(self):
        """
        Read the board under test's hardware config information.
        :return [0]: True if read is successful, else False
        :return [1]: DrcuHwConfigInfo object containing read data, None if the read fails
        """
        ret_val = False
        hci = None

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            self._serial_port.write(self._GET_HW_CONFIG_INFO_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_HW_CONFIG_INFO_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_HW_CONFIG_INFO_RESPONSE_END in resp_str:
                # Split response by lines then process to extract data
                hci = DrcuHwConfigInfo()
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
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            self._serial_port.write(self._RESET_HW_CONFIG_INFO_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._RESET_HW_CONFIG_INFO_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            ret_val = self._RESET_HW_CONFIG_INFO_RESPONSE_END in resp_str and \
                      self._RESET_HW_CONFIG_INFO_SUCCESS in resp_str
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
        ret_val = True

        if type(assy_part_no) is not str or type(assy_rev_no) is not str or \
                type(assy_serial_no) is not str or type(assy_build_batch_no) is not str:
            raise ValueError("One of the parameters is not of type str!")

        id_val = [
            # (param_id, param_val, param_success_str)
            (0, assy_part_no, self._SET_HW_CONFIG_INFO_PART_NO_SUCCESS),
            (1, assy_rev_no, self._SET_HW_CONFIG_INFO_REV_NO_SUCCESS),
            (2, assy_serial_no, self._SET_HW_CONFIG_INFO_SERIAL_NO_SUCCESS),
            (3, assy_build_batch_no, self._SET_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS)
        ]

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            for param_id, param_val, param_success_str in id_val:
                cmd_str = "{} {} {}{}".format(self._SET_HW_CONFIG_INFO_CMD.decode("UTF-8"),
                                              param_id, param_val[0:15],
                                              self._SET_CMD_END.decode("UTF-8"))
                self._serial_port.write(bytes(cmd_str.encode("UTF-8")))
                resp_str = self._serial_port.read_until(self._SET_HW_CONFIG_INFO_RESPONSE_END)

                # Was the command response terminator found or did it timeout?
                ret_val = self._SET_HW_CONFIG_INFO_RESPONSE_END in resp_str and \
                          param_success_str in resp_str and ret_val
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
            self._serial_port.write(self._GET_PPS_INPUT_DETECTED_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_PPS_INPUT_DETECTED_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            ret_val = resp_str.find(self._GET_PPS_INPUT_DETECTED_RESPONSE_END) != -1 and \
                resp_str.find(self._GET_PPS_INPUT_DETECTED_RESPONSE) != -1

            pps_delta_ms = -1
            if ret_val:
                for a_line in resp_str.splitlines():
                    if a_line.find(self._GET_PPS_INPUT_DETECTED_RESPONSE) != -1:
                        pps_delta_ms = int(a_line.decode("UTF-8").split()[-2])
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, pps_delta_ms

    def set_anti_tamper_channel_enable(self, channel, enable):
        """
        Set an anti-tamper device channel enabled/disabled
        :param: channel, one of enumerated values :type: CsmTamperChannels
        :param: enable, True to enable, False to disable :type: boolean
        :return: True if anti-tamer channel enable set, else False
        """
        if channel not in DrcuTamperChannels:
            raise ValueError("Incorrect device or channel parameter value")

        ret_val = False

        if self._serial_port is not None:
            cmd_str = self._SET_TAMPER_CHANNEL_CMD
            cmd_str += (b" " + str(channel.value).encode("UTF-8"))
            cmd_str += " 1".encode("UTF-8") if enable else " 0".encode("UTF-8")
            cmd_str += self._SET_CMD_END

            self._serial_port.write(bytes(cmd_str))
            resp_str = self._serial_port.read_until(self._SET_TAMPER_CHANNEL_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._SET_TAMPER_CHANNEL_RESPONSE_END in resp_str:
                if enable and self._SET_TAMPER_CHANNEL_ENABLED_SUCCESS in resp_str:
                    ret_val = True
                elif not enable and self._SET_TAMPER_CHANNEL_DISABLED_SUCCESS in resp_str:
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_tamper_channel_status(self, channel):
        """
        Read a tamper channel status
        :param: channel, one of enumerated values :type: CsmTamperChannels
        :return: [0] True if commands successful, else False
                 [1] one of CsmTamperChannelStatus values
        """
        if channel not in DrcuTamperChannels:
            raise ValueError("Incorrect  channel parameter value")

        ret_val = False
        status = DrcuTamperChannelStatus.UNKNOWN

        if self._serial_port is not None:
            self._serial_port.write(self._GET_TAMPER_REGISTERS_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_TAMPER_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_TAMPER_RESPONSE_END in resp_str:
                # Which register values are of interest, already checked that channel is valid
                if channel is DrcuTamperChannels.CHANNEL_0:
                    tamper_reg = b"Anti-tamper Tamper 1"
                    flags_reg = b"Anti-tamper Flags"
                    tb_bit = 0x02
                elif channel is DrcuTamperChannels.CHANNEL_1:
                    tamper_reg = b"Anti-tamper Tamper 2"
                    flags_reg = b"Anti-tamper Flags"
                    tb_bit = 0x01
                else:
                    tamper_reg = b"This won't be found!"
                    flags_reg = b"This won't be found!"
                    tb_bit = 0x00

                teb_reg = 256
                tb_reg = 256
                for a_line in resp_str.splitlines():
                    if tamper_reg in a_line:
                        teb_reg = int(a_line[0:2], base=16)
                    elif flags_reg in a_line:
                        tb_reg = int(a_line[0:2], base=16)

                # Did we find the registers of interest?
                if teb_reg < 256 and tb_reg < 256:
                    if teb_reg & 0x80 == 0:
                        status = DrcuTamperChannelStatus.DISABLED
                    elif tb_reg & tb_bit:
                        status = DrcuTamperChannelStatus.TAMPERED
                    else:
                        status = DrcuTamperChannelStatus.ARMED_READY
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, status


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
