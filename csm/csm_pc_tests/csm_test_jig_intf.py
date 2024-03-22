#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0358-00 CSM Test Jig
Utility software running on the KT-000-0197-00 CSM Test Jig STM32 microcontroller.

Software compatibility:
- KT-956-0358-00 K-CEMA CSM Test Jig Utility - v1.0.0
- KT-956-0259-00 K-CEMA Manpack CSM Test Jig Utility - v1.1.0
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
from collections import OrderedDict
from enum import Enum
import logging
import time

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
class CsmTestJigGpoSignals(Enum):
    """ Enumeration class for CSM Test Jig GPO signals """
    POWER_CABLE_DETECT = 0
    TAMPER_SWITCH = 1
    SOM_SD_BOOT_ENABLE = 2
    RCU_POWER_BUTTON = 3
    RCU_POWER_ENABLE_ZEROISE = 4
    KEYPAD_POWER_BUTTON = 5
    KEYPAD_POWER_ENABLE_ZEROISE = 6
    REMOTE_POWER_ON_IN = 7


class MpTestJigGpoSignals(Enum):
    """ Enumeration class for Manpack Test Jig GPO signals """
    TAMPER_SWITCH = 0
    RCU_POWER_BUTTON = 1
    SOM_SD_BOOT_ENABLE = 2
    RCU_POWER_ENABLE_ZEROISE = 3
    CONTROL_PORT_POWER_ENABLE = 11
    CONTROL_PORT_MASTER_SELECT_N = 12
    CONTROL_PORT_RF_MUTE_N = 15
    CONTROL_PORT_RF_MUTE_DIRECTION = 16


class CsmTestJigPpsSource(Enum):
    """ Enumeration class for CSM Test Jig 1PPS sources """
    RCU_PPS = 0
    CSM_MASTER_PPS = 1
    CSM_SLAVE_PPS = 2


class MpTestJigPpsSource(Enum):
    """ Enumeration class for Manpack Test Jig 1PPS sources """
    RCU = 0
    CONTROL_MASTER_SLAVE = 1
    NTM1 = 2
    NTM2 = 3
    NTM3 = 4


class CsmTestJigUartSource(Enum):
    """ Enumeration class for CSM Test Jig UART detection sources"""
    CSM_MASTER_UART = 0
    CSM_SLAVE_UART = 1


class MpTestJigNtmI2cBus(Enum):
    """ Enumeration class for Manpack Test Jig NTM I2C buses """
    NONE = 0
    NTM1 = 1
    NTM2 = 2
    NTM3 = 3


class MpTestJigNtmFanPwm(Enum):
    """ Enumeration class for Manpack Test Jig NTM fan PWM sources """
    FAN_1_1 = 0
    FAN_2_1 = 1
    FAN_2_2 = 2
    FAN_3_1 = 3


