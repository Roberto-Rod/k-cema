#!/usr/bin/env python3
"""
KT-000-0139- Active Backplane board Production Test.

Classes and functions implementing production test cases for the KT-000-0139-00
Active Backplane board.

Hardware/software compatibility:
- KT-000-0164-00 K-CEMA Active Backplane Test Interface Board

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
import ipaddress
import logging
from os import popen
import platform
import time
from telnetlib import Telnet

# Third-party imports -----------------------------------------------
from tenma.tenmaDcLib import Tenma72Base

# Our own imports -------------------------------------------------
import ab_program_devices
from ab_serial_msg_intf import AbSerialMsgInterface, AbMsgId, AbMsgPayloadLen
from ab_test_jig_intf import AbTestJigInterface
from gbe_switch import TelnetGbeSwitch, GbeSwitchLinkState
import rpi4_iperf3 as rpi4ip3
from tl_sg3428 import TLSG3428
import win_iperf3 as winip3

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
class AbProdTest:
    """
    Class that implements Active Backplane, KT-000-0139-00 board production test cases
    """
    _ASSEMBLY_NO = "KT-000-0139-00"
    _BOARD_HOSTNAME = "ab-000000.local"
    _BOARD_GBE_SWITCH_TELNET_PORT = 31
    _UART_TEST_STRING = b"The quick brown fox jumped over the lazy dog!"
    _UART_TEST_TIMEOUT_SEC = 2
    _MANAGED_SWITCH_DEFAULT_ENABLED_PORTS = [1, 2, 3, 4, 5, 6, 7, 8]

    # Test Equipment Interfaces
    tpsu = None

    def __init__(self, tj_com_port, psu_com_port, tpl_sw_com_port, but_com_port,
                 segger_jlink_win32=None, segger_jlink_win64=None, asix_up_win32=None, asix_up_win64=None,
                 iperf3=None, cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param tj_com_port: test jig NUCLEO STM32 COM port :type String
        :param psu_com_port: Tenma bench PSU COM port :type String
        :param tpl_sw_com_port: TP-Link managed switch COM port :type String
        :param but_com_port: board under test CSM COM port :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use ab_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use ab_program_devices constant
        :param asix_up_win32: 32-bit Win ASIX UP exe path, default is None, use ab_program_devices constant
        :param asix_up_win64: 64-bit Win ASIX UP exe path, default is None, use ab_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        # Set test environment initial state
        log.info("INFO - Initialising test environment...")

        # PSU initialisation
        log.info("INFO - Initialising power supply")
        self._psu_com_port = psu_com_port
        self.tpsu = self._get_tenma_psu_instance()
        self.tpsu.OFF()
        log.info("INFO - Power supply initialisation complete - {}".format(self.tpsu.MATCH_STR))

        # Test jig interface initialisation
        log.info("INFO - Initialising test jig interface")
        self._tj_com_port = tj_com_port
        with AbTestJigInterface(self._tj_com_port) as tji:
            tji.set_dcdc_enable(False)
            tji.assert_system_reset(False)
        log.info("INFO - Test jig interface initialisation complete")

        # TP-Link switch Port 1-8 enabled, all other ports disabled
        log.info("INFO - Initialising TP Link switch...")
        self._tpl_sw_com_port = tpl_sw_com_port

        with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
            for port_no in range(1, tpl_sw.MAX_PORT_NO + 1):
                enable_port = port_no in self._MANAGED_SWITCH_DEFAULT_ENABLED_PORTS
                sync_cmd_prompt = (port_no == 1)
                tpl_sw.port_enable(port_no, enable_port, sync_cmd_prompt)
                log.debug("INFO - TP Link switch Port {} enabled:\t{}".format(port_no, enable_port))

        log.info("INFO - TP Link switch initialisation complete")

        # Override exe path constants in ab_program_devices and win_ip3 modules if exe path variables have been passed
        if segger_jlink_win32 is not None:
            ab_program_devices.JLINK_PATH_WIN32 = segger_jlink_win32
        if segger_jlink_win64 is not None:
            ab_program_devices.JLINK_PATH_WIN64 = segger_jlink_win64
        if asix_up_win32 is not None:
            ab_program_devices.ASIX_UP_PATH_WIN32 = asix_up_win32
        if asix_up_win64 is not None:
            ab_program_devices.JLINK_PATH_WIN64 = asix_up_win64
        if iperf3 is not None:
            winip3.IPERF3_EXECUTABLE = iperf3
        if cygwin1_dll is not None:
            winip3.CYGWIN_DLL = cygwin1_dll

        self._but_com_port = but_com_port
        log.info("INFO - Test environment initialisation complete")

    def __del__(self):
        """ Class destructor - Ensure the PSU and board are turned off """
        try:
            with AbTestJigInterface(self._tj_com_port) as tji:
                self._set_psu_but_off(tji)

            if self.tpsu is not None:
                self.tpsu.close()
        except Exception as ex:
            log.debug("Error raised closing PSU serial port - {}".format(ex))

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit """
        try:
            with AbTestJigInterface(self._tj_com_port) as tji:
                self._set_psu_but_off(tji)

            if self.tpsu is not None:
                self.tpsu.close()
        except Exception as ex:
            log.debug("Error raised closing PSU serial port - {}".format(ex))

    def main_power_supply_test(self):
        """
        Test the board under test's main supply, checks the DC-DC enable signal functionality and +3V3 rail
        voltage.
        :return: True if test passes, else False :type Boolean
        """
        ret_val = True

        if self.tpsu is not None:
            with AbTestJigInterface(self._tj_com_port) as tji:
                # Turn the Board Under Test and PSU output off
                self._set_psu_but_off(tji)

                # Set PSU voltage and current limit, then turn the output on
                self.tpsu.setVoltage(1, 28000)   # mV
                self.tpsu.setCurrent(1, 1000)    # mA
                self.tpsu.ON()
                time.sleep(2.0)

                # Check the PSU current
                psu_i = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (0 <= psu_i <= 10)
                log.info("{} - Bench PSU Current: {} < {} < {} mA".format("PASS" if test_pass else "FAIL",
                                                                          0, psu_i, 10))
                ret_val = ret_val and test_pass

                # Turn the Board Under Test On and Assert the Reset Signal, gives consistent measurement
                # if the board is programmed or un-programmed.
                tji.assert_system_reset(True)
                tji.set_dcdc_enable(True)
                time.sleep(5.0)

                # Check the PSU current
                psu_i = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (90 <= psu_i <= 120)
                log.info("{} - Bench PSU Current: {} < {} < {} mA".format("PASS" if test_pass else "FAIL",
                                                                          90, psu_i, 120))
                ret_val = ret_val and test_pass

                # Check the Board Under Test +3V3 rail
                read_success, vref_int_mv, but_3v3_mv = tji.get_adc_data()
                test_pass = read_success and (3135 <= but_3v3_mv <= 3465)
                log.info("{} - Board Under Test +3V3 {} <= {} <= {} mV".format("PASS" if test_pass else "FAIL",
                                                                               3135, but_3v3_mv, 3465))
                ret_val = ret_val and test_pass

                # Turn Board Under Test and PSU Output off
                self._set_psu_but_off(tji)
                tji.assert_system_reset(False)
        else:
            raise RuntimeError("PSU Test Equipment Error!")

        return ret_val

    def set_hw_config_info(self, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board under test's hardware configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        :param assy_rev_no: board assembly revision number :type String
        :param assy_serial_no: board assembly serial number :type String
        :param assy_batch_no: board build/batch number :type String
        :return: True if hardware configuration information set correctly, else False :type Boolean
        """
        ret_val = False

        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off and hold the board in reset
            self._set_psu_but_off(tji)
            tji.assert_system_reset(True)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            time.sleep(1.0)

            # Set hw config info
            if tji.set_hw_config_info(self._ASSEMBLY_NO, assy_rev_no, assy_serial_no, assy_batch_no):
                # Wait to ensure data has been written to EEPROM
                time.sleep(1.0)

                # Power-cycle the board
                self._set_psu_but_off(tji)
                self._set_psu_but_on(tji, 28000, 1000)
                time.sleep(1.0)

                # Read back hardware configuration information and check it is correct
                ret_val, hci = tji.get_hw_config_info()

                test_pass = (hci.assy_part_no == self._ASSEMBLY_NO)
                log.info("{} - Assembly No set to {}".format("PASS" if test_pass else "FAIL", self._ASSEMBLY_NO))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_rev_no == assy_rev_no)
                log.info("{} - Assembly Revision No set to {}".format("PASS" if test_pass else "FAIL", assy_rev_no))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_serial_no == assy_serial_no)
                log.info("{} - Assembly Serial No set to {}".format("PASS" if test_pass else "FAIL", assy_serial_no))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_build_batch_no == assy_batch_no)
                log.info("{} - Assembly Batch No set to {}".format("PASS" if test_pass else "FAIL", assy_batch_no))
                ret_val = ret_val and test_pass

                log.info("INFO - Hardware Version No is {}".format(hci.hw_version_no))
                log.info("INFO - Hardware Modification No is {}".format(hci.hw_mod_version_no))

            # Turn Board Under Test and PSU Output off, de-assert System Reset
            self._set_psu_but_off(tji)
            tji.assert_system_reset(False)

        return ret_val

    def program_micro(self, micro_fw_bin_file):
        """
        Program the Board Under Test microcontroller
        :return: True if the microcontroller is successfully programmed, else False :type Boolean
        """
        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off
            self._set_psu_but_off(tji)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            time.sleep(2.0)

            # Program the microcontroller
            ret_val = ab_program_devices.program_micro_device(micro_fw_bin_file)
            log.info("{} - Program Microcontroller: {}".format("PASS" if ret_val else "FAIL", micro_fw_bin_file))

            # Turn the Board Under Test and PSU output off
            self._set_psu_but_off(tji)

        return ret_val

    def program_gbe_sw(self, gbe_sw_bin_file):
        """
        Program the Board Under Test GbE Switch SPI Flash
        :return: True if the GbE Switch SPI Flash is successfully programmed, else False :type Boolean
        """
        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off and hold the board in reset
            self._set_psu_but_off(tji)
            tji.assert_system_reset(True)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            time.sleep(2.0)

            ret_val = ab_program_devices.program_gbe_sw_spi_flash(gbe_sw_bin_file)
            log.info("{} - Program GbE Switch SPI Flash: {}".format("PASS" if ret_val else "FAIL", gbe_sw_bin_file))

            # De-assert system reset then turn the Board Under Test and PSU output off
            tji.assert_system_reset(False)
            self._set_psu_but_off(tji)

        return ret_val

    def built_in_test(self):
        """
        Tests built-in test data, five sets of readings are acquired, the min/max of the acquired readings is then
        checked against test limits.
        :return: True if test passes, else False :type Boolean
        """
        ret_val = True

        with AbTestJigInterface(self._tj_com_port) as tji:
            with AbSerialMsgInterface(self._but_com_port) as asmi:
                # Ensure the Board Under Test and PSU output are off
                self._set_psu_but_off(tji)

                # Set PSU voltage and current limit, then turn the PSU and board on
                self._set_psu_but_on(tji, 28000, 1000)
                time.sleep(5.0)

                # Get 5x sets of BIT data to analyse
                voltages_1v0_mv = []
                voltages_2v5_mv = []
                ambient_temps_deg = []
                eth_sw_temps_deg = []
                eth_phy_temps_deg = []
                micro_temps_deg = []

                for i in range(0, 5):
                    result, msg = asmi.get_command(AbMsgId.GET_BIT_INFO, AbMsgPayloadLen.GET_BIT_INFO)
                    if result:
                        payload_version, flags, voltage_1v0_mv, voltage_2v5_mv, ambient_temp_deg, eth_sw_temp_deg, \
                            eth_phy_temp_deg, micro_temp_deg = asmi.unpack_get_bit_info_response(msg)
                        voltages_1v0_mv.append(voltage_1v0_mv)
                        voltages_2v5_mv.append(voltage_2v5_mv)
                        ambient_temps_deg.append(ambient_temp_deg)
                        eth_sw_temps_deg.append(eth_sw_temp_deg)
                        eth_phy_temps_deg.append(eth_phy_temp_deg)
                        micro_temps_deg.append(micro_temp_deg)
                    ret_val = ret_val and result

                # If data read successfully process it against pass/fail limits
                if ret_val:
                    log.debug(voltages_1v0_mv)
                    test_pass = min(voltages_1v0_mv) >= 950 and max(voltages_1v0_mv) <= 1050
                    log.info("{} - +1V0: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                 min(voltages_1v0_mv), max(voltages_1v0_mv),
                                                                 950, 1050))
                    ret_val = ret_val and test_pass

                    log.debug(voltages_2v5_mv)
                    test_pass = min(voltages_2v5_mv) >= 2400 and max(voltages_2v5_mv) <= 2600
                    log.info("{} - +2V5: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                 min(voltages_2v5_mv), max(voltages_2v5_mv),
                                                                 2400, 2600))
                    ret_val = ret_val and test_pass

                    log.debug(ambient_temps_deg)
                    test_pass = min(ambient_temps_deg) >= 25 and max(ambient_temps_deg) <= 50
                    log.info("{} - Ambient Temp: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                         min(ambient_temps_deg), max(ambient_temps_deg),
                                                                         25, 50))
                    ret_val = ret_val and test_pass

                    log.debug(eth_sw_temps_deg)
                    test_pass = min(eth_sw_temps_deg) >= 35 and max(eth_sw_temps_deg) <= 65
                    log.info("{} - Eth Sw Temp: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                        min(eth_sw_temps_deg), max(eth_sw_temps_deg),
                                                                        35, 65))
                    ret_val = ret_val and test_pass

                    log.debug(eth_phy_temps_deg)
                    test_pass = min(eth_phy_temps_deg) >= 35 and max(eth_phy_temps_deg) <= 65
                    log.info("{} - Phy Temp: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                     min(eth_phy_temps_deg), max(eth_phy_temps_deg),
                                                                     35, 65))
                    ret_val = ret_val and test_pass

                    log.debug(micro_temps_deg)
                    test_pass = min(micro_temps_deg) >= 25 and max(micro_temps_deg) <= 55
                    log.info("{} - Micro Temp: {}..{} [{}..{}]".format("PASS" if test_pass else "FAIL",
                                                                       min(micro_temps_deg), max(micro_temps_deg),
                                                                       25, 55))
                    ret_val = ret_val and test_pass

            log.info("{} - Built-In Test Overall Result".format("PASS" if ret_val else "FAIL"))

            # Turn the Board Under Test and PSU output off
            self._set_psu_but_off(tji)

        return ret_val

    def discrete_test(self):
        """
        Performs tests on the Rack Address and 1PPS discrete signals.
        :return: True if the test passed, else False :type Boolean
        """
        ret_val = True

        with AbTestJigInterface(self._tj_com_port) as tji:
            with AbSerialMsgInterface(self._but_com_port) as asmi:
                # Ensure the Board Under Test and PSU output are off
                self._set_psu_but_off(tji)

                # Set PSU voltage and current limit, then turn the PSU and board on
                self._set_psu_but_on(tji, 28000, 1000)
                time.sleep(5.0)

                # Test the Rack Address Signal
                rack_addr_pass = True
                rack_addr_flag_mask = 0x04
                for assert_val, masked_bit_flag_val in [(False, 0x00), (True, rack_addr_flag_mask), (False, 0x00)]:
                    tji.set_rack_address(assert_val)
                    time.sleep(1.0)
                    result, msg = asmi.get_command(AbMsgId.GET_BIT_INFO, AbMsgPayloadLen.GET_BIT_INFO)
                    rack_addr_pass = rack_addr_pass and result

                    if result:
                        payload_version, flags, voltage_1v0_mv, voltage_2v5_mv, \
                            ambient_temp_deg, eth_sw_temp_deg, eth_phy_temp_deg, micro_temp_deg = \
                            asmi.unpack_get_bit_info_response(msg)
                        rack_addr_pass = rack_addr_pass and ((flags & rack_addr_flag_mask) == masked_bit_flag_val)

                log.info("{} - Rack Address Signal".format("PASS" if rack_addr_pass else "FAIL"))
                ret_val = ret_val and rack_addr_pass

                # Test the 1PPS Signal
                pps_flag_pass = True
                pps_flag_mask = 0x08
                # (enable test jig PPS, expected masked BIT flags value)
                pps_addr_tc = [(False, 0x00), (True, pps_flag_mask), (False, 0x00)]

                for pps_enable, masked_bit_flag_val in pps_addr_tc:
                    tji.set_pps_enable(pps_enable)
                    time.sleep(2.0)
                    result, msg = asmi.get_command(AbMsgId.GET_BIT_INFO, AbMsgPayloadLen.GET_BIT_INFO)
                    pps_flag_pass = pps_flag_pass and result

                    if result:
                        payload_version, flags, voltage_1v0_mv, voltage_2v5_mv, \
                            ambient_temp_deg, eth_sw_temp_deg, eth_phy_temp_deg, micro_temp_deg = \
                            asmi.unpack_get_bit_info_response(msg)
                        pps_flag_pass = pps_flag_pass and ((flags & pps_flag_mask) == masked_bit_flag_val)

                log.info("{} - 1PPS Signal".format("PASS" if pps_flag_pass else "FAIL"))
                ret_val = ret_val and pps_flag_pass

                # Turn the Board Under Test and PSU output off
                self._set_psu_but_off(tji)

        return ret_val

    def uart_test(self):
        """
        Use the board under test's Telnet Server to perform a loop back test on the EMAx isolated UARTs, the CSM UART
        is tested by built_in_test().
        :return: True if the test passed, else False :type Boolean
        """
        telnet_ports = [(26, "EMA1"), (27, "EMA2"), (28, "EMA3"), (29, "EMA4"), (30, "EMA5")]
        ret_val = True

        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off
            self._set_psu_but_off(tji)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            time.sleep(12.0)

            # Perform a ping to help the test computer find the AB
            self._ping(self._BOARD_HOSTNAME, retries=4)

            for port, port_name in telnet_ports:
                with Telnet(self._BOARD_HOSTNAME, port) as tn:
                    port_pass = True
                    for i in range(0, 10):
                        tn.write(self._UART_TEST_STRING)
                        ret_string = tn.read_until(self._UART_TEST_STRING, self._UART_TEST_TIMEOUT_SEC)
                        port_pass = port_pass and (ret_string == self._UART_TEST_STRING)

                    log.info("{} - UART Test {} - {}:{}".format("PASS" if port_pass else "FALSE", port_name,
                                                                self._BOARD_HOSTNAME, port))
                    ret_val = ret_val and port_pass

            # Turn the Board Under Test and PSU output off
            self._set_psu_but_off(tji)

        return ret_val

    def gbe_sw_connection_test(self, uport, duration_s=30, power_on=True, power_off=True):
        """
        Performs the following tests on the specified GbE Switch port:
            1 - checks that link state is Up/GbE
            2 - enables corresponding TP-Link switch port then performs an iPerf3 bandwidth test for the
                specified number of seconds (default 30), TP-Link to Board uPort mapping is provided by
                uport_2_tp_link_map, expected tx/rx speed is >850 Mbps
            3 - checks that the GbE switch error counters are all zero
        :param uport: GbE Switch port to test :type Integer
        :param duration_s: number of seconds to run the iPerf3 test for, default is 30 seconds :type Interger
        :param power_on: optional parameter, default True, set False to skip powering up the board before
        starting the test :type Boolean
        :param power_off: optional parameter, default True, set False to skip powering down the board after
        finishing the test :type Boolean
        :return: True if the test passed, else False :type Boolean
        """
        if uport not in [1, 2, 3, 7, 8]:
            raise ValueError("Invalid uPort number!")

        uport_2_tp_link_map = {1: 11, 2: 10, 3: 9, 7: 13, 8: 12}
        tp_link_port = uport_2_tp_link_map.get(uport)
        error_counter_attrs = ["rx_crc_alignment", "rx_undersize", "rx_oversize", "rx_fragments", "rx_jabbers",
                               "rx_drops", "rx_classifier_drops", "tx_collisions", "tx_drops", "tx_overflow", "tx_aged"]
        ret_val = True

        with AbTestJigInterface(self._tj_com_port) as tji:
            with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
                tpl_sw.port_enable(tp_link_port, True)

                if power_on:
                    # Ensure the Board Under Test and PSU output are off
                    self._set_psu_but_off(tji)

                    # Set PSU voltage and current limit, then turn the PSU and board on
                    self._set_psu_but_on(tji, 28000, 1000)
                    time.sleep(10.0)
                else:
                    time.sleep(5.0)

                # Perform a ping to help the test computer find the RPi4
                self._ping(rpi4ip3.RPI4_HOSTNAME, retries=4)

                # Perform a ping to help the test computer find the AB
                self._ping(self._BOARD_HOSTNAME, retries=4)

                # Create a GbE Switch instance to check link state and port statistics
                with TelnetGbeSwitch(self._BOARD_HOSTNAME, self._BOARD_GBE_SWITCH_TELNET_PORT) as gs:
                    # Expecting link state to be Up/GbE
                    link_state = gs.get_port_link_state(uport)
                    test_pass = (link_state == GbeSwitchLinkState.UP_GBE)
                    log.info("{} - GbE Connection Test uPort {} link state {}".format("PASS" if test_pass else "FAIL",
                                                                                      uport, link_state))
                    ret_val = ret_val and test_pass
                # Start the Rpi4 iPerf3 server
                if rpi4ip3.start_iperf3_server():
                    # Perform an iPerf3 bandwidth test and check that the tx/rx bandwidth is >850 Mbps
                    log.info("INFO - uPort {} start iPerf3 test >850 Mbps - {} seconds".format(uport, duration_s))
                    tx_bps, rx_bps = winip3.iperf3_client_test(rpi4ip3.RPI4_HOSTNAME, duration_s)
                    test_pass = (tx_bps > 850e6) and (rx_bps > 850e6)
                    log.info("{} - GbE Bandwidth Test uPort {} Tx: {:.2f} Mbps; Rx: {:.2f} Mbps".format(
                        "PASS" if test_pass else "FAIL", uport, tx_bps / 1.0E6, rx_bps / 1.0E6))
                    ret_val = ret_val and test_pass
                else:
                    raise RuntimeError("Failed to start RPi4 iPerf3 server!")

                with TelnetGbeSwitch(self._BOARD_HOSTNAME, self._BOARD_GBE_SWITCH_TELNET_PORT) as gs:
                    # Expecting all the port error counters to STILL be 0
                    log.info("INFO - Check uPort {} statistics:".format(uport))
                    port_stats = gs.get_port_statistics(uport)
                    for error_counter_attr in error_counter_attrs:
                        attr_val = getattr(port_stats, error_counter_attr)
                        test_pass = (attr_val == 0)
                        log.info("{} - GbE Statistic Test uPort {} {}: {}".format(
                            "PASS" if test_pass else "FAIL", uport, error_counter_attr, attr_val))
                        ret_val = ret_val and test_pass

                # Turn the Board Under Test and PSU output off
                if power_off:
                    self._set_psu_but_off(tji)

                tpl_sw.port_enable(tp_link_port, False)

        return ret_val

    def qsgmii_test(self, test_no=0):
        """
        Performs VSC7512/VSC8514 QSGMII bring up test, checking for legacy issue.  Power-cycle board
        then attempt to ping from PC (VSC7512) to RPi4 (VSC8514) which requires the QSGMII between the
        GbE Switch and PHY ICs to be up and running.
        :return: True if the test passed, else False :type Boolean
        """
        ret_val = True

        if self.tpsu is not None:
            self.tpsu.setVoltage(1, 28000)  # mV
            self.tpsu.setCurrent(1, 1000)   # mA
            self.tpsu.ON()

            # Enable TP-Link switch Port 9 (EMA5), connected to VSC8514 Port 3, GbE Switch uPort 3
            with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
                tpl_sw.port_enable(9, True)

            with AbTestJigInterface(self._tj_com_port) as tji:
                tji.set_dcdc_enable(False)
                time.sleep(2)
                tji.set_dcdc_enable(True)

                start_time = time.perf_counter()
                ping_success = self._ping(rpi4ip3.RPI4_HOSTNAME, retries=40)
                end_time = time.perf_counter()

                # Pass if the ping was successful within 25-seconds.
                if ping_success and (end_time - start_time) < 25.0:
                    log.info("PASS - QSGMII Test {}: {:3f} seconds".format(test_no, end_time - start_time))
                    ret_val = ret_val and True
                else:
                    log.info("FAIL - QSGMII Test {}: {:3f} seconds".format(test_no, end_time - start_time))
                    log.info("INFO - QSGMII Test {} Ping Worked: {}".format(test_no, ping_success))

                    # Try to ping the Active Backplane to confirm the switch is up and running
                    if self._ping(self._BOARD_HOSTNAME, retries=3):
                        log.info("INFO - QSGMII Test {} Ping AB Success: {}".format(test_no, self._BOARD_HOSTNAME))
                        with TelnetGbeSwitch(self._BOARD_HOSTNAME, self._BOARD_GBE_SWITCH_TELNET_PORT) as gs:
                            log.info("INFO - QSGMII Test {} GbE Switch QSGMII Sync: {}".format(test_no,
                                                                                               gs.get_sw_qsgmii_sync()))
                            log.info("INFO - QSGMII Test {} GbE PHY QSGMII Sync: {}".format(test_no,
                                                                                            gs.get_phy_qsgmii_sync()))
                    else:
                        log.info("INFO - QSGMII Test {} Ping AB Failed: {}".format(test_no, self._BOARD_HOSTNAME))

                    ret_val = ret_val and False

                tji.set_dcdc_enable(False)

            # Disable TP-Link switch Port 9
            with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
                tpl_sw.port_enable(9, False)
        else:
            raise RuntimeError("PSU Test Equipment Error!")

        return ret_val

    def get_micro_mac_ip_address(self):
        """
        Power up the board under test and read the microcontroller MAC address, this is read from board under test
        via Telnet interface to the GbE Switch.  The read MAC address is then used to determine the microcontroller's
        LWIP zeroconf IPV4 address.
        This method does not perform a pass/fail test.
        :return:True :type Boolean
        """
        # Initialise return values
        mac_address = ""
        ip_address = ""

        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off
            self._set_psu_but_off(tji)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            # Allow the micro to initialise and acquire zeroconf address
            time.sleep(12.0)

            # Perform a ping to help the test computer find the AB
            self._ping(self._BOARD_HOSTNAME, retries=4)

            with TelnetGbeSwitch(self._BOARD_HOSTNAME, self._BOARD_GBE_SWITCH_TELNET_PORT) as gs:
                mac_addresses = gs.get_mac_addresses()

                # The microcontroller is the only device connected to uPort 5
                for ma in mac_addresses:
                    if ma[1] == 5:
                        mac_address = ma[0]
                        ip_address = gs.build_lwip_autoip_address(mac_address)

            # Turn the Board Under Test and PSU output off
            self._set_psu_but_off(tji)

            log.info("INFO - Micro MAC Address: {}".format(mac_address))
            log.info("INFO - Micro IP Address: {}".format(ip_address))

        return True

    def get_switch_mac_address(self):
        """
        Power up the board under test and read the switch MAC address, this is directly read
        from board under test via the test jig serial interface.
        This method does not perform a pass/fail test.
        :return:True :type Boolean
        """
        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off and the board is held in reset
            self._set_psu_but_off(tji)
            tji.assert_system_reset(True)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            time.sleep(1.0)

            # Read the MAC addresses
            micro_mac_address, switch_mac_address = tji.get_mac_addresses()

            # Turn the Board Under Test and PSU output off the de-assert the board reset
            self._set_psu_but_off(tji)
            tji.assert_system_reset(False)

            log.info("INFO - GbE Switch MAC Address: {}".format(switch_mac_address))

        return True

    def get_sw_versions(self):
        """
        Power up the board under test and read the microcontroller and GbE Switch software version numbers.
        This method does not perform a pass/fail test.
        :return:True :type Boolean
        """
        with AbTestJigInterface(self._tj_com_port) as tji:
            # Ensure the Board Under Test and PSU output are off
            self._set_psu_but_off(tji)

            # Set PSU voltage and current limit, then turn the PSU and board on
            self._set_psu_but_on(tji, 28000, 1000)
            # Allow the micro to initialise and acquire zeroconf address
            time.sleep(12.0)

            with AbSerialMsgInterface(self._but_com_port) as asmi:
                result, msg = asmi.get_command(AbMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                               AbMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
                if result:
                    pl_ver, sw_maj, sw_min, sw_patch, sw_build = asmi.unpack_get_software_version_number_response(msg)
                else:
                    sw_maj = sw_min = sw_patch = sw_build = -1
                log.info("INFO - Micro Software Part No: KT-956-0194-00")
                log.info("INFO - Micro Software Version No: {}.{}.{}:{}".format(sw_maj, sw_min, sw_patch, sw_build))

            # Perform a ping to help the test computer find the AB
            self._ping(self._BOARD_HOSTNAME, retries=4)

            with TelnetGbeSwitch(self._BOARD_HOSTNAME, self._BOARD_GBE_SWITCH_TELNET_PORT) as gs:
                gs_sw_part_no, gs_sw_version_no = gs.get_software_version()
            log.info("INFO - GbE Switch Software Part No: {}".format(gs_sw_part_no))
            log.info("INFO - GbE Switch Software Version No: {}".format(gs_sw_version_no))

            # Turn the Board Under Test and PSU output off
            self._set_psu_but_off(tji)

        return True

    def _get_tenma_psu_instance(self):
        """
        Get a proper Tenma PSU subclass depending on the *IDN? response from the unit.
        The subclasses mainly deals with the limit checks for each PSU type.
        """
        # Instantiate base to retrieve ID information
        tpsu = Tenma72Base(self._psu_com_port, debug=False)
        ver = tpsu.getVersion()
        # Need to close the serial port otherwise call to create specific device instance will fail
        tpsu.close()
        log.debug(ver)
        for cls in Tenma72Base.__subclasses__():
            for match_str in cls.MATCH_STR:
                if match_str in ver:
                    return cls(self._psu_com_port, debug=False)

        log.critical("Could not detect Tenma PSU!")
        return None

    def _set_psu_but_off(self, tji):
        """
        Disable the Board Under Test DC-DC converter and turn the PSU off.
        :param tji: Test jig serial interface instance :type AbTestJigInterface
        :return: N/A
        """
        if self.tpsu is not None:
            tji.set_dcdc_enable(False)
            self.tpsu.OFF()
            time.sleep(1.0)
        else:
            raise RuntimeError("PSU Test Equipment Error!")

    def _set_psu_but_on(self, tji, voltage_mv, i_limit_ma):
        """
        Sets the Tenma bench PSU to the specified voltage and current limit then turns it on,
        also ensures that the board under test DC-DC converter is enabled.
        :param tji: test jig serial interface instance :type AbTestJigInterface
        :param voltage_mv: bench PSU supply voltage in mV :type Integer
        :param voltage_mv: bench PSU current limit in mA :type Integer
        :return: N/A
        """
        if self.tpsu is not None:
            self.tpsu.setVoltage(1, voltage_mv)
            self.tpsu.setCurrent(1, i_limit_ma)
            self.tpsu.ON()
            tji.set_dcdc_enable(True)
        else:
            raise RuntimeError("PSU Test Equipment Error!")

    @staticmethod
    def _ping(ip_address, retries=1):
        """
        Calls the system ping command for the specified IP address
        :param ip_address: ip address/hostname to ping :type: string
        :param retries: number of times to retry failed ping before giving up :type: integer
        :return: True if the IP address is successfully pinged with retries attempts, else False
        """
        return_val = False

        # This will throw a ValueError exception if ip_address is NOT a valid IP address
        try:
            a = ipaddress.ip_address(ip_address)
        except Exception as ex:
            log.debug("Using hostname for ping rather than IP address".format(ex))
            a = ip_address

        ping_type = ""

        if platform.system().lower() == "windows":
            count_param = "n"
            if type(a) == ipaddress.IPv6Address:
                ping_type = "-6"
            elif type(a) == ipaddress.IPv4Address:
                ping_type = "-4"
        else:
            count_param = "c"

        for i in range(0, retries):
            output = popen("ping {} -{} 1 {}".format(ping_type, count_param, a)).read()
            log.debug("Ping {}:".format(i))
            log.debug(output)

            if not output or "unreachable" in output or "0 packets received" in output or "could not find" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val


class AbProdTestInfo:
    """
    Utility class used to define the test info to be executed by the test thread class
    """
    main_power_supply_test: bool = False
    set_hw_config_info: bool = False
    program_micro: bool = False
    micro_fw_bin_file: str = ""
    program_gbe_sw: bool = False
    gbe_sw_bin_file: str = ""
    get_sw_versions: bool = False
    built_in_test: bool = False
    discrete_test: bool = False
    uart_test: bool = False
    gbe_sw_connection_test: bool = False
    qsgmii_test: bool = False
    get_micro_mac_ip_address: bool = False
    get_switch_mac_address: bool = False
    assy_rev_no: str = ""
    assy_serial_no: str = ""
    assy_build_batch_no: str = ""
    tj_com_port: str = ""
    psu_com_port: str = ""
    tpl_sw_com_port: str = ""
    but_com_port: str = ""
    segger_jlink_win32: str = ""
    segger_jlink_win64: str = ""
    asix_up_win32: str = ""
    asix_up_win64: str = ""
    iperf3: str = ""
    cygwin1_dll: str = ""
    test_case_list = ["main_power_supply_test", "set_hw_config_info", "program_micro", "program_gbe_sw",
                      "get_sw_versions", "built_in_test", "discrete_test", "uart_test", "gbe_sw_connection_test",
                      "qsgmii_test", "get_micro_mac_ip_address", "get_switch_mac_address"]


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
