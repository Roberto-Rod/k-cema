#!/usr/bin/env python3
"""

Classes and functions implementing production test cases for:

- KT-000-0206-00 K-CEMA Integrated CTS Digital Board

Hardware/software compatibility:

- KT-000-00206-00 K-CEMA Integrated CTS Digital Board - Rev B.1 onwards
- KT-956-0262-00 K-CEMA Integrated CTS Test Jig Utility - v1.2.0 onwards
- KT-956-0256-00 K-CEMA Integrated CTS Digital Board Test Utility - v1.0.0 onwards

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
from csm_plat_test_intf import CsmPlatformTest
import cts_program_devices as cpd
from cts_test_jig_intf import CtsTestJigInterface, CtsTestJigGpoSignals, CtsTestJigRfPaths
from cts_micro_test_intf import CtsMicroTestInterface, CtsMicroGpoSignals, CtsMicroIfPaths
from signal_generator import VisaSignalGenerator

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
class CtsProdTestCommon:
    """
    Common test cases used for testing different items.
    """
    DIGITAL_BOARD_POWER_ENABLE_DELAY_S = 2.0

    def __init__(self, psu_com_port, test_jig_com_port, digital_board_com_port,
                 unit_hostname, csm_hostname, segger_jlink_win32=None, segger_jlink_win64=None):
        """
        Class constructor, initialises common aspects of the test environment, call from child classes.
        :param psu_com_port: Tenma 72-2940 PSU COM port :type String
        :param test_jig_com_port: test jig NUCLEO STM32 COM port :type String
        :param digital_board_com_port: board/unit under test COM port :type String
        :param unit_hostname: board/unit under test network hostname :type String
        :param csm_hostname: CSM network hostname, used for unit testing installed in a CSM :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use cts_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use cts_program_devices constant
        """
        # PSU initialisation
        log.info("INFO - Initialising power supply")
        self._psu_com_port = psu_com_port
        self.tpsu = self._get_tenma_psu_instance()
        self._set_psu_off()
        log.info("INFO - Power supply initialisation complete - {}".format(self.tpsu.MATCH_STR))

        # Test jig interface initialisation
        log.info("INFO - Initialising test jig interface")
        self._test_jig_com_port = test_jig_com_port
        with CtsTestJigInterface(self._test_jig_com_port) as tji:
            pass
        log.info("INFO - Test jig interface initialisation complete")

        # Store unit/board hostname for future use
        self._unit_hostname = unit_hostname
        # This is populated in the enable_som method
        self._unit_ip_address = None

        # Store CSM hostname for future use
        self._csm_hostname = csm_hostname
        # This is populated when CSM related methods are called
        self._csm_ip_address = None

        # Store Digital board COM port for future use
        self._digital_board_com_port = digital_board_com_port

        # Override exe path constants in cts_program_devices and win_ip3 modules if exe path variables have been passed
        if segger_jlink_win32 is not None:
            cpd.JLINK_PATH_WIN32 = segger_jlink_win32
        if segger_jlink_win64 is not None:
            cpd.JLINK_PATH_WIN64 = segger_jlink_win64

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

    def _set_psu_on(self, voltage_mv=12000, i_limit_ma=300):
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

    def power_supply_on(self):
        """
        Turns the bench power supply on
        Prerequisites:
        - None
        Uses:
        - Tenma Bench PSU serial interface
        :return: True
        """
        self._set_psu_on()
        return True

    def _set_psu_off(self):
        """
        Turn the PSU off.
        :return: N/A
        """
        if self.tpsu is not None:
            self.tpsu.OFF()
        else:
            raise RuntimeError("PSU Test Equipment Error!")

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

        for cls in Tenma72Base.__subclasses__():
            if cls.MATCH_STR in ver:
                return cls(self._psu_com_port, debug=False)

        log.critical("Could not detect Tenma PSU!")
        return None

    def _power_enable_digital_board(self):
        """
        Enable the Digital Board power supply rails.
        Prerequisites:
        - None
        Uses:
        - Test jig serial interface
        :return: True if successful, else False
        """
        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P12V_EN, True)
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P3V3_EN, True) and ret_val
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_POWER_EN, True) and ret_val
            time.sleep(self.DIGITAL_BOARD_POWER_ENABLE_DELAY_S)
            return ret_val

    def _power_disable_digital_board(self):
        """
        Disable the Digital Board power supply rails.
        Prerequisites:
        - None
        Uses:
        - Test jig serial interface
        :return: True if successful, else False
        """
        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_POWER_EN, False)
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P3V3_EN, False) and ret_val
            ret_val = ctji.set_gpo_signal(CtsTestJigGpoSignals.UUT_DIGITAL_BOARD_CTS_P12V_EN, False) and ret_val
            return ret_val

    def program_micro(self, fw_bin):
        """
        Program the Board Under Test STM32 Microcontroller
        Prerequisites:
        - None
        Uses:
        - Segger J-Link programmer
        :param fw_bin: firmware binary file
        :return: True if device programmed, else False
        """
        log.info("")
        log.info("Programming Microcontroller:")
        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board()
        ret_val = cpd.program_micro_device(fw_bin) and ret_val
        ret_val = self._power_disable_digital_board() and ret_val
        log.info("{} - Program Microcontroller: {}".format("PASS" if ret_val else "FAIL", fw_bin))
        return ret_val

    @staticmethod
    def find_units(timeout=10):
        ret_val = []
        unit_type_str = "CTS"
        type_str = "_cts._tcp.local."
        count = timeout * 10

        def on_change(zeroconf, service_type, name, state_change):
            nonlocal ret_val
            nonlocal count
            if state_change is zeroconfig.ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    address = "{}".format(socket.inet_ntoa(info.addresses[0]))
                    server = str(info.server)
                    if unit_type_str in server:
                        ret_val.append([server.rstrip("."), address])

        zeroconf = zeroconfig.Zeroconf()
        browser = zeroconfig.ServiceBrowser(zeroconf, type_str, handlers=[on_change])

        while count > 0:
            time.sleep(0.1)
            count = count - 1

        zeroconf.close()
        return ret_val

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

            if not output or "unreachable" in output or "0 packets received" in output or "could not find" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

    @staticmethod
    def _get_ip_address_from_hostname(hostname):
        """ Utility method to resolve a hostname to an IP address """
        response_ip_address = None

        if platform.system().lower() == "windows":
            count_param = "n"
        else:
            count_param = "c"

        for i in range(0, 10):
            output = popen("ping -{} 1 {}".format(count_param, hostname)).read()

            if not output or "unreachable" in output or "0 packets received" in output or "could not find" in output:
                pass
            else:
                # TODO add Linux support
                if platform.system().lower() == "windows":
                    for a_line in output.splitlines():
                        if "Reply from " in a_line:
                            response_ip_address = a_line.split(' ')[2][:-1]
                            break
                break

        return response_ip_address

    @staticmethod
    def _pass_fail_string(test_val):
        """ Utility method to return pass or fail string based on a boolean value """
        return "PASS" if bool(test_val) else "FAIL"


class CtsProdTest(CtsProdTestCommon):
    """
    Class that implements CTS production test cases
    """
    _DIGITAL_BOARD_NO = "KT-000-0206-00"

    def __init__(self, psu_com_port, test_jig_com_port, digital_board_com_port,
                 unit_hostname, segger_jlink_win32=None, segger_jlink_win64=None):
        """
        Class constructor - Sets the test environment initial state
        :param psu_com_port: Tenma 72-2940 PSU COM port :type String
        :param test_jig_com_port: test jig NUCLEO STM32 COM port :type String
        :param digital_board_com_port: board/unit under test COM port :type String
        :param unit_hostname: board/unit under test network hostname :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use cts_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use cts_program_devices constant
        """
        # Set test environment initial state
        log.info("INFO - Initialising test environment...")

        # Call the base class constructor to initialise common aspects of the test environment
        super().__init__(psu_com_port, test_jig_com_port, digital_board_com_port, unit_hostname,
                         segger_jlink_win32, segger_jlink_win64)

        log.info("INFO - Test environment initialisation complete")

    def set_hw_config_info(self, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board under test's hardware configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        Prerequisites:
        - PSU is on
        Uses:
        - Test jig serial interface
        :param assy_type: board/unit assembly type :type String
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if hardware configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Hardware Configuration Information:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            # Disable the test jig I2C loop back
            ret_val = ctji.set_i2c_loop_back_enable(False) and ret_val

            # Reset the configuration information, ensures a new EEPROM is set up correctly
            ret_val = ctji.reset_hw_config_info() and ret_val
            log.info("{} - Reset configuration information".format(self._pass_fail_string(ret_val)))

            # Set the configuration information
            assy_part_no = self._DIGITAL_BOARD_NO
            ret_val = ctji.set_hw_config_info(assy_part_no, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val
            cmd_success, hci = ctji.get_hw_config_info()

            if cmd_success:
                test_pass = (hci.assy_part_no == assy_part_no)
                log.info("{} - Assembly No set to {}".format(self._pass_fail_string(test_pass), assy_part_no))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_rev_no == assy_rev_no)
                log.info("{} - Assembly Revision No set to {}".format(self._pass_fail_string(test_pass), assy_rev_no))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_serial_no == assy_serial_no)
                log.info("{} - Assembly Serial No set to {}".format(self._pass_fail_string(test_pass), assy_serial_no))
                ret_val = ret_val and test_pass

                test_pass = (hci.assy_build_batch_no == assy_batch_no)
                log.info("{} - Assembly Batch No set to {}".format(self._pass_fail_string(test_pass), assy_batch_no))
                ret_val = ret_val and test_pass

                log.info("INFO - Hardware Version No is {}".format(hci.hw_version_no))
                log.info("INFO - Hardware Modification No is {}".format(hci.hw_mod_version_no))
            else:
                log.info("INFO - Failed to set configuration information!")
                ret_val = ret_val and False

            # Enable the test jig I2C loop back
            ret_val = ctji.set_i2c_loop_back_enable(True) and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Set Hardware Configuration Information".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_adc_test(self):
        """
        Test the ADC rail measurements.
        - Sequence 1 - always on rails:
            - Read voltages
            - Check voltages are within limits
        - Sequence 2 - enabled/disabled rails:
            - For each rail in turn:
                - Enable rail
                - Check disabled rail voltage is within "OFF" limits
                - Check enabled rail voltages are within "ON" limits
                - Disable rail

        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        :return: True if test passes, else False :type Boolean
        """
        test_sequence_1 = [
            # (suppply_rail, lim_lo_mv, lim_hi_mv)
            ("BIT +12V Voltage (mV)", 11400, 12600),
            ("BIT +3V3 Voltage (mV)", 3135, 3465),
            ("BIT -3V3 Voltage (mV)", -3465, -3135),
            ("BIT +5V0 Voltage (mV)", 4750, 5250)
        ]

        test_sequence_2 = [
            # (rail_en_gpo, suppply_rail, lim_lo_mv, lim_hi_mv)
            (CtsMicroGpoSignals.RX_PATH_3V3_IF_EN, "BIT +3V3 IF Voltage (mV)", 3135, 3465),
            (CtsMicroGpoSignals.TX_PATH_3V3_TX_EN, "BIT +3V3 Tx Voltage (mV)", 3135, 3465),
            (CtsMicroGpoSignals.TX_PATH_5V0_TX_EN, "BIT +5V0 Tx Voltage (mV)", 4750, 5250)
        ]

        enable_disable_rails = [
            "BIT +3V3 IF Voltage (mV)",
            "BIT +3V3 Tx Voltage (mV)",
            "BIT +5V0 Tx Voltage (mV)"
        ]

        off_lim_lo_mv = 0
        off_lim_hi_mv = 100

        log.info("")
        log.info("Board ADC Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
            # Test Sequence 1
            test_pass, adc_data = cmti.get_adc_data()
            ret_val = test_pass and ret_val

            for supply_rail, test_lim_lo_mv, test_lim_hi_mv in test_sequence_1:
                test_mv = adc_data.get(supply_rail, -999999)
                test_pass = (test_lim_lo_mv <= test_mv <= test_lim_hi_mv)
                log.info("{} - {}: {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                          supply_rail, test_lim_lo_mv, test_mv, test_lim_hi_mv))
                ret_val = ret_val and test_pass

            # Test Sequence 2
            for rail_en_gpo, supply_rail, test_lim_lo_mv, test_lim_hi_mv in test_sequence_2:
                test_pass = cmti.set_gpo_signal(rail_en_gpo, True)
                time.sleep(1.0)
                cmd_success, adc_data = cmti.get_adc_data()
                test_pass = cmd_success and test_pass

                for rail in enable_disable_rails:
                    if rail == supply_rail:
                        test_mv = adc_data.get(rail, -999999)
                        test_pass = (test_lim_lo_mv <= test_mv <= test_lim_hi_mv) and test_pass
                        log.info("{} - {}: {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                                  rail, test_lim_lo_mv, test_mv, test_lim_hi_mv))
                    else:
                        test_mv = adc_data.get(rail, -999999)
                        test_pass = (off_lim_lo_mv <= test_mv <= off_lim_hi_mv) and test_pass
                        log.info("{} - {}: {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                                  rail, off_lim_lo_mv, test_mv, off_lim_hi_mv))

                test_pass = cmti.set_gpo_signal(rail_en_gpo, False)
                time.sleep(1.0)
                cmd_success, adc_data = cmti.get_adc_data()
                test_pass = cmd_success and test_pass

                test_mv = adc_data.get(supply_rail, -999999)
                test_pass = (off_lim_lo_mv <= test_mv <= off_lim_hi_mv) and test_pass
                log.info("{} - {}: {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                          supply_rail, off_lim_lo_mv, test_mv, off_lim_hi_mv))

                ret_val = test_pass and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board ADC Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_temp_sensor_test(self):
        """
        Read the temperature sensor and check the return value is "reasonable" for room ambient conditions.
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        test_lim_lo = 15
        test_lim_hi = 40

        log.info("")
        log.info("Board Temperature Sensor Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
            temp = cmti.get_temperature()
            ret_val = test_lim_lo <= temp <= test_lim_hi and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board Temperature Sensor Test {} <= {} <= {} deg C".format(self._pass_fail_string(ret_val),
                                                                                  test_lim_lo, temp, test_lim_hi))
        return ret_val

    def board_mac_address_test(self):
        """
        Read the MAC address EUI48 and check that the OUI is a valid Microchip OUI
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        # http://ww1.microchip.com/downloads/en/AppNotes/TB3187-Organizationally-Unique-Identifiers-Tech-Brief-90003187A.pdf
        # https://ouilookup.com/vendor/microchip-technology-inc
        microchip_oui = ["44-B7-D0", "D8-47-8F", "9C-95-6E", "40-84-32", "FC-0F-E7", "80-34-28", "60-8A-10", "60-8A-19",
                         "00-04-A3", "54-10-EC", "D8-80-39", "00-1E-C0", "80-1F-12", "04-91-62", "E8-EB-1B", "FC-C2-3D",
                         "68-27-19"]

        log.info("")
        log.info("Board MAC Address Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
            mac_address = cmti.get_mac_address()
            mac_address_oui = mac_address[0:len(microchip_oui[0])].upper()
            ret_val = mac_address_oui in microchip_oui and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board MAC Address Test - {}".format(self._pass_fail_string(ret_val), mac_address.upper()))
        return ret_val

    def board_ping_test(self):
        """
        Ping the digital board micro test utility and check that it replies.  The micro test utillity uses a fixed
        MAC address of 00-80-E1-01-02-03 which yields an LwIP autoconf IPV4 address of !169.254.4.2!
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        :return: True if test passes, else False
        """
        ipv4_address = "169.254.4.2"

        log.info("")
        log.info("Board Ping Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val
        # Give the LwIP stack some extra time to start up
        time.sleep(5.0)
        ret_val = self._ping(ipv4_address, retries=4) and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board Ping Test - {}".format(self._pass_fail_string(ret_val), ipv4_address))
        return ret_val

    def board_pps_test(self):
        """
        Tests the test jig 1PPS is being received by the digital board micro.
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Board 1PPS Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
                # Disable test jig 1PPS and confirm 1PPS NOT detected
                log.info("INFO - 1PPS Source Disabled")
                ret_val = ctji.enable_pps_output(False) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = cmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

                # Enable test jig 1PPS and confirm 1PPS IS detected
                log.info("INFO - 1PPS Source Enabled")
                ret_val = ctji.enable_pps_output(True) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = cmti.get_pps_detected()
                log.info("{} - 1PPS detected {} ms".format(self._pass_fail_string(pps_detected), pps_delta))
                ret_val = pps_detected and ret_val

                # Disable test jig 1PPS and confirm 1PPS NOT detected
                log.info("INFO - 1PPS Source Disabled")
                ret_val = ctji.enable_pps_output(False) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = cmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board 1PPS Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_loop_back_test(self):
        """
        Command the digital board mirco test utility to perform a loop back test and check the test results.
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Board Loop Back Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
            ret_val = cmti.get_loop_back_test() and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board Loop Back Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_if_path_test(self, instruction_dialog_func):
        """
        Perform an IF path test, for the time being the tester must set the signal generator frequency and power level.
        For each IF band:
        - Set signal generator to in-band frequency
        - Set signal levels to -15 and -35 dBm
        - Set digital board IF path
        - Take RF detector voltage readings
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        - Manually controlled signal generator
        :return: True if test passes, else False :type Boolean
        """
        test_sequence = [
            # (test frequency_mhz, test_level_dbm, [test_if_bands], test_lim_lo_mv, test_lim_hi_mv)
            (916.5, -15.0, [CtsMicroIfPaths.IF0_916_917_MHZ], 1400, 1600),
            (916.5, -15.0, [CtsMicroIfPaths.IF1_910_920_MHZ], 1450, 1650),
            (916.5, -35.0, [CtsMicroIfPaths.IF0_916_917_MHZ], 1050, 1250),
            (916.5, -35.0, [CtsMicroIfPaths.IF1_910_920_MHZ], 1475, 1675),
            (2310.0, -35.0, [CtsMicroIfPaths.IF2_2305_2315_MHZ], 1050, 1250),
            (2310.0, -15.0, [CtsMicroIfPaths.IF2_2305_2315_MHZ], 1400, 1600),
            (2355.0, -15.0, [CtsMicroIfPaths.IF3_2350_2360_MHZ], 1400, 1600),
            (2355.0, -35.0, [CtsMicroIfPaths.IF3_2350_2360_MHZ], 1050, 1250)
        ]
        no_readings_to_average = 10
        dwell_time_100_us = 1000    # 100 ms

        log.info("")
        log.info("Board IF Path Test:")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
                # Set the test jig RF path for digital board rx testing and enable the digital board IF +3V3 supply
                ret_val = ctji.set_test_jig_rf_path(CtsTestJigRfPaths.DIGITAL_BOARD_TEST_RX_MODE) and ret_val
                ret_val = cmti.set_gpo_signal(CtsMicroGpoSignals.RX_PATH_3V3_IF_EN, True) and ret_val

                # Calling ADC command provides an accurate external reference voltage to RF detector command
                cmd_success, adc_data = cmti.get_adc_data()
                ret_val = cmd_success and ret_val
                log.info("INFO - Reference Voltage (mV): {}"
                         "".format(adc_data.get("STM32 Vref Internal Voltage (mV)", -99999)))

                for frequency_mhz, test_level_dbm, test_if_bands, test_lim_lo_mv, test_lim_hi_mv in test_sequence:
                    instruction_dialog_func("Set the Signal Generator output to then click OK to proceed:\n\n"
                                            "Frequency (MHz):\t{}\nRF Level (dBm):\t{}"
                                            "".format(frequency_mhz, test_level_dbm))

                    for test_if_band in test_if_bands:
                        # Set the IF path
                        test_pass = cmti.set_if_path(test_if_band)

                        # Get RF detector voltage reading
                        running_total_mv = 0
                        for i in range(0, no_readings_to_average):
                            results = cmti.get_rf_detector(dwell_time_100_us)
                            running_total_mv += results[1]
                            time.sleep(0.1)

                        rf_detector_voltage_mv = running_total_mv / no_readings_to_average

                        # Check that the RF detector voltage reading is within limits
                        test_pass = test_lim_lo_mv <= rf_detector_voltage_mv <= test_lim_hi_mv and test_pass
                        log.info("{} - IF Path {}: {} <= {} <= {} mV".format(self._pass_fail_string(test_pass),
                                                                                test_if_band.name, test_lim_lo_mv,
                                                                                rf_detector_voltage_mv, test_lim_hi_mv))
                        ret_val = test_pass and ret_val

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board IF Path Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_if_path_test_auto(self, sig_gen, if_916_5_mhz_dbm, if_2310_mhz_dbm, if_2355_mhz_dbm):
        """
        Perform an automated IF path test.
        For each IF band:
        - Set signal generator to in-band frequency
        - Set signal levels to -15 and -35 dBm
        - Set digital board IF path
        - Take RF detector voltage readings
        Prerequisites:
        - PSU is on
        - Micro test utility installed on board under test
        Uses:
        - Test jig serial interface
        - Micro test utility serial interface
        - Manually controlled signal generator
        :param sig_gen: VISA signal generator instance :type VisaSignalGenerator
        :param if_916_5_mhz_dbm: test jig and cable loss at 916.5 MHz in dBm :type Float
        :param if_2310_mhz_dbm: test jig and cable loss at 2310 MHz in dBm :type Float
        :param if_2355_mhz_dbm: test jig and cable loss at 2355 MHz in dBm :type Float
        :return: True if test passes, else False :type Boolean
        """
        if not issubclass(type(sig_gen), VisaSignalGenerator):
            raise TypeError("sig_gen is not subclass of VisaSignalGenerator!")

        test_sequence = [
            # (test frequency_hz, test_level_dbm, [test_if_bands], test_lim_lo_mv, test_lim_hi_mv)
            (916.5E6, -35.0 + if_916_5_mhz_dbm, [CtsMicroIfPaths.IF0_916_917_MHZ], 1050, 1250),
            (916.5E6, -15.0 + if_916_5_mhz_dbm, [CtsMicroIfPaths.IF0_916_917_MHZ], 1450, 1650),
            (916.5E6, -35.0 + if_916_5_mhz_dbm, [CtsMicroIfPaths.IF1_910_920_MHZ], 1075, 1275),
            (916.5E6, -15.0 + if_916_5_mhz_dbm, [CtsMicroIfPaths.IF1_910_920_MHZ], 1475, 1675),
            (2310.0E6, -35.0 + if_2310_mhz_dbm, [CtsMicroIfPaths.IF2_2305_2315_MHZ], 1050, 1250),
            (2310.0E6, -15.0 + if_2310_mhz_dbm, [CtsMicroIfPaths.IF2_2305_2315_MHZ], 1400, 1600),
            (2355.0E6, -35.0 + if_2355_mhz_dbm, [CtsMicroIfPaths.IF3_2350_2360_MHZ], 1050, 1250),
            (2355.0E6, -15.0 + if_2355_mhz_dbm, [CtsMicroIfPaths.IF3_2350_2360_MHZ], 1400, 1600)
        ]
        no_readings_to_average = 10
        dwell_time_100_us = 1000    # 100 ms

        log.info("")
        log.info("Board IF Path Test (Auto):")
        ret_val = True

        # Enable the Digital Board power supplies
        ret_val = self._power_enable_digital_board() and ret_val

        with CtsTestJigInterface(self._test_jig_com_port) as ctji:
            with CtsMicroTestInterface(self._digital_board_com_port) as cmti:
                # Disable the signal generator output
                ret_val = sig_gen.set_output_enable(False) and ret_val
                time.sleep(0.1)

                # Set the test jig RF path for digital board rx testing and enable the digital board IF +3V3 supply
                ret_val = ctji.set_test_jig_rf_path(CtsTestJigRfPaths.DIGITAL_BOARD_TEST_RX_MODE) and ret_val
                ret_val = cmti.set_gpo_signal(CtsMicroGpoSignals.RX_PATH_3V3_IF_EN, True) and ret_val

                # Calling ADC command provides an accurate external reference voltage to RF detector command
                cmd_success, adc_data = cmti.get_adc_data()
                ret_val = cmd_success and ret_val
                log.info("INFO - Reference Voltage (mV): {}"
                         "".format(adc_data.get("STM32 Vref Internal Voltage (mV)", -99999)))

                for frequency_hz, test_level_dbm, test_if_bands, test_lim_lo_mv, test_lim_hi_mv in test_sequence:
                    # Set the signal generator frequency and power, enable the output and allow it to settle
                    ret_val = sig_gen.set_carrier_freq_hz(frequency_hz) and ret_val
                    time.sleep(0.1)
                    ret_val = sig_gen.set_output_power_dbm(test_level_dbm) and ret_val
                    time.sleep(0.1)
                    ret_val = sig_gen.set_output_enable(True) and ret_val
                    time.sleep(0.5)

                    for test_if_band in test_if_bands:
                        # Set the IF path
                        test_pass = cmti.set_if_path(test_if_band)

                        # Get RF detector voltage reading
                        running_total_mv = 0
                        for i in range(0, no_readings_to_average):
                            results = cmti.get_rf_detector(dwell_time_100_us)
                            running_total_mv += results[1]
                            time.sleep(0.1)

                        rf_detector_voltage_mv = running_total_mv / no_readings_to_average

                        # Check that the RF detector voltage reading is within limits
                        test_pass = test_lim_lo_mv <= rf_detector_voltage_mv <= test_lim_hi_mv and test_pass
                        log.info("{} - IF Path {}: {} <= {} <= {} mV".format(self._pass_fail_string(test_pass),
                                                                                test_if_band.name, test_lim_lo_mv,
                                                                                rf_detector_voltage_mv, test_lim_hi_mv))
                        ret_val = test_pass and ret_val

                    # Disable the signal generator output
                    ret_val = sig_gen.set_output_enable(False) and ret_val
                    time.sleep(0.1)

        # Disable the Digital Board power supplies
        ret_val = self._power_disable_digital_board() and ret_val

        log.info("{} - Board IF Path Test (Auto)".format(self._pass_fail_string(ret_val)))
        return ret_val

    def copy_test_scripts_to_som(self, test_script_archive):
        """
        Copy the test scripts to the CSM
        Prerequisites:
        - CSM is powered and running Linux
        Uses:
        - CSM SSH connection
        :return: True if successful, else False
        """
        log.info("")
        log.info("Copying Test Scripts to CSM:")

        with CsmPlatformTest(self._csm_username, self._csm_hostname) as cpt:
            ret_val = cpt.copy_test_scripts_to_som(test_script_archive)

        log.info("{} - Copied test scripts to SoM eMMC".format("PASS" if ret_val else "FAIL"))
        return ret_val


class CtsProdTestInfo:
    """
    Utility class used to define the test info to be executed by the test thread class
    """
    # Test Cases:
    power_supply_on: bool = False
    set_hw_config_info: bool = False
    program_micro_test_fw: bool = False
    board_adc_test: bool = False
    board_temp_sensor_test: bool = False
    board_mac_address_test: bool = False
    board_ping_test: bool = False
    board_pps_test: bool = False
    board_loop_back_test: bool = False
    board_if_path_test: bool = False
    board_if_path_test_auto: bool = False
    program_micro_operational_fw: bool = False
    power_supply_off: bool = False
    # Test Parameters:
    micro_test_fw: str = ""
    micro_operational_fw: str = ""
    assy_type: str = ""
    assy_rev_no: str = ""
    assy_serial_no: str = ""
    assy_build_batch_no: str = ""
    hostname: str = ""
    psu_com_port: str = ""
    test_jig_com_port: str = ""
    digital_board_com_port: str = ""
    sig_gen_resource_name: str = ""
    csm_hostname: str = ""
    segger_jlink_win32: str = ""
    segger_jlink_win64: str = ""
    if_916_5_mhz_dbm: float = 0.0
    if_2310_mhz_dbm: float = 0.0
    if_2355_mhz_dbm: float = 0.0
    # Test Case Lists:
    cts_test_case_list = [
        # Tests are specified in the order needed for production
        "power_supply_on",
        "set_hw_config_info",
        # START - Require  Micro Test Utility
        "program_micro_test_fw",
        "board_adc_test",
        "board_temp_sensor_test",
        "board_mac_address_test",
        "board_ping_test",
        "board_pps_test",
        "board_loop_back_test",
        "board_if_path_test",
        "board_if_path_test_auto",
        # END - Require Micro Test Utility
        # START - Require Micro Operational Fw
        "program_micro_operational_fw",
        # END - Require Micro Operational Fw
        "power_supply_off"
    ]
    cts_csm_test_case_list = [
        # Tests are specified in the order needed for production
        # START - Require Board Powered and Linux Booted with platform test scripts installed
        "copy_test_scripts_to_csm",
        "update_operational_firmware_csm_uart",
        "get_cts_ip_address_csm",
        "set_unit_config_info",
        "tx_test",
        "rf_detector_calibration",
        "remove_test_scripts_from_csm"
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