class NtmHwConfigInfo:
    """
    Class for encapsulating NTM Hardware Config Information
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
        return "CtsHwConfigInfo({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
                self.hw_version_no, self.hw_mod_version_no, self.assy_part_no, self.assy_rev_no,
                self.assy_serial_no, self.assy_build_batch_no, self.hw_info_valid)


class CommonCsmTestJigInterface:
    """
    Base class for wrapping up the interface to the CSM and Manpack Test Jig Utility Interface, contains elements
    that are common to both the CSM and Manpack Test Jigs, separate classes are implemented for test jig specific
    elements.
    """
    _POWER_ON_TIME_S = 1.1
    _HARD_POWER_OFF_TIME_S = 12.0
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _GET_ADC_CMD = b"$ADC"
    _GET_ADC_CMD_SUCCESS = b"!ADC\r\n"
    _SET_GPO_CMD = b"#GPO"
    _SET_GPO_CMD_SUCCESS = b">GPO\r\n"
    _SET_GPO_RCU_POWER_BUTTON_RESP = b"RCU Power Button set to: "
    _SET_GPO_ASSERT_SIGNAL_RESP = b" set to: "
    _GET_GPI_CMD = b"$GPI"
    _GET_GPI_CMD_SUCCESS = b"!GPI\r\n"
    _SET_PPS_SOURCE_CMD = b"#PPSS"
    _SET_PPS_SOURCE_CMD_SUCCESS = b">PPSS"
    _SET_PPS_SOURCE_RESP = b"1PPS Source Selected"
    _GET_PPS_INPUT_DETECTED_CMD = b"$PPS"
    _GET_PPS_INPUT_DETECTED_CMD_SUCCESS = b"!PPS"
    _GET_PPS_INPUT_DETECTED_RESP = b"1PPS detected"
    _SET_PPS_OUTPUT_ENABLE_CMD = b"#PPS"
    _SET_PPS_OUTPUT_ENABLE_CMD_SUCCESS = b">PPS"
    _SET_PPS_OUTPUT_ENABLE_RESP = b"1PPS Enabled"
    _SET_PPS_OUTPUT_DISABLE_RESP = b"1PPS Disabled"
    _SET_PPS_DIRECTION_CMD = b"#PPSD"
    _SET_PPS_DIRECTION_CMD_SUCCESS = b">PPSD"

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
            if self._GET_ADC_CMD_SUCCESS in resp_str:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 3:
                        adc_data[" ".join(split_line[1:])] = int(split_line[0])
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, adc_data

    def base_toggle_rcu_power_button(self, rcu_power_button, hard_power_off=False):
        """
        Simulate the RCU Power Button being pressed
        :param hard_power_off: Set to True to simulate hard 10-second power off
        :param rcu_power_button: RCU Power Button GPO signal :type CsmTestJigGpoSignals or MpTestJigGpoSignals
        :return: True if successful, else False
        """
        if rcu_power_button not in CsmTestJigGpoSignals and rcu_power_button not in MpTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        toggle_vals = [1, 0]

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            ret_val = True

            for toggle_val in toggle_vals:
                cmd_str = self._SET_GPO_CMD + " {} {}".format(rcu_power_button.value,
                                                              toggle_val).encode("UTF-8")
                self._serial_port.write(cmd_str + self._SET_CMD_END)
                resp_str = self._serial_port.read_until(self._SET_GPO_CMD_SUCCESS)

                ret_val = self._SET_GPO_CMD_SUCCESS in resp_str and \
                          self._SET_GPO_RCU_POWER_BUTTON_RESP in resp_str and ret_val

                time.sleep(self._HARD_POWER_OFF_TIME_S) if (hard_power_off and toggle_val) else \
                    time.sleep(self._POWER_ON_TIME_S)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def base_assert_gpo_signal(self, gpo_signal, assert_value):
        """
        Assert/de-assert the RCU power enable zeroise signal
        :param gpo_signal: GPO signal to assert/de-assert :type CsmTestJigGpoSignals or MpTestJigGpoSignals
        :param assert_value: Set to True to assert signal, False to de-assert
        :return: True if successful, else False
        """
        if gpo_signal not in CsmTestJigGpoSignals and gpo_signal not in MpTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_GPO_CMD + " {} {}".format(gpo_signal.value,
                                                          1 if assert_value else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_GPO_CMD_SUCCESS)
            ret_val = self._SET_GPO_CMD_SUCCESS in resp_str and self._SET_GPO_ASSERT_SIGNAL_RESP in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_gpi_state(self):
        """
        Read the state of the test jig's general purpose inputs
        :return [0]: True if ADC read, else False
        :return [1]: Dictionary of GPI data {"signal name": signal value, ...} :type OrderedDict
        """
        ret_val = False
        gpi_data = OrderedDict()

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_GPI_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_GPI_CMD_SUCCESS)

            # Was the command response terminator found or did it timeout?
            if self._GET_GPI_CMD_SUCCESS in resp_str:
                for a_line in resp_str.splitlines():
                    split_line = a_line.decode("UTF-8").split()
                    if len(split_line) > 3:
                        gpi_data[" ".join(split_line[2:])] = int(split_line[0])
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, gpi_data

    def set_pps_source(self, pps_source):
        """
        Set the PPS source from the Board/Unit to the Test Jig NUCLEO board
        :param pps_source: the required PPS source :type CsmTestJigPpsSource
        :return: True if successful, else False
        """
        if pps_source not in CsmTestJigPpsSource and pps_source not in MpTestJigPpsSource:
            raise ValueError("Incorrect PPS Source Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_PPS_SOURCE_CMD + " {}".format(pps_source.value).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_PPS_SOURCE_CMD_SUCCESS)
            ret_val = self._SET_PPS_SOURCE_CMD_SUCCESS in resp_str and self._SET_PPS_SOURCE_RESP in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

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
            ret_val = self._GET_PPS_INPUT_DETECTED_CMD_SUCCESS in resp_str and \
                      self._GET_PPS_INPUT_DETECTED_RESP in resp_str

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
            ret_val = self._SET_PPS_OUTPUT_ENABLE_CMD_SUCCESS in resp_str and \
                      ((self._SET_PPS_OUTPUT_ENABLE_RESP in resp_str and enable) or
                       (self._SET_PPS_OUTPUT_DISABLE_RESP in resp_str and not enable))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val


class CsmTestJigInterface(CommonCsmTestJigInterface):
    """
    Class for wrapping up the interface to the CSM Test Jig Utility Interface
    """
    _SET_PPS_DIRECTION_OUTPUT_RESP = b"CSM Slave 1PPS direction Output"
    _SET_PPS_DIRECTION_INPUT_RESP = b"CSM Slave 1PPS direction Input"
    _SET_UART_DETECT_SOURCE_CMD = b"#USS"
    _SET_UART_DETECT_SOURCE_CMD_SUCCESS = b">USS"
    _SET_UART_DETECT_SOURCE_RESP = b"UART Source Selected"
    _SET_START_UART_DETECTION_CMD = b"#UDET"
    _SET_START_UART_DETECTION_CMD_SUCCESS = b">UDET"
    _SET_START_UART_DETECTION_RESP = b"Started searching for string:"
    _GET_UART_INPUT_DETECTED_CMD = b"$UDET"
    _GET_UART_INPUT_DETECTED_CMD_SUCCESS = b"!UDET"
    _GET_UART_INPUT_DETECTED_RESP = b"String found:"

    def __init__(self, com_port=None):
        """
        Class constructor - just call the base class with the com_port parameter
        :param: optional parameter COM port associated with the interface :type string
        :return: N/A
        """
        super().__init__(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "CsmTestJigInterface({!r})".format(self._com_port)

    def assert_gpo_signal(self, gpo_signal, assert_value):
        """
        Assert/de-assert the specified GPO signal.
        :param gpo_signal: GPO signal to assert/de-assert CsmTestJigGpoSignals
        :param assert_value: Set to True to assert signal, False to de-assert
        :return: True if successful, else False
        """
        if gpo_signal not in CsmTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        return self.base_assert_gpo_signal(gpo_signal, assert_value)

    def toggle_rcu_power_button(self, hard_power_off=False):
        """
        Simulate the RCU Power Button being pressed
        :param hard_power_off: Set to True to simulate hard 10-second power off
        :return: True if successful, else False
        """
        return self.base_toggle_rcu_power_button(CsmTestJigGpoSignals.RCU_POWER_BUTTON, hard_power_off)

    def set_pps_direction(self, output):
        """
        Set the CSM Slave interface PPS direction
        :param output: Set to True to enable PPS output to CSM, False to enable input from CSM :type Boolean
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_PPS_DIRECTION_CMD + "{}".format(1 if output else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_PPS_DIRECTION_CMD_SUCCESS)
            ret_val = self._SET_PPS_DIRECTION_CMD_SUCCESS in resp_str and \
                      ((self._SET_PPS_DIRECTION_OUTPUT_RESP in resp_str and output) or
                       (self._SET_PPS_DIRECTION_INPUT_RESP in resp_str and not output))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_uart_source(self, uart_source):
        """
        Set the UART source from the CSM to the Test Jig NUCLEO board
        :param uart_source: the required UART source :type CsmTestJigUartSource
        :return: True if successful, else False
        """
        if uart_source not in CsmTestJigUartSource:
            raise ValueError("Incorrect PPS Source Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_UART_DETECT_SOURCE_CMD + " {}".format(uart_source.value).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_UART_DETECT_SOURCE_CMD_SUCCESS)
            ret_val = self._SET_UART_DETECT_SOURCE_CMD_SUCCESS in resp_str and \
                      self._SET_UART_DETECT_SOURCE_RESP in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def start_uart_detection(self):
        """
        Start the test jig NUCLEO board looking for the test string on the selected UART
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._SET_START_UART_DETECTION_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_START_UART_DETECTION_CMD_SUCCESS)
            ret_val = self._SET_START_UART_DETECTION_CMD_SUCCESS in resp_str and \
                      self._SET_START_UART_DETECTION_RESP in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_uart_detected(self):
        """
        Check if the test jig NUCLEO board has received the test string on the selected port
        :return: True if test string detected, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_UART_INPUT_DETECTED_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_UART_INPUT_DETECTED_CMD_SUCCESS)

            # Was the command response terminator found or did it timeout?
            ret_val = self._GET_UART_INPUT_DETECTED_CMD_SUCCESS in resp_str and \
                      self._SET_PPS_OUTPUT_ENABLE_RESP in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val


