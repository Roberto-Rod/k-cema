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
from enum import Enum
import ipaddress
import logging
from os import popen
import platform
import socket
import time

# Third-party imports -----------------------------------------------
from serial import Serial
from tenma.tenmaDcLib import Tenma72Base
import zeroconf as zeroconfig

# Our own imports -------------------------------------------------
import csm_program_devices as cpd
from csm_plat_test_intf import CsmPlatformTest
from csm_test_jig_intf import CsmTestJigInterface, CsmTestJigPpsSource, CsmTestJigGpoSignals, \
    MpTestJigInterface, MpTestJigGpoSignals, MpTestJigPpsSource, MpTestJigNtmI2cBus, MpTestJigNtmFanPwm
from csm_zero_micro_test_intf import CsmZeroiseMircoTestInterface, CsmGpoSignals, CsmGpiSignals, \
    CsmPoePseChannelStatus, CsmTamperDevices, CsmTamperChannels, CsmTamperChannelStatus, MpZeroiseMircoTestInterface, \
    MpGpoSignals, MpGpiSignals
import ptp_phy_test as ppt
import rpi4_iperf3 as rpi4ip3
import som_eia422_intf_test as seit
from tl_sg3428 import TLSG3428
from uart_test import UartTest
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
class UnitTypes(Enum):
    """ Enumeration class for unit types """
    VEHICLE = 0
    MANPACK = 1
    MANPACK_KBAN = 2


