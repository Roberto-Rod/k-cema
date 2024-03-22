#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0230-00 software running
on the KT-000-0140-00 CSM Motherboard STM32 microcontroller.

Software compatibility:
- KT-956-0230-00 K-CEMA CSM PCB Zeroise Micro Test Utility - Vx.y.z
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
class CsmTamperDevices(Enum):
    ANTI_TAMPER = 0
    POWER_CABLE_DETECT = 1


class CsmTamperChannels(Enum):
    CHANNEL_0 = 0
    CHANNEL_1 = 1


class CsmTamperChannelStatus(Enum):
    DISABLED = 0
    ARMED_READY = 1
    TAMPERED = 2


class CsmGpiSignals(Enum):
    IRQ_TAMPER_N = 0
    BATT_CHRG_STAT_N = 1
    IRQ_CABLE_UNPLUG_N = 4
    POE_PSE_INT_N = 7


class MpGpiSignals(Enum):
    IRQ_TAMPER_N = 0
    BATT_CHRG_STAT_N = 1


class CsmGpoSignals(Enum):
    # These signal names match the names used by the test utility in the ASCII terminal
    ZER_PWR_HOLD = 0
    ZER_FPGA_PWR_EN = 1
    ZER_I2C_FPGA_EN = 3
    ZER_FPGA_RST = 4
    BATT_CHRG_LOW = 6
    BATT_CHRG_EN_N = 7
    POE_PSE_RST_N = 8
    ZER_I2C_POE_EN = 10


class MpGpoSignals(Enum):
    # These signal names match the names used by the test utility in the ASCII terminal
    ZER_PWR_HOLD = 0
    ZER_FPGA_PWR_EN = 1
    ZER_I2C_FPGA_EN = 3
    ZER_FPGA_RST = 4
    BATT_CHRG_LOW = 6
    BATT_CHRG_EN_N = 7


@dataclass
class CsmZeroiseBitAdcData:
    """ Utility class to represent BIT ADC data """
    vbat_zer_mv: int = -1
    p3v3_zer_buf_mv: int = -1
    p3v0_zer_proc_mv: int = -1
    p3v0_zer_fpga: int = -1
    p2v5_zer_mv: int = -1
    p2v5_som_mv: int = -1
    p1v2_zer_fpga_mv: int = -1
    p4v2_zer_mv: int = -1
    adc_vcc_mv: int = -1
    adc_temp_k: int = -1


@dataclass
class CsmPoePseChannelStatus:
    """ Utility class to represent PoE PSE channel status """
    port_mode: int = -1
    # 0 - Shutdown
    # 1 - Manual
    # 2 - Semi Auto
    # 3 - Auto
    power_enable: bool = False
    power_good: bool = False
    power_on_fault: bool = False
    port_2p4p_mode: bool = False
    power_allocation: int = -1
    # 0 - 15 W Class 3 SS/7 W Class 2 + 7 W Class 2
    # 3 - 30 W Class 4 SS/15 W Class 3 + 15 W Class 3
    # 4 - 45 W Class 5 SS/30 W Class 4 + 15 W Class 3
    # 5 - 60 W Class 6 SS/30 W Class 4 + 30 W Class 4
    # 6 - 75 W Class 7 SS/45 W Class 5 + 30 W Class 4
    # 7 - 90 W Class 8 SS/45 W Class 5 + 45 W Class 5
    class_status: int = -1
    # 0 - Unknown
    # 1-4 - Class 1-4
    # 6 - Class 0
    # 7 - Over-current
    # 8 - Class 5 4P SS
    # 9 - Class 6 4P SS
    # 10 - Class 7 4P SS
    # 11 - Class 8 4P SS
    # 12 - Class 4 + Type 1 Limited
    # 13 - Class 5 DS
    # 15 - Class mismatch
    detection_status: int = -1
    # 0 -Unknown
    # 1 - Short circuit
    # 2 - Capacitive
    # 3 - RLOW
    # 4 - RGOOD
    # 5 - RHIGH
    # 6 - Open circuit
    # 7 - PSE to PSE; 15 - MOSFET fault
    voltage_mv: int = -1
    current_ma: int = -1