class MpTestJigInterface(CommonCsmTestJigInterface):
    """
    Class for wrapping up the interface to the Manpack Test Jig Utility Interface
    """
    _SET_PPS_DIRECTION_OUTPUT_RESP = b"Control Master/Slave 1PPS direction Output"
    _SET_PPS_DIRECTION_INPUT_RESP = b"Control Master/Slave 1PPS direction Input"
    _GET_HW_CONFIG_INFO_CMD = b"$HCI"
    _GET_HW_CONFIG_INFO_RESP_END = b"!HCI\r\n"
    _RESET_HW_CONFIG_INFO_CMD = b"#RHCI"
    _RESET_HW_CONFIG_INFO_RESP_END = b">RHCI\r\n"
    _RESET_HW_CONFIG_INFO_SUCCESS = b"Successfully cleared HCI EEPROM"
    _SET_NTM_HW_CONFIG_INFO_CMD = b"#SHCI"
    _SET_NTM_HW_CONFIG_INFO_RESP_END = b">SHCI\r\n"
    _SET_NTM_HW_CONFIG_INFO_PART_NO_SUCCESS = b"Successfully set parameter [Part No] to"
    _SET_NTM_HW_CONFIG_INFO_REV_NO_SUCCESS = b"Successfully set parameter [Revision No] to"
    _SET_NTM_HW_CONFIG_INFO_SERIAL_NO_SUCCESS = b"Successfully set parameter [Serial No] to"
    _SET_NTM_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS = b"Successfully set parameter [Build Batch No] to"
    _SET_NTM_I2C_BUS_SOURCE_CMD = b"#I2CB"
    _SET_NTM_I2C_BUS_SOURCE_CMD_SUCCESS = b">I2CB"
    _SET_NTM_I2C_BUS_SOURCE_RESP = "I2C Bus {} Selected"
    _INIT_FAN_CONTROLLER_CMD = b"#INIFAN"
    _INIT_FAN_CONTROLLER_CMD_SUCCESS = b"EMC2104 fan controller successfully initialised"
    _GET_FAN_SPEED_CMD = b"$FSP"
    _GET_FAN_SPEED_CMD_SUCCESS = b"!FSP"
    _GET_FAN_SPEED_FAN1_RPM_RESP = b"Fan 1 Speed RPM"
    _GET_FAN_SPEED_FAN2_RPM_RESP = b"Fan 2 Speed RPM"
    _GET_FAN_DUTY_CMD = b"$FDS"
    _GET_FAN_DUTY_CMD_SUCCESS = b"!FDS"
    _GET_FAN_DUTY_RESP = b"Fan PWM Duty"
    _SET_FAN_DUTY_CMD = b"#FDS"
    _SET_FAN_DUTY_CMD_SUCCESS = b">FDS"
    _SET_FAN_DUTY_RESP = "Set direct fan drive duty setting: {}"
    _SET_NTM_FAN_PWM_SOURCE_CMD = b"#FPS"
    _SET_NTM_FAN_PWM_SOURCE_CMD_SUCCESS = b">FPS"
    _SET_NTM_FAN_PWM_SOURCE_RESP = "Fan PWM Source {} Selected"

    def __init__(self, com_port=None):
        """
        Class constructor - just call the base class with the com_port parameter
        :param: optional parameter COM port associated with the interface :type string
        :return: N/A
        """
        super().__init__(com_port)

    def __repr__(self):
        """ :return: string representing the class """
        return "MpTestJigInterface({!r})".format(self._com_port)

    def assert_gpo_signal(self, gpo_signal, assert_value):
        """
        Assert/de-assert the specified GPO signal.
        :param gpo_signal: GPO signal to assert/de-assert MpTestJigGpoSignals
        :param assert_value: Set to True to assert signal, False to de-assert
        :return: True if successful, else False
        """
        if gpo_signal not in MpTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        return self.base_assert_gpo_signal(gpo_signal, assert_value)

    def toggle_rcu_power_button(self, hard_power_off=False):
        """
        Simulate the RCU Power Button being pressed
        :param hard_power_off: Set to True to simulate hard 10-second power off
        :return: True if successful, else False
        """
        return self.base_toggle_rcu_power_button(MpTestJigGpoSignals.RCU_POWER_BUTTON, hard_power_off)

    def set_pps_direction(self, output):
        """
        Set the CSM Slave interface PPS direction
        :param output: Set to True to enable PPS output to CSM, False to enable input from CSM :type Boolean
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_PPS_DIRECTION_CMD + "{}".format(1 if output else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_PPS_DIRECTION_CMD_SUCCESS)
            ret_val = self._SET_PPS_DIRECTION_CMD_SUCCESS in resp_str and \
                      ((self._SET_PPS_DIRECTION_OUTPUT_RESP in resp_str and output) or
                       (self._SET_PPS_DIRECTION_INPUT_RESP in resp_str and not output))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_hw_config_info(self):
        """
        Read the Digital Board's hardware config information.
        :return [0]: True if command successful, else False
        :return [1]: CtsHwConfigInfo object containing read data, None if the read fails
        """
        ret_val = False
        hci = None

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_HW_CONFIG_INFO_CMD + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._GET_HW_CONFIG_INFO_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_HW_CONFIG_INFO_RESP_END in resp_str:
                # Split response by lines then process to extract data
                hci = NtmHwConfigInfo()
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
            cmd_str = self._RESET_HW_CONFIG_INFO_CMD + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._RESET_HW_CONFIG_INFO_RESP_END)

            # Was the command response terminator found or did it timeout?
            ret_val = self._RESET_HW_CONFIG_INFO_RESP_END in resp_str and self._RESET_HW_CONFIG_INFO_SUCCESS in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_ntm_hw_config_info(self, assy_part_no, assy_rev_no, assy_serial_no, assy_build_batch_no):
        """
        Set the NTM Hardware Configuration Information, strings are truncated to 15 characters
        plus Null termination.
        Need to select the required NTM I2C bus interface before calling this method.
        :param assy_build_batch_no: :type string
        :param assy_serial_no: :type string
        :param assy_rev_no: :type string
        :param assy_part_no: :type string
        :return: True if Hardware Configuration Information set, else False
        """
        ret_val = True

        if type(assy_part_no) is not str or type(assy_rev_no) is not str or \
           type(assy_serial_no) is not str or type(assy_build_batch_no) is not str:
            raise TypeError("One of the parameters is not of type str!")

        id_val = [(0, assy_part_no, self._SET_NTM_HW_CONFIG_INFO_PART_NO_SUCCESS),
                  (1, assy_rev_no, self._SET_NTM_HW_CONFIG_INFO_REV_NO_SUCCESS),
                  (2, assy_serial_no, self._SET_NTM_HW_CONFIG_INFO_SERIAL_NO_SUCCESS),
                  (3, assy_build_batch_no, self._SET_NTM_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS)]

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            for param_id, param_val, param_success in id_val:
                cmd_str = "{} {} {}{}".format(self._SET_NTM_HW_CONFIG_INFO_CMD.decode("UTF-8"),
                                              param_id, param_val[0:15],
                                              self._SET_CMD_END.decode("UTF-8"))
                self._serial_port.write(bytes(cmd_str.encode("UTF-8")))
                resp_str = self._serial_port.read_until(self._SET_NTM_HW_CONFIG_INFO_RESP_END)

                # Was the command response terminator found or did it timeout?
                ret_val = self._SET_NTM_HW_CONFIG_INFO_RESP_END in resp_str and param_success in resp_str and ret_val
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_ntm_i2c_bus(self, bus):
        """
        Set the NTM I2C bus source from the CSM to the Test Jig NUCLEO board
        :param bus: the required I2C bus source :type MpTestJigNtmI2cBus
        :return: True if successful, else False
        """
        if bus not in MpTestJigNtmI2cBus:
            raise ValueError("Incorrect NTM I2C Bus Source Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_NTM_I2C_BUS_SOURCE_CMD + " {}".format(bus.value).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_NTM_I2C_BUS_SOURCE_CMD_SUCCESS)
            ret_val = self._SET_NTM_I2C_BUS_SOURCE_CMD_SUCCESS in resp_str and \
                      self._SET_NTM_I2C_BUS_SOURCE_RESP.format(bus.value).encode("UTF-8") in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def initialise_fan_controller(self):
        """
        Initialise a connected NTM EMC2104 fan controller IC.
        Need to select the required NTM I2C bus interface before calling this method.
        :return: True if Hardware Configuration Information set, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._INIT_FAN_CONTROLLER_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._INIT_FAN_CONTROLLER_CMD_SUCCESS)
            ret_val = self._INIT_FAN_CONTROLLER_CMD_SUCCESS in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def get_ntm_fan_speed(self):
        """
        Read the connected NTM EMC2104 fan speed registers.
        Need to select the required NTM I2C bus interface before calling this method.
        :return: [0] fan1_speed_rpm :type Integer; [1] fan2_speed_rpm :type Integer
        """
        fan1_speed_rpm = -1
        fan2_speed_rpm = -1

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_FAN_SPEED_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._GET_FAN_SPEED_CMD_SUCCESS)

            for a_line in resp_str.splitlines():
                if self._GET_FAN_SPEED_FAN1_RPM_RESP in a_line:
                    fan1_speed_rpm = int(a_line.decode("UTF-8").split()[-1])
                elif self._GET_FAN_SPEED_FAN2_RPM_RESP in a_line:
                    fan2_speed_rpm = int(a_line.decode("UTF-8").split()[-1])
        else:
            raise RuntimeError("Serial port is not open!")

        return fan1_speed_rpm, fan2_speed_rpm

    def get_ntm_fan_duty_percent(self):
        """
        Read the connected NTM EMC2104 fan duty cycle percentage.
        Need to select the required NTM I2C bus interface before calling this method.
        :return: fan duty cycle percentage :type Integer
        """
        fan_duty_percent = -1

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            self._serial_port.write(self._GET_FAN_DUTY_CMD + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._GET_FAN_DUTY_CMD_SUCCESS)

            for a_line in resp_str.splitlines():
                if self._GET_FAN_DUTY_RESP in a_line:
                    fan_duty_percent = int(a_line.decode("UTF-8").split()[-2])
        else:
            raise RuntimeError("Serial port is not open!")

        return fan_duty_percent

    def set_ntm_fan_duty(self, duty_percent):
        """
        Set the connected NTM fan speed duty-cycle.
        Need to select the required NTM I2C bus interface before calling this method.
        :param duty_percent: required duty-cycle, range [0..100] :type Integer
        :return: True if setting duty-cycle is successful, else False
        """
        if duty_percent < 0 or duty_percent > 100:
            raise ValueError("Duty-cycle percentage outside allow range [0..100]")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_FAN_DUTY_CMD + " {}".format(int(duty_percent)).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_FAN_DUTY_CMD_SUCCESS)
            ret_val = self._SET_FAN_DUTY_CMD_SUCCESS in resp_str and \
                      self._SET_FAN_DUTY_RESP.format(int(duty_percent)).encode("UTF-8") in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_ntm_fan_source(self, fan_pwm):
        """
        Set the NTM I2C bus source from the CSM to the Test Jig NUCLEO board
        :param fan_pwm: the required I2C bus source :type MpTestJigNtmFanPwm
        :return: True if successful, else False
        """
        if fan_pwm not in MpTestJigNtmFanPwm:
            raise ValueError("Incorrect NTM Fan PWM Source Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_NTM_FAN_PWM_SOURCE_CMD + " {}".format(fan_pwm.value).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)

            resp_str = self._serial_port.read_until(self._SET_NTM_FAN_PWM_SOURCE_CMD_SUCCESS)
            ret_val = self._SET_NTM_FAN_PWM_SOURCE_CMD_SUCCESS in resp_str and \
                      self._SET_NTM_FAN_PWM_SOURCE_RESP.format(fan_pwm.value).encode("UTF-8") in resp_str
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
