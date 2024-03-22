#!/usr/bin/env python3
"""
Class that encapsulates the interface to the KT-956-0261-00 Integrated CTS
Test Jig Utility software running on the KT-000-0214-00 Integraged CTS Test
Jig STM32 microcontroller.

Software compatibility:
- KT-956-0261-00 K-CEMA Integrated CTS Test Jig Utility V1.0.0 onwards
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
class CtsTestJigRfBoardRxPaths(Enum):
    """ Enumeration class for RF Board receive paths """
    RX0_20_500_MHZ = 0
    RX1_500_800_MHZ = 1
    RX2_800_2000_MHZ = 2
    RX3_2000_2600_MHZ = 3
    RX4_2600_4400_MHZ = 4
    RX5_4400_6000_MHZ = 5
    ISOLATION = 6
    TX = 7


class CtsTestJigRfBoardTxPaths(Enum):
    """ Enumeration class for RF Board transmit paths """
    TX0_20_800_MHZ = 0
    TX1_700_1500_MHZ = 1
    TX2_1200_2700_MHZ = 2
    TX3_2400_6000_MHZ = 3


class CtsTestJigRfBoardTxDividerValues(Enum):
    """ Enumeration class for RF Board transmit divider values """
    DIVIDE_RATIO_1 = 0
    DIVIDE_RATIO_2 = 1
    DIVIDE_RATIO_4 = 3
    DIVIDE_RATIO_8 = 7


class CtsTestJigGpoSignals(Enum):
    """ Enumeration class for GPO signals """
    UUT_RF_BOARD_SYNTH_EN = 0
    UUT_RF_BOARD_NTX_RX_SEL = 1
    UUT_RF_BOARD_RX_PATH_MIXER_EN = 2
    UUT_RF_BOARD_P3V3_EN = 3
    UUT_RF_BOARD_P5V0_EN = 4
    UUT_RF_BOARD_P3V3_TX_EN = 5
    UUT_RF_BOARD_P5V0_TX_EN = 6
    UUT_DIGITAL_BOARD_CTS_POWER_EN = 7
    UUT_DIGITAL_BOARD_CTS_P12V_EN = 8
    UUT_DIGITAL_BOARD_CTS_P3V3_EN = 9


class CtsTestJigRfPaths(Enum):
    """ Enumeration class for test jig RF paths """
    DIGITAL_BOARD_TEST_RX_MODE = 0
    RF_BOARD_TEST_RX_MODE = 1
    RF_BOARD_TEST_TX_MODE = 2


class CtsHwConfigInfo:
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
        return "CtsHwConfigInfo({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
                self.hw_version_no, self.hw_mod_version_no, self.assy_part_no, self.assy_rev_no,
                self.assy_serial_no, self.assy_build_batch_no, self.hw_info_valid)


class CtsTestJigInterface:
    """
    Class for wrapping up the interface to the Integrated CTS Test Jig Utility Interface
    """
    _BAUD_RATE = 115200
    _RX_TIMEOUT = 3
    _SET_CMD_END = b"\r"
    _CMD_UNKNOWN = b"?\r\n"
    _SET_RX_ATTEN_CMD = b"#RXATT"
    _SET_RX_ATTEN_RESP_END = b">RXATT"
    _SET_RX_ATTEN_SUCCESS = "Set rx attenuator to {} (x0.5 dB)"
    _SET_RX_PATH_CMD = b"#RXP"
    _SET_RX_PATH_RESP_END = b">RXP"
    _SET_RX_PATH_SUCCESS = "Set rx path to {}"
    _SET_TX_ATTEN_CMD = b"#TXATT"
    _SET_TX_ATTEN_RESP_END = b">TXATT"
    _SET_TX_ATTEN_SUCCESS = "Set tx attenuator to {} (x0.5 dB)"
    _SET_TX_PATH_CMD = b"#TXP"
    _SET_TX_PATH_RESP_END = b">TXP"
    _SET_TX_PATH_SUCCESS = "Set tx path to {}"
    _SET_TX_DIVIDER_CMD = b"#TXD"
    _SET_TX_DIVIDER_RESP_END = b">TXD"
    _SET_TX_DIVIDER_SUCCESS = "Set tx divider to {}"
    _SET_GPO_CMD = b"#GPO"
    _SET_GPO_RESP_END = b">GPO\r\n"
    _SET_GPO_ASSERT_SIGNAL_SUCCESS = b" set to: "
    _SET_TEST_JIG_RF_PATH_CMD = b"#TRFP"
    _SET_TEST_JIG_RF_PATH_RESP_END = b">TRFP"
    _SET_TEST_JIG_RF_PATH_SUCCESS = "Set test board RF path to {}"
    _SET_PPS_OUTPUT_ENABLE_CMD = b"#PPSE"
    _SET_PPS_OUTPUT_ENABLE_RESP_END = b">PPSE"
    _SET_PPS_OUTPUT_ENABLE_RESP = b"1PPS Enabled"
    _SET_PPS_OUTPUT_DISABLE_RESP = b"1PPS Disabled"
    _GET_ADC_CMD = b"$ADC"
    _GET_ADC_CMD_RESP_END = b"!ADC\r\n"
    _GET_SYNTH_LD_CMD = b"$SYNLD"
    _GET_SYNTH_LD_RESP_END = b"!SYNLD"
    _GET_SYNTH_LD_LOCKED_RESP = b"Synth Lock Detect: 1"
    _GET_SYNTH_LD_UNLOCKED_RESP = b"Synth Lock Detect: 1"
    _SET_SYNTH_FREQUENCY_CMD = b"#SYNFQ"
    _SET_SYNTH_FREQUENCY_RESP_END = b">SYNFQ"
    _SET_SYNTH_FREQUENCY_SUCCESS = "Set synth to {} MHz"
    _SET_SYNTH_POWER_DOWN_CMD = b"#SYNPD"
    _SET_SYNTH_POWER_DOWN_RESP_END = b">SYNPD"
    _SET_SYNTH_POWER_DOWN_ENABLE_RESP = b"Set synth power down to: Enabled"
    _SET_SYNTH_POWER_DOWN_DISABLE_RESP = b"Set synth power down to: Disabled"
    _WRITE_SYNTH_REGISTER_CMD = b"#SYNRG"
    _WRITE_SYNTH_REGISTER_RESP_END = b">SYNRG"
    _WRITE_SYNTH_REGISTER_SUCCESS = b"Wrote synth register value: "
    _INITIALISE_SYNTH_CMD = b"#SYNI"
    _INITIALISE_SYNTH_RESP_END = b">SYNI"
    _INITIALISE_SYNTH_SUCCESS = b"Synth successfully initialised."
    _GET_HW_CONFIG_INFO_CMD = b"$HCI"
    _GET_HW_CONFIG_INFO_RESP_END = b"!HCI\r\n"
    _RESET_HW_CONFIG_INFO_CMD = b"#RHCI"
    _RESET_HW_CONFIG_INFO_RESP_END = b">RHCI\r\n"
    _RESET_HW_CONFIG_INFO_SUCCESS = b"Successfully cleared HCI EEPROM"
    _SET_HW_CONFIG_INFO_CMD = b"#SHCI"
    _SET_HW_CONFIG_INFO_RESP_END = b">SHCI\r\n"
    _SET_HW_CONFIG_INFO_PART_NO_SUCCESS = b"Successfully set parameter [Part No] to"
    _SET_HW_CONFIG_INFO_REV_NO_SUCCESS = b"Successfully set parameter [Revision No] to"
    _SET_HW_CONFIG_INFO_SERIAL_NO_SUCCESS = b"Successfully set parameter [Serial No] to"
    _SET_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS = b"Successfully set parameter [Build Batch No] to"
    _SET_I2C_LOOP_BACK_CMD = b"#ILB"
    _SET_I2C_LOOP_BACK_RESP_END = b">ILB\r\n"
    _SET_I2C_LOOP_BACK_SUCCESS = b"I2C Loopback Enable set to: "
    _EEPROM_WRITE_BYTE_CMD = b"#EWRB"
    _EEPROM_WRITE_BYTE_RESP_END = b">EWRB"
    _EEPROM_WRITE_BYTE_SUCCESS = "Write I2C EEPROM address 0x{:X}: 0x{:02X}"
    _EEPROM_READ_BYTE_CMD = b"$ERDB"
    _EEPROM_READ_BYTE_RESP_END = b"!ERDB"
    _EEPROM_READ_BYTE_RESP_DATA_LINE = b"Read I2C EEPROM address"
    _EEPROM_READ_PAGE_CMD = b"$ERDP"
    _EEPROM_READ_PAGE_RESP_END = b"!ERDP"
    _EEPROM_READ_PAGE_RESP_DATA_LINE = b"Read I2C EEPROM page address"

    def __init__(self, com_port=None, timeout=_RX_TIMEOUT):
        """
        Class constructor
        :param: optional parameter COM port associated with the interface :type string
        :return: N/A
        """
        self._rx_timeout = timeout
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
        self._serial_port = Serial(com_port, self._BAUD_RATE, timeout=self._rx_timeout,
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
        self._serial_port.read_until(self._CMD_UNKNOWN, self._rx_timeout)

    def set_rx_attenuator(self, attenuation_0_5db):
        """
        Set the RF Board Receive Attenuation
        :param attenuation_0_5db: required attenuation in 0.5 dB steps :type Integer
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_RX_ATTEN_CMD + " {}".format(int(attenuation_0_5db)).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_RX_ATTEN_RESP_END)

            ret_val = self._SET_RX_ATTEN_RESP_END in resp_str and \
                (self._SET_RX_ATTEN_SUCCESS.format(int(attenuation_0_5db)).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_rx_path(self, path):
        """
        Set the RF Board Receive Path
        :param path: required path enumerated value :type CtsTestJigRfBoardRxPaths
        :return: True if successful, else False
        """
        if path not in CtsTestJigRfBoardRxPaths:
            raise ValueError("Incorrect Rx Path Signal Type!")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_RX_PATH_CMD + " {}".format(path.value).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_RX_PATH_RESP_END)

            ret_val = self._SET_RX_PATH_RESP_END in resp_str and \
                (self._SET_RX_PATH_SUCCESS.format(path.value).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_tx_attenuator(self, attenuation_0_5db):
        """
        Set the Transmit Attenuation
        :param attenuation_0_5db: required attenuation in 0.5 dB steps :type Integer
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_TX_ATTEN_CMD + " {}".format(int(attenuation_0_5db)).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_TX_ATTEN_RESP_END)

            ret_val = self._SET_TX_ATTEN_RESP_END in resp_str and \
                (self._SET_TX_ATTEN_SUCCESS.format(int(attenuation_0_5db)).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_tx_path(self, path):
        """
        Set the RF Board Transmit Path
        :param path: required path enumerated value :type CtsTestJigRfBoardTxPaths
        :return: True if successful, else False
        """
        if path not in CtsTestJigRfBoardTxPaths:
            raise ValueError("Incorrect Tx Path Signal Type!")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_TX_PATH_CMD + " {}".format(path.value).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_TX_PATH_RESP_END)

            ret_val = self._SET_TX_PATH_RESP_END in resp_str and \
                (self._SET_TX_PATH_SUCCESS.format(path.value).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_tx_divider_value(self, value):
        """
        Set the RF Board Transmit Path divider value
        :param value: required divider value, enumerated value :type CtsTestJigRfBoardTxDividerValues
        :return: True if successful, else False
        """
        if value not in CtsTestJigRfBoardTxDividerValues:
            raise ValueError("Incorrect Tx Path Divider Value Type!")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_TX_DIVIDER_CMD + " {}".format(value.value).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_TX_DIVIDER_RESP_END)

            ret_val = self._SET_TX_DIVIDER_RESP_END in resp_str and \
                (self._SET_TX_DIVIDER_SUCCESS.format(value.value).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_gpo_signal(self, gpo_signal,  set_value):
        """
        Assert/de-assert the specified GPO signal
        :param gpo_signal: GPO signal to assert/de-assert :type CtsTestJigGpoSignals
        :param set_value: True to set signal high, False to set signal low
        :return: True if successful, else False
        """
        if gpo_signal not in CtsTestJigGpoSignals:
            raise ValueError("Incorrect GPO Signal Type")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_GPO_CMD + " {} {}".format(gpo_signal.value, 1 if set_value else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._SET_GPO_RESP_END)

            ret_val = (self._SET_GPO_RESP_END in resp_str and self._SET_GPO_ASSERT_SIGNAL_SUCCESS in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_test_jig_rf_path(self, path):
        """
        Set the test jig RF path
        :param path: required path enumerated value :type CtsTestJigRfPaths
        :return: True if successful, else False
        """
        if path not in CtsTestJigRfPaths:
            raise ValueError("Incorrect Tx Path Signal Type!")

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_TEST_JIG_RF_PATH_CMD + " {}".format(path.value).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_TEST_JIG_RF_PATH_RESP_END)

            ret_val = self._SET_TEST_JIG_RF_PATH_RESP_END in resp_str and \
                (self._SET_TEST_JIG_RF_PATH_SUCCESS.format(path.value).encode("UTF-8") in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def enable_pps_output(self, enable):
        """
        Enable/disable the PPS output from the test jig NUCLEO board to the CSM Slave interface
        :param enable: Set to True to enable PPS output, False to disable :type Boolean
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_PPS_OUTPUT_ENABLE_CMD + " {}".format(1 if enable else 0).encode("UTF-8")
            self._serial_port.write(cmd_str + self._SET_CMD_END)
            resp_str = self._serial_port.read_until(self._SET_PPS_OUTPUT_ENABLE_RESP_END)

            ret_val = self._SET_PPS_OUTPUT_ENABLE_RESP_END in resp_str and \
                ((self._SET_PPS_OUTPUT_ENABLE_RESP in resp_str and enable) or
                 (self._SET_PPS_OUTPUT_DISABLE_RESP in resp_str and not enable))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

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
            cmd_str = self._GET_ADC_CMD + self._SET_CMD_END
            self._serial_port.write(cmd_str)
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

    def get_synth_lock_detect(self):
        """
        Get the state of the synth lock detect signal
        :return[0]: success, True if command successful, else False
        :return[1]: lock_state, True for locked, False for unlocked, None if the command fails
        """
        ret_val = False
        locked = None

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._GET_SYNTH_LD_CMD + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._GET_SYNTH_LD_RESP_END)

            # Was the command response terminator found or did it timeout?
            if self._GET_SYNTH_LD_RESP_END in resp_str:
                locked = True if self._GET_SYNTH_LD_LOCKED_RESP in resp_str else False
                ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, locked

    def set_synth_frequency_mhz(self, frequency_mhz):
        """
        Set the synth frequency.
        :param frequency_mhz: required frequency in MHz :type Integer
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_SYNTH_FREQUENCY_CMD + " {}".format(frequency_mhz).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_SYNTH_FREQUENCY_RESP_END)

            ret_val = self._SET_SYNTH_FREQUENCY_RESP_END in resp_str and \
                (self._SET_SYNTH_FREQUENCY_SUCCESS.format(int(frequency_mhz)).encode("UTF-8") in resp_str)

        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_synth_power_down(self, power_down):
        """
        Power down the synth
        :param power_down: True to power down synth, False to power up
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_SYNTH_POWER_DOWN_CMD + " {}".format(1 if power_down else 0).encode("UTF-8") + \
                self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_SYNTH_POWER_DOWN_RESP_END)

            ret_val = self._SET_SYNTH_POWER_DOWN_RESP_END in resp_str and \
                ((self._SET_SYNTH_POWER_DOWN_ENABLE_RESP in resp_str and power_down) or
                 (self._SET_SYNTH_POWER_DOWN_DISABLE_RESP in resp_str and not power_down))
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def write_synth_register(self, reg_data):
        """
        Write the specified synth register data value
        :param reg_data: 32-bit data register word to write to the synth :type Integer
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._WRITE_SYNTH_REGISTER_CMD + " {:x}".format(reg_data).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._WRITE_SYNTH_REGISTER_RESP_END)

            ret_val = self._WRITE_SYNTH_REGISTER_RESP_END in resp_str and self._WRITE_SYNTH_REGISTER_SUCCESS in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def initialise_synth(self):
        """
        Power down the synth
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._INITIALISE_SYNTH_CMD + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._INITIALISE_SYNTH_RESP_END)

            ret_val = self._INITIALISE_SYNTH_RESP_END in resp_str and self._INITIALISE_SYNTH_SUCCESS in resp_str
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
                hci = CtsHwConfigInfo()
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
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._RESET_HW_CONFIG_INFO_RESP_END)

            # Was the command response terminator found or did it timeout?
            ret_val = self._RESET_HW_CONFIG_INFO_RESP_END in resp_str and self._RESET_HW_CONFIG_INFO_SUCCESS in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_hw_config_info(self, assy_part_no, assy_rev_no, assy_serial_no, assy_build_batch_no):
        """
        Set the Digital Board Hardware Configuration Information, strings are truncated to 15 characters
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
            raise TypeError("One of the parameters is not of type str!")

        id_val = [(0, assy_part_no, self._SET_HW_CONFIG_INFO_PART_NO_SUCCESS),
                  (1, assy_rev_no, self._SET_HW_CONFIG_INFO_REV_NO_SUCCESS),
                  (2, assy_serial_no, self._SET_HW_CONFIG_INFO_SERIAL_NO_SUCCESS),
                  (3, assy_build_batch_no, self._SET_HW_CONFIG_INFO_BUILD_BATCH_NO_SUCCESS)]

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()

            for param_id, param_val, param_success in id_val:
                cmd_str = "{} {} {}{}".format(self._SET_HW_CONFIG_INFO_CMD.decode("UTF-8"),
                                              param_id, param_val[0:15],
                                              self._SET_CMD_END.decode("UTF-8"))
                self._serial_port.write(bytes(cmd_str.encode("UTF-8")))
                resp_str = self._serial_port.read_until(self._SET_HW_CONFIG_INFO_RESP_END)

                # Was the command response terminator found or did it timeout?
                ret_val = self._SET_HW_CONFIG_INFO_RESP_END in resp_str and param_success in resp_str and ret_val
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def set_i2c_loop_back_enable(self, enable):
        """
        Assert/de-assert the specified GPO signal
        :param enable: True to enable, False to disable
        :return: True if successful, else False
        """
        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._SET_I2C_LOOP_BACK_CMD + " {}".format(1 if enable else 0).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._SET_I2C_LOOP_BACK_RESP_END)

            ret_val = (self._SET_I2C_LOOP_BACK_RESP_END in resp_str and self._SET_I2C_LOOP_BACK_SUCCESS in resp_str)
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def eeprom_write_byte(self, address, data):
        """
        Write a byte to the test jig I2C EEPROM
        :param address: memory address to write to :type Integer
        :param data: data value to write to EEPROM :type Integer
        :return: True if successful, else False
        """
        address = int(address)
        data = int(data)

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._EEPROM_WRITE_BYTE_CMD + " {:x}".format(address).encode("UTF-8") + \
                " {:x}".format(data).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._EEPROM_WRITE_BYTE_RESP_END)

            success_str = self._EEPROM_WRITE_BYTE_SUCCESS.format(address, data).encode("UTF-8")
            ret_val = self._EEPROM_WRITE_BYTE_RESP_END in resp_str and success_str in resp_str
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val

    def eeprom_read_byte(self, address):
        """
        Read a byte from the test jig I2C EEPROM
        :param address: memory address to read from :type Integer
        :return [0]: True if successful, else False :type Boolean
        :return [1]: read data value :type Integer
        """
        address = int(address)
        ret_val = False
        data = 0xFF

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._EEPROM_READ_BYTE_CMD + " {:x}".format(address).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._EEPROM_READ_BYTE_RESP_END)

            if self._EEPROM_READ_BYTE_RESP_END in resp_str:
                for a_line in resp_str.splitlines():
                    if self._EEPROM_READ_BYTE_RESP_DATA_LINE in a_line:
                        data = int(a_line.decode("UTF-8").split()[-1], base=16)
                        ret_val = True
                        break
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, data

    def eeprom_read_page(self, address):
        """
        Read a page from the test jig I2C EEPROM
        :param address: start of page memory address to read from :type Integer
        :return [0]: True if successful, else False :type Boolean
        :return [1]: list of read data values :type Integer
        """
        address = int(address)
        ret_val = False
        data = []

        if self._serial_port is not None:
            self._synchronise_cmd_prompt()
            cmd_str = self._EEPROM_READ_PAGE_CMD + " {:x}".format(address).encode("UTF-8") + self._SET_CMD_END
            self._serial_port.write(cmd_str)
            resp_str = self._serial_port.read_until(self._EEPROM_READ_PAGE_RESP_END)

            if self._EEPROM_READ_PAGE_RESP_END in resp_str:
                split_lines = resp_str.splitlines()
                data_start_line = -1
                for i, a_line in enumerate(split_lines):
                    if self._EEPROM_READ_PAGE_RESP_DATA_LINE in a_line:
                        # Subsequent lines up to the response end include the read data...
                        data_start_line = i + 1
                        break

                if data_start_line > 0:
                    for i in range(data_start_line, len(split_lines)):
                        if split_lines[i] != self._EEPROM_READ_PAGE_RESP_END:
                            data.append(int(split_lines[i].decode("UTF-8").split()[-1], base=16))
                    ret_val = True
        else:
            raise RuntimeError("Serial port is not open!")

        return ret_val, data

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