class CommonZeroiseMircoTestInterface:
    """
    Base class for wrapping up the common interface to the Manpack and Vehicle CSM Zeroise Microcontroller Test
    Utility Interfaces.
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _GET_GPI_CMD = b"$GPI"
    _GET_GPI_RESPONSE_END = b"!GPI\r\n"
    _SET_GPO_CMD = b"#GPO "
    _SET_GPO_RESPONSE_END = b">GPO\r\n"
    _GET_KEYPAD_BTN_HELD = b"0 - KEYPAD_BTN_IN"
    _GET_KEYPAD_BTN_RELEASED = b"1 - KEYPAD_BTN_IN"
    _GET_BATTERY_FAULT_ASSERTED = b"0 - BATT_FAULT_N"
    _GET_BATTERY_FAULT_NOT_ASSERTED = b"1 - BATT_FAULT_N"
    _GET_BATT_TEMP_CMD = b"$BTMP"
    _GET_BATT_TEMP_RESPONSE_END = b"!BTMP\r\n"
    _GET_PGOOD_3V3_SUP_ASSERTED = b"1 - PGOOD_3V3_SUP"
    _GET_PGOOD_3V3_SUP_NOT_ASSERTED = b"0 - PGOOD_3V3_SUP"
    _GET_ZGPO_CMD = b"$ZGPO"
    _GET_ZGPO_RESPONSE_END = b"!ZGPO\r\n"
    _GET_ZGPO_GPO_REGISTER_LINE = b"- GPO register"
    _SET_ZGPO_CMD = b"#ZGPO "
    _SET_ZGPO_RESPONSE_END = b">ZGPO\r\n"
    _SET_ZGPO_SUCCESS = b"Zeroise FPGA GPO register set to:"
    _GET_PPS_CMD = b"$PPS\r"
    _GET_PPS_RESPONSE_END = b"!PPS\r\n"
    _GET_PPS_DETECTED = b"1PPS detected"
    _GET_PPS_NOT_DETECTED = b"1PPS NOT detected"
    _SET_BUZZER_CMD = b"#BZR"
    _SET_BUZZER_RESPONSE_END = b">BZR\r\n"
    _SET_BUZZER_ENABLED_SUCCESS = b"Buzzer enabled"
    _SET_BUZZER_DISABLED_SUCCESS = b"Buzzer disabled"
    _SET_ALL_LED_GREEN_CMD = b"#LEDA"
    _SET_ALL_LED_GREEN_RESPONSE_END = b">LEDA\r\n"
    _SET_ALL_LED_GREEN_SUCCESS = b"All LEDs set to GREEN"
    _SET_ALL_LED_OFF_SUCCESS = b"All LEDs set to OFF"
    _GET_RTC_CMD = b"$RTC"
    _GET_RTC_RESPONSE_END = b"!RTC\r\n"
    _SET_TAMPER_CHANNEL_CMD = b"#SAT"
    _SET_TAMPER_CHANNEL_RESPONSE_END = b">SAT\r\n"
    _SET_TAMPER_CHANNEL_ENABLED_SUCCESS = b"ENABLED"
    _SET_TAMPER_CHANNEL_DISABLED_SUCCESS = b"DISABLED"
    _GET_TAMPER_REGISTERS_CMD = b"$RAT"
    _GET_TAMPER_RESPONSE_END = b"!RAT\r\n"
    _TEST_KEYPAD_CMD = b"#TKP"
    _TEST_KEYPAD_END = b"!TKP\r\n"
    _TEST_KEYPAD_SUCCESS = b"PASS - Button 0\r\nPASS - Button 1\r\nPASS - Button 2"
    _ASSERT_KEYPAD_PWR_BTN_CMD = b"#SKPB"
    _ASSERT_KEYPAD_PWR_BTN_END = b">SKPB\r\n"
    _GET_ADC_DATA_CMD = b"$ADC"
    _GET_ADC_DATA_END = b"!ADC\r\n"
    _GET_POE_PSE_CHANNEL_STATUS_CMD = b"$POEP"
    _GET_POE_PSE_CHANNEL_STATUS_END = b"!POEP\r\n"
    _GET_POE_PSE_TEMP_VOLTAGE_CMD = b"$POED"
    _GET_POE_PSE_TEMP_VOLTAGE_END = b"!POED\r\n"
    _GET_STM32_TEMP_CMD = b"$TMP"
    _GET_STM32_TEMP_RESPONSE_END = b"!TMP\r\n"

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

    def __del__(self):
        """ Class destructor - close the serial port """
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

    def get_pps_detected(self):
        """
        Query if a 1PPS signal is being detected
        :return: [0] True if PPS detected, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_PPS_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_PPS_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            ret_val = resp_str.find(self._GET_PPS_RESPONSE_END) != -1 and \
                resp_str.find(self._GET_PPS_DETECTED) != -1

            pps_delta_ms = -1
            if ret_val:
                for a_line in resp_str.splitlines():
                    if a_line.find(self._GET_PPS_DETECTED) != -1:
                        pps_delta_ms = int(a_line.decode("UTF-8").split()[-2])
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, pps_delta_ms

    def get_keypad_button_held(self, btn_no):
        """
        Query if a button is asserted
        :param: btn_no index of button to check, valid range 0 to 2 :type integer
        :return: [0] if command was successful, else False
                 [1] True, if button is held down, else False
        """
        ret_val = False
        btn_held = False

        if btn_no in range(0, 3, 1):
            if self._serial_port is not None:
                self._synchronise_cmd_prompt()
                self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)

                resp_str = self._serial_port.read_until(self._GET_GPI_RESPONSE_END)
                # Was the command response terminator found or did the read timeout?
                if resp_str.find(self._GET_GPI_RESPONSE_END) != -1:
                    btn = bytearray()
                    btn.append(btn_no + 48)
                    if resp_str.find(self._GET_KEYPAD_BTN_HELD + btn) != -1:
                        log.debug("Keypad button {} HELD".format(btn_no))
                        btn_held = True
                        ret_val = True
                    elif resp_str.find(self._GET_KEYPAD_BTN_RELEASED + btn) != -1:
                        log.debug("Keypad button {} RELEASED".format(btn_no))
                        btn_held = False
                        ret_val = True
                    elif resp_str.find(self._GET_KEYPAD_BTN_HELD) == -1 and \
                            resp_str.find(self._GET_KEYPAD_BTN_RELEASED) == -1:
                        log.critical("Get Keypad Button Held Unexpected Response!")
            else:
                raise RuntimeError("Serial port is not open!")
        else:
            raise RuntimeError("Get Keypad Button Invalid Button - {}!".format(btn_no))

        return ret_val, btn_held

    def get_battery_fault(self):
        """
        Query if the BATT_FAULT_N signal is asserted
        :return: [0] if command was successful, else False
                 [1] True, if signal is asserted, else False
        """
        ret_val = False
        battery_fault_asserted = False

        if self._serial_port is not None:
            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_RESPONSE_END)

            # Was the command response terminator found or did we timeout?
            if self._GET_GPI_RESPONSE_END in resp_str:
                if self._GET_BATTERY_FAULT_ASSERTED in resp_str:
                    log.debug("Battery Fault Asserted")
                    battery_fault_asserted = True
                    ret_val = True
                elif self._GET_BATTERY_FAULT_NOT_ASSERTED in resp_str:
                    log.debug("Battery Fault NOT Asserted")
                    battery_fault_asserted = False
                    ret_val = True
                elif self._GET_BATTERY_FAULT_ASSERTED not in resp_str and \
                        self._GET_BATTERY_FAULT_NOT_ASSERTED not in resp_str:
                    log.critical("Get Battery Fault Asserted Unexpected Response!")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, battery_fault_asserted

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
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return batt_temp

    def get_pgood_3v3_sup_asserted(self):
        """
        Query if the PGOOD_3V3_SUP signal is asserted
        :return: [0] True if command was successful, else False
                 [1] True, if signal is asserted, else False
        """
        ret_val = False
        asserted = False

        if self._serial_port is not None:
            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_RESPONSE_END)

            # Was the command response terminator found or did we timeout?
            if self._GET_GPI_RESPONSE_END in resp_str:
                if self._GET_PGOOD_3V3_SUP_ASSERTED in resp_str:
                    log.debug("GOOD +3V3 SUPAsserted")
                    asserted = True
                    ret_val = True
                elif self._GET_PGOOD_3V3_SUP_NOT_ASSERTED in resp_str:
                    log.debug("PGOOD +3V3 SUP NOT Asserted")
                    asserted = False
                    ret_val = True
                elif self._GET_PGOOD_3V3_SUP_ASSERTED not in resp_str and \
                        self._GET_PGOOD_3V3_SUP_NOT_ASSERTED not in resp_str:
                    log.critical("Get GOOD +3V3 SUP Asserted Unexpected Response!")
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, asserted

    def set_buzzer_enable(self, enable):
        """
        Enable the case buzzer
        :param: enable, True to enable, False to disable :type: boolean
        :return: True if buzzer enable set, else False
        """
        if self._serial_port is not None:
            cmd_str = self._SET_BUZZER_CMD
            cmd_str += "1".encode("Utf-8") if enable else "0".encode("Utf-8")
            cmd_str += self._SET_CMD_END
            self._serial_port.write(bytes(cmd_str))

            resp_str = self._serial_port.read_until(self._SET_BUZZER_RESPONSE_END)
            # Was the command response terminator found or did the response timeout?
            ret_val = resp_str.find(self._SET_BUZZER_RESPONSE_END) != -1 and \
                      (resp_str.find(self._SET_BUZZER_ENABLED_SUCCESS) != -1 or
                       resp_str.find(self._SET_BUZZER_DISABLED_SUCCESS) != -1)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_rtc(self):
        """
        Query anti-tamper and power cable detect RTC values
        :return: [0] = Anti-tamper RTC string HH:MM:SS, "" if read fails :type bytes
                 [1] Power Cable Detect RTC string HH:MM:SS, "" if read fails :type bytes
        """
        at_rtc = ""
        pcd_rtc = ""

        if self._serial_port is not None:
            self._serial_port.write(self._GET_RTC_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_RTC_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_RTC_RESPONSE_END in resp_str:
                for a_line in resp_str.splitlines():
                    if b"Anti-tamper RTC:" in a_line:
                        at_rtc = a_line[a_line.find(b": ")+len(b":\t"):]
                    if b"Power Cable Detect RTC:" in a_line:
                        pcd_rtc = a_line[a_line.find(b": ") + len(b":\t"):]
        else:
            raise RuntimeError("Serial port is not open!")

        return at_rtc, pcd_rtc

    def set_anti_tamper_channel_enable(self, device, channel, enable):
        """
        Set an anti-tamper device channel enabled/disabled
        :param: device, one of enumerated values :type: CsmTamperDevices
        :param: channel, one of enumerated values :type: CsmTamperChannels
        :param: enable, True to enable, False to disable :type: boolean
        :return: True if anti-tamper channel enable set, else False
        """
        if device not in CsmTamperDevices or channel not in CsmTamperChannels:
            raise ValueError("Incorrect device or channel parameter value")

        ret_val = False

        if self._serial_port is not None:
            cmd_str = self._SET_TAMPER_CHANNEL_CMD
            cmd_str += (b" " + str(device.value).encode("UTF-8"))
            cmd_str += (b" " + str(channel.value).encode("UTF-8"))
            cmd_str += " 1".encode("UTF-8") if enable else " 0".encode("UTF-8")
            cmd_str += self._SET_CMD_END

            self._serial_port.write(bytes(cmd_str))
            resp_str = self._serial_port.read_until(self._SET_TAMPER_CHANNEL_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._SET_TAMPER_CHANNEL_RESPONSE_END in resp_str:
                if enable and self._SET_TAMPER_CHANNEL_ENABLED_SUCCESS in resp_str:
                    log.debug("Anti-tamper channel {} {} ENABLED".format(device.value, channel.value))
                    ret_val = True
                elif not enable and self._SET_TAMPER_CHANNEL_DISABLED_SUCCESS in resp_str:
                    log.debug("Anti-tamper channel {} {} DISABLED".format(device.value, channel.value))
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_tamper_channel_status(self, device, channel):
        """
        Read a tamper channel status
        :param: device, one of enumerated values :type: CsmTamperDevices
        :param: channel, one of enumerated values :type: CsmTamperChannels
        :return: [0] True if commands successful, else False
                 [1] one of CsmTamperChannelStatus values
        """
        if device not in CsmTamperDevices or channel not in CsmTamperChannels:
            raise ValueError("Incorrect device or channel parameter value")

        ret_val = False
        status = CsmTamperChannelStatus.DISABLED

        if self._serial_port is not None:
            self._serial_port.write(self._GET_TAMPER_REGISTERS_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_TAMPER_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_TAMPER_RESPONSE_END in resp_str:
                # Which register values are of interest, already checked that device and channel are valid
                if device is CsmTamperDevices.ANTI_TAMPER and channel is CsmTamperChannels.CHANNEL_0:
                    tamper_reg = b"Anti-tamper Tamper 1"
                    flags_reg = b"Anti-tamper Flags"
                    tb_bit = 0x02
                elif device is CsmTamperDevices.ANTI_TAMPER and channel is CsmTamperChannels.CHANNEL_1:
                    tamper_reg = b"Anti-tamper Tamper 2"
                    flags_reg = b"Anti-tamper Flags"
                    tb_bit = 0x01
                elif device is CsmTamperDevices.POWER_CABLE_DETECT and channel is CsmTamperChannels.CHANNEL_0:
                    tamper_reg = b"Cable Detect Tamper 1"
                    flags_reg = b"Cable Detect Flags"
                    tb_bit = 0x02
                elif device is CsmTamperDevices.POWER_CABLE_DETECT and channel is CsmTamperChannels.CHANNEL_1:
                    tamper_reg = b"Cable Detect Tamper 2"
                    flags_reg = b"Cable Detect Flags"
                    tb_bit = 0x01
                else:
                    tamper_reg = b"This won't be found!"
                    flags_reg = b"This won't be found!"
                    tb_bit = 0x00

                teb_reg = 256
                tb_reg = 256
                for a_line in resp_str.splitlines():
                    if tamper_reg in a_line:
                        log.debug(a_line[0:2])
                        teb_reg = int(a_line[0:2], base=16)
                    elif flags_reg in a_line:
                        log.debug(a_line[0:2])
                        tb_reg = int(a_line[0:2], base=16)

                # Did we find the registers of interest?
                if teb_reg < 256 and tb_reg < 256:
                    if teb_reg & 0x80 == 0:
                        status = CsmTamperChannelStatus.DISABLED
                    elif tb_reg & tb_bit:
                        status = CsmTamperChannelStatus.TAMPERED
                    else:
                        status = CsmTamperChannelStatus.ARMED_READY
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, status

    def base_get_gpi_signal_asserted(self, signal):
        """
        Check if a GPI signal is asserted.
        :param signal: signal to check :type: CsmGpiSignals or MpGpiSignals
        :return: ret_val True if command successful, else False; signal_asserted True if asserted, else False
        """
        if signal not in CsmGpiSignals and signal not in MpGpiSignals:
            raise ValueError("Get GPI Invalid Signal!")

        ret_val = False
        signal_asserted = False

        if self._serial_port is not None:
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

    def base_set_gpo_signal(self, signal, state):
        """
        Set a GPO signal to the required state
        :param signal: signal to check :type: CsmGpoSignals or MpGpoSignals
        :param state: set state, True '1', False '0'
        :return: ret_val True if command successful, else False
        """
        if signal not in CsmGpoSignals and signal not in MpGpoSignals:
            raise ValueError("Set GPO Invalid Signal!")

        if self._serial_port is not None:
            cmd_str = self._SET_GPO_CMD
            if state:
                cmd_str += bytes(str(signal.value), encoding="UTF-8") + b" 1"
                succ_str = bytes(signal.name, encoding="UTF-8") + b" set to: 1"
            else:
                cmd_str += bytes(str(signal.value), encoding="UTF-8") + b" 0"
                succ_str = bytes(signal.name, encoding="UTF-8") + b" set to: 0"
            cmd_str += self._SET_CMD_END

            self._serial_port.write(bytes(cmd_str))
            resp_str = self._serial_port.read_until(self._SET_GPO_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            ret_val = self._SET_GPO_RESPONSE_END in resp_str and succ_str in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_zeroise_fpga_gpo_reg(self, value):
        """
        Set the Zeroise FPGA 8-bit register to value
        :param value: 8-bit value to write :type: integer
        :return: True, if Zeroise FPGA GPO register written with value, else False
        """
        if self._serial_port is not None:
            cmd_str = self._SET_ZGPO_CMD
            cmd_str += bytes(str(value & 0xFF), encoding="UTF-8")
            cmd_str += self._SET_CMD_END

            self._serial_port.write(bytes(cmd_str))
            resp_str = self._serial_port.read_until(self._SET_ZGPO_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            ret_val = self._SET_ZGPO_RESPONSE_END in resp_str and self._SET_ZGPO_SUCCESS in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_zeroise_fpga_gpo_reg(self):
        """
        Get the Zeroise FPGA 8-bit register value
        :return: [0] True, if Zeroise FPGA GPO register written with value, else False :type: boolean
                 [1] 8-bit register value :type: integer
        """
        value = -1
        ret_val = False

        if self._serial_port:
            self._serial_port.write(self._GET_ZGPO_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_ZGPO_RESPONSE_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_ZGPO_RESPONSE_END in resp_str and self._GET_ZGPO_GPO_REGISTER_LINE in resp_str:
                for a_line in resp_str.splitlines():
                    if self._GET_ZGPO_GPO_REGISTER_LINE in a_line:
                        value = int(str(a_line[2:4].decode("UTF-8")), base=16)
                        ret_val = True
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, value

    def test_keypad(self):
        """
        Command the Zeroise Micro to perform a loopback test using the KT-000-0197-00 test jig
        :return: True if loopback test passes, else False :type: Boolean
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._TEST_KEYPAD_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._TEST_KEYPAD_END)

            # Was the command response terminator found or did it timeout and did the test pass??
            ret_val = resp_str.find(self._TEST_KEYPAD_END) != -1 and resp_str.find(self._TEST_KEYPAD_SUCCESS) != -1
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def toggle_keypad_power_button(self, hard_power_off=False):
        """
        Simulate the Keypad Power Button being pressed using the KT-000-0197/0203-00 test jig
        :param hard_power_off: Set to True to simulate hard 10-second power off
        :return: True if command successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._ASSERT_KEYPAD_PWR_BTN_CMD
            cmd_str += bytes("{}".format("0" if hard_power_off else "1"), encoding="UTF-8")
            cmd_str += self._SET_CMD_END

            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._ASSERT_KEYPAD_PWR_BTN_END)

            # Was the command response terminator found or did it timeout and did the test pass??
            ret_val = resp_str.find(self._ASSERT_KEYPAD_PWR_BTN_END) != -1
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_adc_data(self):
        """
        Read the Zeroise Power Domain BIT ADC data
        :return [0]: True if ADC read, else False
        :return [1]: dataclass representing the read ADC data :type CsmZeroiseBitAdcData
        """
        ret_val = False
        adc_data = CsmZeroiseBitAdcData()

        resp_dataclass_map = {
            "+VBAT_ZER": "vbat_zer_mv",
            "+3V3_ZER_BUF": "p3v3_zer_buf_mv",
            "+3V0_ZER_PROC": "p3v0_zer_proc_mv",
            "+3V0_ZER_FPGA": "p3v0_zer_fpga",
            "+2V5_ZER": "p2v5_zer_mv",
            "+2V5_SOM": "p2v5_som_mv",
            "+1V2_ZER_FPGA": "p1v2_zer_fpga_mv",
            "+4V2_ZER": "p4v2_zer_mv",
            "VCC": "adc_vcc_mv",
            "Temp": "adc_temp_k"
        }

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_ADC_DATA_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_ADC_DATA_END)

            # Was the command response terminator found or did it timeout?
            if resp_str.find(self._GET_ADC_DATA_END) != -1:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 3:
                        if getattr(adc_data, resp_dataclass_map.get(split_line[0], ""), None) is not None:
                            setattr(adc_data, resp_dataclass_map.get(split_line[0]), int(split_line[-1]))
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, adc_data

    def get_stm32_temperature(self):
        """
        Query STM32 temperature
        :return: STM32 temperature, -255 if read fails :type integer
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
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return stm32_temp


class CsmZeroiseMircoTestInterface(CommonZeroiseMircoTestInterface):
    """
    Concrete class for wrapping up the common interface to the Vehicle CSM Zeroise Microcontroller Test
    Utility Interface.
    """
    def __init__(self, com_port=None):
        """
        Class constructor
        :param: COM port associated with the interface :type: string
        :return: None
        """
        super().__init__(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "CsmTestJigInterface({!r})".format(self._com_port)

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the serial port"""
        self.close_com_port()

    def get_gpi_signal_asserted(self, signal):
        """
        Check if a GPI signal is asserted.
        :param signal: signal to check :type: CsmGpiSignals
        :return: ret_val True if command successful, else False; signal_asserted True if asserted, else False
        """
        if signal not in CsmGpiSignals:
            raise ValueError("Get GPI Invalid Signal!")

        return self.base_get_gpi_signal_asserted(signal)

    def set_gpo_signal(self, signal, state):
        """
        Set a GPO signal to the required state
        :param signal: signal to check :type: CsmGpoSignals
        :param state: set state, True '1', False '0'
        :return: ret_val True if command successful, else False
        """
        if signal not in CsmGpoSignals:
            raise ValueError("Set GPO Invalid Signal!")

        return self.base_set_gpo_signal(signal, state)

    def get_poe_pse_channel_status(self, ch_no):
        """
        Read the PoE PSE channel status for the specified channel
        :param ch_no: valid range 1..8 :type integer
        :return: [0] True if command successful, else False :type boolean
                 [1] CsmPoePseChannelStatus instance representing channel status
        """
        if int(ch_no) not in range(1, 9):
            raise ValueError("Invalid channel number = {}!".format(ch_no))

        ret_val = False
        chan_status = CsmPoePseChannelStatus()

        resp_dataclass_map = {
            "Port Mode": "port_mode",
            "Power Enable": "power_enable",
            "Power Good": "power_good",
            "Power On Fault": "power_on_fault",
            "2P4P Mode": "port_2p4p_mode",
            "Pwr Allocation": "power_allocation",
            "Class Status": "class_status",
            "Detect Status": "detection_status",
            "Voltage (mV)": "voltage_mv",
            "Current (mA)": "current_ma"
        }

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_POE_PSE_CHANNEL_STATUS_CMD + b" " +
                                    bytes(str(ch_no), encoding="UTF-8") + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_POE_PSE_CHANNEL_STATUS_END)

            # Was the command response terminator found or did it timeout?
            success_string = b"PoE Port " + bytes(str(ch_no), encoding="UTF-8") + b" Status:"
            if resp_str.find(self._GET_POE_PSE_CHANNEL_STATUS_END) != -1 and resp_str.find(success_string) != -1:
                for a_line in resp_str.decode("UTF-8").splitlines():
                    attr_name = resp_dataclass_map.get(a_line[0:a_line.find(':')], "")
                    if getattr(chan_status, attr_name, None) is not None:
                        setattr(chan_status, attr_name, int(a_line.split()[-1]))

                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, chan_status

    def get_poe_pse_temperature(self):
        """
        Query the PoE PSE device temperature
        :return: PoE PSE temperature, -255 if read fails :type integer
        """
        temperature = -255.0

        # Ensure the PoE PSE I2C buffer is enabled
        if self._serial_port is not None:
            if self.set_gpo_signal(CsmGpoSignals.ZER_I2C_POE_EN, True):
                self._serial_port.write(self._GET_POE_PSE_TEMP_VOLTAGE_CMD + self._SET_CMD_END)
                resp_str = self._serial_port.read_until(self._GET_POE_PSE_TEMP_VOLTAGE_END)

                # Was the command response terminator found or did it timeout?
                if self._GET_POE_PSE_TEMP_VOLTAGE_END in resp_str:
                    for a_line in resp_str.splitlines():
                        if b"Temp (0.1 dC):" in a_line:
                            temperature = float(a_line.split()[-1]) / 10.0
                            break
        else:
            raise RuntimeError("Serial port is not open!")

        return temperature


class MpZeroiseMircoTestInterface(CommonZeroiseMircoTestInterface):
    """
    Concrete class for wrapping up the common interface to the Manpack CSM Zeroise Microcontroller Test
    Utility Interface.
    """

    def __init__(self, com_port=None):
        """
        Class constructor
        :param: COM port associated with the interface :type: string
        :return: None
        """
        super().__init__(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "MpTestJigInterface({!r})".format(self._com_port)

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the serial port"""
        self.close_com_port()

    def get_gpi_signal_asserted(self, signal):
        """
        Check if a GPI signal is asserted.
        :param signal: signal to check :type: MpGpiSignals
        :return: ret_val True if command successful, else False; signal_asserted True if asserted, else False
        """
        if signal not in MpGpiSignals:
            raise ValueError("Get GPI Invalid Signal!")

        return self.base_get_gpi_signal_asserted(signal)

    def set_gpo_signal(self, signal, state):
        """
        Set a GPO signal to the required state
        :param signal: signal to check :type: MpGpoSignals
        :param state: set state, True '1', False '0'
        :return: ret_val True if command successful, else False
        """
        if signal not in MpGpoSignals:
            raise ValueError("Set GPO Invalid Signal!")

        return self.base_set_gpo_signal(signal, state)

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