class CommonCsmProdTest:
    """
    Class that implements common test cases and functionality for Manpaack and Vehicle CSM testing.
    """
    _MANAGED_SWITCH_DEFAULT_ENABLED_PORTS = [1, 2, 3, 4, 5, 6, 7, 8]
    _CSM_PASSWORD = "gbL^58TJc"

    # Test Equipment Interfaces
    tpsu = None

    def __init__(self, tj_com_port, psu_com_port, tpl_sw_com_port, master_com_port, rcu_com_port,
                 csm_hostname, csm_username, zeroise_micro_serial_port, csm_slave_serial_port,
                 rcu_serial_port, programming_serial_port, gnss1_serial_port, gbe_switch_serial_port,
                 exp_slot_1_serial_port, exp_slot_2_serial_port,
                 segger_jlink_win32=None, segger_jlink_win64=None, flash_pro=None, iperf3=None, cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param tj_com_port: test jig NUCLEO STM32 COM port :type String
        :param psu_com_port: Tenma bench PSU COM port :type String
        :param tpl_sw_com_port: TP-Link managed switch COM port :type String
        :param master_com_port: board/unit under test CSM Master COM port :type String
        :param rcu_com_port: board/unit under test RCU COM port :type String
        :param csm_hostname: board/unit under test network hostname :type String
        :param zeroise_micro_serial_port: CSM serial port :type String
        :param csm_slave_serial_port: CSM serial port :type String
        :param rcu_serial_port: CSM serial port :type String
        :param programming_serial_port: CSM serial port :type String
        :param gnss1_serial_port: CSM serial port :type String
        :param gbe_switch_serial_port: CSM serial port :type String
        :param exp_slot_1_serial_port: Expansion Slot 1 serial port :type String
        :param exp_slot_2_serial_port: Expansion Slot 2 serial port :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param flash_pro: Microchip FlashPro exe path, default is None, use csm_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        # Set test environment initial state
        log.info("INFO - Initialising test environment...")

        # PSU initialisation
        log.info("INFO - Initialising power supply")
        self._psu_com_port = psu_com_port
        self.tpsu = self._get_tenma_psu_instance()
        # self.tpsu.OFF()
        log.info("INFO - Power supply initialisation complete - {}".format(self.tpsu.MATCH_STR))

        # Test jig interface initialisation
        log.info("INFO - Initialising test jig interface")
        self._tj_com_port = tj_com_port
        with CsmTestJigInterface(self._tj_com_port) as tji:
            tji.assert_gpo_signal(CsmTestJigGpoSignals.SOM_SD_BOOT_ENABLE, False)
            tji.assert_gpo_signal(CsmTestJigGpoSignals.RCU_POWER_BUTTON, False)
            tji.assert_gpo_signal(CsmTestJigGpoSignals.RCU_POWER_ENABLE_ZEROISE, False)
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

        self._master_com_port = master_com_port
        self._rcu_com_port = rcu_com_port
        self._csm_hostname = csm_hostname
        self._csm_username = csm_username
        # This is populated in the power_up_board method if the linux_run_check option is set to True
        self._csm_ip_address = None

        # Board/unit serial ports
        self._zeroise_micro_serial_port = zeroise_micro_serial_port
        self._csm_slave_serial_port = csm_slave_serial_port
        self._rcu_serial_port = rcu_serial_port
        self._programming_serial_port = programming_serial_port
        self._gnss1_serial_port = gnss1_serial_port
        self._gbe_switch_serial_port = gbe_switch_serial_port
        self._exp_slot_1_serial_port = exp_slot_1_serial_port
        self._exp_slot_2_serial_port = exp_slot_2_serial_port

        # Override exe path constants in csm_program_devices and win_ip3 modules if exe path variables have been passed
        if segger_jlink_win32 is not None:
            cpd.JLINK_PATH_WIN32 = segger_jlink_win32
        if segger_jlink_win64 is not None:
            cpd.JLINK_PATH_WIN64 = segger_jlink_win64
        if flash_pro is not None:
            cpd.FLASHPRO_PATH_WIN32 = flash_pro
        if iperf3 is not None:
            winip3.IPERF3_EXECUTABLE = iperf3
        if cygwin1_dll is not None:
            winip3.CYGWIN_DLL = cygwin1_dll

        self.unit_type = None

        log.info("INFO - Test environment initialisation complete")

    def __del__(self):
        """ Class destructor - Ensure the PSU is turned off """
        try:
            self._set_psu_off()
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
            self._set_psu_off()
            if self.tpsu is not None:
                self.tpsu.close()
        except Exception as ex:
            log.debug("Error raised closing PSU serial port - {}".format(ex))

    def zeroise_psu_rail_test(self):
        """
        Test the board under test Zeroise Power domain supply rails.
        Prerequisites:
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        test_limits_zer_fpga_on = [
            # rail, lim_mv_lo, lim_mv_hi
            ("vbat_zer_mv", 4000, 4600),
            ("p3v3_zer_buf_mv", 3200, 3400),
            ("p3v0_zer_proc_mv", 2900, 3100),
            ("p3v0_zer_fpga", 2900, 3100),
            ("p2v5_zer_mv", 2400, 2600),
            ("p2v5_som_mv", 2400, 2600),
            ("p1v2_zer_fpga_mv", 1100, 1300),
            ("p4v2_zer_mv", 4100, 4300)
        ]
        test_limits_zer_fpga_off = [
            # rail, lim_mv_lo, lim_mv_hi
            ("vbat_zer_mv", 4000, 4600),
            ("p3v3_zer_buf_mv", 0, 100),
            ("p3v0_zer_proc_mv", 2900, 3100),
            ("p3v0_zer_fpga", 0, 100),
            ("p2v5_zer_mv", 0, 500),
            ("p2v5_som_mv", 0, 500),
            ("p1v2_zer_fpga_mv", 0, 100),
            ("p4v2_zer_mv", 4100, 4300)
        ]
        test_sequence = [
            # zer_fpgpa_pwr_en, test_limits, meas_delay_s
            (True, test_limits_zer_fpga_on, 2.0),
            (False, test_limits_zer_fpga_off, 10.0),
            (True, test_limits_zer_fpga_on, 2.0)
        ]
        full_sc_adc_lim_mv_lo = 9900
        full_sc_adc_lim_mv_hi = 10000

        log.info("")
        log.info("Zeroise PSU Rail Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()

            zer_fpgpa_pwr_en_signal = CsmGpoSignals.ZER_FPGA_PWR_EN if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_FPGA_PWR_EN

            for zer_fpgpa_pwr_en, test_limits, meas_delay_s in test_sequence:
                ret_val = czm.set_gpo_signal(zer_fpgpa_pwr_en_signal, zer_fpgpa_pwr_en) and ret_val
                time.sleep(meas_delay_s)
                adc_read, adc_data = czm.get_adc_data()
                ret_val = adc_read and ret_val
                if adc_read:
                    for rail, lim_mv_lo, lim_mv_hi in test_limits:
                        # Special case for p1v2_zer_fpga_mv and p3v0_zer_fpga rail which can go ADC full-scale
                        # when they are disabled.
                        if not zer_fpgpa_pwr_en and (rail == "p1v2_zer_fpga_mv" or rail == "p3v0_zer_fpga"):
                            test_pass = (lim_mv_lo <= getattr(adc_data, rail) <= lim_mv_hi) or \
                                        (full_sc_adc_lim_mv_lo <= getattr(adc_data, rail) <= full_sc_adc_lim_mv_hi)
                            log.info("{} - {} Rail: {} <= {} <= {} mV; OR {} <= {} <= {} mV"
                                     "".format("PASS" if test_pass else "FAIL",
                                               rail, lim_mv_lo, getattr(adc_data, rail), lim_mv_hi,
                                               full_sc_adc_lim_mv_lo, getattr(adc_data, rail), full_sc_adc_lim_mv_hi))
                        # Special case for 1p4v2_zer_mv rail which is not connected to the ADC on the Manpack.
                        elif (self.unit_type == UnitTypes.MANPACK or self.unit_type == UnitTypes.MANPACK_KBAN) and \
                                rail == "p4v2_zer_mv":
                            pass
                        else:
                            test_pass = (lim_mv_lo <= getattr(adc_data, rail) <= lim_mv_hi)
                            log.info("{} - {} Rail: {} <= {} <= {} mV"
                                     "".format("PASS" if test_pass else "FAIL",
                                               rail, lim_mv_lo, getattr(adc_data, rail), lim_mv_hi))
                        ret_val = test_pass and ret_val

            self._set_psu_off()

        log.info("{} - Zeroise PSU Rail Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def battery_signal_test(self):
        """
        Test the battery charger signals, only run the test if the charging status signal indicates that
        the battery is being charged, should always be the case on new boards under test.
        Prerequisites:
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Battery Charger Signal Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board(psu_voltage_mv=17000)
            # Allow extra time for the supply current to settle
            time.sleep(40.0)

            batt_chrg_stat_n_signal = CsmGpiSignals.BATT_CHRG_STAT_N if self.unit_type is UnitTypes.VEHICLE else \
                MpGpiSignals.BATT_CHRG_STAT_N
            batt_chrg_low_signal = CsmGpoSignals.BATT_CHRG_LOW if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.BATT_CHRG_LOW
            batt_chrg_en_n = CsmGpoSignals.BATT_CHRG_EN_N if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.BATT_CHRG_EN_N

            if czm.get_gpi_signal_asserted(batt_chrg_stat_n_signal):
                start_i_ma = self._get_average_psu_running_i_ma(period_s=5)

                # Test the high charge current enable signal
                czm.set_gpo_signal(batt_chrg_low_signal, False)
                time.sleep(1.0)
                high_charge_i_ma = self._get_average_psu_running_i_ma(period_s=5)
                test_pass = high_charge_i_ma >= (start_i_ma + 20)
                log.info("{} - High current charge enable: {:.2f} >= {:.2f}".format("PASS" if test_pass else "FAIL",
                                                                                    high_charge_i_ma,
                                                                                    start_i_ma + 20))
                ret_val = test_pass and ret_val

                # Test the charger enable signal
                czm.set_gpo_signal(batt_chrg_en_n, True)
                time.sleep(1.0)
                batt_charger_disabled_i_ma = self._get_average_psu_running_i_ma(period_s=5)
                test_pass = batt_charger_disabled_i_ma <= (high_charge_i_ma - 30)
                log.info("{} - Battery charger enable/disable: {:.2f} <= {:.2f}".format("PASS" if test_pass else "FAIL",
                                                                                        batt_charger_disabled_i_ma,
                                                                                        high_charge_i_ma - 30))
                ret_val = test_pass and ret_val

            else:
                log.info("Battery NOT charging, skipping battery signal test")

            self._set_psu_off()

        log.info("{} - Battery Charger Signal Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def rtc_test(self):
        """
        Test the anti-tamper IC real-time clocks.
        Get 2x RTC readings 1-second apart and check that the values are not the same.
        Prerequisites:
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Anti-Tamper RTC Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()
            at_rtc_1, pcd_rtc_1 = czm.get_rtc()
            time.sleep(1.0)
            at_rtc_2, pcd_rtc_2 = czm.get_rtc()

            test_pass = at_rtc_1 != "" and at_rtc_2 != "" and at_rtc_1 != at_rtc_2
            log.info("{} - Anti-Tamper RTC Test".format("PASS" if test_pass else "FAIL"))
            ret_val = test_pass and ret_val

            test_pass = pcd_rtc_1 != "" and pcd_rtc_2 != "" and pcd_rtc_1 != pcd_rtc_2
            log.info("{} - Power-Cable Detect RTC Test".format("PASS" if test_pass else "FAIL"))
            ret_val = test_pass and ret_val

            self._set_psu_off()

        return ret_val

    def case_switch_test(self, instruction_dialog_func):
        """
        Test the anti-tamper mechanical switch.
            - Ask user to hold down case switch
            - Arm sensor and check GPI and register status
            - Ask user to release case switch
            - Check GPI signal and registers for tamper detection
            - Disable sensor and check register status
        Prerequisites:
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Case Tamper Switch Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()

            irq_tamper_n_signal = CsmGpiSignals.IRQ_TAMPER_N if self.unit_type is UnitTypes.VEHICLE else \
                MpGpiSignals.IRQ_TAMPER_N

            # Need to assert the TAMPER_SW NFET on the test jig for Manpack KBAN
            if self.unit_type is UnitTypes.MANPACK_KBAN:
                with self._get_test_jig_interface_instance() as ctji:
                    ctji.assert_gpo_signal(MpTestJigGpoSignals.TAMPER_SWITCH, True)

            # Ensure all tamper channels are disabled
            for device in CsmTamperDevices:
                # Set all the TEBx bits to '0'
                for channel in CsmTamperChannels:
                    ret_val = czm.set_anti_tamper_channel_enable(device, channel, False) and ret_val
                # Read the Flags registers to make sure nIRQ signals are cleared,
                # Flags register is shared so just check Channel 0
                ret_val = czm.get_tamper_channel_status(device, CsmTamperChannels.CHANNEL_0) and ret_val

            if self.unit_type is UnitTypes.MANPACK_KBAN:
                instruction_dialog_func("MAKE a short-circuit across connector P17 Pins 2 and 4")
            else:
                instruction_dialog_func("Press and HOLD down the board under test case switch, S1")

            # Arm the tamper sensor
            ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                         CsmTamperChannels.CHANNEL_0, True) and ret_val

            # Check the IRQ_TAMPER signal is NOT asserted
            cmd_success, asserted = czm.get_gpi_signal_asserted(irq_tamper_n_signal)
            ret_val = cmd_success and not asserted and ret_val

            # Check that the tamper channel status is ARMED_READY
            cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                CsmTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == CsmTamperChannelStatus.ARMED_READY and ret_val

            # Trigger the tamper sensor
            if self.unit_type is UnitTypes.MANPACK_KBAN:
                instruction_dialog_func("REMOVE the short-circuit from connector P17 Pins 2 and 4")
            else:
                instruction_dialog_func("RELEASE the board under test case switch, S1")

            # Check that the IRQ_TAMPER signal has been asserted
            cmd_success, asserted = czm.get_gpi_signal_asserted(irq_tamper_n_signal)
            ret_val = cmd_success and asserted and ret_val

            # Check that the tamper channel status is TAMPERED
            cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                CsmTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == CsmTamperChannelStatus.TAMPERED and ret_val

            # Disable the tamper channel and check its status is reported correctly
            ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                         CsmTamperChannels.CHANNEL_0, False) and ret_val

            cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                CsmTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == CsmTamperChannelStatus.DISABLED and ret_val

            # Need to assert the TAMPER_SW NFET on the test jig for Manpack KBAN
            if self.unit_type is UnitTypes.MANPACK_KBAN:
                with self._get_test_jig_interface_instance() as ctji:
                    ctji.assert_gpo_signal(MpTestJigGpoSignals.TAMPER_SWITCH, False)

            self._set_psu_off()

        log.info("{} - Case Tamper Switch (S1) Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def light_sensor_test(self, instruction_dialog_func):
        """
        Test steps:
            - Ask user to cover light sensor
            - Arm sensor and check GPI and register status
            - Power-down the board under test using the test jig
            - Check powered-down by sending a command that will fail
            - Ask user to uncover light sensor
            - Check tamper status by reading registers, in battery mode IRQ is pulsed so this can't be read
            - De-assert ZER_PWR_HOLD to turn off zeroise micro, full command response not received so command fails
            - Power-on board under test using the test jig
            - Disable the sensor and check register status
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if test passes, else False
        """
        log.info("")
        log.info("Light Sensor Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()

            irq_tamper_n_signal = CsmGpiSignals.IRQ_TAMPER_N if self.unit_type is UnitTypes.VEHICLE else \
                MpGpiSignals.IRQ_TAMPER_N
            zer_pwr_hold_signal = CsmGpoSignals.ZER_PWR_HOLD if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_PWR_HOLD

            with self._get_test_jig_interface_instance() as ctji:
                if self.unit_type is UnitTypes.VEHICLE:
                    ls_ref_des = "Q14"
                elif self.unit_type is UnitTypes.MANPACK:
                    ls_ref_des = "Q9"
                elif self.unit_type is UnitTypes.MANPACK_KBAN:
                    ls_ref_des = "Q38"
                else:
                    ls_ref_des = "Q?"

                instruction_dialog_func("COVER the board under test light sensor, {}".format(ls_ref_des))
                # Arm the tamper sensor
                ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                             CsmTamperChannels.CHANNEL_1, True) and ret_val

                # Check the IRQ_TAMPER signal is NOT asserted
                cmd_success, asserted = czm.get_gpi_signal_asserted(irq_tamper_n_signal)
                ret_val = cmd_success and not asserted and ret_val

                # Check that the tamper channel status is ARMED_READY
                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                    CsmTamperChannels.CHANNEL_1)
                ret_val = cmd_success and status == CsmTamperChannelStatus.ARMED_READY and ret_val

                # Power-down the board under test
                ret_val = ctji.toggle_rcu_power_button(hard_power_off=True) and ret_val

                # Try to check the IRQ_TAMPER signal status - command WILL FAIL as the Zeroise Micro powered-down
                cmd_success, asserted = czm.get_gpi_signal_asserted(irq_tamper_n_signal)
                ret_val = not cmd_success and ret_val

                instruction_dialog_func("UNCOVER the board under test light sensor, {}".format(ls_ref_des))
                time.sleep(3.0)

                # Check that the tamper channel status is TAMPERED
                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                    CsmTamperChannels.CHANNEL_1)
                ret_val = cmd_success and status == CsmTamperChannelStatus.TAMPERED and ret_val

                # De-assert the ZER_PWR_HOLD signal
                czm.set_gpo_signal(zer_pwr_hold_signal, False)
                time.sleep(3.0)
                cmd_success, asserted = czm.get_gpi_signal_asserted(irq_tamper_n_signal)
                ret_val = not cmd_success and ret_val

                # Power on the board under test
                ret_val = ctji.toggle_rcu_power_button() and ret_val
                time.sleep(3.0)

                # Disable the tamper channel and check its status is reported correctly
                ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.ANTI_TAMPER,
                                                             CsmTamperChannels.CHANNEL_1, False) and ret_val

                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.ANTI_TAMPER,
                                                                    CsmTamperChannels.CHANNEL_1)
                ret_val = cmd_success and status == CsmTamperChannelStatus.DISABLED and ret_val

            self._set_psu_off()

        log.info("{} - Light Sensor (Q14) Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def unit_tamper_test(self):
        """
        Test the unit under test tamper detect function.
        Prerequisites:
        - Unit is powered up
        - Linux is booted
        - CSM Zeroise Microcontroller is programmed with operational firmware
        - Unit lid is fitted
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit Tamper Detect Test")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = cpt.unit_tamper_bit_test()

        log.info("{} - Unit Tamper Detect Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def check_for_sd_card(self):
        """
        Check if an SD Card is present, used for unit level testing where an SD Card should NOT be present
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False
        """
        log.info("")
        log.info("Check SD Card is NOT present")
        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = not cpt.check_for_sd_card()
            log.info("{} - SD Card is NOT present".format("PASS" if ret_val else "FAIL"))

        return ret_val

    def gbe_sw_connection_test(self, uport, test_uport, test_sw_port, duration_s=30, rpi4_ip6_address=""):
        """
        Performs the following tests on the specified GbE Switch port:
            1 - checks that link state is Up/GbE
            2 - enables corresponding TP-Link switch port then performs an iPerf3 bandwidth test for the
                specified number of seconds (default 30), TP-Link to Board uPort mapping is provided by
                uport_2_tp_link_map, expected tx/rx speed is >850 Mbps
            3 - checks that the GbE switch error counters are all zero
        Assumes that the board is powered up at entry
        :param uport: GbE Switch port to test :type Integer
        :param test_uport: GbE Switch port used to connect to the board under test :type Integer
        :param test_sw_port: Test managed switch port that the uport is connected to :type Integer
        :param duration_s: number of seconds to run the iPerf3 test for, default is 30 seconds :type Integer
        :param rpi4_ip6_address: Raspberry Pi4 IPv6 address, default use constants from rpi4_iperf3.py :type String
        :return: True if the test passed, else False :type Boolean
        """
        error_counter_attrs = ["rx_error_packets", "rx_crc_alignment", "rx_fragments", "rx_jabbers", "rx_drops",
                               "rx_classifier_drops", "tx_error_packets", "tx_drops", "tx_overflow"]
        ret_val = True
        log.info("")

        rpi4_host = rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address
        rpi4_password_dict = {rpi4_host: rpi4ip3.RPI4_PASSWORD}

        with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                tpl_sw.port_enable(test_sw_port, True)
                time.sleep(10.0)

                # Expecting link state to be Up/GbE for uport under test and test uport
                link_state = cpt.get_gbe_sw_port_link_state(self._gbe_switch_serial_port, uport)
                test_pass = (link_state == "UP_GBE")
                log.info("{} - GbE Connection uPort Under Test {} link state {}".format("PASS" if test_pass else "FAIL",
                                                                                        uport, link_state))
                ret_val = test_pass and ret_val

                link_state = cpt.get_gbe_sw_port_link_state(self._gbe_switch_serial_port, test_uport)
                test_pass = (link_state == "UP_GBE")
                log.info("{} - GbE Connection Test uPort {} link state {}".format("PASS" if test_pass else "FAIL",
                                                                                  test_uport, link_state))
                ret_val = test_pass and ret_val

                # Perform a ping to help the test computer find the RPi4
                self._ping(rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address, retries=4)

                # Start the Rpi4 iPerf3 server
                if rpi4ip3.start_iperf3_server(rpi4_host, rpi4ip3.RPI4_USERNAME, rpi4_password_dict):
                    # Perform an iPerf3 bandwidth test and check that the tx/rx bandwidth is >850 Mbps
                    log.info("INFO - uPort {} start iPerf3 test >850 Mbps - {} seconds".format(uport, duration_s))
                    tx_bps, rx_bps = winip3.iperf3_client_test(rpi4ip3.RPI4_HOSTNAME, duration_s)
                    test_pass = (tx_bps > 850e6) and (rx_bps > 850e6)
                    log.info("{} - GbE Bandwidth Test uPort {} Tx: {:.2f} Mbps; Rx: {:.2f} Mbps".format(
                        "PASS" if test_pass else "FAIL", uport, tx_bps / 1.0E6, rx_bps / 1.0E6))
                    ret_val = test_pass and ret_val
                else:
                    raise RuntimeError("Failed to start RPi4 iPerf3 server!")

                # Expecting all the port error counters to STILL be 0
                log.info("INFO - Check uPort {} statistics:".format(uport))
                port_stats = cpt.get_gbe_sw_port_statistics(self._gbe_switch_serial_port, uport)
                for error_counter_attr in error_counter_attrs:
                    attr_val = port_stats.get(error_counter_attr, -1)
                    test_pass = (attr_val == 0)
                    log.info("{} - GbE Statistic Test uPort {} {}: {}".format(
                        "PASS" if test_pass else "FAIL", uport, error_counter_attr, attr_val))
                    ret_val = test_pass and ret_val

                tpl_sw.port_enable(test_sw_port, False)

        return ret_val

    def qsgmii_test(self, test_no=0, rpi4_ip6_address=""):
        """
        Performs VSC7512/VSC8514 QSGMII bring up test, checking for legacy issue.  Power-cycle board
        then attempt to ping from PC (VSC7512) to RPi4 (VSC8514) which requires the QSGMII between the
        GbE Switch and PHY ICs to be up and running.
        :param test_no: used for reporting test number when performing more than one iteration of the test :type Integer
        :param rpi4_ip6_address: Raspberry Pi4 IPv6 address, default use constants from rpi4_iperf3.py :type String
        Prerequisites:
        - GbE Switch firmware programmed into SPI Flash
        Uses:
        - TP-Link TL-SG3428 serial terminal interface
        - Tenma Bench PSU serial interface
        :return: True if the test passed, else False :type Boolean
        """
        ret_val = True

        # Enable TP-Link switch Port 17 (RCU), connected to VSC8514 Port 3, GbE Switch uPort 3,
        # common to Vehicle and Manpack CSMs
        with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
            tpl_sw.port_enable(17, True)

        self.power_up_board()

        start_time = time.perf_counter()
        ping_success = self._ping(rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address, retries=40)
        end_time = time.perf_counter()

        # Pass if the ping was successful within 25-seconds.
        if ping_success and (end_time - start_time) < 25.0:
            log.info("PASS - QSGMII Test {}: {:.3f} seconds".format(test_no, end_time - start_time))
            ret_val = ret_val and True
        else:
            log.info("FAIL - QSGMII Test {}: {:.3f} seconds".format(test_no, end_time - start_time))
            log.info("INFO - QSGMII Test {} Ping Worked: {}".format(test_no, ping_success))
            ret_val = ret_val and False

        self._set_psu_off()

        # Disable TP-Link switch Port 17
        with TLSG3428(self._tpl_sw_com_port) as tpl_sw:
            tpl_sw.port_enable(17, False)

        return ret_val

    def set_config_info(self, assy_type, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board/unit under test's configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        :param assy_type: board/unit assembly type :type String
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Configuration Information:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            # Set hw config info
            ret_val = cpt.set_config_info(assy_type, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val
            if ret_val:
                # Read back hardware configuration information and check it is correct
                time.sleep(2.0)
                config_dict = cpt.get_config_info(assy_type)

                test_pass = (config_dict.get("Assembly Part Number", "") == assy_type)
                log.info("{} - Assembly No set to {}".format("PASS" if test_pass else "FAIL", assy_type))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Revision Number", "") == assy_rev_no)
                log.info("{} - Assembly Revision No set to {}".format("PASS" if test_pass else "FAIL", assy_rev_no))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Serial Number", "") == assy_serial_no)
                log.info("{} - Assembly Serial No set to {}".format("PASS" if test_pass else "FAIL", assy_serial_no))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Build Date/Batch Number", "") == assy_batch_no)
                log.info("{} - Assembly Batch No set to {}".format("PASS" if test_pass else "FAIL", assy_batch_no))
                ret_val = ret_val and test_pass

                if assy_type == self._CSM_MOTHERBOARD_NO:
                    log.info("INFO - Hardware Version No is {}".format(config_dict.get("Hardware Version", "")))
                    log.info("INFO - Hardware Modification No is {}"
                             "".format(config_dict.get("Hardware Mod Version", "")))
            else:
                log.info("INFO - Failed to set configuration information!")
                ret_val = ret_val and False

        return ret_val

    def som_built_in_test(self):
        """
        Tests the SoM BIT sensors
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        adc_channels = [
            # channel_name, test_lim_lo_v, test_lim_hi_v
            ("XADC_CHAN_3V3", 3.20, 3.40),
            ("XADC_CHAN_12V", 11.60, 12.40),
            ("XADC_CHAN_3V0_GPS", 2.90, 3.10)
            # ("XADC_CHAN_1V0_ETH", 0.95, 1.05),
            # ("XADC_CHAN_2V5_ETH", 2.40, 2.60)
        ]

        pgood_channels = ["PGD_BAT_5V", "PGD_GBE"]

        log.info("")
        log.info("SoM Built-In Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            for channel_name, test_lim_lo_v, test_lim_hi_v in adc_channels:
                adc_reading = cpt.read_som_bit_adc(channel_name)
                test_pass = test_lim_lo_v <= adc_reading <= test_lim_hi_v
                log.info("{} - {}: {} <= {} <= {}".format("PASS" if test_pass else "FAIL", channel_name,
                                                          test_lim_lo_v, adc_reading, test_lim_hi_v))
                ret_val = test_pass and ret_val

            for channel_name in pgood_channels:
                test_pass = cpt.read_som_bit_pgood(channel_name)
                log.info("{} - {}".format("PASS" if test_pass else "FAIL", channel_name))
                ret_val = test_pass and ret_val

        return ret_val

    def external_pps_test(self):
        """
        Tests the external 1PPS sources of the board/unit under test.
        Prerequisites:
        - Board is powered up
        - Linux is booted
        Uses:
        - Test jig STM32 serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("External 1PPS Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            for pps_source in CsmTestJigPpsSource if self.unit_type is UnitTypes.VEHICLE else MpTestJigPpsSource:
                if pps_source is CsmTestJigPpsSource.CSM_SLAVE_PPS or \
                        pps_source is MpTestJigPpsSource.CONTROL_MASTER_SLAVE:
                    with CsmPlatformTest(self._csm_username,
                                         self._csm_hostname if self._csm_ip_address is None else
                                         self._csm_ip_address) as cpt:
                        ret_val = cpt.set_external_1pps_direction(output=True) and ret_val

                test_pass1 = ctji.set_pps_source(pps_source)
                time.sleep(3.0)
                test_pass2, pps_delta = ctji.get_pps_detected()
                log.info("{} - {} ms {}".format("PASS" if test_pass2 else "FAIL", pps_delta, pps_source))
                ret_val = ret_val and test_pass1 and test_pass2

        return ret_val

    def internal_pps_test(self):
        """
        Tests the internal 1PPS sources of the board under test.
        Prerequisites:
        - Board is powered up
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Internal 1PPS Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            test_pass, pps_delta = czm.get_pps_detected()
            log.info("{} - {} ms Zeroise Micro".format("PASS" if test_pass else "FAIL", pps_delta))
            ret_val = ret_val and test_pass

        return ret_val

    def ptp_phy_test(self):
        """
        Tests the board/unit under test PTP Fast Ethernet Phy connected to the SoM.
        Prerequisites:
        - Board is powered up
        - Linux is booted
        Uses:
        - CSM Master serial port connected to Linux terminal
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("PTP PHY Test:")
        return ppt.run_test(self._master_com_port, self._csm_username, self._CSM_PASSWORD)

    def uart_test(self):
        """
        Tests the board under test UARTs.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_sequence = [
            # serial_port, baud_rate
            (self._zeroise_micro_serial_port, 115200),  # Zeroise Micro
            (self._csm_slave_serial_port, 115200),      # CSM Slave
            (self._programming_serial_port, 115200)     # Programming
        ] if self.unit_type is UnitTypes.VEHICLE else [
            (self._zeroise_micro_serial_port, 115200),  # Zeroise Micro
            (self._programming_serial_port, 115200)  # Programming
        ]

        log.info("")
        log.info("UART Test:")
        ret_val = True
        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            for serial_port, baud_rate in test_sequence:
                test_pass = cpt.uart_test(serial_port, baud_rate)
                log.info("{} - UART Test {}".format("PASS" if test_pass else "FAIL", serial_port))
                ret_val = test_pass and ret_val
        return ret_val

    def tmp442_test(self):
        """
        Tests the board/unit under test TMP442 temperature sensor.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_values = [
            # channel, test_lim_lo, test_lim_hi
            ("Internal", 20, 60),
            ("Remote 1", 35, 75),
            ("Remote 2", 35, 75)
        ]

        log.info("")
        log.info("TMP442 Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            temp_vals = cpt.get_tmp442_temperatures()

            if len(temp_vals) == len(test_values):
                for channel, test_lim_lo, test_lim_hi in test_values:
                    test_pass = test_lim_lo <= temp_vals.get(channel, -128) <= test_lim_hi
                    log.info("{} - {} {} <= {} <= {}".format("PASS" if test_pass else "FAIL", channel,
                                                             test_lim_lo, temp_vals.get(channel, -128), test_lim_hi))
                    ret_val = test_pass and ret_val
            else:
                log.info("FAIL - Failed to read TMP442 temperature sensor!")

        return ret_val

    def ad7415_test(self):
        """
        Tests the board/unit under test AD7415 temperature sensor.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_lim_lo = 20
        test_lim_hi = 60

        log.info("")
        log.info("AD7415 Test:")

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            temperature = cpt.get_ad7415_temperature()
            ret_val = test_lim_lo <= temperature <= test_lim_hi
            log.info("{} - Temperature {} <= {} <= {}".format("PASS" if ret_val else "FAIL",
                                                              test_lim_lo, temperature, test_lim_hi))
        return ret_val

    def eui48_id_test(self):
        """
        Reads the EUI48 Device IDs from the board and checks their validity.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type: Boolean
        """
        log.info("")
        log.info("EUI48 ID Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            eui48_id_vals = cpt.read_eui48_ids()

            for device in eui48_id_vals:
                log.info("INFO - {} EUI48 {}".format(device, eui48_id_vals[device].get("dev_id", "")))
                test_pass = eui48_id_vals[device].get("dev_id_valid", False)
                log.info("{} - {} OUI valid".format("PASS" if test_pass else "FAIL", device))
                ret_val = test_pass and ret_val

        return ret_val

    def print_som_mac_ipv4_address(self):
        """
        Reads and prints the SoM MAC and IPV4 address.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True
        """
        log.info("")

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            mac_address, ipv4_address = cpt.read_som_mac_ipv4_address()
            log.info("INFO - SoM MAC Address:\t\t{}".format(mac_address))
            log.info("INFO - SoM IPV4 Address:\t{}".format(ipv4_address))

        return True

    def super_flash_mount_test(self):
        """
        Check that all of the SuperFlash devices have been mounted by Linux.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        mounted_superflash_devices = {
            "mtd0 on /mnt/sf0 type jffs2 (rw,noatime,sync)",
            "mtd1 on /mnt/sf1 type jffs2 (rw,noatime,sync)",
            "mtd2 on /mnt/sf2 type jffs2 (rw,noatime,sync)",
            "mtd3 on /mnt/sf3 type jffs2 (rw,noatime,sync)",
            "mtd4 on /mnt/sf4 type jffs2 (rw,noatime,sync)",
            "mtd5 on /mnt/sf5 type jffs2 (rw,noatime,sync)",
            "mtd6 on /mnt/sf6 type jffs2 (rw,noatime,sync)",
            "mtd7 on /mnt/sf7 type jffs2 (rw,noatime,sync)"
        }

        log.info("")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            mount_string = cpt.read_mount_cmd_response()
            log.debug(mount_string)
            for device in mounted_superflash_devices:
                ret_val = (mount_string.find(device) != -1) and ret_val

        log.info("{} - SuperFlash Mount Test".format("PASS" if ret_val else "FAIL"))

        return ret_val

    def gps_lock_test(self):
        """
        Perform GPS lock test.
        Prerequisites:
        - Board is powered up
        - Active GPS antenna connected to P9
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("GPS Lock Test:")
        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            # Allow up to three-minutes for the GPS to clock, NEO-M8T cold start time is <30 seconds
            for i in range(0, 6):
                ret_val = cpt.read_gps_lock(self._gnss1_serial_port)
                if ret_val:
                    break
            log.info("{} - GPS Lock Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def tcxo_adjust_test(self):
        """
        Perform TCXO adjustment test.
        Prerequisites:
        - Board is powered up
        - Active GPS antenna connected to P9
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("TCXO Adjustment Test:")
        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = cpt.tcxo_adjust_test()
            log.info("{} - TCXO Adjustment Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def som_i2c_device_detect_test(self):
        """
        Perform SoM I2C device detection test.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        som_i2c_device_address_list = [
            "20: -- -- 22",
            "40: -- -- -- -- -- -- -- -- 48 49 -- -- 4c ",
            "50: UU UU UU ",
            "60: -- -- -- -- 64 -- -- -- UU "
        ]

        log.info("")
        log.info("SoM I2C Device Detection Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            i2c_detect_string = cpt.read_i2c_device_detect_string()
            for i2c_device in som_i2c_device_address_list:
                if i2c_detect_string.find(i2c_device) == -1:
                    ret_val = False

        log.info("{} - SoM I2C Device Detection Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def som_eia422_intf_test(self):
        """
        Tests the board/unit under test RCU EIA-422 serial interface to the SoM.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - CSM Zeroise Microcontroller is programmed with test utility
        Uses:
        - CSM Master serial port connected to Linux terminal
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("SoM EIA-422 Interface Test:")
        return seit.run_test(self._rcu_com_port, self._master_com_port,
                             self._csm_username, self._CSM_PASSWORD, self._rcu_serial_port)

    def keypad_test(self):
        """
        Test the board under test Keypad interface.
        Prerequisites:
        - KT-000-0197-00 loopback board is fitted to KT-000-0140-00 Keypad connector, P7; OR KT-000-0203-00 loopback
          circuit is connected to KT-000-0180-00 Keypad connector, P33
        - Board is powered on
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        hard_power_off_time_lo = 8.0
        hard_power_off_time_hi = 13.0

        log.info("")
        log.info("Keypad Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()

            # Test Keypad Buttons 0-2
            test_pass = czm.test_keypad()
            log.info("{} - Keypad Button 0-2 Test".format("PASS" if test_pass else "FAIL"))
            ret_val = ret_val and test_pass

            # Test the Keypad Power Button
            start_time = time.perf_counter()
            test_pass = czm.toggle_keypad_power_button(hard_power_off=True)

            while True:
                end_time = time.perf_counter()
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)

                if psu_i_ma < 100 or \
                        end_time > (start_time + hard_power_off_time_hi + (hard_power_off_time_hi * 0.1)):
                    break

            # Check the reset time
            test_pass = test_pass and (hard_power_off_time_lo <= end_time - start_time <= hard_power_off_time_hi)
            log.info("{} - Keypad Power Button Hard Off Time: {} <= {:.2f} <= {} seconds"
                     "".format("PASS" if test_pass else "FAIL",
                               hard_power_off_time_lo, end_time - start_time, hard_power_off_time_hi))
            ret_val = ret_val and test_pass

        self._set_psu_off()

        log.info("{} - Keypad Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def buzzer_test(self):
        """
        Test the board under test buzzer.
        Prerequisites:
        - Board is powered up
        - Linux is booted
        - CSM Zeroise Microcontroller is programmed with test utility
        Uses:
        - Test jig STM32 serial interface
        - CSM RCU serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Buzzer Test:")
        ret_val = True

        with self._get_zero_micro_interface_instance() as czm:
            with self._get_test_jig_interface_instance() as ctji:
                # De-assert -> Assert -> De-assert the buzzer then check the ADC data
                for assert_val in [False, True, False]:
                    ret_val = czm.set_buzzer_enable(assert_val) and ret_val
                    time.sleep(1.0)
                    adc_read, adc_data = ctji.get_adc_data()
                    adc_key = "(mv) Buzzer +12V Supply"
                    if assert_val:
                        test_pass = (11400 <= adc_data.get(adc_key, -1) <= 12600)
                        log.info("{} - Buzzer +12V: 11400 <= {} <= 126500"
                                 "".format(self._pass_fail_string(test_pass), adc_data.get(adc_key, -1)))
                    else:
                        test_pass = (adc_data.get(adc_key, -1) < 11400 or adc_data.get(adc_key, -1) > 12600)
                        log.info("{} - Buzzer +12V: {} < 11400 OR {} > 12600"
                                 "".format(self._pass_fail_string(test_pass), adc_data.get(adc_key, -1),
                                           adc_data.get(adc_key, -1)))

                    ret_val = ret_val and test_pass

        log.info("{} - Buzzer Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def zeroise_fpga_test(self):
        """
        Tests the Zeroise FPGA and its interfaces.
        Prerequisites:
        - CSM Zeroise Microcontroller is programmed with test utility
        - CSM Zeroise FPGA is programmed with test utility
        Uses:
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        self.power_up_board()
        log.info("")
        log.info("Zeroise FGPA Test:")

        with self._get_zero_micro_interface_instance() as czm:
            zer_fpga_pwr_en_signal = CsmGpoSignals.ZER_FPGA_PWR_EN if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_FPGA_PWR_EN
            zer_i2c_fpga_en_signal = CsmGpoSignals.ZER_I2C_FPGA_EN if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_I2C_FPGA_EN
            zer_fpga_rst_signal = CsmGpoSignals.ZER_FPGA_RST if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_FPGA_RST

            ret_val = czm.set_gpo_signal(zer_fpga_pwr_en_signal, 1)
            ret_val = czm.set_gpo_signal(zer_i2c_fpga_en_signal, 0) and ret_val
            time.sleep(0.5)

            ret_val = not czm.set_zeroise_fpga_gpo_reg(0x00) and ret_val

            ret_val = czm.set_gpo_signal(zer_i2c_fpga_en_signal, 1) and ret_val
            time.sleep(0.5)

            ret_val = czm.set_zeroise_fpga_gpo_reg(0x55) and ret_val

            cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
            ret_val = ret_val and cmd_success and value == 0x55

            ret_val = czm.set_zeroise_fpga_gpo_reg(0xCA) and ret_val

            cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
            ret_val = ret_val and cmd_success and value == 0xCA

            ret_val = czm.set_gpo_signal(zer_fpga_pwr_en_signal, 0) and ret_val
            time.sleep(0.5)

            ret_val = not czm.set_zeroise_fpga_gpo_reg(0x00) and ret_val
            time.sleep(1.0)

            ret_val = czm.set_gpo_signal(zer_fpga_pwr_en_signal, 1) and ret_val
            time.sleep(0.5)

            ret_val = czm.set_zeroise_fpga_gpo_reg(0xAA) and ret_val

            cmd_success, value = czm.get_zeroise_fpga_gpo_reg()
            ret_val = ret_val and cmd_success and value == 0xAA

            ret_val = czm.set_gpo_signal(zer_fpga_rst_signal, 1) and ret_val
            time.sleep(0.1)

            ret_val = not czm.set_zeroise_fpga_gpo_reg(0x00) and ret_val

            ret_val = czm.set_gpo_signal(zer_fpga_rst_signal, 0) and ret_val
            time.sleep(0.1)

        self._set_psu_off()

        log.info("{} - Zeroise FPGA Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def power_up_board(self, psu_voltage_mv=24000, psu_i_limit_ma=5000, linux_run_check=False, csm_serial_no="000000"):
        """
        Powers up the board
        :return: True if board powered up, else False
        """
        serial_no = str(csm_serial_no)
        ret_val = True

        self._set_psu_off()
        time.sleep(1.0)
        self._set_psu_on(psu_voltage_mv, psu_i_limit_ma)
        time.sleep(1.0)
        with self._get_test_jig_interface_instance() as ctji:
            ctji.toggle_rcu_power_button()
        time.sleep(1.0)

        if linux_run_check:
            log.info("")
            log.info("Powering up board and waiting for Linux to boot... (approx 60-seconds)")
            # Look for the login prompt on the CSM Master SoM serial terminal
            with Serial(self._master_com_port, 115200, timeout=3.0,
                        xonxoff=False, rtscts=False, dsrdtr=False) as cmsp:
                # Allow 30 x 3-second timeout, 90-seconds for boot
                at_login_prompt = False
                console_str = b""
                for _ in range(0, 30):
                    # console_str += cmsp.read_until(b"CSM-" + serial_no.encode("UTF-8") + b" login:")
                    console_str += cmsp.read_until(b" login:")
                    log.debug("{}: {}".format(_, console_str))
                    # if b"CSM-" + serial_no.encode("UTF-8") + b" login:" in console_str:
                    if b" login:" in console_str:
                        at_login_prompt = True
                        
                        # Use the Zeroconf CSM lookup to try to determine the board/unit's IPv4 address as this will 
                        # make SSH connections to the device quicker.  The unit serial no. may not have been set at this 
                        # point so search for a single CSM and assume that this is the one to be tested.
                        time.sleep(10.0)
                        found_units = self.find_csms()
                        if len(found_units) == 1:
                            self._csm_ip_address = found_units[0][1]
                        break

                if not at_login_prompt:
                    log.info("FAIL - Failed to find Linux login prompt!")
                    ret_val = False
                else:
                    log.info("PASS - Found Linux login prompt")

        return ret_val

    def gbe_chassis_gnd_test(self):
        """
        Test the external GbE port chassis ground connections are present.
        Prerequisites:
        - Board is powered up
        Uses:
        - Test jig STM32 serial interface
        :return: True if test passes, else False :type: Boolean
        """
        test_sequence = [
            # ch_name, lim_lo_mv, lim_hi_mv
            ("RCU Eth Gnd", 770, 880),
            ("Prog Eth Gnd", 1640, 1740),
            ("CSM Master Eth Gnd", 4130, 4230),
            ("CSM Slave Eth Gnd", 3260, 3360)
        ]

        log.info("")
        log.info("GbE Chassis Ground Test")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            read_success, adc_data = ctji.get_adc_data()
            ret_val = ret_val and read_success

            for ch_name, lim_lo_mv, lim_hi_mv in test_sequence:
                test_mv = adc_data.get("(mv) {}".format(ch_name), -1)
                test_pass = (lim_lo_mv <= test_mv <= lim_hi_mv)
                log.info("{} - {}: {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", ch_name, lim_lo_mv, test_mv, lim_hi_mv))
                ret_val = ret_val and test_pass

        log.info("{} - GbE Chassis Ground Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def pb_controller_irq_test(self):
        """
        Tests the push-button controller interrupt output, need to do this in <10-seconds to avoid hard power-off
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - Test jig STM32 serial interface
        - CSM SSH connection
        :return: True if test passes, else False :type: Boolean
        """
        log.info("")
        log.info("Power Button Controller Interrupt Test")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            with self._get_test_jig_interface_instance()as ctji:
                rcu_pwr_butt_sig = CsmTestJigGpoSignals.RCU_POWER_BUTTON if self.unit_type is UnitTypes.VEHICLE else \
                    MpTestJigGpoSignals.RCU_POWER_BUTTON
                ret_val = not cpt.get_pb_ctrl_irq() and ret_val
                ctji.assert_gpo_signal(rcu_pwr_butt_sig, True)
                time.sleep(4.0)
                ret_val = cpt.get_pb_ctrl_irq() and ret_val
                ctji.assert_gpo_signal(rcu_pwr_butt_sig, False)
                time.sleep(4.0)
                ret_val = not cpt.get_pb_ctrl_irq() and ret_val

        log.info("{} - Power Button Controller Interrupt Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def power_kill_test(self):
        """
        Uses the SoM power kill signal to the push-button controller to turn the board off.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM Master serial port connected to Linux terminal
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Power Kill Test:")

        with Serial(self._master_com_port, 115200, timeout=3.0, xonxoff=False, rtscts=False, dsrdtr=False) as cmsp:
            # Try to ensure that we are at the root command line prompt:
            # - send Ctr-X, just in case a microcom terminal is open
            # - send login username and password credentials
            cmsp.write(b"\x18")
            time.sleep(1.0)
            cmsp.write("{}\r".format(self._csm_username).encode("UTF-8"))
            time.sleep(1.0)
            cmsp.write("{}\r".format(self._CSM_PASSWORD).encode("UTF-8"))
            cmsp.read_until("{}@CSM-".format(self._csm_username).encode("UTF-8"))
            cmsp.write(b"cd ~\r")
            cmsp.read_until(b":~#")
            cmsp.write(b"python3 /run/media/mmcblk1p2/test/kill_power.py\r")
            time.sleep(3.0)
            ret_val = int(float(self.tpsu.runningCurrent(1)) * 1000.0) < 50.0
            log.info("{} - Power Kill Test".format("PASS" if ret_val else "FAIL"))

        return ret_val

    def remove_test_scripts(self):
        """
        Remove the test scripts from the eMMC
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - CSM Master serial terminal
        - CSM SSH connection
        :return: True if successful, else FAlse
        """
        log.info("")
        log.info("Removing Test Scripts from eMMC:")

        self.power_supply_off()
        self.power_up_board(linux_run_check=True)

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = cpt.remove_test_scripts()

        time.sleep(10.0)
        self.power_supply_off()

        log.info("{} - Removed test scripts from SoM eMMC".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def copy_test_scripts_to_som(self, test_script_archive):
        """
        Copy the test scripts from the eMMC
        Prerequisites:
        - Board is powered and running Linux
        Uses:
        - CSM SSH connection
        :return: True if successful, else False
        """
        log.info("")
        log.info("Copying Test Scripts to eMMC:")

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = cpt.copy_test_scripts_to_som(test_script_archive)

        log.info("{} - Copied test scripts to SoM eMMC".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def power_supply_off(self):
        """
        Turns the bench power supply off
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        :return: True
        """
        self._set_psu_off()
        return True

    def program_som(self):
        """
        Program the SoM.
        Prerequisites:
        - boot.bin, system.bin and image.ub files on SoM SD Card installed on board under test
        Uses:
        - Test jig STM32 serial interface
        - CSM Master serial port connected to Linux terminal
        :return: True if device programmed, else False
        """
        self._set_psu_off()
        time.sleep(1.0)
        self._set_psu_on()
        time.sleep(1.0)
        log.info("")
        log.info("Programming SoM")
        som_sd_boot_en_signal = CsmTestJigGpoSignals.SOM_SD_BOOT_ENABLE if self.unit_type is UnitTypes.VEHICLE else \
            MpTestJigGpoSignals.SOM_SD_BOOT_ENABLE
        with self._get_test_jig_interface_instance() as ctji:
            ret_val = cpd.program_som(self._csm_username, self._CSM_PASSWORD, self._tj_com_port, self._master_com_port,
                                      test_jig_intf=ctji, som_sd_boot_en_signal=som_sd_boot_en_signal)
        log.info("{} - Program SoM".format("PASS" if ret_val else "FAIL"))
        self._set_psu_off()
        return ret_val

    def program_gbe_sw_fw(self, csm_serial_no="000000",
                          fw_file="KT-956-0195-00.bin", fw_file_path="/run/media/mmcblk0p1/"):
        """
        Program the GbE Switch SPI Flash device using the SoM.
        Prerequisites:
        - GbE Switch Firmware binary file on SoM SD Card or eMMC
        Uses:
        - Test jig STM32 serial interface
        - CSM Master serial port connected to Linux terminal
        :return: True if device programmed, else False
        """
        self._set_psu_off()
        time.sleep(1.0)
        self._set_psu_on()
        time.sleep(1.0)
        log.info("")
        log.info("Programming GbE Switch Firmware")
        with self._get_test_jig_interface_instance() as ctji:
            ret_val = cpd.program_gbe_sw_spi_flash_from_som(self._csm_username, self._tj_com_port,
                                                            self._master_com_port, fw_file, fw_file_path, ctji)
        log.info("{} - Program GbE Switch Firmware".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def program_zeroise_fpga(self, fpga_job_file, erase=False):
        """
        Program the Board Under Test Zeroise FPGA
        Prerequisites:
        - None
        Uses:
        - Microchip FlashPro programmer
        - Zeroise Microcontroller Test Utility RCU serial interface
        :param erase: set True to erase the FPGA, leave unspecified or set to False to program the FPGA
        :param fpga_job_file: FlashPro Express job file
        :return: True if device programmed, else False
        """
        with self._get_zero_micro_interface_instance() as czm:
            self.power_up_board()
            log.info("")

            zer_fpga_pwr_en_signal = CsmGpoSignals.ZER_FPGA_PWR_EN if self.unit_type is UnitTypes.VEHICLE else \
                MpGpoSignals.ZER_FPGA_PWR_EN

            # Ensure that the the Zeroise FPGA power is enabled
            czm.set_gpo_signal(zer_fpga_pwr_en_signal, True)
            time.sleep(1.0)
            if erase:
                log.info("Erasing Zeroise FPGA:")
                ret_val = cpd.erase_zeroise_fpga(fpga_job_file)
                action = "Erase"
            else:
                log.info("Programming Zeroise FPGA:")
                ret_val = cpd.program_zeroise_fpga(fpga_job_file)
                action = "Program"
            log.info("{} - {} Zeroise FPGA".format("PASS" if ret_val else "FAIL", action))

            # Disable Zeroise FPGA power
            czm.set_gpo_signal(zer_fpga_pwr_en_signal, False)
            time.sleep(1.0)

            self._set_psu_off()

        return ret_val

    def program_zeroise_micro(self, zeroise_fw_bin):
        """
        Program the Board Under Test Zeroise STM32 Microcontroller
        Prerequisites:
        - None
        Uses:
        - Segger J-Link programmer
        :param zeroise_fw_bin: firmware binary file
        :return: True if device programmed, else False
        """
        log.info("")
        log.info("Programming Zeroise Microcontroller:")
        # self.power_up_board()
        with self._get_test_jig_interface_instance() as ctji:
            pwr_en_zer_sig = CsmTestJigGpoSignals.RCU_POWER_ENABLE_ZEROISE if self.unit_type is UnitTypes.VEHICLE else \
                MpTestJigGpoSignals.RCU_POWER_ENABLE_ZEROISE
            ctji.assert_gpo_signal(pwr_en_zer_sig, True)
            time.sleep(1.0)
            ret_val = cpd.program_micro_device(zeroise_fw_bin)
            ctji.assert_gpo_signal(pwr_en_zer_sig, False)
        log.info("{} - Program Zeroise Microcontroller: {}".format("PASS" if ret_val else "FAIL", zeroise_fw_bin))
        self._set_psu_off()
        return ret_val

    @staticmethod
    def find_csms(timeout=10):
        ret_val = []
        type_ = "_{}._tcp.local.".format("ssh")
        count = timeout * 10

        def on_change(zeroconf, service_type, name, state_change):
            nonlocal ret_val
            nonlocal count
            if state_change is zeroconfig.ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    address = "{}".format(socket.inet_ntoa(info.addresses[0]))
                    server = str(info.server)
                    if "CSM-" in server:
                        ret_val.append([server.rstrip("."), address])

        zeroconf = zeroconfig.Zeroconf()
        browser = zeroconfig.ServiceBrowser(zeroconf, type_, handlers=[on_change])

        while count > 0:
            time.sleep(0.1)
            count = count - 1

        zeroconf.close()
        return ret_val

    def _set_psu_on(self, voltage_mv=24000, i_limit_ma=3000):
        """
        Sets the Tenma bench PSU to the specified voltage and current limit then turns it on.
        :param voltage_mv: bench PSU supply voltage in mV, optional :type Integer
        :param voltage_mv: bench PSU current limit in mA, optional :type Integer
        :return: N/A
        """
        if self.tpsu is not None:
            self.tpsu.setVoltage(1, voltage_mv)
            self.tpsu.setCurrent(1, i_limit_ma)
            self.tpsu.ON()
        else:
            raise RuntimeError("PSU Test Equipment Error!")

    def _get_average_psu_running_i_ma(self, period_s):
        """
        Monitor the PSU running current for the given period and return the average
        :param period_s: number of seconds to monitor PSU running current for :type Integer
        :return: average current in mA :type Integer
        """
        no_samples = int(period_s) * 10
        running_total = 0
        for i in range(0, no_samples):
            running_total += int(float(self.tpsu.runningCurrent(1)) * 1000.0)
            time.sleep(0.1)
        return running_total / no_samples

    def _set_psu_off(self):
        """
        Turn the PSU off.
        :return: N/A
        """
        if self.tpsu is not None:
            self.tpsu.OFF()
        else:
            raise RuntimeError("PSU Test Equipment Error!")

    def _get_tenma_psu_instance(self):
        """
        Get a proper Tenma PSU subclass depending on the *IDN? response from the unit.
        The subclasses mainly deals with the limit checks for each PSU type.
        """
        # Instantiate base to retrieve ID information
        tpsu = Tenma72Base(self._psu_com_port, debug=False)
        ver = tpsu.getVersion()
        # Need to close the serial port otherwise call to create specific device
        # instance will fail
        tpsu.close()

        for cls in Tenma72Base.__subclasses__():
            if cls.MATCH_STR[0] in ver:
                return cls(self._psu_com_port, debug=False)

        log.critical("Could not detect Tenma PSU!")
        return None

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

            if not output or "unreachable" in output or "0 packets received" in output or \
                    "could not find" in output or "Request timed out" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

    def _get_zero_micro_interface_instance(self):
        """
        Utility method to return the correct type of Zeroise Micro Test Utility Interface object for the
        unit type being tested.
        :return:
        """
        return CsmZeroiseMircoTestInterface(self._rcu_com_port) if self.unit_type is UnitTypes.VEHICLE else \
            MpZeroiseMircoTestInterface(self._rcu_com_port)

    def _get_test_jig_interface_instance(self):
        """
        Utility method to return the correct type of Test Jig Interface object for the unit type being tested.
        :return:
        """
        return CsmTestJigInterface(self._tj_com_port) if self.unit_type is UnitTypes.VEHICLE else \
            MpTestJigInterface(self._tj_com_port)

    @staticmethod
    def _pass_fail_string(test_val):
        """ Utility method to return pass or fail string based on a boolean value """
        return "PASS" if bool(test_val) else "FAIL"


class CsmProdTest(CommonCsmProdTest):
    """
    Concrete class that implements test cases and functionality for Vehicle CSM testing.
    """
    _CSM_MOTHERBOARD_NO = "KT-000-0140-00"
    _CSM_ASSEMBLY_NO = "KT-950-0351-00"

    def __init__(self, tj_com_port, psu_com_port, tpl_sw_com_port, master_com_port, rcu_com_port,
                 csm_hostname, csm_username, zeroise_micro_serial_port, csm_slave_serial_port,
                 rcu_serial_port, programming_serial_port, gnss1_serial_port, gbe_switch_serial_port,
                 exp_slot_1_serial_port, exp_slot_2_serial_port,
                 segger_jlink_win32=None, segger_jlink_win64=None, flash_pro=None, iperf3=None, cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param tj_com_port: test jig NUCLEO STM32 COM port :type String
        :param psu_com_port: Tenma bench PSU COM port :type String
        :param tpl_sw_com_port: TP-Link managed switch COM port :type String
        :param master_com_port: board/unit under test CSM Master COM port :type String
        :param rcu_com_port: board/unit under test RCU COM port :type String
        :param csm_hostname: board/unit under test network hostname :type String
        :param zeroise_micro_serial_port: CSM serial port :type String
        :param csm_slave_serial_port: CSM serial port :type String
        :param rcu_serial_port: CSM serial port :type String
        :param programming_serial_port: CSM serial port :type String
        :param gnss1_serial_port: CSM serial port :type String
        :param gbe_switch_serial_port: CSM serial port :type String
        :param exp_slot_1_serial_port: Expansion Slot 1 serial port :type String
        :param exp_slot_2_serial_port: Expansion Slot 2 serial port :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param flash_pro: Microchip FlashPro exe path, default is None, use csm_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        super().__init__(tj_com_port, psu_com_port, tpl_sw_com_port, master_com_port, rcu_com_port,
                         csm_hostname, csm_username, zeroise_micro_serial_port, csm_slave_serial_port,
                         rcu_serial_port, programming_serial_port, gnss1_serial_port, gbe_switch_serial_port,
                         exp_slot_1_serial_port, exp_slot_2_serial_port, segger_jlink_win32, segger_jlink_win64,
                         flash_pro, iperf3, cygwin1_dll)

        self.unit_type = UnitTypes.VEHICLE

    def over_under_voltage_lockout_test(self):
        """
        Tests board/unit under test over/under-voltage lockout protection circuit.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        :return: True if the test passed, else False :type Boolean
        """
        under_voltage_lockout_mv = 6000
        over_voltage_lockout_mv = 41000
        operational_voltage_mv = [32000, 18000, 24000]
        off_i_ma_lo = 0
        off_i_ma_hi = 10
        on_i_ma_lo = 15
        on_i_ma_hi = 35

        pb_above_uv_threshold_mv = 11200
        pb_below_uv_threshold_mv = 10200
        pb_i_ma_lo = 20
        pb_i_ma_hi = 40
        pb_test_sequence = [(pb_above_uv_threshold_mv, pb_i_ma_lo, pb_i_ma_hi),
                            (pb_below_uv_threshold_mv, pb_i_ma_lo, pb_i_ma_hi),
                            (pb_above_uv_threshold_mv, pb_i_ma_lo, pb_i_ma_hi)]

        log.info("")
        log.info("Over/Under Voltage Lockout Test:")
        ret_val = True

        if self.tpsu is not None:
            # Under-voltage lockout
            self.tpsu.OFF()
            self.tpsu.setVoltage(1, under_voltage_lockout_mv)
            self.tpsu.setCurrent(1, 5000)   # mA
            self.tpsu.ON()
            time.sleep(2.0)

            # Check the PSU current
            psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
            test_pass = (off_i_ma_lo <= psu_i_ma <= off_i_ma_hi)
            log.info("{} - Under-Voltage Bench PSU Current: {} <= {} <= {} mA"
                     "".format("PASS" if test_pass else "FAIL", off_i_ma_hi, psu_i_ma, off_i_ma_hi))
            ret_val = ret_val and test_pass

            # Over-voltage lockout
            self.tpsu.OFF()
            self.tpsu.setVoltage(1, over_voltage_lockout_mv)  # mV
            self.tpsu.setCurrent(1, 5000)  # mA
            self.tpsu.ON()
            time.sleep(2.0)

            # Check the PSU current
            psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
            test_pass = (off_i_ma_lo <= psu_i_ma <= off_i_ma_hi)
            log.info("{} - Over-Voltage Bench PSU Current: {} <= {} <= {} mA"
                     "".format("PASS" if test_pass else "FAIL", off_i_ma_hi, psu_i_ma, off_i_ma_hi))
            ret_val = ret_val and test_pass

            # Operational voltage range
            self.tpsu.OFF()
            for op_volt_mv in operational_voltage_mv:
                self.tpsu.setVoltage(1, op_volt_mv)
                self.tpsu.ON()
                time.sleep(2.0)
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (on_i_ma_lo <= psu_i_ma <= on_i_ma_hi)
                log.info("{} - {} V Bench PSU Current: {} <= {} <= {} mA"
                         "".format("PASS" if test_pass else "FAIL", op_volt_mv / 1000.0,
                                   on_i_ma_lo, psu_i_ma, on_i_ma_hi))
                ret_val = ret_val and test_pass

            # Push-button controller under-voltage lockout
            for test_mv, lim_lo, lim_hi in pb_test_sequence:
                self.tpsu.setVoltage(1, test_mv)
                time.sleep(1.0)
                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (lim_lo <= psu_i_ma <= lim_hi)
                log.info("{} - PB Under-Voltage Bench PSU Current: {} <= {} <= {} mA"
                         "".format("PASS" if test_pass else "FAIL", lim_lo, psu_i_ma, lim_hi))
                ret_val = ret_val and test_pass

            self.tpsu.OFF()
        else:
            raise RuntimeError("PSU Test Equipment Error!")

        log.info("{} - Over/Under Voltage Lockout Test".format("PASS" if ret_val else "FAIL"))

        return ret_val

    def external_power_off_test(self):
        """
        Tests the board under test external power on/off signals.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :return: True if the test passed, else False :type Boolean
        """
        test_sequence1 = [
            # rcu_pwr_btn_hard_pwr_off, rem_pwr_en_mv_lo, rem_pwr_en_mv_hi, rcu_12v_mv_lo, rcu_12v_mv_hi,
            # pwr_off_range_lo, pwr_off_range_hi, psu_ma_lo, psu_ma_hi
            (True, 2475, 2525, 0, 100, 450, 550, 15, 35),
            (False, 450, 550, 11400, 12600, 2475, 2525, 100, 3000),
            (True, 2475, 2525, 0, 1200, 450, 550, 15, 35),
        ]
        test_sequence2 = [
            # rem_pwr_on_in, meas_delay, rcu_12v_mv_lo, rcu_12v_mv_hi, psu_ma_lo, psu_ma_hi
            (False, 2.0, 0, 100, 15, 35),
            (True, 2.0, 11400, 12600, 100, 3000),
            (False, 12.0, 0, 100, 15, 35)
        ]

        log.info("")
        log.info("External Power On/Off Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            self._set_psu_on()
            time.sleep(1.0)
            # Cheat to make sure the first iteration of the test sequence works
            ctji.toggle_rcu_power_button()
            time.sleep(2.0)

            for rcu_pwr_btn_hard_pwr_off, rem_pwr_en_mv_lo, rem_pwr_en_mv_hi, rcu_12v_mv_lo, rcu_12v_mv_hi, \
                    pwr_off_range_lo, pwr_off_range_hi, psu_ma_lo, psu_ma_hi in test_sequence1:

                ctji.toggle_rcu_power_button(rcu_pwr_btn_hard_pwr_off)
                time.sleep(2.0)
                adc_read, adc_data = ctji.get_adc_data()

                # RCU +12V Voltage
                test_mv = adc_data.get("(mv) RCU +12V Out", -1)
                test_pass = (rcu_12v_mv_lo <= test_mv <= rcu_12v_mv_hi)
                log.info("{} - RCU +12V Voltage: {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", rcu_12v_mv_lo, test_mv, rcu_12v_mv_hi))
                ret_val = ret_val and test_pass

                # Remote Power On Out
                test_mv = adc_data.get("(mv) Rem Pwr On Out CSM Slave", -1)
                test_pass = (rem_pwr_en_mv_lo <= test_mv <= rem_pwr_en_mv_hi)
                log.info("{} - Remote Power On Out Voltage: {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", rem_pwr_en_mv_lo, test_mv, rem_pwr_en_mv_hi))
                ret_val = ret_val and test_pass

                # CSM Master Power Off
                test_mv = adc_data.get("(mv) Power Off CS Master", -1)
                test_pass = (pwr_off_range_lo <= test_mv <= pwr_off_range_hi)
                log.info("{} - CSM Master Power Off Voltage:  {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", pwr_off_range_lo, test_mv, pwr_off_range_hi))
                ret_val = ret_val and test_pass

                # CSM Slave Power Off
                test_mv = adc_data.get("(mv) Power Off CS Slave", -1)
                test_pass = (pwr_off_range_lo <= test_mv <= pwr_off_range_hi)
                log.info("{} - CSM Slave Power Off Voltage: {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", pwr_off_range_lo, test_mv, pwr_off_range_hi))
                ret_val = ret_val and test_pass

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (psu_ma_lo <= psu_i_ma <= psu_ma_hi)
                log.info("{} - Bench PSU Current: {} <= {} <= {} mA"
                         "".format("PASS" if test_pass else "FAIL", psu_ma_lo, psu_i_ma, psu_ma_hi))
                ret_val = ret_val and test_pass

            for rem_pwr_on_in, meas_delay, rcu_12v_mv_lo, rcu_12v_mv_hi, psu_ma_lo, psu_ma_hi in test_sequence2:
                ctji.assert_gpo_signal(CsmTestJigGpoSignals.REMOTE_POWER_ON_IN, rem_pwr_on_in)
                time.sleep(meas_delay)

                # RCU +12V Voltage
                adc_read, adc_data = ctji.get_adc_data()
                test_mv = adc_data.get("(mv) RCU +12V Out", -1)
                test_pass = (rcu_12v_mv_lo <= test_mv <= rcu_12v_mv_hi)
                log.info("{} - RCU +12V Voltage: {} <= {} <= {} mV"
                         "".format("PASS" if test_pass else "FAIL", rcu_12v_mv_lo, test_mv, rcu_12v_mv_hi))
                ret_val = ret_val and test_pass

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (psu_ma_lo <= psu_i_ma <= psu_ma_hi)
                log.info("{} - Bench PSU Current: {} <= {} <= {} mA"
                         "".format("PASS" if test_pass else "FAIL", psu_ma_lo, psu_i_ma, psu_ma_hi))
                ret_val = ret_val and test_pass

        self._set_psu_off()
        log.info("{} - External Power Off Test".format("PASS" if ret_val else "FAIL"))

        return ret_val

    def over_voltage_test(self):
        """
        Tests the board under test over-voltage protection circuit.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :return: True if the test passed, else False :type Boolean
        """
        poe_mv_on_mv_lo = 49400
        poe_mv_on_mv_hi = 57200
        rcu_12v_on_mv_lo = 11400
        rcu_12v_on_mv_hi = 12600
        poe_rcu_12v_off_mv_lo = 0
        poe_rcu_12v_off_mv_hi = 1000
        bench_psu_on_ma_lo = 100
        bench_psu_on_ma_hi = 3000
        bench_psu_off_ma_lo = 0
        bench_psu_off_ma_hi = 50
        ovp_reset_time_lo = 20.0
        ovp_reset_time_hi = 40.0

        log.info("")
        log.info("Over Voltage Protection Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            self._set_psu_on(voltage_mv=28000)
            time.sleep(1.0)
            ctji.toggle_rcu_power_button()
            time.sleep(5.0)

            adc_read, adc_data = ctji.get_adc_data()

            # PoE Voltage
            test_mv = adc_data.get("(mv) PoE Supply Out", -1)
            test_pass = (poe_mv_on_mv_lo <= test_mv <= poe_mv_on_mv_hi)
            log.info("{} - PoE Voltage: {} <= {} <= {} mV"
                     "".format("PASS" if test_pass else "FAIL", poe_mv_on_mv_lo, test_mv, poe_mv_on_mv_hi))
            ret_val = ret_val and test_pass

            # RCU +12V Voltage
            test_mv = adc_data.get("(mv) RCU +12V Out", -1)
            test_pass = (rcu_12v_on_mv_lo <= test_mv <= rcu_12v_on_mv_hi)
            log.info("{} - RCU +12V Voltage: {} <= {} <= {} mV"
                     "".format("PASS" if test_pass else "FAIL", rcu_12v_on_mv_lo, test_mv, rcu_12v_on_mv_hi))
            ret_val = ret_val and test_pass

            # Check the PSU current
            psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
            test_pass = (bench_psu_on_ma_lo <= psu_i_ma <= bench_psu_on_ma_hi)
            log.info("{} - Bench PSU Current: {} <= {} <= {} mA"
                     "".format("PASS" if test_pass else "FAIL", bench_psu_on_ma_lo, psu_i_ma, bench_psu_on_ma_hi))
            ret_val = ret_val and test_pass

            # Step Bench PSU to 50 V to simulate voltage surge
            start_time = time.perf_counter()
            start_time = time.perf_counter()
            self.tpsu.setVoltage(1, 50000)  # mV
            self.tpsu.setVoltage(1, 28000)  # mV

            adc_read, adc_data = ctji.get_adc_data()

            # PoE Voltage
            test_mv = adc_data.get("(mv) PoE Supply Out", -1)
            test_pass = (poe_rcu_12v_off_mv_lo <= test_mv <= poe_rcu_12v_off_mv_hi)
            log.info("{} - PoE Voltage: {} <= {} <= {} mV"
                     "".format("PASS" if test_pass else "FAIL", poe_rcu_12v_off_mv_lo, test_mv, poe_rcu_12v_off_mv_hi))
            ret_val = ret_val and test_pass

            # RCU +12V Voltage
            test_mv = adc_data.get("(mv) RCU +12V Out", -1)
            test_pass = (poe_rcu_12v_off_mv_lo <= test_mv <= poe_rcu_12v_off_mv_hi)
            log.info("{} - RCU +12V Voltage: {} <= {} <= {} mV"
                     "".format("PASS" if test_pass else "FAIL", poe_rcu_12v_off_mv_lo, test_mv, poe_rcu_12v_off_mv_hi))
            ret_val = ret_val and test_pass

            # Check the PSU current
            psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
            test_pass = (bench_psu_off_ma_lo <= psu_i_ma <= bench_psu_off_ma_hi)
            log.info("{} - Bench PSU Current: {} <= {} <= {} mA"
                     "".format("PASS" if test_pass else "FAIL", 0, psu_i_ma, bench_psu_off_ma_hi))
            ret_val = ret_val and test_pass

            while True:
                end_time = time.perf_counter()
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)

                if psu_i_ma > bench_psu_off_ma_hi or \
                        end_time > (start_time + ovp_reset_time_hi + (ovp_reset_time_hi * 0.1)):
                    break

            # Check the reset time
            test_pass = (ovp_reset_time_lo <= end_time - start_time <= ovp_reset_time_hi)
            log.info("{} - Over-Voltage Reset Time: {} <= {:.2f} <= {} seconds"
                     "".format("PASS" if test_pass else "FAIL",
                               ovp_reset_time_lo, end_time - start_time, ovp_reset_time_hi))
            ret_val = ret_val and test_pass

        log.info("{} - Over Voltage Protection Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def power_cable_detect_test(self):
        """
        Test the board/unit under test power cable detect function.
        Test steps:
            - Make power cable detect loop back on test jig
            - Arm sensor and check GPI and register status
            - Break power cable detect loop back on test jig
            - Check GPI and register status for tamper detected
            - Make power cable detect loop back on test jig
            - Arm sensor and check register status
            - Break power cable detect loop back and power down the board under test using test jig
            - Check the SoM PGOOD_3V3_SUP signal is low
            - Power on the board under test using test jig
            - Check the SoM PGOOD_3V3_SUP signal is high
            - Disable sensor and check register status
        Prerequisites:
            - CSM Zeroise Microcontroller is programmed with test utility
        Uses:
            - Test jig STM32 serial interface
            - CSM RCU serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Power Cable Detect Test:")
        ret_val = True

        with CsmZeroiseMircoTestInterface(self._rcu_com_port) as czm:
            self.power_up_board()

            with CsmTestJigInterface(self._tj_com_port) as ctji:
                # Arm the tamper sensor
                ret_val = ctji.assert_gpo_signal(CsmTestJigGpoSignals.POWER_CABLE_DETECT, True) and ret_val
                time.sleep(0.5)
                ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                             CsmTamperChannels.CHANNEL_0, True) and ret_val

                # Check the IRQ_CABLE_UNPLUG signal is NOT asserted
                cmd_success, asserted = czm.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG_N)
                ret_val = cmd_success and not asserted and ret_val

                # Check that the tamper channel status is ARMED_READY
                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                    CsmTamperChannels.CHANNEL_0)
                ret_val = cmd_success and status == CsmTamperChannelStatus.ARMED_READY and ret_val

                # Trigger the tamper sensor
                ret_val = ctji.assert_gpo_signal(CsmTestJigGpoSignals.POWER_CABLE_DETECT, False) and ret_val
                time.sleep(0.5)

                # Check that the IRQ_CABLE_UNPLUG signal has been asserted
                cmd_success, asserted = czm.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG_N)
                ret_val = cmd_success and asserted and ret_val

                # Check that the tamper channel status is TAMPERED
                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                    CsmTamperChannels.CHANNEL_0)
                ret_val = cmd_success and status == CsmTamperChannelStatus.TAMPERED and ret_val

                # Arm the tamper sensor
                ret_val = ctji.assert_gpo_signal(CsmTestJigGpoSignals.POWER_CABLE_DETECT, True) and ret_val
                time.sleep(0.5)
                ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                             CsmTamperChannels.CHANNEL_0, True) and ret_val

                # Check that the tamper channel status is ARMED_READY
                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                    CsmTamperChannels.CHANNEL_0)
                ret_val = cmd_success and status == CsmTamperChannelStatus.ARMED_READY and ret_val

                # Trigger the tamper sensor
                ret_val = ctji.assert_gpo_signal(CsmTestJigGpoSignals.POWER_CABLE_DETECT, False) and ret_val
                time.sleep(0.5)

                # Check that the IRQ_CABLE_UNPLUG signal has been asserted
                cmd_success, asserted = czm.get_gpi_signal_asserted(CsmGpiSignals.IRQ_CABLE_UNPLUG_N)
                ret_val = cmd_success and asserted and ret_val

                # # Power-down the unit
                # ret_val = ctji.toggle_rcu_power_button(hard_power_off=True) and ret_val
                #
                # # Check that the PGOOD_3V3_SUP signal is NOT asserted
                # cmd_success, asserted = czm.get_pgood_3v3_sup_asserted()
                # ret_val = cmd_success and not asserted and ret_val
                #
                # # Power on the board under test
                # ret_val = ctji.toggle_rcu_power_button() and ret_val
                # time.sleep(3.0)
                #
                # # Check that the PGOOD_3V3_SUP signal is asserted
                # cmd_success, asserted = czm.get_pgood_3v3_sup_asserted()
                # ret_val = cmd_success and asserted and ret_val

                # Disable the tamper channel and check its status is reported correctly
                ret_val = czm.set_anti_tamper_channel_enable(CsmTamperDevices.POWER_CABLE_DETECT,
                                                             CsmTamperChannels.CHANNEL_0, False) and ret_val

                cmd_success, status = czm.get_tamper_channel_status(CsmTamperDevices.POWER_CABLE_DETECT,
                                                                    CsmTamperChannels.CHANNEL_0)
                ret_val = cmd_success and status == CsmTamperChannelStatus.DISABLED and ret_val

            self._set_psu_off()

        log.info("{} - Power Cable Detect Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def poe_pse_test(self):
        """
        Prerequisites:
        - Board is powered on
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - Tenma Bench PSU serial interface
        - RCU serial port
        :return: True if test successful, else False
        """
        # channel_load_ma = {1: 175, 2: 175, 5: 216, 6: 216}
        expected_voltage_mv = 52000.0
        expected_channel_load_ma = {1: 175.0, 5: 216.0}
        expected_channel_status = CsmPoePseChannelStatus(port_mode=3, power_enable=True, power_good=True,
                                                         power_on_fault=False, port_2p4p_mode=True,
                                                         power_allocation=3, class_status=4, detection_status=4)

        log.info("")
        log.info("PoE PSE Test:")
        ret_val = True

        self.power_up_board()
        time.sleep(5.0)

        with CsmZeroiseMircoTestInterface(self._rcu_com_port) as czm:
            # De-assert PoE PSE I2C buffer enable
            ret_val = czm.set_gpo_signal(CsmGpoSignals.ZER_I2C_POE_EN, False) and ret_val
            time.sleep(0.1)

            # Check that reading channel status fails
            test_pass, ch_status = czm.get_poe_pse_channel_status(1)
            log.info("{} - PoE PSE I2C buffer test".format("PASS" if not test_pass else "FAIL"))
            ret_val = not test_pass and ret_val

            # Assert PoE PSE I2C buffer enable
            ret_val = czm.set_gpo_signal(CsmGpoSignals.ZER_I2C_POE_EN, True) and ret_val
            time.sleep(0.1)

            # Assert PoE PSE reset signal
            ret_val = czm.set_gpo_signal(CsmGpoSignals.POE_PSE_RST_N, False) and ret_val
            time.sleep(0.1)

            # Check that reading channel status fails
            test_pass, ch_status = czm.get_poe_pse_channel_status(1)
            log.info("{} - PoE PSE reset test".format("PASS" if not test_pass else "FAIL"))
            ret_val = not test_pass and ret_val

            # De-assert PoE PSE reset signal
            ret_val = czm.set_gpo_signal(CsmGpoSignals.POE_PSE_RST_N, True) and ret_val
            time.sleep(5.0)

            # The reset should have caused the interrupt signal to be set low by the PoE PSE
            test_pass, int_asserted = czm.get_gpi_signal_asserted(CsmGpiSignals.POE_PSE_INT_N)
            log.info("{} - PoE PSE reset signal asserted".format("PASS" if test_pass and int_asserted else "FAIL"))
            ret_val = test_pass and int_asserted and ret_val

            # Read all 8x channel statuses to clear the interrupt
            for ch_no in range(1, 9):
                test_pass, ch_status = czm.get_poe_pse_channel_status(ch_no)
                ret_val = test_pass and ret_val

                # For channels that will have a load connected check status values
                if ch_no in expected_channel_load_ma.keys():
                    log.info("")
                    log.info("INFO - Channel {} Status:".format(ch_no))

                    for param in ch_status.__dict__.keys():
                        if param == "voltage_mv":
                            lim_lo = expected_voltage_mv * 0.9
                            lim_hi = expected_voltage_mv * 1.1
                            test_pass = lim_lo <= getattr(ch_status, param) <= lim_hi
                            log.info("{} - {}: {:.1f} <= {:.1f} <= {:.1f}".format("PASS" if test_pass else "FAIL",
                                                                                  param, lim_lo,
                                                                                  getattr(ch_status, param), lim_hi))
                        elif param == "voltage_mv" or param == "current_ma":
                            lim_lo = expected_channel_load_ma[ch_no] * 0.9
                            lim_hi = expected_channel_load_ma[ch_no] * 1.1
                            test_pass = lim_lo <= getattr(ch_status, param) <= lim_hi
                            log.info("{} - {}: {:.1f} <= {:.1f} <= {:.1f}".format("PASS" if test_pass else "FAIL",
                                                                                  param, lim_lo,
                                                                                  getattr(ch_status, param), lim_hi))
                        else:
                            test_pass = getattr(expected_channel_status, param) == getattr(ch_status, param)
                            log.info("{} - {}: {}".format("PASS" if test_pass else "FAIL",
                                                          param, getattr(ch_status, param)))
                        ret_val = test_pass and ret_val

            time.sleep(0.1)
            test_pass, int_asserted = czm.get_gpi_signal_asserted(CsmGpiSignals.POE_PSE_INT_N)
            log.info("")
            log.info("{} - PoE PSE reset signal de-asserted"
                     "".format("PASS" if test_pass and not int_asserted else "FAIL"))
            ret_val = test_pass and not int_asserted and ret_val

        self._set_psu_off()

        log.info("")
        log.info("{} - PoE PSE Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def unit_set_config_info(self, assy_type, assy_rev_no, assy_serial_no, assy_batch_no, test_script_archive):
        """
        Sets the unit under test's configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - CSM Master Serial Terminal
        - CSM SSH Connection
        :param test_script_archive: test script archive path :type String
        :param assy_type: board/unit assembly type :type String
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Unit Configuration Information:")
        ret_val = True

        self.power_supply_off()
        self.power_up_board(linux_run_check=True)

        time.sleep(10.0)
        found_csms = self.find_csms()
        if len(found_csms) == 1:
            hostname = found_csms[0][0]
        else:
            raise RuntimeError("Unable to find a single CSM unit - {}".format(found_csms))

        with CsmPlatformTest(self._csm_username, hostname) as cpt:
            ret_val = cpt.copy_test_scripts_to_som(test_script_archive) and ret_val

            # Set configuration information
            ret_val = cpt.set_config_info(assy_type, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val

            if ret_val:
                # Read back configuration information and check it is correct
                config_dict = cpt.get_config_info(assy_type)

                test_pass = (config_dict.get("Assembly Part Number", "") == assy_type)
                log.info("{} - Assembly No set to {}".format("PASS" if test_pass else "FAIL", assy_type))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Revision Number", "") == assy_rev_no)
                log.info("{} - Assembly Revision No set to {}".format("PASS" if test_pass else "FAIL", assy_rev_no))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Serial Number", "") == assy_serial_no)
                log.info("{} - Assembly Serial No set to {}".format("PASS" if test_pass else "FAIL", assy_serial_no))
                ret_val = ret_val and test_pass

                test_pass = (config_dict.get("Assembly Build Date/Batch Number", "") == assy_batch_no)
                log.info("{} - Assembly Batch No set to {}".format("PASS" if test_pass else "FAIL", assy_batch_no))
                ret_val = ret_val and test_pass

                if assy_type == self._CSM_MOTHERBOARD_NO:
                    log.info("INFO - Hardware Version No is {}".format(config_dict.get("Hardware Version", "")))
                    log.info("INFO - Hardware Modification No is {}"
                             "".format(config_dict.get("Hardware Mod Version", "")))

            ret_val = cpt.remove_test_scripts() and ret_val

        time.sleep(10.0)
        self.power_supply_off()

        log.info("{} - Set unit configuration information".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def unit_uart_test(self):
        """
        Tests the unit under test UARTs.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        - RCU serial port
        :return: True if test passes, else False :type Boolean
        """
        test_sequence = [
            # serial_port, baud_rate
            (self._csm_slave_serial_port, 115200),      # CSM Slave
            (self._programming_serial_port, 115200)     # Programming
        ]

        log.info("")
        log.info("Unit UART Test:")
        ret_val = True
        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            # Test the CSM Slave and Programming UARTs
            for serial_port, baud_rate in test_sequence:
                test_pass = cpt.uart_test(serial_port, baud_rate)
                log.info("{} - UART Test {}".format("PASS" if test_pass else "FAIL", serial_port))
                ret_val = test_pass and ret_val

        with Serial(self._master_com_port, 115200, timeout=3.0, xonxoff=False, rtscts=False, dsrdtr=False) as cmsp:
            # Test the RCU serial port
            cmsp.write(b"\x18")
            time.sleep(1.0)
            cmsp.write("{}\r".format(self._csm_username).encode("UTF-8"))
            time.sleep(1.0)
            cmsp.write("{}\r".format(self._CSM_PASSWORD).encode("UTF-8"))
            cmsp.read_until("{}@CSM-".format(self._csm_username).encode("UTF-8"))
            cmsp.write("python3 /run/media/mmcblk1p2/test/serial_echo.py -s {}\r"
                       "".format(self._rcu_serial_port).encode("UTF-8"))
            time.sleep(1.0)

            ut = UartTest()
            test_pass = ut.test_serial_port(self._rcu_com_port, 115200)
            log.info("{} - UART Test {}".format("PASS" if test_pass else "FAIL", self._rcu_serial_port))
            ret_val = test_pass and ret_val

            cmsp.write(b"\x03")
            time.sleep(1.0)
            cmsp.write(b"\x18")
            time.sleep(1.0)

        return ret_val

    def unit_buzzer_test(self, yesno_check_dialog_func):
        """
        Test the unit under test buzzer.
        Prerequisites:
        - Unit is powered up
        - Linux is booted
        - CSM Zeroise Microcontroller is programmed with operational firmware
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit Buzzer Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            # De-assert -> Assert -> De-assert the buzzer then check it sounded
            for set_val in [False, True, False]:
                ret_val = cpt.set_buzzer_state(self._zeroise_micro_serial_port, set_val) and ret_val
                time.sleep(1.0)

            ret_val = yesno_check_dialog_func("Did the Unit Buzzer Sound?")

        log.info("{} - Unit Buzzer Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def unit_keypad_test(self, instruction_dialog_func, yesno_check_dialog_func):
        """
        Test the unit under test Keypad interface.
        Prerequisites:
        - Unit is powered up
        - Linux is booted
        - CSM Zeroise Microcontroller is programmed with operational firmware
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit Keypad Test:")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            instruction_dialog_func("The CSM Unit Keypad will now tested...")

            # Keypad LEDs
            test_pass = cpt.set_all_keypad_green_leds(self._zeroise_micro_serial_port, "ON")
            test_pass = yesno_check_dialog_func("Did all 10x Keypad GREEN LEDs turn on?") and test_pass
            log.info("{} - LED test".format("PASS" if test_pass else "FAIL"))
            ret_val = test_pass and ret_val

            # Buttons
            for button in ["JAM", "X", "EXCLAMATION"]:
                instruction_dialog_func("Wait for five seconds then press the Keypad '{}' Button followed by any other "
                                        "button except the Power button.".format(button))
                test_pass = cpt.check_for_keypad_button_press(self._zeroise_micro_serial_port, button)
                log.info("{} - {} button test".format("PASS" if test_pass else "FAIL", button))
                ret_val = test_pass and ret_val

        log.info("{} - Unit Keypad Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def unit_pb_controller_irq_test(self, instruction_dialog_func):
        """
        Tests the push-button controller interrupt output, need to do this in <10-seconds to avoid hard power-off
        Prerequisites:
        - Unit is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :return: True if test passes, else False :type: Boolean
        """
        log.info("")
        log.info("Power Button Test")
        ret_val = True

        with CsmPlatformTest(self._csm_username,
                             self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
            ret_val = not cpt.get_pb_ctrl_irq() and ret_val
            instruction_dialog_func("Press and hold the Power Button for approximately 3-seconds")
            end_time = time.perf_counter() + 10.0
            while True:
                pb_asserted = cpt.get_pb_ctrl_irq()
                if pb_asserted:
                    ret_val = True and ret_val
                    break
                if time.perf_counter() > end_time:
                    ret_val = False and ret_val
                    break

            time.sleep(4.0)
            ret_val = not cpt.get_pb_ctrl_irq() and ret_val

        log.info("{} - Power Button Test".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def rf_mute_test(self):
        """
        Tests the external RF Mute signals of the board/unit under test.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - Test jig STM32 serial interface
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("RF Mute Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                # De-assert -> Assert -> De-assert the signal then check the ADC data
                master_pass = True
                slave_pass = True
                for assert_val in [False, True, False]:
                    ret_val = cpt.assert_rf_mute(assert_val) and ret_val
                    time.sleep(1.0)
                    adc_read, adc_data = ctji.get_adc_data()
                    ret_val = ret_val and adc_read
                    master_pass = (450 <= adc_data.get("(mv) RF Mute CSM Master", -1) <= 600 if assert_val else
                                   2450 <= adc_data.get("(mv) RF Mute CSM Master", -1) <= 2550) and master_pass
                    slave_pass = (450 <= adc_data.get("(mv) RF Mute CSM Slave", -1) <= 600 if assert_val else
                                  2450 <= adc_data.get("(mv) RF Mute CSM Slave", -1) < 2550) and slave_pass

                    log.debug("{}\t{}".format(adc_data.get("(mv) RF Mute CSM Master", -1),
                                              adc_data.get("(mv) RF Mute CSM Slave", -1)))

                log.info("{} - RF Mute CSM Master".format("PASS" if master_pass and ret_val else "FAIL"))
                log.info("{} - RF Mute CSM Slave".format("PASS" if slave_pass and ret_val else "FAIL"))
                ret_val = ret_val and master_pass and slave_pass

        return ret_val

    def power_off_override_test(self):
        """
        Tests the Power Off Override signal of the board under test.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - Test jig STM32 serial interface
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Power Off Override Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                # De-assert -> Assert -> De-assert the signal then check the ADC data
                master_pass = True
                slave_pass = True
                for assert_val in [False, True, False]:
                    ret_val = cpt.assert_power_off_override(assert_val) and ret_val
                    time.sleep(1.0)
                    adc_read, adc_data = ctji.get_adc_data()
                    ret_val = ret_val and adc_read
                    master_pass = (450 <= adc_data.get("(mv) Power Off CS Master", -1) <= 600 if assert_val else
                                   2450 <= adc_data.get("(mv) Power Off CS Master", -1) <= 2550) and master_pass
                    slave_pass = (450 <= adc_data.get("(mv) Power Off CS Slave", -1) <= 600 if assert_val else
                                  2450 <= adc_data.get("(mv) Power Off CS Slave", -1) < 2550) and slave_pass

                    log.debug("{}\t{}".format(adc_data.get("(mv) Power Off CS Master", -1),
                                              adc_data.get("(mv) Power Off CS Slave", -1)))

                log.info("{} - Power Off CS Master".format("PASS" if master_pass and ret_val else "FAIL"))
                log.info("{} - Power Off CS Slave".format("PASS" if slave_pass and ret_val else "FAIL"))
                ret_val = ret_val and master_pass and slave_pass

        return ret_val

    def expansion_slot_test(self, instruction_dialog_func, slot_no, gbe_conn_test_duration_s, rpi4_ip6_addr):
        """
        Run Expansion Slot test, tests the Cu and SFP GbE connections, serial port and reference clock.
        Prerequisites:
        - SoM is programmed
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        - CSM SSH connection
        - RPi4 SSH connection
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param slot_no: Expansion Slot number to test, range 1..2 :type Integer
        :param gbe_conn_test_duration_s:
        :param rpi4_ip6_addr: Raspberry Pi4 IPv6 address, default use constants from rpi4_iperf3.py :type String
        :return: True if test passes, else False
        """
        test_data = {
            "1": {"uart": self._exp_slot_1_serial_port, "cu_gbe_port": 1, "sfp_gbe_port": 9, "ref_clk": ""},
            "2": {"uart": self._exp_slot_2_serial_port, "cu_gbe_port": 2, "sfp_gbe_port": 10, "ref_clk": ""},
        }
        log.info("")
        log.info("Expansion Slot {} Test:".format(slot_no))
        ret_val = True
        if slot_no in [1, 2]:
            self.power_supply_off()
            instruction_dialog_func("Fit KT-000-0205-00 PCB in Expansion Slot {}".format(slot_no))
            self.power_up_board(linux_run_check=True)
            time.sleep(5.0)

            # Test the Cu GbE Switch interface
            ret_val = self.gbe_sw_connection_test(uport=test_data[str(slot_no)]["cu_gbe_port"],
                                                  test_uport=6,
                                                  test_sw_port=20,
                                                  duration_s=gbe_conn_test_duration_s,
                                                  rpi4_ip6_address=rpi4_ip6_addr) and ret_val

            # Test the Fibre GbE Switch interface
            ret_val = self.gbe_sw_connection_test(uport=test_data[str(slot_no)]["sfp_gbe_port"],
                                                  test_uport=6,
                                                  test_sw_port=25,
                                                  duration_s=gbe_conn_test_duration_s,
                                                  rpi4_ip6_address=rpi4_ip6_addr) and ret_val

            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                # Test the UART
                if test_data[str(slot_no)]["uart"] != "":
                    test_pass = cpt.uart_test(test_data[str(slot_no)]["uart"], 115200)
                    log.info("{} - UART Test {}"
                             "".format("PASS" if test_pass else "FAIL", test_data[str(slot_no)]["uart"]))
                    ret_val = test_pass and ret_val

                # Test the Reference Clock
                if test_data[str(slot_no)]["ref_clk"] != "":
                    pass

            self.power_supply_off()
            instruction_dialog_func("Remove KT-000-0205-00 PCB from Expansion Slot {}".format(slot_no))
        else:
            ret_val = False

        log.info("{} - Expansion Slot {} Test".format("PASS" if ret_val else "FAIL", slot_no))
        return ret_val


class MpCsmProdTest(CommonCsmProdTest):
    """
    Concrete class that implements test cases and functionality for Vehicle CSM testing.
    """
    _CSM_MOTHERBOARD_NO = "KT-000-0180-00"

    def __init__(self, tj_com_port, psu_com_port, tpl_sw_com_port, master_com_port, rcu_com_port,
                 csm_hostname, csm_username, zeroise_micro_serial_port, csm_slave_serial_port,
                 rcu_serial_port, programming_serial_port, gnss1_serial_port, gbe_switch_serial_port,
                 exp_slot_1_serial_port, exp_slot_2_serial_port,
                 unit_type, segger_jlink_win32=None, segger_jlink_win64=None, flash_pro=None, iperf3=None,
                 cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param tj_com_port: test jig NUCLEO STM32 COM port :type String
        :param psu_com_port: Tenma bench PSU COM port :type String
        :param tpl_sw_com_port: TP-Link managed switch COM port :type String
        :param master_com_port: board/unit under test CSM Master COM port :type String
        :param rcu_com_port: board/unit under test RCU COM port :type String
        :param csm_hostname: board/unit under test network hostname :type String
        :param zeroise_micro_serial_port: CSM serial port :type String
        :param csm_slave_serial_port: CSM serial port :type String
        :param rcu_serial_port: CSM serial port :type String
        :param programming_serial_port: CSM serial port :type String
        :param gnss1_serial_port: CSM serial port :type String
        :param gbe_switch_serial_port: CSM serial port :type String
        :param exp_slot_1_serial_port: Expansion Slot 1 serial port :type String
        :param exp_slot_2_serial_port: Expansion Slot 2 serial port :type String
        :param unit_type: one of UnitTypes enumerated values :type UnitTypes
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use csm_program_devices constant
        :param flash_pro: Microchip FlashPro exe path, default is None, use csm_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        super().__init__(tj_com_port, psu_com_port, tpl_sw_com_port, master_com_port, rcu_com_port,
                         csm_hostname, csm_username, zeroise_micro_serial_port, csm_slave_serial_port,
                         rcu_serial_port, programming_serial_port, gnss1_serial_port, gbe_switch_serial_port,
                         exp_slot_1_serial_port, exp_slot_2_serial_port, segger_jlink_win32, segger_jlink_win64,
                         flash_pro, iperf3, cygwin1_dll)

        self.unit_type = unit_type

    def over_under_voltage_lockout_test(self, instruction_dialog_func):
        """
        Tests board/unit under test over/under-voltage lockout protection circuit.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if the test passed, else False :type Boolean
        """
        under_voltage_lockout_mv = 6000
        over_voltage_lockout_mv = 41000
        operational_voltage_mv = [32000, 18000, 24000]
        off_i_ma_lo = 0
        off_i_ma_hi = 0
        on_i_ma_lo = 1
        on_i_ma_hi = 45

        log.info("")
        log.info("Over/Under Voltage Lockout Test:")
        ret_val = True

        if self.tpsu is not None:
            # Under-voltage lockout
            self.tpsu.OFF()

            for psu_input in ["INTF2 +VIN (J9)", "INTF1 +VIN (J6)"]:
                instruction_dialog_func("Connect the Bench PSU positive feed to Test Jig 4mm plug: {}\n\n"
                                        "Click OK to proceed...".format(psu_input))

                self.tpsu.setVoltage(1, under_voltage_lockout_mv)
                self.tpsu.setCurrent(1, 5000)   # mA
                self.tpsu.ON()
                time.sleep(5.0)

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (off_i_ma_lo <= psu_i_ma <= off_i_ma_hi)
                log.info("{} - {} Under-Voltage Bench PSU Current: {} <= {} <= {} mA"
                         "".format(self._pass_fail_string(test_pass), psu_input, off_i_ma_hi, psu_i_ma, off_i_ma_hi))
                ret_val = ret_val and test_pass

                # Over-voltage lockout
                self.tpsu.OFF()
                self.tpsu.setVoltage(1, over_voltage_lockout_mv)  # mV
                self.tpsu.setCurrent(1, 5000)  # mA
                self.tpsu.ON()
                time.sleep(5.0)

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (off_i_ma_lo <= psu_i_ma <= off_i_ma_hi)
                log.info("{} - {} Over-Voltage Bench PSU Current: {} <= {} <= {} mA"
                         "".format(self._pass_fail_string(test_pass), psu_input, off_i_ma_hi, psu_i_ma, off_i_ma_hi))
                ret_val = ret_val and test_pass

                # Operational voltage range
                self.tpsu.OFF()
                for op_volt_mv in operational_voltage_mv:
                    self.tpsu.setVoltage(1, op_volt_mv)
                    self.tpsu.ON()
                    time.sleep(5.0)
                    psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                    test_pass = (on_i_ma_lo <= psu_i_ma <= on_i_ma_hi)
                    log.info("{} - {} {} V Bench PSU Current: {} <= {} <= {} mA"
                             "".format(self._pass_fail_string(test_pass), psu_input, op_volt_mv / 1000.0,
                                       on_i_ma_lo, psu_i_ma, on_i_ma_hi))
                    ret_val = ret_val and test_pass

                self.tpsu.OFF()
        else:
            raise RuntimeError("PSU Test Equipment Error!")

        log.info("{} - Over/Under Voltage Lockout Test".format(self._pass_fail_string(ret_val)))

        return ret_val

    def external_power_off_test(self):
        """
        Tests the board under test external power on/off signals.
        Prerequisites:
        - CSM Zeroise Micro is programmed with test utility
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        - RCU serial port
        :return: True if the test passed, else False :type Boolean
        """
        test_sequence1 = [
            # rcu_pwr_btn_hard_pwr_off, rcu_12v_mv_lo, rcu_12v_mv_hi, psu_ma_lo, psu_ma_hi,
            # ntm_x_dc_out_mv_lo, ntm_x_dc_out_mv_hi, ipam_x_dc_out_mv_lo, ipam_x_dc_out_mv_hi,
            # ntm_x_p3v4_stdby_mv_lo, ntm_x_p3v4_stdby_mv_hi
            (True, 0, 1200, 0, 35, 0, 1000, 23000, 25000, 3200, 3600),
            (False, 11400, 12600, 100, 3000, 23000, 25000, 23000, 25000, 3200, 3600),
            (True, 0, 1200, 0, 35, 0, 1000, 23000, 25000, 3200, 3600),
        ]

        log.info("")
        log.info("External Power On/Off Test:")
        ret_val = True

        with MpTestJigInterface(self._tj_com_port)as ctji:
            self._set_psu_on()
            time.sleep(1.0)
            # Cheat to make sure the first iteration of the test sequence works
            ctji.toggle_rcu_power_button()
            time.sleep(2.0)

            # Test the RCU Power Button Input
            for rcu_pwr_btn_hard_pwr_off, rcu_12v_mv_lo, rcu_12v_mv_hi, psu_ma_lo, psu_ma_hi,\
                    ntm_x_dc_out_mv_lo, ntm_x_dc_out_mv_hi, ipam_x_dc_out_mv_lo, ipam_x_dc_out_mv_hi,\
                    ntm_x_p3v4_stdby_mv_lo, ntm_x_p3v4_stdby_mv_hi in test_sequence1:
                ctji.toggle_rcu_power_button(rcu_pwr_btn_hard_pwr_off)
                time.sleep(5.0)
                adc_read, adc_data = ctji.get_adc_data()

                # RCU +12V Voltage
                test_mv = adc_data.get("(mv) RCU +12V Out", -1)
                test_pass = (rcu_12v_mv_lo <= test_mv <= rcu_12v_mv_hi)
                log.info("{} - RCU Power Button - RCU +12V Voltage: {} <= {} <= {} mV"
                         "".format(self._pass_fail_string(test_pass), rcu_12v_mv_lo, test_mv, rcu_12v_mv_hi))
                ret_val = ret_val and test_pass

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (psu_ma_lo <= psu_i_ma <= psu_ma_hi)
                log.info("{} - RCU Power Button - Bench PSU Current: {} <= {} <= {} mA"
                         "".format(self._pass_fail_string(test_pass), psu_ma_lo, psu_i_ma, psu_ma_hi))
                ret_val = ret_val and test_pass

                # NTM x DC Out Voltage
                for ntm in range(1, 4):
                    test_mv = adc_data.get("(mv) NTM {} DC Out".format(ntm), -1)
                    test_pass = (ntm_x_dc_out_mv_lo <= test_mv <= ntm_x_dc_out_mv_hi)
                    log.info("{} - RCU Power Button - NTM {} DC Out Voltage: {} <= {} <= {} mV"
                             "".format(self._pass_fail_string(test_pass), ntm, ntm_x_dc_out_mv_lo,
                                       test_mv, ntm_x_dc_out_mv_hi))
                    ret_val = ret_val and test_pass

                # NTM x +3V4 Standby Voltage
                for ntm in range(1, 4):
                    test_mv = adc_data.get("(mv) NTM {} +3V4 STBY".format(ntm), -1)
                    test_pass = (ntm_x_p3v4_stdby_mv_lo <= test_mv <= ntm_x_p3v4_stdby_mv_hi)
                    log.info("{} - RCU Power Button - NTM {} +3V4 STBYVoltage: {} <= {} <= {} mV"
                             "".format(self._pass_fail_string(test_pass), ntm, ntm_x_p3v4_stdby_mv_lo,
                                       test_mv, ntm_x_p3v4_stdby_mv_hi))
                    ret_val = ret_val and test_pass

                # IPAM x DC Out Voltage
                for ipam in range(1, 4):
                    test_mv = adc_data.get("(mv) IPAM {} DC Out".format(ipam), -1)
                    test_pass = (ipam_x_dc_out_mv_lo <= test_mv <= ipam_x_dc_out_mv_hi)
                    log.info("{} - RCU Power Button - IPAM {} DC Out Voltage: {} <= {} <= {} mV"
                             "".format(self._pass_fail_string(test_pass), ipam, ipam_x_dc_out_mv_lo,
                                       test_mv, ipam_x_dc_out_mv_hi))
                    ret_val = ret_val and test_pass

            with MpZeroiseMircoTestInterface(self._rcu_com_port) as czm:
                # Test the Control Port Master/Slave Power Button Inhibit...

                # Set Master/Slave Select signal to Master
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_MASTER_SELECT_N, False)

                # Turn the board on using the RCU Power Button, using zeroise micro serial commands to confirm
                # that the board is powered up.
                time.sleep(1.0)
                ctji.toggle_rcu_power_button()
                time.sleep(3.0)

                # Set Master/Slave Select signal to Master, toggle the Keypad Power Button and
                # check that the board remains powered on
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_MASTER_SELECT_N,
                                                   True) and test_pass
                test_pass = czm.toggle_keypad_power_button(hard_power_off=True) and test_pass
                time.sleep(12.0)
                test_pass = (czm.get_battery_temperature() != -255) and test_pass

                # Set Master/Slave Select signal to Master, toggle the Keypad Power Button and
                # check that the board powers down
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_MASTER_SELECT_N,
                                                   False) and test_pass
                test_pass = czm.toggle_keypad_power_button(hard_power_off=True) and test_pass
                time.sleep(12.0)
                test_pass = (czm.get_battery_temperature() == -255) and test_pass

                log.info("{} - Control Master/Slave Select".format(self._pass_fail_string(test_pass)))
                ret_val = ret_val and test_pass

                # Test the Control Port Power Enable In/Out signals...

                # Set the Power Enable Input to the board under test low
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_POWER_ENABLE, False)

                # Check that the Power Enable Output from the board under test is low
                gpi_ret, gpi_data = ctji.get_gpi_state()
                ret_val = gpi_ret and ret_val
                if gpi_ret:
                    power_en_op_key = "Control Port Power Enable"
                    power_en_op_state = True if gpi_data.get(power_en_op_key, -1) == 1 else False
                    test_pass = (power_en_op_state is False) and test_pass

                # Set the Power Enable Input to the board under test high
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_POWER_ENABLE, False) and test_pass
                time.sleep(3.0)

                # Check that the Power Enable Output from the board under test is high
                gpi_ret, gpi_data = ctji.get_gpi_state()
                ret_val = gpi_ret and ret_val
                if gpi_ret:
                    power_en_op_key = "Control Port Power Enable"
                    power_en_op_state = True if gpi_data.get(power_en_op_key, -1) == 1 else False
                    test_pass = (power_en_op_state is False) and test_pass

                # Set the Power Enable Input to the board under test low
                test_pass = ctji.assert_gpo_signal(MpTestJigGpoSignals.CONTROL_PORT_POWER_ENABLE, False) and test_pass
                time.sleep(12.0)

                # Check that the Power Enable Output from the board under test is low
                gpi_ret, gpi_data = ctji.get_gpi_state()
                ret_val = gpi_ret and ret_val
                if gpi_ret:
                    power_en_op_key = "Control Port Power Enable"
                    power_en_op_state = True if gpi_data.get(power_en_op_key, -1) == 1 else False
                    test_pass = (power_en_op_state is False) and test_pass

                log.info("{} - Control Power Enable In/Out".format(self._pass_fail_string(test_pass)))
                ret_val = ret_val and test_pass

        self._set_psu_off()
        log.info("{} - External Power Off Test".format(self._pass_fail_string(ret_val)))

        return ret_val

    def over_voltage_test(self, instruction_dialog_func):
        """
        Tests the board under test over-voltage protection circuit.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if the test passed, else False :type Boolean
        """
        rcu_12v_on_mv_lo = 11400
        rcu_12v_on_mv_hi = 12600
        rcu_12v_off_mv_lo = 0
        rcu_12v_off_mv_hi = 2000
        bench_psu_on_ma_lo = 100
        bench_psu_on_ma_hi = 3000
        bench_psu_off_ma_lo = 0
        bench_psu_off_ma_hi = 1
        ovp_reset_time_lo = 20.0
        ovp_reset_time_hi = 40.0

        log.info("")
        log.info("Over Voltage Protection Test:")
        ret_val = True

        with self._get_test_jig_interface_instance() as ctji:
            for psu_input in ["INTF1 +VIN (J6)", "INTF2 +VIN (J9)"]:
                instruction_dialog_func("Connect the Bench PSU positive feed to Test Jig 4mm plug: {}\n\n"
                                        "Click OK to proceed...".format(psu_input))

                self._set_psu_on(voltage_mv=28000)
                time.sleep(2.0)
                ctji.toggle_rcu_power_button()
                time.sleep(5.0)

                adc_read, adc_data = ctji.get_adc_data()

                # RCU +12V Voltage
                test_mv = adc_data.get("(mv) RCU +12V Out", -1)
                test_pass = (rcu_12v_on_mv_lo <= test_mv <= rcu_12v_on_mv_hi)
                log.info("{} - {} RCU +12V Voltage: {} <= {} <= {} mV"
                         "".format(self._pass_fail_string(test_pass), psu_input,
                                   rcu_12v_on_mv_lo, test_mv, rcu_12v_on_mv_hi))
                ret_val = ret_val and test_pass

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (bench_psu_on_ma_lo <= psu_i_ma <= bench_psu_on_ma_hi)
                log.info("{} - {} Bench PSU Current: {} <= {} <= {} mA"
                         "".format(self._pass_fail_string(test_pass), psu_input,
                                   bench_psu_on_ma_lo, psu_i_ma, bench_psu_on_ma_hi))
                ret_val = ret_val and test_pass

                # Step Bench PSU to 50 V to simulate voltage surge
                start_time = time.perf_counter()
                start_time = time.perf_counter()
                self.tpsu.setVoltage(1, 50000)  # mV
                self.tpsu.setVoltage(1, 28000)  # mV

                adc_read, adc_data = ctji.get_adc_data()

                # RCU +12V Voltage
                test_mv = adc_data.get("(mv) RCU +12V Out", -1)
                test_pass = (rcu_12v_off_mv_lo <= test_mv <= rcu_12v_off_mv_hi)
                log.info("{} - {} RCU +12V Voltage: {} <= {} <= {} mV"
                         "".format(self._pass_fail_string(test_pass), psu_input,
                                   rcu_12v_off_mv_lo, test_mv, rcu_12v_off_mv_hi))
                ret_val = ret_val and test_pass

                # Check the PSU current
                psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)
                test_pass = (bench_psu_off_ma_lo <= psu_i_ma <= bench_psu_off_ma_hi)
                log.info("{} - {} Bench PSU Current: {} <= {} <= {} mA"
                         "".format(self._pass_fail_string(test_pass), psu_input, 0, psu_i_ma, bench_psu_off_ma_hi))
                ret_val = ret_val and test_pass

                while True:
                    end_time = time.perf_counter()
                    psu_i_ma = int(float(self.tpsu.runningCurrent(1)) * 1000.0)

                    if psu_i_ma > bench_psu_off_ma_hi or \
                            end_time > (start_time + ovp_reset_time_hi + (ovp_reset_time_hi * 0.1)):
                        break

                # Check the reset time
                test_pass = (ovp_reset_time_lo <= end_time - start_time <= ovp_reset_time_hi)
                log.info("{} - {} Over-Voltage Reset Time: {} <= {:.2f} <= {} seconds"
                         "".format(self._pass_fail_string(test_pass), psu_input,
                                   ovp_reset_time_lo, end_time - start_time, ovp_reset_time_hi))
                ret_val = ret_val and test_pass

        log.info("{} - Over Voltage Protection Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def pb_controller_supply_test(self):
        """
        Tests the power-button controller supply rail.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :return: True if the test passed, else False :type Boolean
        """
        test_sequence = [
            # bench_psu_mv, vsup_stby_mv_lo, vsup_stby_mv_hi
            (15600, 0, 100),
            (15900, 4000, 5500),
            (15600, 4000, 5500),
            (15300, 0, 100),
        ]
        log.info("")
        log.info("Power Button Controller Supply Test:")
        ret_val = True

        with MpTestJigInterface(self._tj_com_port) as ctji:
            # Start with the PSU off
            self._set_psu_off()
            time.sleep(3.0)

            for bench_psu_mv, vsup_stby_mv_lo, vsup_stby_mv_hi in test_sequence:
                self._set_psu_on(voltage_mv=bench_psu_mv)
                time.sleep(2.0)
                adc_read, adc_data = ctji.get_adc_data()
                test_mv = adc_data.get("(mv) VSUP STBY", -1)
                test_pass = (vsup_stby_mv_lo <= test_mv <= vsup_stby_mv_hi)
                log.info("{} - VSUP STBY: {} <= {} <= {} mV"
                         "".format(self._pass_fail_string(test_pass), vsup_stby_mv_lo, test_mv, vsup_stby_mv_hi))
                ret_val = ret_val and test_pass

        self._set_psu_off()
        log.info("{} - Power Button Controller Supply Test".format(self._pass_fail_string(ret_val)))

        return ret_val

    def rf_mute_test(self):
        """
        Tests the external RF Mute signals of the board/unit under test.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - Test jig STM32 serial interface
        - CSM SSH connection
        :return: True if test passes, else False :type Boolean
        """
        rf_mute_gpi_signals = ["Control Port RF Mute", "NTM 1 RF Mute", "NTM 2 RF Mute", "NTM 3 RF Mute"]
        log.info("")
        log.info("RF Mute Test:")
        ret_val = True

        with MpTestJigInterface(self._tj_com_port) as ctji:
            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                # Low -> High -> Low the signal then check the GPI

                # Set the Master signal as output and Low, the NTM and Control RF Mute signals should
                # follow the Slave signal.
                test_pass = cpt.set_rf_mute_direction(True)
                test_pass = cpt.assert_master_rf_mute(False) and test_pass
                for assert_val in [False, True, False]:
                    test_pass = cpt.assert_slave_rf_mute(assert_val) and test_pass
                    time.sleep(1.0)
                    gpi_get, gpi_data = ctji.get_gpi_state()
                    if gpi_get:
                        for gpi in rf_mute_gpi_signals:
                            mute_state = True if gpi_data.get(gpi, -1) == 1 else False
                            gpi_pass = (mute_state == assert_val)
                            log.info("{} - {}: {} - {}"
                                     "".format(self._pass_fail_string(gpi_pass), gpi, mute_state, assert_val))
                            test_pass = gpi_pass and test_pass
                    else:
                        log.info("INFO - Failed to get Test Jig GPI Signal State!")
                        test_pass = False

                log.info("{} - RF Mute Slave Signal".format("PASS" if test_pass else "FAIL"))
                ret_val = ret_val and test_pass

                # Set the Slave signal Low, the Control RF Mute signal should follow the Master signal
                test_pass = cpt.assert_slave_rf_mute(False)
                for assert_val in [False, True, False]:
                    test_pass = cpt.assert_master_rf_mute(assert_val) and test_pass
                    time.sleep(1.0)
                    gpi_get, gpi_data = ctji.get_gpi_state()
                    if gpi_get:
                        mute_state = True if gpi_data.get("Control Port RF Mute", -1) == 1 else False
                        gpi_pass = (mute_state == assert_val)
                        log.info("{} - Control Port RF Mute: {} - {}"
                                 "".format(self._pass_fail_string(gpi_pass), mute_state, assert_val))
                        test_pass = gpi_pass and test_pass
                    else:
                        log.info("INFO - Failed to get Test Jig GPI Signal State!")
                        test_pass = False

                log.info("{} - RF Mute Master Signal".format("PASS" if test_pass else "FAIL"))
                ret_val = ret_val and test_pass

        log.info("{} - RF Mute Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def ntm_pfi_test(self):
        """
        Tests the board under test NTM PFI outputs.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :return: True if the test passed, else False :type Boolean
        """
        test_sequence = [
            # (voltage_mv, pfi_assreted)
            (18000, False),
            (16000, True),
            (17000, False)
        ]
        log.info("")
        log.info("NTM PFI Test:")
        ret_val = True

        with MpTestJigInterface(self._tj_com_port) as ctji:
            self._set_psu_on(voltage_mv=28000)
            time.sleep(1.0)
            ctji.toggle_rcu_power_button()
            time.sleep(5.0)

            for voltage_mv, pfi_asserted in test_sequence:
                self.tpsu.setVoltage(1, voltage_mv)
                gpi_ret, gpi_data = ctji.get_gpi_state()
                ret_val = gpi_ret and ret_val
                if gpi_ret:
                    for signal in ["NTM 1 PFI (active-low)", "NTM 2 PFI (active-low)", "NTM 3 PFI (active-low)"]:
                        test_pass = gpi_data.get(signal, -1) == (0 if pfi_asserted else 1)
                        log.info("{} - {}: {} (PSU: {}) mV".format("PASS" if test_pass else "FAIL",
                                                                   signal,
                                                                   "Asserted" if pfi_asserted else "Not Asserted",
                                                                   voltage_mv))
                        ret_val = test_pass and ret_val

        self._set_psu_off()
        time.sleep(1.0)
        return ret_val

    def set_ntm_hw_config_info(self, assy_rev_no, assy_serial_no, assy_batch_no):
        """
          Sets the board under test's NTM hardware configuration information to the specified values then reads back
          the data to check that it has been correctly written to EEPROM.
          The assembly number is 'KT-000-0143-00' as the KT-000-0180-00 emulates the EMA PCM, revision, serial and
          build / batch numbers are set to the same values as the KT-000-0180-00 board.
          Prerequisites:
          - Test Jig STM32 board connected to Test PC
          Uses:
          - Test jig serial interface
          :param assy_rev_no: board/unit assembly revision number :type String
          :param assy_serial_no: board/unit assembly serial number :type String
          :param assy_batch_no: board/unit build/batch number :type String
          :return: True if hardware configuration information set correctly, else False :type Boolean
          """
        log.info("")
        log.info("Set Hardware Configuration Information:")
        ret_val = True

        # Don't need the Bench PSU turned for this test
        self._set_psu_off()
        time.sleep(1.0)

        with MpTestJigInterface(self._tj_com_port) as ctji:
            for ntm, bus in enumerate([MpTestJigNtmI2cBus.NTM1, MpTestJigNtmI2cBus.NTM2, MpTestJigNtmI2cBus.NTM3]):
                ntm_pass = True

                # Set the NTM I2C bus
                ntm_pass = ctji.set_ntm_i2c_bus(bus) and ntm_pass
                time.sleep(1.0)

                # Reset the configuration information, ensures a new EEPROM is set up correctly
                ntm_pass = ctji.reset_hw_config_info() and ntm_pass
                log.info("{} - Reset configuration information".format(self._pass_fail_string(ntm_pass)))

                # Set the configuration information
                assy_part_no = "KT-000-0143-00"
                ntm_pass = ctji.set_ntm_hw_config_info(assy_part_no, assy_rev_no,
                                                       assy_serial_no, assy_batch_no) and ntm_pass
                cmd_success, hci = ctji.get_hw_config_info()

                if cmd_success:
                    test_pass = (hci.assy_part_no == assy_part_no)
                    log.info("{} - Assembly No set to {}".format(self._pass_fail_string(test_pass), assy_part_no))
                    ntm_pass = ntm_pass and test_pass

                    test_pass = (hci.assy_rev_no == assy_rev_no)
                    log.info("{} - Assembly Revision No set to {}".format(self._pass_fail_string(test_pass),
                                                                          assy_rev_no))
                    ntm_pass = ntm_pass and test_pass

                    test_pass = (hci.assy_serial_no == assy_serial_no)
                    log.info("{} - Assembly Serial No set to {}".format(self._pass_fail_string(test_pass),
                                                                        assy_serial_no))
                    ntm_pass = ntm_pass and test_pass

                    test_pass = (hci.assy_build_batch_no == assy_batch_no)
                    log.info("{} - Assembly Batch No set to {}".format(self._pass_fail_string(test_pass),
                                                                       assy_batch_no))
                    ntm_pass = ntm_pass and test_pass

                    log.info("INFO - Hardware Version No is {}".format(hci.hw_version_no))
                    log.info("INFO - Hardware Modification No is {}".format(hci.hw_mod_version_no))
                else:
                    log.info("INFO - Failed to set configuration information!")
                    ntm_pass = ntm_pass and False

                log.info("{} - Set NTM {} Hardware Configuration Information".format(self._pass_fail_string(ntm_pass),
                                                                                     ntm + 1))
                ret_val = ret_val and ntm_pass

            # Set the NTM I2C bus back to none
            ret_val = ctji.set_ntm_i2c_bus(MpTestJigNtmI2cBus.NONE) and ret_val

        log.info("{} - Set NTM Hardware Configuration Information".format(self._pass_fail_string(ret_val)))
        return ret_val

    def expansion_slot_test(self, slot_no):
        """
        Run Expansion Slot test, tests the serial port and reference clock.
        Cu and SFP GbE connections are tested by gbe_sw_connection_test test case.
        Prerequisites:
        - Board is powered up
        - Linux is booted on SoM
        - Platform test scripts are in folder /run/media/mmcblk1p2/test on SoM
        Uses:
        - CSM SSH connection
        :param slot_no: Expansion Slot number to test, range 1..2 :type Integer
        :return: True if test passes, else False
        """
        test_data = {
            "1": {"uart": "/dev/ttyExp1", "ref_clk": ""},
            "2": {"uart": "/dev/ttyExp2", "ref_clk": ""},
        }
        log.info("")
        log.info("Expansion Slot {} Test:".format(slot_no))
        ret_val = True
        if slot_no in [1, 2]:
            with CsmPlatformTest(self._csm_username,
                                 self._csm_hostname if self._csm_ip_address is None else self._csm_ip_address) as cpt:
                # Test the UART
                if test_data[str(slot_no)]["uart"] != "":
                    test_pass = cpt.uart_test(test_data[str(slot_no)]["uart"], 115200)
                    log.info("{} - UART Test {}".format(self._pass_fail_string(test_pass),
                                                        test_data[str(slot_no)]["uart"]))
                    ret_val = test_pass and ret_val

                # Test the Reference Clock
                if test_data[str(slot_no)]["ref_clk"] != "":
                    pass
        else:
            ret_val = False

        log.info("{} - Expansion Slot {} Test".format(self._pass_fail_string(ret_val), slot_no))
        return ret_val

    def board_fan_test(self):
        """
        Test the NTM fan interfaces.  Uses the test jig utility to simulate fan tacho and measure fan PWM duty-cycle
        signals.
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        - Test jig STM32 serial interface
        :return: True if the test passed, else False :type Boolean
        :return:
        """
        fan_12v_mv_lo = 11400
        fan_12v_mv_hi = 12600

        test_sequence = [
            # (fan_pwm_source, i2c_bus)
            (MpTestJigNtmFanPwm.FAN_1_1, MpTestJigNtmI2cBus.NTM1),
            (MpTestJigNtmFanPwm.FAN_2_1, MpTestJigNtmI2cBus.NTM2),
            (MpTestJigNtmFanPwm.FAN_2_2, MpTestJigNtmI2cBus.NTM2),
            (MpTestJigNtmFanPwm.FAN_3_1, MpTestJigNtmI2cBus.NTM3)
        ]
        fan_speed_test_lim_lo = int(12000 * 0.9)
        fan_speed_test_lim_hi = int(12000 * 1.1)

        log.info("")
        log.info("Board Fan Test:")
        ret_val = True

        with MpTestJigInterface(self._tj_com_port) as ctji:
            self._set_psu_on(voltage_mv=28000)
            time.sleep(1.0)
            ctji.toggle_rcu_power_button()
            time.sleep(3.0)

            adc_read, adc_data = ctji.get_adc_data()

            for fan in ["1.1", "2.1", "2.2", "3.1"]:
                test_mv = adc_data.get("(mv) Fan {} +12V".format(fan), -1)
                test_pass = (fan_12v_mv_lo <= test_mv <= fan_12v_mv_hi)
                log.info("{} - Fan {} +12V Voltage: {} <= {} <= {} mV"
                         "".format(self._pass_fail_string(test_pass), fan, fan_12v_mv_lo, test_mv, fan_12v_mv_hi))
                ret_val = ret_val and test_pass

            for fan, i2c_bus in test_sequence:
                fan_pass = True

                # Set the NTM fan PWM signal source and I2C bus for the fan
                fan_pass = ctji.set_ntm_i2c_bus(i2c_bus) and fan_pass
                fan_pass = ctji.set_ntm_fan_source(fan) and fan_pass
                time.sleep(0.1)

                # Initialise the fan controller
                fan_pass = ctji.initialise_fan_controller() and fan_pass

                # Test the fan PWM signal
                for duty_percent in [37, 55]:
                    test_pass = ctji.set_ntm_fan_duty(duty_percent)
                    # The EMC2104 will take several seconds to ramp the fan PWM up to the requested value
                    time.sleep(0.5)
                    read_duty_percent = ctji.get_ntm_fan_duty_percent()
                    test_lim_hi = duty_percent + 5
                    test_lim_lo = duty_percent - 5
                    test_pass = (test_lim_lo <= read_duty_percent <= test_lim_hi) and test_pass
                    log.info("{} - {}: {} <= {} <= {}"
                             "".format(self._pass_fail_string(test_pass), fan.name,
                                       test_lim_lo, read_duty_percent, test_lim_hi))
                    fan_pass = test_pass and fan_pass

                # Test the fan speed readings, these should both be the same and 12000 rpm +/- 10 %
                fan1_speed_rpm, fan2_speed_rpm = ctji.get_ntm_fan_speed()

                test_pass = fan_speed_test_lim_lo <= fan1_speed_rpm <= fan_speed_test_lim_hi
                log.info("{} - {} Fan 1: {} <= {} <= {}"
                         "".format(self._pass_fail_string(test_pass), fan.name,
                                   fan_speed_test_lim_lo, fan1_speed_rpm, fan_speed_test_lim_hi))
                fan_pass = test_pass and fan_pass

                test_pass = fan_speed_test_lim_lo <= fan1_speed_rpm <= fan_speed_test_lim_hi
                log.info("{} - {} Fan 2: {} <= {} <= {}"
                         "".format(self._pass_fail_string(test_pass), fan.name,
                                   fan_speed_test_lim_lo, fan1_speed_rpm, fan_speed_test_lim_hi))
                fan_pass = test_pass and fan_pass

                ret_val = fan_pass and ret_val

        self._set_psu_off()
        time.sleep(1.0)

        log.info("{} - Board Fan Test".format(self._pass_fail_string(ret_val)))
        return ret_val


class CsmCommonProdTestInfo:
    """
    Utility base class used to define the test info common to the Manpack and Vehicle CSM to be executed by the
    test thread class.
    """
    over_under_voltage_lockout_test: bool = False
    external_power_off_test: bool = False
    over_voltage_test: bool = False
    program_zeroise_test_fw: bool = False
    zeroise_psu_rail_test: bool = False
    battery_signal_test: bool = False
    rtc_test: bool = False
    case_switch_test: bool = False
    light_sensor_test: bool = False
    keypad_test: bool = False
    program_zeroise_fpga_test_image: bool = False
    zeroise_fpga_test: bool = False
    erase_zeroise_fpga_test_image: bool = False
    set_config_info: bool = False
    unit_set_config_info: bool = False
    program_som: bool = False
    program_gbe_sw_fw: bool = False
    qsgmii_test: bool = False
    power_up_board_linux: bool = False
    check_for_sd_card: bool = False
    unit_tamper_test: bool = False
    unit_keypad_test: bool = False
    unit_buzzer_test: bool = False
    unit_uart_test: bool = False
    gbe_sw_connection_test: bool = False
    som_built_in_test: bool = False
    external_pps_test: bool = False
    internal_pps_test: bool = False
    rf_mute_test: bool = False
    ptp_phy_test: bool = False
    uart_test: bool = False
    tmp442_test: bool = False
    ad7415_test: bool = False
    eui48_id_test: bool = False
    print_som_mac_ipv4_address: bool = False
    super_flash_mount_test: bool = False
    gps_lock_test: bool = False
    tcxo_adjust_test: bool = False
    som_i2c_device_detect_test: bool = False
    som_eia422_intf_test: bool = False
    buzzer_test: bool = False
    gbe_chassis_gnd_test: bool = True
    pb_controller_irq_test: bool = False
    unit_pb_controller_irq_test: bool = False
    power_kill_test: bool = False
    expansion_slot_1_test: bool = False
    expansion_slot_2_test: bool = False
    remove_test_scripts: bool = False
    power_supply_off: bool = False
    zeroise_test_fpga: str = ""
    zeroise_test_fw: str = ""
    zeroise_operational_fw: str = ""
    platform_test_scripts: str = ""
    gbe_switch_fw: str = ""
    assy_type: str = ""
    assy_rev_no: str = ""
    assy_serial_no: str = ""
    assy_build_batch_no: str = ""
    csm_hostname: str = ""
    csm_username: str = ""
    tj_com_port: str = ""
    psu_com_port: str = ""
    tpl_sw_com_port: str = ""
    master_com_port: str = ""
    rcu_com_port: str = ""
    segger_jlink_win32: str = ""
    segger_jlink_win64: str = ""
    flash_pro: str = ""
    iperf3: str = ""
    cygwin1_dll: str = ""
    test_case_list = []     # Must be populated by concrete classes


class CsmProdTestInfo(CsmCommonProdTestInfo):
    """
    Utility base class used to define the test info specific to the Vehicle CSM to be executed by the test thread class.
    """
    power_cable_detect_test: bool = False
    poe_pse_test: bool = False
    power_off_override_test: bool = False
    test_case_list = [
        # Tests are specified in the order needed for production
        "over_under_voltage_lockout_test",
        "external_power_off_test",
        "over_voltage_test",
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        "zeroise_psu_rail_test",
        "battery_signal_test",
        "rtc_test",
        "case_switch_test",
        "power_cable_detect_test",
        "light_sensor_test",
        "keypad_test",
        # START - Require Zeroise FGPA Test Image
        "program_zeroise_fpga_test_image",
        "zeroise_fpga_test",
        "erase_zeroise_fpga_test_image",
        # END - Require Zeroise FGPA Test Image
        # START - Require SoM Programmed
        # START - Require GbE Switch Programmed
        "program_som",
        "program_gbe_sw_fw",
        "poe_pse_test",
        "qsgmii_test",
        # START - Set Unit Config Info
        "unit_set_config_info",
        # END - Set Unit Config Info
        # START - Require Board Powered and Linux Booted with platform test scripts installed
        "power_up_board_linux",
        "copy_test_scripts_to_som",
        # START - Unit Specific Tests
        "unit_keypad_test",
        "unit_pb_controller_irq_test",
        "unit_buzzer_test",
        "check_for_sd_card",
        "unit_tamper_test",
        "unit_uart_test",
        # END - Unit Specific Tests
        "set_config_info",
        "gbe_sw_connection_test",
        "pb_controller_irq_test",
        "som_built_in_test",
        "external_pps_test",
        "internal_pps_test",
        "rf_mute_test",
        "power_off_override_test",
        "ptp_phy_test",
        "uart_test",
        "tmp442_test",
        "ad7415_test",
        "eui48_id_test",
        "print_som_mac_ipv4_address",
        "super_flash_mount_test",
        "gps_lock_test",
        "tcxo_adjust_test",
        "som_i2c_device_detect_test",
        "som_eia422_intf_test",
        "buzzer_test",
        "gbe_chassis_gnd_test",
        "power_kill_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        # END - Require Board Powered and Linux Booted with platform test scripts installed
        # END - Require Board Powered
        "program_zeroise_operational_fw",
        "expansion_slot_1_test",
        "expansion_slot_2_test",
        "remove_test_scripts",
        "power_supply_off"
    ]
    motherboard_part1_test_case_list = [
        # Tests are specified in the order needed for production
        "over_under_voltage_lockout_test",
        "external_power_off_test",
        "over_voltage_test",
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        "zeroise_psu_rail_test",
        "battery_signal_test",
        "rtc_test",
        "case_switch_test",
        "power_cable_detect_test",
        "light_sensor_test",
        "keypad_test",
        # START - Require Zeroise FGPA Test Image
        "program_zeroise_fpga_test_image",
        "zeroise_fpga_test",
        "erase_zeroise_fpga_test_image",
        # END - Require Zeroise FGPA Test Image
        # START - Require SoM Programmed
        # START - Require GbE Switch Programmed
        "program_som",
        "program_gbe_sw_fw",
        "poe_pse_test",
        "qsgmii_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        "program_zeroise_operational_fw",
        "remove_test_scripts",
        "power_supply_off"
    ]
    motherboard_part2_test_case_list = [
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        # START - Require Board Powered and Linux Booted with platform test scripts installed
        "power_up_board_linux",
        "copy_test_scripts_to_som",
        "set_config_info",
        "gbe_sw_connection_test",
        "pb_controller_irq_test",
        "som_built_in_test",
        "external_pps_test",
        "internal_pps_test",
        "rf_mute_test",
        "power_off_override_test",
        "ptp_phy_test",
        "uart_test",
        "tmp442_test",
        "ad7415_test",
        "eui48_id_test",
        "print_som_mac_ipv4_address",
        "super_flash_mount_test",
        "gps_lock_test",
        "tcxo_adjust_test",
        "som_i2c_device_detect_test",
        "som_eia422_intf_test",
        "buzzer_test",
        "gbe_chassis_gnd_test",
        "power_kill_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        # END - Require Board Powered and Linux Booted with platform test scripts installed
        # END - Require Board Powered
        "program_zeroise_operational_fw",
        "expansion_slot_1_test",
        "expansion_slot_2_test",
        "remove_test_scripts",
        "power_supply_off"
    ]


class MpCsmProdTestInfo(CsmCommonProdTestInfo):
    """
    Utility base class used to define the test info specific to the Manpack CSM to be executed by the test thread class.
    """
    pb_controller_supply_test: bool = False
    ntm_pfi_test: bool = False
    set_ntm_hw_config_info: bool = False
    board_fan_test: bool = False
    test_case_list = [
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        # Tests are specified in the order needed for production
        "over_under_voltage_lockout_test",
        "pb_controller_supply_test",
        "over_voltage_test",
        "ntm_pfi_test",
        "set_ntm_hw_config_info",
        "board_fan_test",
        "external_power_off_test",
        "zeroise_psu_rail_test",
        "battery_signal_test",
        "rtc_test",
        "case_switch_test",
        "light_sensor_test",
        "keypad_test",
        # START - Require Zeroise FGPA Test Image
        "program_zeroise_fpga_test_image",
        "zeroise_fpga_test",
        "erase_zeroise_fpga_test_image",
        # END - Require Zeroise FGPA Test Image
        # START - Require SoM Programmed
        # START - Require GbE Switch Programmed
        "program_som",
        "program_gbe_sw_fw",
        "qsgmii_test",
        # START - Require Board Powered and Linux Booted with platform test scripts installed
        "power_up_board_linux",
        "copy_test_scripts_to_som",
        "set_config_info",
        "gbe_sw_connection_test",
        "pb_controller_irq_test",
        "som_built_in_test",
        "external_pps_test",
        "internal_pps_test",
        "rf_mute_test",
        "uart_test",
        "tmp442_test",
        "ad7415_test",
        "eui48_id_test",
        "print_som_mac_ipv4_address",
        "super_flash_mount_test",
        "gps_lock_test",
        "tcxo_adjust_test",
        "som_i2c_device_detect_test",
        "som_eia422_intf_test",
        "buzzer_test",
        "gbe_chassis_gnd_test",
        "expansion_slot_1_test",
        "expansion_slot_2_test",
        "ptp_phy_test",
        "power_kill_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        # END - Require Board Powered and Linux Booted with platform test scripts installed
        # END - Require Board Powered
        "remove_test_scripts",
        "program_zeroise_operational_fw",
        "power_supply_off"
    ]
    motherboard_part1_test_case_list = [
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        # Tests are specified in the order needed for production
        "over_under_voltage_lockout_test",
        "pb_controller_supply_test",
        "over_voltage_test",
        "ntm_pfi_test",
        "set_ntm_hw_config_info",
        "board_fan_test",
        "external_power_off_test",
        "zeroise_psu_rail_test",
        "battery_signal_test",
        "rtc_test",
        "case_switch_test",
        "light_sensor_test",
        "keypad_test",
        # START - Require Zeroise FGPA Test Image
        "program_zeroise_fpga_test_image",
        "zeroise_fpga_test",
        "erase_zeroise_fpga_test_image",
        # END - Require Zeroise FGPA Test Image
        # START - Require SoM Programmed
        # START - Require GbE Switch Programmed
        "program_som",
        "program_gbe_sw_fw",
        "qsgmii_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        "remove_test_scripts",
        "program_zeroise_operational_fw",
        "power_supply_off"
    ]
    motherboard_part2_test_case_list = [
        # START - Require Zeroise Micro Test Utility
        "program_zeroise_test_fw",
        # START - Require Board Powered and Linux Booted with platform test scripts installed
        "power_up_board_linux",
        "copy_test_scripts_to_som",
        "set_config_info",
        "gbe_sw_connection_test",
        "pb_controller_irq_test",
        "som_built_in_test",
        "external_pps_test",
        "internal_pps_test",
        "rf_mute_test",
        "uart_test",
        "tmp442_test",
        "ad7415_test",
        "eui48_id_test",
        "print_som_mac_ipv4_address",
        "super_flash_mount_test",
        "gps_lock_test",
        "tcxo_adjust_test",
        "som_i2c_device_detect_test",
        "som_eia422_intf_test",
        "buzzer_test",
        "gbe_chassis_gnd_test",
        "expansion_slot_1_test",
        "expansion_slot_2_test",
        "ptp_phy_test",
        "power_kill_test",
        # END - Require GbE Switch Programmed
        # END - Require SoM Programmed
        # END - Require Zeroise Micro Test Utility
        # END - Require Board Powered and Linux Booted with platform test scripts installed
        # END - Require Board Powered
        "remove_test_scripts",
        "program_zeroise_operational_fw",
        "power_supply_off"
    ]

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
