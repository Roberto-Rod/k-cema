#!/usr/bin/env python3
"""

Classes and functions implementing production test cases for:
- KT-000-0198-00 Display RCU Motherboard
- KT-000-0199-00 Fill Device Motherboard
- KT-950-0429-00 Display RCU Unit
- KT-950-0430-00 Fill Device Unit

Hardware/software compatibility:
- KT-000-0198-00 Display RCU Motherboard - Rev B.1 onwards
- KT-950-0429-00 Display RCU Unit - Rev B.1 onwards
- KT-956-0258-00 K-CEMA DRCU & FD Platform Test Scripts - v1.1.0 onwards
- KT-956-0262-00 K-CEMA DRCU & FD Test Jig Utility - v1.0.0 onwards
- KT-956-0376-00 K-CEMA DRCU Micro Operational Firmware - v1.1.3 onwards
- KT-956-0256-00 K-CEMA DRCU Micro Test Utility - v1.2.0 onwards
- KT-956-0xxx-00 K-CEMA DRCU SoM Software Package - v3.0.1.1-develop onwards

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
import zeroconf as zeroconfig

# Our own imports -------------------------------------------------
import drcu_fd_program_devices as dfpd
from drcu_plat_test_intf import DrcuFdPlatformTest, DrcuSomBitVoltages, FdSomBitVoltages, DrcuFunctionButtonState, \
    DrcuFunctionButtons, DrcuFdKeypadLedColours, FdKeypadButtons
from drcu_fd_test_jig_intf import DrcuFdTestJigInterface, DrcuFdTestJigGpoSignals
from drcu_micro_test_intf import DrcuMircoTestInterface, DrcuPoEPseType, DrcuGpoSignals, DrcuTamperChannels, \
    DrcuTamperChannelStatus, DrcuGpiSignals
from fd_micro_test_intf import FdMircoTestInterface, FdPoEPseType, FdGpoSignals, FdTamperChannels, \
    FdTamperChannelStatus, FdGpiSignals
from drcu_serial_msg_intf import DrcuSerialMsgInterface, DrcuButtonId
import rpi4_iperf3 as rpi4ip3
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
class DrcuFdUnitTypes(Enum):
    """ Enumeration class for 1PPS sources """
    DRCU = 0
    FILL_DEVICE = 1


class DrcuFdProdTestCommon:
    """
    Common test cases used for DRCU and FD testing.
    """
    def __init__(self, test_jig_com_port, unit_hostname,
                 segger_jlink_win32=None, segger_jlink_win64=None, iperf3=None, cygwin1_dll=None):
        """
        Class constructor, initialises common aspects of the test environment, call from child classes.
        :param test_jig_com_port: test jig NUCLEO STM32 COM port :type String
        :param unit_hostname: board/unit under test network hostname :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        # Test jig interface initialisation
        log.info("INFO - Initialising test jig interface")
        self._test_jig_com_port = test_jig_com_port
        with DrcuFdTestJigInterface(self._test_jig_com_port) as tji:
            # 1PPS EIA-485 bi-directional driver set to transmit mode
            tji.assert_gpo_signal(DrcuFdTestJigGpoSignals.CSM_1PPS_DIRECTION, True)
            # SoM system held in reset
            tji.assert_gpo_signal(DrcuFdTestJigGpoSignals.SOM_SYS_RESET, True)
            tji.assert_gpo_signal(DrcuFdTestJigGpoSignals.SOM_SD_BOOT_ENABLE, False)
        log.info("INFO - Test jig interface initialisation complete")

        # Store unit/board hostname for future use
        self._unit_username = "root"
        self._unit_hostname = unit_hostname
        # This is populated in the enable_som method
        self._unit_ip_address = None

        # Override exe path constants in csm_program_devices and win_ip3 modules if exe path variables have been passed
        if segger_jlink_win32 is not None:
            dfpd.JLINK_PATH_WIN32 = segger_jlink_win32
        if segger_jlink_win64 is not None:
            dfpd.JLINK_PATH_WIN64 = segger_jlink_win64
        if iperf3 is not None:
            winip3.IPERF3_EXECUTABLE = iperf3
        if cygwin1_dll is not None:
            winip3.CYGWIN_DLL = cygwin1_dll

    @staticmethod
    def program_micro(fw_bin):
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
        ret_val = dfpd.program_micro_device(fw_bin)
        log.info("{} - Program Microcontroller: {}".format("PASS" if ret_val else "FAIL", fw_bin))
        return ret_val

    def unit_som_bring_up(self, instruction_dialog_func, yesno_check_dialog_func, unit_type):
        """
        Bring up the unit  SoM:
        - Prompt the tester to connect the
        - Prompt the tester to confirm that the unit has started up
        - Try to ping the device, will only work if the SoM has come up
        - Get the SoM IP address to speed up future SSH connections to the unit
        Prerequisites:
        - None
        Uses:
        - None
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param yesno_check_dialog_func: reference to function that will pause execution and prompt the tester to confirm
        the success of an operation.
        :param unit_type: unit type of SoM that is being brought up :type DrcuFdUnitTypes
        :return: True if SoM bring up is successful, else False
        """
        log.info("")
        log.info("Unit SoM Bring Up:")

        instruction_dialog_func("Connect the unit's '{}'' Port to a PoE Power Injector.\n\n""Click OK to proceed."
                                "".format("CSM" if unit_type == DrcuFdUnitTypes else "FILL DEVICE"))

        if unit_type is DrcuFdUnitTypes.DRCU:
            ret_val = yesno_check_dialog_func("A number of software splash screens will be shown on the display.\n\n"
                                              "Click OK when the splash screens STOP UPDATING and a GRID is displayed "
                                              "on the screen with the text 'Loading...' appearing at the top of the "
                                              "screen.\n\nHas the unit booted as described?")
        elif unit_type is DrcuFdUnitTypes.FILL_DEVICE:
            ret_val = yesno_check_dialog_func("A number of software splash screens will be shown on the display.\n\n"
                                              "Click OK when the splash screens STOP UPDATING and the application is "
                                              "displayed on the screen.\n\nHas the unit booted as described?")

        # The unit serial no. may not have been set at this point so search for a single DRCU and assume that
        # this is the one to be tested.
        found_units = self.find_units(unit_type)
        if len(found_units) == 1:
            # Grab the IP address as this will be the quickest way to open an SSH connection
            self._unit_ip_address = found_units[0][1]
        else:
            raise RuntimeError("Unable to find a single {} unit - {}"
                               "".format("DRCU" if unit_type == DrcuFdUnitTypes.DRCU else "Fill Device", found_units))

        log.info("{} - Unit SoM Bring Up".format(self._pass_fail_string(ret_val)))
        return ret_val

    def enable_som(self, enable):
        """
        Utility method to enable/disable the SoM by releasing the test jig reset signal.
        :param enable: True to enable the SoM, False to disable it :type Boolean
        :return: True if the operation is successful, else False
        TODO: Make the ping timeouts based on time rather than number of ping attempts for consistency.
        """
        log.info("")
        log.info("{} SoM:".format("Enabling" if enable else "Disabling"))
        ret_val = True

        with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
            ret_val = dtji.assert_gpo_signal(DrcuFdTestJigGpoSignals.SOM_SYS_RESET, not enable) and ret_val
            # Give the SoM a few seconds to change state.
            time.sleep(5.0)

            if enable:
                # Ping the SoM, expecting success, retries gives the SoM ~1-minute to start up
                ping_timeout = time.time() + 60.0
                while time.time() < ping_timeout:
                    ping_success = self._ping(self._unit_hostname, retries=1)
                    if ping_success:
                        break
                    time.sleep(1.0)
                ret_val = ping_success and ret_val
                if ret_val:
                    ip_address = self._get_ip_address_from_hostname(self._unit_hostname)
                    self._unit_ip_address = ip_address if ip_address is not None else None
                # Give the SoM a few more seconds to finish booting.
                time.sleep(5.0)
            else:
                # Give the SoM a few more seconds to power-down.
                time.sleep(5.0)

                # Ping the SoM, expecting failure
                ping_timeout = time.time() + 20.0
                while time.time() < ping_timeout:
                    ping_success = self._ping(self._unit_hostname, retries=1)
                    if ping_success:
                        break
                    time.sleep(1.0)
                ret_val = not ping_success and ret_val

        log.info("{} - {} SoM".format(self._pass_fail_string(ret_val), "Enabling" if enable else "Disabling"))
        return ret_val

    def remove_test_scripts(self):
        """
        Remove the test scripts from the eMMC
        Prerequisites:
        - Board/Unit is powered and running Linux
        Uses:
        - DRCU/FD SSH connection
        :return: True if successful, else False
        TODO: do a Linux reset and wait for reboot to ensure the eMMC changes are flushed to disk.
        """
        log.info("")
        log.info("Removing Test Scripts from eMMC:")

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            ret_val = pt.remove_test_scripts()
        # Allow some time for the SoM to flush the eMMC
        time.sleep(10.0)

        # Pause to let the reboot start
        # log.info("INFO - Waiting for reboot...")
        # time.sleep(5.0)
        # # Ping the SoM, expecting success, retries gives the SoM ~1-minute to start up
        # for _ in range(0, 60):
        #     ping_success = self._ping(self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address,
        #                               retries=1)
        #     if ping_success:
        #         break
        #     time.sleep(1.0)
        # ret_val = ping_success and ret_val

        log.info("{} - Removed test scripts from SoM eMMC".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def copy_test_scripts_to_som(self, test_script_archive):
        """
        Copy the test scripts to the eMMC
        Prerequisites:
        - Board/Unit is powered and running Linux
        Uses:
        - DRCU/FD SSH connection
        :return: True if successful, else False
        """
        log.info("")
        log.info("Copying Test Scripts to eMMC:")

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            ret_val = pt.copy_test_scripts_to_som(test_script_archive)

        log.info("{} - Copied test scripts to SoM eMMC".format("PASS" if ret_val else "FAIL"))
        return ret_val

    def som_bring_up(self, instruction_dialog_func, unit_type):
        """
        Bring up the board SoM:
        - Prompt user to check SD Card is installed on the board under test
        - Release the SoM reset signal
        - Prompt the user to confirm that the board has started up
        - Try to ping the device, will only work if the software installation has been successful
        - Re-assert the SoM reset signal
        Prerequisites:
        - SD Card with DRCU/FD Debug Software Image
        Uses:
        - Test jig STM32 serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param unit_type: type of unit under test :type DrcuFdUnitTypes
        :return: True if SoM bring up is successful, else False
        """
        log.info("")
        log.info("SoM Bring Up:")
        ret_val = True

        if type(unit_type) is not DrcuFdUnitTypes:
            raise TypeError("unit_type is not DrcuFdUnitTypes")

        with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
            instruction_dialog_func("Check that an SD Card with the Debug Software Image is installed in the board "
                                    "under test SD Card holder.")
            for reset in [False, True, False]:
                ret_val = dtji.assert_gpo_signal(DrcuFdTestJigGpoSignals.SOM_SYS_RESET, reset) and ret_val
                time.sleep(1.0)

            time.sleep(3.0)

            if unit_type is DrcuFdUnitTypes.DRCU:
                instruction_dialog_func("A number of software installation/upgrade splash screens will be shown on the "
                                        "display.\n\n"
                                        "Click OK when the splash screens STOP UPDATING and a GREEN TICK is "
                                        "shown on the display.\n\n"
                                        "If the display does NOT come up in 30-seconds disconnect the CSM Ethernet "
                                        "cable on the test jig and then re-connect it.")
            elif unit_type is DrcuFdUnitTypes.FILL_DEVICE:
                instruction_dialog_func("A number of software installation/upgrade splash screens will be shown on the "
                                        "display.\n\n"
                                        "Click OK when the splash screen INSTALL FIRMWARE stops updating  and a YELLOW "
                                        "TICK is shown on the display.\n\n"
                                        "If the display does NOT come up in 30-seconds disconnect the FILL DEVICE "
                                        "Ethernet cable on the test jig and then re-connect it.")

            if unit_type is DrcuFdUnitTypes.DRCU:
                for _ in range(0, 3):
                    ping_success = self._ping(self._unit_hostname, retries=1)
                    if ping_success:
                        break
                    time.sleep(1.0)
                ret_val = ping_success and ret_val

            dtji.assert_gpo_signal(DrcuFdTestJigGpoSignals.SOM_SYS_RESET, True)
            time.sleep(5.0)

        log.info("{} - SoM Bring Up".format(self._pass_fail_string(ret_val)))
        return ret_val

    def unit_set_config_info(self, assy_type, assy_rev_no, assy_serial_no, assy_batch_no,
                             test_script_archive, instruction_dialog_func, unit_type):
        """
        Sets the unit under test's configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        Prerequisites:
        - Unit is powered and running Linux
        Uses:
        - DRCU/FD SSH connection
        :param test_script_archive: test script archive path :type String
        :param assy_type: board/unit assembly type :type String
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        tester to take an action
        :param unit_type: unit type to set config information for :type DrcuFdUnitTypes
        :return: True if configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Unit Configuration Information:")
        ret_val = True

        found_units = self.find_units(unit_type)
        if len(found_units) == 1:
            # Grab the IP address as this will be the quickest way to open an SSH connection
            ip_address = found_units[0][1]
        else:
            raise RuntimeError("Unable to find a single {} unit - {}".format(unit_type, found_units))

        with DrcuFdPlatformTest(self._unit_username, ip_address) as pt:
            ret_val = pt.copy_test_scripts_to_som(test_script_archive) and ret_val

            # Stop the application whilst we set the unit config information
            ret_val = pt.start_stop_application(False) and ret_val
            time.sleep(2.0)

            # Set configuration information
            ret_val = pt.set_config_info(assy_type, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val
            time.sleep(2.0)

            if ret_val:
                # Read back configuration information and check it is correct
                config_dict = pt.get_config_info(assy_type)

                test_pass = (config_dict.get("Assembly Part Number", "") == assy_type)
                log.info("{} - Assembly No set to {}".format(self._pass_fail_string(test_pass), assy_type))
                ret_val = test_pass and ret_val

                test_pass = (config_dict.get("Assembly Revision Number", "") == assy_rev_no)
                log.info("{} - Assembly Revision No set to {}".format(self._pass_fail_string(test_pass), assy_rev_no))
                ret_val = test_pass and ret_val

                test_pass = (config_dict.get("Assembly Serial Number", "") == assy_serial_no)
                log.info("{} - Assembly Serial No set to {}".format(self._pass_fail_string(test_pass), assy_serial_no))
                ret_val = test_pass and ret_val

                test_pass = (config_dict.get("Assembly Build Date/Batch Number", "") == assy_batch_no)
                log.info("{} - Assembly Batch No set to {}".format(self._pass_fail_string(test_pass), assy_batch_no))
                ret_val = test_pass and ret_val

            # Restart the application
            ret_val = pt.start_stop_application(True) and ret_val

            ret_val = pt.remove_test_scripts() and ret_val

        instruction_dialog_func("Disconnect the PoE Power Converter 'PWR + DATA OUT' Port to power-down the unit then "
                                "reconnect to change the hostname to the new unit serial number.\n\n"
                                "Wait for the unit to boot then click OK to proceed.")

        # Check we can find a unit with the configured serial number
        found_units = self.find_units(unit_type)
        test_pass = (len(found_units) == 1) and (assy_serial_no in found_units[0][0])
        log.info("{} - Found unit with hostname '{}-{}.local'"
                 "".format(self._pass_fail_string(test_pass),
                           "rcu" if unit_type == DrcuFdUnitTypes.DRCU else "fd",
                           assy_serial_no))

        if (len(found_units) == 1) and (assy_serial_no in found_units[0]):
            # Store the IP address to speed up future connections to the unit
            self._unit_ip_address = found_units[0][1]

        log.info("{} - Set unit configuration information".format(self._pass_fail_string(ret_val)))
        return ret_val

    def unit_tamper_test(self):
        """
        Test the unit under test tamper detect function.
        Prerequisites:
        - Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        - Unit lid is fitted
        Uses:
        - DRCU/FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit Tamper Detect Test")

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            # Stop the application whilst we set the unit config information
            ret_val = pt.start_stop_application(False)
            time.sleep(2.0)

            ret_val = pt.unit_tamper_bit_test() and ret_val

            # Restart the application
            ret_val = pt.start_stop_application(True) and ret_val

        log.info("{} - Unit Tamper Detect Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def rtc_test(self):
        """
        Test the anti-tamper IC real-time clock (RTC).
        Get 2x RTC readings 1.1-seconds apart and check that the values are not the same.
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        log.info("")
        log.info("Anti-Tamper RTC Test:")

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            at_rtc_1 = pt.get_tamper_device_rtc()
            time.sleep(1.1)
            at_rtc_2 = pt.get_tamper_device_rtc()

            ret_val = at_rtc_1 != "" and at_rtc_2 != "" and at_rtc_1 != at_rtc_2
            log.info("{} - Anti-Tamper RTC Test".format(self._pass_fail_string(ret_val)))

        return ret_val

    def som_ad7415_temp_sensor_test(self):
        """
        Tests the Board/Unit under test AD7415 temperature sensor.
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_lim_lo = 20
        test_lim_hi = 60

        log.info("")
        log.info("SoM AD7415 Test:")

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            temperature = pt.get_ad7415_temperature()
            ret_val = test_lim_lo <= temperature <= test_lim_hi
            log.info("{} - SoM AD7415 Test - Temperature {} <= {} <= {}".format(self._pass_fail_string(ret_val),
                                                                                test_lim_lo, temperature, test_lim_hi))
        return ret_val

    def som_nvme_test(self):
        """
        Test that the NVMe is connected to the Som:
        1 - check it is mounted using Linux dmesg command
        2 - check the temperature by reading the SMART interface
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_lim_lo = 20
        test_lim_hi = 60

        log.info("")
        log.info("SoM NVMe Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            # Check that the NVMe is mounted
            test_pass = pt.is_nvme_mounted()
            log.info("{} - Is NVMe Mounted Check".format(self._pass_fail_string(test_pass)))
            ret_val = test_pass and ret_val

            # Read the NVMe SMART temperature and check that is reasonable for ambient conditions
            temperature = pt.get_nvme_temperature()
            test_pass = test_lim_lo <= temperature <= test_lim_hi
            log.info("{} - SoM NVMe Temperature {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                                       test_lim_lo, temperature, test_lim_hi))
            ret_val = test_pass and ret_val

        log.info("{} - SoM NVMe  Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def check_for_sd_card(self):
        """
        Check if an SD Card is present, used for unit level testing where an SD Card should NOT be present
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if test passes, else False
        """
        log.info("")
        log.info("Check SD Card is NOT present:")
        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            ret_val = not pt.check_for_sd_card()
            log.info("{} - SD Card is NOT present".format("PASS" if ret_val else "FAIL"))

        return ret_val

    @staticmethod
    def find_units(unit_type, timeout=10):
        if unit_type not in DrcuFdUnitTypes:
            raise ValueError("unit_type is must be one of DrcuFdUnitTypes enumerated values")

        ret_val = []
        if unit_type is DrcuFdUnitTypes.DRCU:
            unit_type_str = "RCU-"
            type_str = "_rcu._tcp.local."
        elif unit_type is DrcuFdUnitTypes.FILL_DEVICE:
            unit_type_str = "KFD-"
            type_str = "_kfd._tcp.local."
        else:
            unit_type_str = "-"
            type_str = "_ssh._tcp.local."
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
            log.debug("Using hostname {} for ping rather than IP address - {}".format(ip_address, ex))
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
            log.debug("ping output: {}".format(output))

            if not output or "unreachable" in output or "0 packets received" in output or \
                    "could not find" in output or "Request timed out" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

    @staticmethod
    def _get_ip_address_from_hostname(hostname):
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


class DrcuProdTest(DrcuFdProdTestCommon):
    """
    Class that implements DRCU production test cases
    """
    _DRCU_MOTHERBOARD_NO = "KT-000-0198-00"
    _DRCU_ASSEMBLY_NO = "KT-950-0429-00"
    _MANAGED_SWITCH_DEFAULT_ENABLED_PORTS = [1, 2, 3, 4, 5, 6, 7, 8]

    def __init__(self, test_jig_com_port, csm_com_port, unit_hostname, gbe_switch_serial_port,
                 segger_jlink_win32=None, segger_jlink_win64=None, iperf3=None, cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param test_jig_com_port: test jig NUCLEO STM32 COM port :type String
        :param csm_com_port: board/unit under test CSM COM port :type String
        :param unit_hostname: board/unit under test network hostname :type String
        :param gbe_switch_serial_port: CSM serial port :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        # Call the base class constructor to initialise common aspects of the test environment
        super().__init__(test_jig_com_port, unit_hostname,
                         segger_jlink_win32, segger_jlink_win64, iperf3, cygwin1_dll)

        # Set test environment initial state
        log.info("INFO - Initialising test environment...")

        # Test environment serial ports
        self._drcu_csm_com_port = csm_com_port

        # Board/unit internal serial ports
        self._gbe_switch_serial_port = gbe_switch_serial_port

        log.info("INFO - Test environment initialisation complete")

    def __del__(self):
        """ Class destructor - Ensure the PSU is turned off """
        pass

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit """
        pass

    def discrete_op_test(self, instruction_dialog_func):
        """
        Tests the Power and Zeroise Power Enable discrete outputs from the DRCU, these signals are asserted
        by pressing and holding the Power and X buttons respectively.
        For each discrete:
        - check de-asserted
        - prompt tester to hold down button and check asserted
        - prompt tester to release button and check de-asserted
        Prerequisites:
        - None
        Uses:
        - Test jig STM32 serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if test passes, else False
        """
        log.info("")
        log.info("Discrete Output Test:")
        ret_val = True

        with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
            for output, button in [("POWER_BUTTON_N", "Power"), ("POWER_ENABLE_ZEROISE_N", "X")]:
                # Discrete outputs are active low
                test_pass = True

                # Check that the signal is NOT asserted
                cmd_success, gpi_signal_state = dtji.get_gpi_state()
                test_pass = (gpi_signal_state.get(output, -1) == 1) and cmd_success and test_pass

                instruction_dialog_func("PRESS AND HOLD the Keypad {} button then click on OK".format(button))

                # Check that the signal is asserted
                cmd_success, gpi_signal_state = dtji.get_gpi_state()
                test_pass = (gpi_signal_state.get(output, -1) == 0) and cmd_success and test_pass

                instruction_dialog_func("RELEASE the Keypad {} button then click on OK".format(button))

                # Check that the signal is NOT asserted
                cmd_success, gpi_signal_state = dtji.get_gpi_state()
                test_pass = (gpi_signal_state.get(output, -1) == 1) and cmd_success and test_pass

                log.info("{} - {} Discrete Output".format(self._pass_fail_string(test_pass), output))
                ret_val = test_pass and ret_val

        log.info("{} - Discrete Output Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def offboard_supply_rail_test(self):
        """
        Tests the power supply rails that are connected from the board
        Prerequisites:
        - Board is powered up
        Uses:
        - Test jig STM32 serial interface
        :return: True if test passes, else False
        """
        test_data = [
            # (rail, test_lim_lo_mv, test_lim_hi_mv)
            ("Xchange +12V (mV)", 11400, 12600)
        ]
        no_test_samples = 3

        log.info("")
        log.info("Off-board Supply Rail Test:")
        ret_val = True

        with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
            for sample_no in range(0, no_test_samples):
                cmd_success, adc_data = dtji.get_adc_data()
                ret_val = cmd_success and ret_val

                if cmd_success:
                    for rail, test_lim_lo_mv, test_lim_hi_mv in test_data:
                        test_mv = adc_data.get(rail, -1)
                        test_pass = (test_lim_lo_mv <= test_mv <= test_lim_hi_mv)
                        log.info("{} - Sample {} {}: {} <= {} <= {} mV".format(self._pass_fail_string(test_pass),
                                                                               sample_no, rail, test_lim_lo_mv, test_mv,
                                                                               test_lim_hi_mv))
                        ret_val = ret_val and test_pass

                time.sleep(1.0)

        log.info("{} - Off-board Supply Rail Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def poe_pd_pse_type_test(self):
        """
        Check the PoE Power Device Power Supply Equipment Type, expecting IEEE802.3bt Type 3 when connected to
        TP-Link TL-POE170S power injector.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        log.info("")
        log.info("PoE PD PSE Type Test:")

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            ret_val, poe_pd_pse_type = dmti.get_poe_pd_pse_type()

        log.info("INFO - PoE PD PSE Type {}".format(poe_pd_pse_type.name))
        ret_val = (poe_pd_pse_type == DrcuPoEPseType.IEEE802_3_BT_TYPE3) and ret_val
        log.info("{} - PoE PD PSE Type Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def set_hw_config_info(self, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board under test's hardware configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if hardware configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Hardware Configuration Information:")
        ret_val = True

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            # Reset the configuration information, ensures a new EEPROM is set up correctly
            ret_val = dmti.reset_hw_config_info() and ret_val
            log.info("{} - Reset configuration information".format(self._pass_fail_string(ret_val)))

            # Set the configuration information
            assy_part_no = self._DRCU_MOTHERBOARD_NO
            ret_val = dmti.set_hw_config_info(assy_part_no, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val
            cmd_success, hci = dmti.get_hw_config_info()

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

        log.info("{} - Set Hardware Configuration Information".format(self._pass_fail_string(ret_val)))
        return ret_val

    def batt_temp_sensor_test(self):
        """
        Read the battery temperature sensor and check the return value is "reasonable" for room ambient conditions.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        test_lim_lo = 15
        test_lim_hi = 60

        log.info("")
        log.info("Battery Temperature Sensor:")

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            batt_temp = dmti.get_battery_temperature()
            ret_val = test_lim_lo <= batt_temp <= test_lim_hi

        log.info("{} - Battery Temperature Sensor {} <= {} <= {} deg C".format(self._pass_fail_string(ret_val),
                                                                               test_lim_lo, batt_temp, test_lim_hi))
        return ret_val

    def board_pps_test(self):
        """
        Tests the test jig 1PPS is being received by the STM32 and that the test jig is receiving the Xchange 1PPS.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        - Test jig STM32 serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Board 1PPS Test:")
        ret_val = True

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
                # Disable test jig 1PPS and confirm 1PPS NOT detected
                log.info("INFO - 1PPS Source Disabled")
                ret_val = dtji.enable_pps_output(False) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = dmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected - Micro".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

                pps_detected, pps_delta = dmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected - Xchange".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

                # Enable test jig 1PPS and confirm 1PPS IS detected
                log.info("INFO - 1PPS Source Enabled")
                ret_val = dtji.enable_pps_output(True) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = dmti.get_pps_detected()
                log.info("{} - 1PPS detected {} ms - Micro".format(self._pass_fail_string(pps_detected), pps_delta))
                ret_val = pps_detected and ret_val

                pps_detected, pps_delta = dtji.get_pps_detected()
                log.info("{} - 1PPS detected {} ms - Xchange".format(self._pass_fail_string(pps_detected), pps_delta))
                ret_val = pps_detected and ret_val

                # Disable test jig 1PPS and confirm 1PPS NOT detected
                log.info("INFO - 1PPS Source Disabled")
                ret_val = dtji.enable_pps_output(False) and ret_val
                time.sleep(2.1)

                pps_detected, pps_delta = dmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected - Micro".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

                pps_detected, pps_delta = dmti.get_pps_detected()
                log.info("{} - 1PPS NOT detected - Xchange".format(self._pass_fail_string(not pps_detected)))
                ret_val = not pps_detected and ret_val

        log.info("{} - Board 1PPS Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def unit_pps_test(self, instruction_dialog_func, yesno_check_dialog_func):
        """
        Tests the test jig 1PPS is being received by the unit.
        Prerequisites:
        - Board is powered
        - Operational firmware loaded in the STM32 micro
        Uses:
        - Test Jig STM32 serial interface
        - STM32 CSM operational binary serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param yesno_check_dialog_func: reference to function that will pause execution and prompt the tester to confirm
        the success of an operation.
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit 1PPS Test:")
        ret_val = True

        with DrcuSerialMsgInterface(self._drcu_csm_com_port) as dsmi:
            with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
                # Enable the test jig 1PPS signal
                dtji.enable_pps_output(True)
                time.sleep(5.0)

                instruction_dialog_func("The 10x Unit Keypad LEDs will ALL Blink Green once every 6-seconds "
                                        "synchronised to the green LED on the Test Jig NUCLEO Board.")

                # Set the LEDs to full brightness
                ret_val = dsmi.send_set_led_brightness(255) and ret_val

                # Set all the LEDs OFF
                all_leds_list = list("OFF" for element in range(20))
                ret_val = dsmi.send_set_all_leds(all_leds_list) and ret_val

                # Set the green LEDs to BLINK_SYNC_START
                for i in range(0, 20, 2):
                    all_leds_list[i] = "BLINK_SYNC_START"
                ret_val = dsmi.send_set_all_leds(all_leds_list) and ret_val

                # Loop for 20-seconds so the tester has the opportunity to observe the LED blink patter
                for i in range(0, 20):
                    dsmi.send_ping()
                    time.sleep(1.0)

                # Disable the test jig 1PPS signal
                dtji.enable_pps_output(False)

                ret_val = yesno_check_dialog_func("Did the 10x Unit Keypad LEDs ALL Blink Green once every 6-seconds "
                                                  "synchronised to the green LED on the Test Jig NUCLEO Board?"
                                                  "") and ret_val

        log.info("{} - Unit 1PPS Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def xchange_reset_test(self):
        """
        Test the Xchange reset output from the board.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        - Test jig STM32 serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Xchange Reset Test:")
        ret_val = True

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
                for state in [False, True, False]:
                    ret_val = dmti.set_gpo_signal(DrcuGpoSignals.XCHANGE_RESET, state) and ret_val
                    time.sleep(0.1)
                    cmd_success, gpi_state = dtji.get_gpi_state()
                    ret_val = cmd_success and ret_val
                    if cmd_success:
                        test_pass = gpi_state.get("XCHANGE_RESET", -1) == (1 if state else 0)
                        log.info("{} - Xchange Reset {}".format(self._pass_fail_string(test_pass), (1 if state else 0)))
                        ret_val = test_pass and ret_val

        log.info("{} - Xchange Reset Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def som_supply_rail_test(self):
        """
        Test the SoM voltage supply rails.
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_sequence = [
            # (suppply_rail, lim_lo_mv, lim_hi_mv)
            (DrcuSomBitVoltages.VOLTAGE_12V, 11400, 12600),
            (DrcuSomBitVoltages.VOLTAGE_3V7, 3515, 3885),
            (DrcuSomBitVoltages.VOLTAGE_3V3, 3135, 3465),
            (DrcuSomBitVoltages.VOLTAGE_2V5, 2375, 2625),
            (DrcuSomBitVoltages.VOLTAGE_1V8, 1710, 1890),
            (DrcuSomBitVoltages.VOLTAGE_1V0, 950, 1050),
            (DrcuSomBitVoltages.VOLTAGE_VBAT, 2500, 5000),
            (DrcuSomBitVoltages.VOLTAGE_3V3_BAT, 3135, 3465),
            (DrcuSomBitVoltages.VOLTAGE_5V, 4750, 5250),
            (DrcuSomBitVoltages.VOLTAGE_6V7_DPY, 6365, 7035),
            (DrcuSomBitVoltages.VOLTAGE_15V_DPY, 14250, 15750),
            (DrcuSomBitVoltages.VOLTAGE_N6V7_DPY, -7035, -6365),
            (DrcuSomBitVoltages.VOLTAGE_N15V_DPY, -15750, -14250)
        ]

        log.info("")
        log.info("SoM Supply Rail Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            for supply_rail, test_lim_lo_mv, test_lim_hi_mv in test_sequence:
                test_mv = pt.get_drcu_bit_voltage(supply_rail)
                test_pass = (test_lim_lo_mv <= test_mv <= test_lim_hi_mv)
                log.info("{} - {}: {} <= {} <= {} mV".format(self._pass_fail_string(test_pass),
                                                             supply_rail.name, test_lim_lo_mv, test_mv, test_lim_hi_mv))
                ret_val = ret_val and test_pass

        log.info("{} - SoM Supply Rail Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def gbe_sw_connection_test(self):
        """
        Checks that all the connected GbE Switch ports have the connection status Up/GbE
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        # 1 = CSM Cu; 2 = FD; 3 = SoM
        uports = [1, 2, 3]

        log.info("")
        log.info("GbE Switch Connection Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            for uport in uports:
                # Expecting link state to be Up/GbE
                link_state = pt.get_gbe_sw_port_link_state(self._gbe_switch_serial_port, uport)
                test_pass = (link_state == "UP_GBE")
                log.info("{} - uPort {} link state {}".format("PASS" if test_pass else "FAIL", uport, link_state))
                ret_val = test_pass and ret_val

        log.info("{} - GbE Switch Connection Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def gbe_sw_bandwidth_test(self, duration_s=30, rpi4_ip6_address=""):
        """
        Performs a GbE Switch bandwidth test on the GbE Switch:
        1 - perform an iPerf3 bandwidth test for the specified number of seconds (default 30), expected tx/rx speed
            is >850 Mbps
        2 - check that uport under test GbE switch error counters are all zero
        3 - check that CSM uport GbE switch error counters are all zero (CSM is test entry port to GbE Switch)
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        # uPort: 1 = CSM Cu; 2 = FD; 3 = SoM
        test_sequence = [
            # (uport, iperf3_server, server_username, server_password_dict, ps_cmd)
            (2, rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address, rpi4ip3.RPI4_USERNAME,
             {rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address: rpi4ip3.RPI4_PASSWORD}, "ps aux"),
            (3, self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address,
             self._unit_username, None, "ps")
        ]
        error_counter_attrs = ["rx_crc_alignment", "rx_undersize", "rx_oversize", "rx_fragments", "rx_jabbers",
                               "rx_drops", "rx_classifier_drops", "tx_collisions", "tx_drops", "tx_overflow", "tx_aged"]

        log.info("")
        log.info("GbE Switch Bandwidth Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:

            # Ping the RPi4 to help the SSH client find it
            self._ping(rpi4ip3.RPI4_HOSTNAME if rpi4_ip6_address == "" else rpi4_ip6_address, retries=4)

            for uport, iperf3_server, server_username, server_password_dict, ps_cmd in test_sequence:
                # Start the Rpi4 iPerf3 server
                if rpi4ip3.start_iperf3_server(iperf3_server, server_username, server_password_dict, ps_cmd):
                    # Perform an iPerf3 bandwidth test and check that the tx/rx bandwidth is >850 Mbps
                    log.info("INFO - uPort {} starting iPerf3 test >850 Mbps - {} seconds".format(uport, duration_s))
                    tx_bps, rx_bps = winip3.iperf3_client_test(iperf3_server, duration_s)
                    test_pass = (tx_bps > 850e6) and (rx_bps > 850e6)
                    log.info("{} - GbE Bandwidth Test uPort {} Tx: {:.2f} Mbps; Rx: {:.2f} Mbps"
                             "".format(self._pass_fail_string(test_pass), uport, tx_bps / 1.0E6, rx_bps / 1.0E6))
                    ret_val = test_pass and ret_val
                else:
                    raise RuntimeError("Failed to start iPerf3 server!")

                # Expecting all the port error counters to be 0
                for test_uport in [uport, 1]:
                    log.info("INFO - Check uPort {} statistics:".format(test_uport))
                    port_stats = pt.get_gbe_sw_port_statistics(self._gbe_switch_serial_port, test_uport)
                    for error_counter_attr in error_counter_attrs:
                        attr_val = port_stats.get(error_counter_attr, -1)
                        test_pass = (attr_val == 0)
                        log.info("{} - GbE Statistics uPort {} {}: {}".format(
                                self._pass_fail_string(test_pass), test_uport, error_counter_attr, attr_val))
                        ret_val = test_pass and ret_val

        log.info("{} - GbE Switch Bandwidth Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def poe_pse_test(self):
        """
        Check the status of the PoE PSE device.
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        - AG5800 Evaluation Board connected to the Programming Port
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        test_lim_lo_v = 48.0
        test_lim_hi_v = 56.0
        expected_detection_status = "Resistance Good"

        log.info("")
        log.info("PoE PSE Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            poe_pse_status = pt.get_poe_pse_status()

            for port in ["port1", "port2"]:
                voltage = poe_pse_status.get(port, {}).get("voltage_value", 0.0)
                test_pass = (test_lim_lo_v <= voltage <= test_lim_hi_v)
                log.info("{} - {} Voltage: {} <= {} <= {}".format(self._pass_fail_string(test_pass),
                                                                  port, test_lim_lo_v, voltage, test_lim_hi_v))
                ret_val = ret_val and test_pass

                detection_status = poe_pse_status.get(port, {}).get("detection_status", "")
                test_pass = (detection_status == expected_detection_status)
                log.info("{} - {} Detection Status: {} == {}".format(self._pass_fail_string(test_pass),
                                                                     port, detection_status, expected_detection_status))
                ret_val = ret_val and test_pass

        log.info("{} - PoE PSE  Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_buzzer_test(self):
        """
        Board level buzzer test, makes use of the test jig ADC to check that the buzzer signal is asserted.
        Prerequisites:
        - Board is powered
        - Operational firmware loaded in the STM32 micro
        Uses:
        - STM32 CSM operational binary serial interface
        - Test jig STM32 serial interface
        :return: True if the test passes, else False :type Boolean
        """
        test_adc_rail = "Buzzer +12V (mV)"
        test_lim_lo_mv = 10500
        test_lim_hi_mv = 13500

        log.info("")
        log.info("Board-Level Buzzer Test:")
        ret_val = True

        with DrcuSerialMsgInterface(self._drcu_csm_com_port) as dsmi:
            with DrcuFdTestJigInterface(self._test_jig_com_port) as dtji:
                for buzzer_state in [False, True, False]:
                    test_pass = dsmi.send_set_buzzer_pattern("ON" if buzzer_state else "OFF")
                    time.sleep(1.0)
                    cmd_success, adc_data = dtji.get_adc_data()
                    test_pass = cmd_success and test_pass

                    if buzzer_state:
                        test_pass = (test_lim_lo_mv <= adc_data.get(test_adc_rail, 0) <= test_lim_hi_mv) and test_pass
                        log.info("{} - Buzzer Enabled - +12V: {} <= {} <= {} mV"
                                 "".format(self._pass_fail_string(test_pass),
                                           test_lim_lo_mv, adc_data.get(test_adc_rail, 0), test_lim_hi_mv))
                    else:
                        test_pass = (adc_data.get(test_adc_rail, 0) < test_lim_lo_mv) or \
                                    (adc_data.get(test_adc_rail, 0) > test_lim_hi_mv) and test_pass
                        log.info("{} - Buzzer Disabled - +12V: ({} < {}) OR ({} > {}) mV"
                                 "".format(self._pass_fail_string(test_pass), adc_data.get(test_adc_rail, 0),
                                           test_lim_lo_mv, adc_data.get(test_adc_rail, 0), test_lim_hi_mv))

                    ret_val = ret_val and test_pass

        log.info("{} - Board-Level Buzzer Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def unit_buzzer_test(self, yesno_check_dialog_func):
        """
        Test the unit under test buzzer.
        Prerequisites:
        - Board is powered
        - Operational firmware loaded in the STM32 micro
        Uses:
        - STM32 CSM operational binary serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Unit Buzzer Test:")
        ret_val = True

        with DrcuSerialMsgInterface(self._drcu_csm_com_port) as dsmi:
            # De-assert -> Assert -> De-assert the buzzer then check it sounded
            for buzzer_state in [False, True, False]:
                ret_val = dsmi.send_set_buzzer_pattern("ON" if buzzer_state else "OFF") and ret_val
                time.sleep(1.0)

            ret_val = yesno_check_dialog_func("Did the Unit Buzzer Sound?")

        log.info("{} - Unit Buzzer Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def function_button_test(self, instruction_dialog_func):
        """
        Test the Keypad function buttons.
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        log.info("")
        log.info("Function Button Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            # Check all the buttons are in the Released state
            log.info("INFO - Checking all buttons are in the Released state...")
            for button in DrcuFunctionButtons:
                button_state = pt.get_function_button_state(button)
                test_pass = (button_state == DrcuFunctionButtonState.RELEASED)
                log.info("{} - {} State {} - {}".format(self._pass_fail_string(test_pass), button.name,
                                                        DrcuFunctionButtonState.RELEASED, button_state))
                ret_val = test_pass and ret_val

            log.info("INFO - Checking buttons in the Held state...")
            for button in DrcuFunctionButtons:
                for button_test_state in [DrcuFunctionButtonState.HELD, DrcuFunctionButtonState.RELEASED]:
                    instruction_dialog_func("{} Keypad Button {} then press OK".format(
                        "RELEASE" if button_test_state == DrcuFunctionButtonState.RELEASED else "HOLD DOWN",
                        button.name))
                    time.sleep(0.5)

                    button_state = pt.get_function_button_state(button)
                    test_pass = (button_state == button_test_state)
                    log.info("{} - {} State {} - {}".format(self._pass_fail_string(test_pass), button.name,
                                                            button_test_state, button_state))
                    ret_val = test_pass and ret_val

        log.info("{} - Function Button Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def display_backlight_test(self, yesno_check_dialog_func):
        """
        Test the Display Backlight intensity can be changed, requires the tester to confirm that the backlight has
        changed state:
        - Set backlight PWM 0 (backlight off, screen dark)
        - Set backlight PWM 255 (backlight on, full brightness)
        - Set backlight PWM 20 (default, screen dim)
        :param yesno_check_dialog_func: reference to function that will pause execution and prompt the tester to confirm
        the success of an operation.
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - DRCU/FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        test_sequence = [
            # (brightness, expected_brightness_str)
            (0, "Off, Screen Dark"),
            (255, "Full Intensity, Screen Bright"),
            (20, "Default, Screen Dim")
        ]
        log.info("")
        log.info("Display Backlight Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            for brightness, expected_brightness_str in test_sequence:
                test_pass = pt.set_display_backlight(brightness)
                test_pass = yesno_check_dialog_func("Is the Display Backlight: {}?"
                                                    .format(expected_brightness_str)) and test_pass
                log.info("{} - Display Backlight - {}"
                         "".format(self._pass_fail_string(test_pass), expected_brightness_str))
                ret_val = test_pass and ret_val

        log.info("{} - Display Backlight Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def keypad_button_test(self, instruction_dialog_func):
        """
        Test the unit under test Keypad Button interface.
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        Prerequisites:
        - Board is powered
        - Operational firmware loaded in the STM32 micro
        Uses:
        - STM32 CSM operational binary serial interface
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Keypad Test:")
        ret_val = True

        with DrcuSerialMsgInterface(self._drcu_csm_com_port) as dsmi:
            for test_button in ["JAM", "EXCLAMATION", "X"]:
                instruction_dialog_func("PRESS and then RELEASE the Keypad '{}' Button followed by any button other "
                                        "than the Power button within 20-seconds.\n\nClick OK to proceed."
                                        "".format(test_button))

                test_timeout = time.time() + 20.0
                button_pressed = False
                button_released = False
                dsmi.smh.clear_rx_queue()

                while True:
                    time.sleep(0.001)
                    rx_msg = dsmi.smh.get_from_rx_queue()
                    if rx_msg:
                        button_status_msg, button_status = dsmi.unpack_button_status_message(rx_msg)

                        # If a button status message was received check for pressed and released states
                        if button_status_msg:
                            for button in button_status:
                                if button.get("button_id") == getattr(DrcuButtonId, test_button).value and \
                                        button.get("button_state"):
                                    log.debug("{} button pressed".format(test_button))
                                    button_pressed = True

                                if button.get("button_id") == getattr(DrcuButtonId, test_button).value and not\
                                        button.get("button_state"):
                                    log.debug("{} button released".format(test_button))
                                    button_released = True

                    if (button_pressed and button_released) or (time.time() > test_timeout):
                        break

                test_pass = button_pressed and button_released
                log.info("{} - '{}' Keypad Button Pressed".format(self._pass_fail_string(test_pass), test_button))
                ret_val = test_pass and ret_val

        log.info("{} - Unit Keypad Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def keypad_led_test(self, instruction_dialog_func, yesno_check_dialog_func):
        """
        Test the Keypad LEDs:
        - Set LED brightness to full
        - Flash all 10x LEDs in repeating colour pattern Green -> Red -> Yellow
        - Prompt tester to confirm that all the LEDs lit as expected
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param yesno_check_dialog_func: reference to function that will pause execution and prompt the tester to confirm
        the success of an operation.
        Prerequisites:
        - Board is powered
        - Operational firmware loaded in the STM32 micro
        Uses:
        - STM32 CSM operational binary serial interface
        :return: True if the test passes, else False :type Boolean
        """
        log.info("")
        log.info("Keypad LED Test:")

        with DrcuSerialMsgInterface(self._drcu_csm_com_port) as dsmi:
            instruction_dialog_func("The 10x Keypad LEDs will all now light at full brightness in the repeating "
                                    "colour pattern:\nGreen -> Red -> Yellow")

            dsmi.send_set_led_brightness(255)

            for _ in range(0, 2):
                log.info("INFO - LEDs Green..")
                dsmi.send_set_all_leds(["ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF",
                                        "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF"])
                time.sleep(1.0)

                log.info("INFO - LEDs Red..")
                dsmi.send_set_all_leds(["OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON",
                                        "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON", "OFF", "ON"])
                time.sleep(1.0)

                log.info("INFO - LEDs Yellow..")
                dsmi.send_set_all_leds(["ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON",
                                        "ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON", "ON"])
                time.sleep(1.0)

            ret_val = yesno_check_dialog_func("Did all 10x Keypad LEDs light?")

        log.info("{} - Keypad LED Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_case_switch_test(self, instruction_dialog_func):
        """
        Test the anti-tamper mechanical switch.
            - Ask user to hold down case switch
            - Arm sensor and check register status
            - Ask user to release case switch
            - Check registers for tamper detection
            - Disable sensor and check register status
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        - SoM is disabled as the test case needs to grab the shared I2C bus
        Uses:
        - Micro test utility serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        tester to take an action
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Board Case Tamper Switch (S13) Test:")
        ret_val = True

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            # Grab the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, True) and ret_val

            for channel in DrcuTamperChannels:
                # Ensure all tamper channels are disabled, set all the TEBx bits to '0'
                ret_val = dmti.set_anti_tamper_channel_enable(channel, False) and ret_val
                # Read the Flags registers to make sure nIRQ signals are cleared,
                # Flags register is shared so just check Channel 0
                ret_val = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_0) and ret_val

            instruction_dialog_func("Press and HOLD down the board under test case tamper switch, S13.\n\n"
                                    "Click OK to proceed.")
            # Arm the tamper sensor
            ret_val = dmti.set_anti_tamper_channel_enable(DrcuTamperChannels.CHANNEL_0, True) and ret_val

            # Check that the tamper channel status is ARMED_READY
            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.ARMED_READY and ret_val

            # Trigger the tamper sensor
            instruction_dialog_func("RELEASE the board under test case tamper switch, S13.\n\n"
                                    "Click OK to proceed.")

            # Check that the tamper channel status is TAMPERED
            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.TAMPERED and ret_val

            # Disable the tamper channel and check its status is reported correctly
            ret_val = dmti.set_anti_tamper_channel_enable(DrcuTamperChannels.CHANNEL_0, False) and ret_val

            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.DISABLED and ret_val

            # Release the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, False) and ret_val

        log.info("{} - Board Case Tamper Switch (S13) Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_light_sensor_test(self, instruction_dialog_func):
        """
        Test steps:
            - Ask user to cover light sensor
            - Arm sensor and check register status
            - Power-down the board under test using the test jig
            - Check powered-down by sending a command that will fail
            - Ask user to uncover light sensor
            - Check tamper status by reading registers, in battery mode IRQ is pulsed so this can't be read
            - De-assert ZER_PWR_HOLD to turn off zeroise micro, full command response not received so command fails
            - Power-on board under test using the test jig
            - Disable the sensor and check register status
        - Board is powered up
        - Micro test utility installed on board under test
        - SoM is disabled as the test case needs to grab the shared I2C bus
        Uses:
        - Micro test utility serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if test passes, else False
        TODO: Not fully testing the IRQ_TAMPER_N signal because of a hardware but, the SoC pulls this signal low
              when it is powered-down or held in reset.
        """
        log.info("")
        log.info("Board Light Sensor (Q7) Test:")
        ret_val = True

        with DrcuMircoTestInterface(self._drcu_csm_com_port) as dmti:
            # Grab the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, True) and ret_val

            for channel in DrcuTamperChannels:
                # Ensure all tamper channels are disabled, set all the TEBx bits to '0'
                ret_val = dmti.set_anti_tamper_channel_enable(channel, False) and ret_val
                # Read the Flags registers to make sure nIRQ signals are cleared,
                # Flags register is shared so just check Channel 0
                ret_val = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_0) and ret_val

            instruction_dialog_func("COVER the board under test light sensor, Q7")
            # Arm the tamper sensor
            ret_val = dmti.set_anti_tamper_channel_enable(DrcuTamperChannels.CHANNEL_1, True) and ret_val

            # Check that the tamper channel status is ARMED_READY
            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.ARMED_READY and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # Power-down the board under test
            # TODO: Need to clear ZER_PWR_HOLD because of hardware bug
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.ZER_PWR_HOLD, False) and ret_val
            instruction_dialog_func("DISCONNECT the Test Jig CSM RJ45 cable to power down the board under test.\n\n"
                                    "Click OK to proceed.")

            # Try to check the IRQ_TAMPER_N signal status - command WILL FAIL as the Zeroise Micro powered-down
            cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            ret_val = not cmd_success and ret_val

            instruction_dialog_func("UNCOVER the board under test light sensor, Q7.\n\n"
                                    "Click OK to proceed.")
            time.sleep(3.0)

            # Grab the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, True) and ret_val

            # Check that the tamper channel status is TAMPERED
            # Try to check the IRQ_TAMPER_N signal status - command WILL WORK as the Zeroise Micro is powered
            cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            ret_val = cmd_success and asserted and ret_val

            # Reading the tamper registers should de-assert IRQ_TAMPER_N
            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.TAMPERED and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # De-assert the ZER_PWR_HOLD signal
            dmti.set_gpo_signal(DrcuGpoSignals.ZER_PWR_HOLD, False)
            time.sleep(3.0)

            # Try to check the IRQ_TAMPER_N signal status - command WILL FAIL as the Zeroise Micro powered-down
            cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            ret_val = not cmd_success and ret_val

            # Power on the board under test
            instruction_dialog_func("CONNECT the Test Jig CSM RJ45 cable to power up the board under test.\n\n"
                                    "Click OK to proceed.")
            time.sleep(3.0)

            # Grab the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, True) and ret_val

            # Disable the tamper channel and check its status is reported correctly
            ret_val = dmti.set_anti_tamper_channel_enable(DrcuTamperChannels.CHANNEL_1, False) and ret_val

            cmd_success, status = dmti.get_tamper_channel_status(DrcuTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == DrcuTamperChannelStatus.DISABLED and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # Release the shared I2C bus
            ret_val = dmti.set_gpo_signal(DrcuGpoSignals.MICRO_I2C_EN, False) and ret_val

        log.info("{} - Board Light Sensor (Q7) Test".format(self._pass_fail_string(ret_val)))
        return ret_val


class DrcuProdTestInfo:
    """
    Utility class used to define the test info to be executed by the test thread class
    """
    # Test Cases:
    offboard_supply_rail_test: bool = False
    program_micro_test_fw: bool = False
    poe_pd_pse_type_test: bool = False
    set_hw_config_info: bool = False
    unit_set_config_info: bool = False
    batt_temp_sensor_test: bool = False
    board_pps_test: bool = False
    xchange_reset_test: bool = False
    board_case_switch_test: bool = False
    board_light_sensor_test: bool = False
    program_micro_operational_fw: bool = False
    som_bring_up: bool = False
    unit_som_bring_up: bool = False
    enable_som: bool = False
    disable_som: bool = False
    copy_test_scripts_to_som: bool = False
    remove_test_scripts: bool = False
    som_supply_rail_test: bool = False
    som_ad7415_temp_sensor_test: bool = False
    som_nvme_test: bool = False
    gbe_sw_connection_test: bool = False
    gbe_sw_bandwidth_test: bool = False
    unit_tamper_test: bool = False
    poe_pse_test: bool = False
    rtc_test: bool = False
    board_buzzer_test: bool = False
    function_button_test: bool = False
    discrete_op_test: bool = False
    display_backlight_test: bool = False
    keypad_button_test: bool = False
    unit_buzzer_test: bool = False
    unit_pps_test: bool = False
    check_for_sd_card: bool = False
    keypad_led_test: bool = False
    # Test Parameters:
    micro_test_fw: str = ""
    micro_operational_fw: str = ""
    platform_test_scripts: str = ""
    assy_type: str = ""
    assy_rev_no: str = ""
    assy_serial_no: str = ""
    assy_build_batch_no: str = ""
    hostname: str = ""
    test_jig_com_port: str = ""
    csm_com_port: str = ""
    segger_jlink_win32: str = ""
    segger_jlink_win64: str = ""
    flash_pro: str = ""
    iperf3: str = ""
    cygwin1_dll: str = ""
    # Test Case Lists:
    test_case_list = [
        # Tests are specified in the order needed for production
        "disable_som",
        "offboard_supply_rail_test",
        # START - Require  Micro Test Utility
        "program_micro_test_fw",
        "poe_pd_pse_type_test",
        "set_hw_config_info",
        "batt_temp_sensor_test",
        "board_pps_test",
        "xchange_reset_test",
        "board_case_switch_test",
        "board_light_sensor_test",
        # END - Require Micro Test Utility
        # START - Require Micro Operational Fw
        "program_micro_operational_fw",
        # START - Require SoM Programmed
        "som_bring_up",
        "unit_som_bring_up",
        "unit_set_config_info",
        # START - Require Board/Unit Powered and Linux Booted with platform test scripts installed
        "enable_som",
        "copy_test_scripts_to_som",
        "som_supply_rail_test",
        "function_button_test",
        "discrete_op_test",
        "display_backlight_test",
        "keypad_button_test",
        "unit_buzzer_test",
        "unit_pps_test",
        "check_for_sd_card",
        "keypad_led_test",
        "som_ad7415_temp_sensor_test",
        "som_nvme_test",
        "gbe_sw_connection_test",
        "gbe_sw_bandwidth_test",
        "unit_tamper_test",
        "poe_pse_test",
        "rtc_test",
        "board_buzzer_test",
        "remove_test_scripts",
        # END - Require Board/Unit Powered and Linux Booted with platform test scripts installed
        "disable_som",
        # END - Require SoM Programmed
        # END - Require Micro Operational Fw
    ]


class FdProdTest(DrcuFdProdTestCommon):
    """
    Class that implements Fill-Device production test cases
    """
    _FD_MOTHERBOARD_NO = "KT-000-0199-00"
    _FD_ASSEMBLY_NO = "KT-950-0431-00"

    def __init__(self, test_jig_com_port, fd_com_port, soc_console_com_port, unit_hostname,
                 segger_jlink_win32=None, segger_jlink_win64=None, iperf3=None, cygwin1_dll=None):
        """
        Class constructor - Sets the test environment initial state
        :param test_jig_com_port: test jig NUCLEO STM32 COM port :type String
        :param fd_com_port: board/unit under test Fill-Device COM port :type String
        :param soc_console_com_port: test jig SoC Console CON port :type String
        :param unit_hostname: board/unit under test network hostname :type String
        :param segger_jlink_win32: 32-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param segger_jlink_win64: 64-bit Win Segger J-Link exe path, default is None, use drcu_program_devices constant
        :param iperf3: iPerf3 exe path, default is None, use win_iperf3 constant
        :param cygwin1_dll: cygwin1 DLL path, default is None, use win_iperf3 constant
        """
        # Call the base class constructor to initialise common aspects of the test environment
        super().__init__(test_jig_com_port, unit_hostname,
                         segger_jlink_win32, segger_jlink_win64, iperf3, cygwin1_dll)

        # Set test environment initial state
        log.info("INFO - Initialising test environment...")

        # Test environment serial ports
        self._fd_com_port = fd_com_port
        self._soc_console_com_port = soc_console_com_port

        log.info("INFO - Test environment initialisation complete")

    def __del__(self):
        """ Class destructor """
        pass

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit """
        pass

    def poe_pd_pse_type_test(self):
        """
        Check the PoE Power Device Power Supply Equipment Type, expecting IEEE802.3bt Type 3 when connected to
        TP-Link TL-POE170S power injector.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        log.info("")
        log.info("PoE PD PSE Type Test:")

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            ret_val, poe_pd_pse_type = fmti.get_poe_pd_pse_type()

        log.info("INFO - PoE PD PSE Type {}".format(poe_pd_pse_type.name))
        ret_val = (poe_pd_pse_type == FdPoEPseType.IEEE802_3_BT_TYPE3) and ret_val
        log.info("{} - PoE PD PSE Type Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def set_hw_config_info(self, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board under test's hardware configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if hardware configuration information set correctly, else False :type Boolean
        """
        log.info("")
        log.info("Set Hardware Configuration Information:")
        ret_val = True

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            # Reset the configuration information, ensures a new EEPROM is set up correctly
            ret_val = fmti.reset_hw_config_info() and ret_val
            log.info("{} - Reset configuration information".format(self._pass_fail_string(ret_val)))

            # Set the configuration information
            assy_part_no = self._FD_MOTHERBOARD_NO
            ret_val = fmti.set_hw_config_info(assy_part_no, assy_rev_no, assy_serial_no, assy_batch_no) and ret_val
            cmd_success, hci = fmti.get_hw_config_info()

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

        log.info("{} - Set Hardware Configuration Information".format(self._pass_fail_string(ret_val)))
        return ret_val

    def batt_temp_sensor_test(self):
        """
        Read the battery temperature sensor and check the return value is "reasonable" for room ambient conditions.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        test_lim_lo = 15
        test_lim_hi = 60

        log.info("")
        log.info("Battery Temperature Sensor:")

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            batt_temp = fmti.get_battery_temperature()
            ret_val = test_lim_lo <= batt_temp <= test_lim_hi

        log.info("{} - Battery Temperature Sensor {} <= {} <= {} deg C".format(self._pass_fail_string(ret_val),
                                                                               test_lim_lo, batt_temp, test_lim_hi))
        return ret_val

    def pvbat_monitor_test(self):
        """
        Read the STM32 VBAT monitor ADC channel and check that the voltage is within expected limits.
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        Uses:
        - Micro test utility serial interface
        :return: True if test passes, else False
        """
        test_lim_lo_mv = 2500
        test_lim_hi_mv = 5000

        log.info("")
        log.info("STM32 VBAT Monitor Test:")

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            vbat_mv = fmti.get_vbat_monitor_mv()
            ret_val = test_lim_lo_mv <= vbat_mv <= test_lim_hi_mv

        log.info("{} - STM32 VBAT Monitor {} <= {} <= {} mV".format(self._pass_fail_string(ret_val),
                                                                    test_lim_lo_mv, vbat_mv, test_lim_hi_mv))
        return ret_val

    def som_supply_rail_test(self):
        """
        Test the SoM voltage supply rails.
        Prerequisites:
        - Board/Unit is powered and running Linux
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        test_sequence = [
            # (suppply_rail, lim_lo_mv, lim_hi_mv)
            (FdSomBitVoltages.VOLTAGE_12V, 11400, 12600),
            (FdSomBitVoltages.VOLTAGE_3V7, 3515, 3885),
            (FdSomBitVoltages.VOLTAGE_3V3, 3135, 3465),
            (FdSomBitVoltages.VOLTAGE_1V8, 1710, 1890),
            (FdSomBitVoltages.VOLTAGE_VBAT, 2500, 5000),
            (FdSomBitVoltages.VOLTAGE_3V3_BAT, 3135, 3465),
            (FdSomBitVoltages.VOLTAGE_5V, 4750, 5250)
        ]

        log.info("")
        log.info("")
        log.info("SoM Supply Rail Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            for supply_rail, test_lim_lo_mv, test_lim_hi_mv in test_sequence:
                test_mv = pt.get_fd_bit_voltage(supply_rail)
                test_pass = (test_lim_lo_mv <= test_mv <= test_lim_hi_mv)
                log.info("{} - {}: {} <= {} <= {} mV".format(self._pass_fail_string(test_pass),
                                                             supply_rail.name, test_lim_lo_mv, test_mv, test_lim_hi_mv))
                ret_val = ret_val and test_pass

        log.info("{} - SoM Supply Rail Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def gbe_bandwidth_test(self, duration_s=30):
        """
        Performs an iPerf3 bandwidth test to the SoM for the specified number of seconds (default 30), expected tx/rx
        speed is >850 Mbps.
        Prerequisites:
        - Board/Unit is powered and running Linux
        Uses:
        - Fill Device SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        # uPort: 1 = CSM Cu; 2 = FD; 3 = SoM
        test_sequence = [
            # (iperf3_server, server_username, server_password_dict, ps_cmd)
            (self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address, self._unit_username,
             None, "ps")
        ]

        log.info("")
        log.info("GbE Bandwidth Test:")
        ret_val = True

        for iperf3_server, server_username, server_password_dict, ps_cmd in test_sequence:
            # Start the iPerf3 server
            if rpi4ip3.start_iperf3_server(iperf3_server, server_username, server_password_dict, ps_cmd):
                # Perform an iPerf3 bandwidth test and check that the tx/rx bandwidth is >850 Mbps
                log.info("INFO - starting iPerf3 test >850 Mbps - {} seconds".format(duration_s))
                tx_bps, rx_bps = winip3.iperf3_client_test(iperf3_server, duration_s)
                test_pass = (tx_bps > 850e6) and (rx_bps > 850e6)
                log.info("{} - GbE Bandwidth Test Tx: {:.2f} Mbps; Rx: {:.2f} Mbps"
                         "".format(self._pass_fail_string(test_pass), tx_bps / 1.0E6, rx_bps / 1.0E6))
                ret_val = test_pass and ret_val
            else:
                raise RuntimeError("Failed to start iPerf3 server!")

        log.info("{} - GbE Bandwidth Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def fd_uart_test(self):
        """
        Test the external EIA-422 UART.  Send a string and check it is echoed, relies on the SoM terminal being
        routed to the external EIA-422 UART.
        Prerequisites:
        - Board is powered and the SoM is running Linux
        Uses:
        - FD EIA-422 UART
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Fill Device UART Test:")

        with Serial(self._fd_com_port, 115200, timeout=3.0, xonxoff=False, rtscts=False, dsrdtr=False) as s:
            test_string = b"The quick brown fox jumps over the lazy dog"
            s.write(test_string)
            resp_str = s.read_until(test_string)
            ret_val = test_string in resp_str

        log.info("{} - Fill Device UART Test".format(self._pass_fail_string(ret_val)))

        return ret_val

    def keypad_button_test(self, instruction_dialog_func):
        """
        Test the unit under test Keypad Button interface.
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        Prerequisites:
        - Board is powered
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - FD SSH connection
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Keypad Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:

            # Stop the application whilst we use the UART to talk to the STM32 from the SoM
            ret_val = pt.start_stop_application(False) and ret_val
            time.sleep(1.0)

            for test_button in [FdKeypadButtons.UP_ARROW, FdKeypadButtons.X, FdKeypadButtons.DOWN_ARROW]:
                instruction_dialog_func("PRESS and then RELEASE the Keypad '{}' Button followed by any button other "
                                        "within 10-seconds after clicking OK.\n\nClick OK to proceed."
                                        "".format(test_button.name))

                test_pass = pt.fd_check_for_keypad_button_press(test_button)
                log.info("{} - '{}' Keypad Button Pressed".format(self._pass_fail_string(test_pass), test_button.name))
                ret_val = test_pass and ret_val

            # Restart the application
            ret_val = pt.start_stop_application(True) and ret_val

        log.info("{} - Unit Keypad Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def keypad_led_test(self, instruction_dialog_func, yesno_check_dialog_func):
        """
        Test the Keypad LEDs:
        - Flash all 3x LEDs in repeating colour pattern Green -> Red -> Yellow
        - Prompt tester to confirm that all the LEDs lit as expected
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :param yesno_check_dialog_func: reference to function that will pause execution and prompt the tester to confirm
        the success of an operation.
        Prerequisites:
        - Board is powered
        - Platform test scripts are in folder /home/root/test on SoM
        Uses:
        - FD SSH connection
        :return: True if the test passes, else False :type Boolean
        """
        log.info("")
        log.info("Keypad LED Test:")
        ret_val = True

        with DrcuFdPlatformTest(self._unit_username,
                                self._unit_hostname if self._unit_ip_address is None else self._unit_ip_address) as pt:
            # Stop the application whilst we use the UART to talk to the STM32 from the SoM
            ret_val = pt.start_stop_application(False) and ret_val

            instruction_dialog_func("The 3x Keypad LEDs will all now light at full brightness in the repeating "
                                    "colour pattern:\nGreen -> Red -> Yellow")

            for _ in range(0, 2):
                log.info("INFO - LEDs Green..")
                ret_val = pt.fd_set_all_keypad_leds(DrcuFdKeypadLedColours.GREEN) and ret_val

                log.info("INFO - LEDs Red..")
                ret_val = pt.fd_set_all_keypad_leds(DrcuFdKeypadLedColours.RED) and ret_val

                log.info("INFO - LEDs Yellow..")
                ret_val = pt.fd_set_all_keypad_leds(DrcuFdKeypadLedColours.YELLOW) and ret_val

            # Restart the application
            ret_val = pt.start_stop_application(True) and ret_val

            ret_val = yesno_check_dialog_func("Did all 3x Keypad LEDs light each colour?") and ret_val

        log.info("{} - Keypad LED Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_case_switch_test(self, instruction_dialog_func):
        """
        Test the anti-tamper mechanical switch.
            - Ask user to hold down case switch
            - Arm sensor and check register status
            - Ask user to release case switch
            - Check registers for tamper detection
            - Disable sensor and check register status
        Prerequisites:
        - Board is powered up
        - Micro test utility installed on board under test
        - SoM is disabled as the test case needs to grab the shared I2C bus
        Uses:
        - Micro test utility serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        tester to take an action
        :return: True if test passes, else False :type Boolean
        """
        log.info("")
        log.info("Board Case Tamper Switch (S4) Test:")
        ret_val = True

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            # Grab the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, True) and ret_val

            for channel in FdTamperChannels:
                # Ensure all tamper channels are disabled, set all the TEBx bits to '0'
                ret_val = fmti.set_anti_tamper_channel_enable(channel, False) and ret_val
                # Read the Flags registers to make sure nIRQ signals are cleared,
                # Flags register is shared so just check Channel 0
                ret_val = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_0) and ret_val

            instruction_dialog_func("Press and HOLD down the board under test case tamper switch, S4.\n\n"
                                    "Click OK to proceed.")
            # Arm the tamper sensor
            ret_val = fmti.set_anti_tamper_channel_enable(FdTamperChannels.CHANNEL_0, True) and ret_val

            # Check that the tamper channel status is ARMED_READY
            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == FdTamperChannelStatus.ARMED_READY and ret_val

            # Trigger the tamper sensor
            instruction_dialog_func("RELEASE the board under test case tamper switch, S4.\n\n"
                                    "Click OK to proceed.")

            # Check that the tamper channel status is TAMPERED
            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == FdTamperChannelStatus.TAMPERED and ret_val

            # Disable the tamper channel and check its status is reported correctly
            ret_val = fmti.set_anti_tamper_channel_enable(FdTamperChannels.CHANNEL_0, False) and ret_val

            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_0)
            ret_val = cmd_success and status == FdTamperChannelStatus.DISABLED and ret_val

            # Release the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, False) and ret_val

        log.info("{} - Board Case Tamper Switch (S4) Test".format(self._pass_fail_string(ret_val)))
        return ret_val

    def board_light_sensor_test(self, instruction_dialog_func):
        """
        Test steps:
            - Ask user to cover light sensor
            - Arm sensor and check register status
            - Power-down the board under test using the test jig
            - Check powered-down by sending a command that will fail
            - Ask user to uncover light sensor
            - Check tamper status by reading registers, in battery mode IRQ is pulsed so this can't be read
            - De-assert ZER_PWR_HOLD to turn off zeroise micro, full command response not received so command fails
            - Power-on board under test using the test jig
            - Disable the sensor and check register status
        - Board is powered up
        - Micro test utility installed on board under test
        - SoM is disabled as the test case needs to grab the shared I2C bus
        Uses:
        - Micro test utility serial interface
        :param instruction_dialog_func: reference to function that will pause execution and prompt the
        user to take an action
        :return: True if test passes, else False
        TODO: Not fully testing the IRQ_TAMPER_N signal because of a hardware but, the SoC pulls this signal low
              when it is powered-down or held in reset.
        """
        log.info("")
        log.info("Board Light Sensor (Q4) Test:")
        ret_val = True

        with FdMircoTestInterface(self._soc_console_com_port) as fmti:
            # Grab the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, True) and ret_val

            for channel in FdTamperChannels:
                # Ensure all tamper channels are disabled, set all the TEBx bits to '0'
                ret_val = fmti.set_anti_tamper_channel_enable(channel, False) and ret_val
                # Read the Flags registers to make sure nIRQ signals are cleared,
                # Flags register is shared so just check Channel 0
                ret_val = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_0) and ret_val

            instruction_dialog_func("COVER the board under test light sensor, Q4")
            # Arm the tamper sensor
            ret_val = fmti.set_anti_tamper_channel_enable(FdTamperChannels.CHANNEL_1, True) and ret_val

            # Check that the tamper channel status is ARMED_READY
            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == FdTamperChannelStatus.ARMED_READY and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # Power-down the board under test
            # TODO: Need to clear ZER_PWR_HOLD because of hardware bug
            ret_val = fmti.set_gpo_signal(FdGpoSignals.ZER_PWR_HOLD, False) and ret_val
            instruction_dialog_func("DISCONNECT the Test Jig FILL DEVICE RJ45 cable to power down the board under test."
                                    "\n\nClick OK to proceed.")

            # Try to check the IRQ_TAMPER_N signal status - command WILL FAIL as the Zeroise Micro powered-down
            cmd_success, asserted = fmti.get_gpi_signal_asserted(FdGpiSignals.IRQ_TAMPER_N)
            ret_val = not cmd_success and ret_val

            instruction_dialog_func("UNCOVER the board under test light sensor, Q4.\n\n"
                                    "Click OK to proceed.")
            time.sleep(5.0)

            # Grab the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, True) and ret_val

            # Check that the tamper channel status is TAMPERED
            # Try to check the IRQ_TAMPER_N signal status - command WILL WORK as the Zeroise Micro is powered
            cmd_success, asserted = fmti.get_gpi_signal_asserted(FdGpiSignals.IRQ_TAMPER_N)
            ret_val = cmd_success and asserted and ret_val

            # Reading the tamper registers should de-assert IRQ_TAMPER_N
            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == FdTamperChannelStatus.TAMPERED and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = fmti.get_gpi_signal_asserted(FdGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # De-assert the ZER_PWR_HOLD signal
            fmti.set_gpo_signal(FdGpoSignals.ZER_PWR_HOLD, False)
            time.sleep(3.0)

            # Try to check the IRQ_TAMPER_N signal status - command WILL FAIL as the Zeroise Micro powered-down
            cmd_success, asserted = fmti.get_gpi_signal_asserted(FdGpiSignals.IRQ_TAMPER_N)
            ret_val = not cmd_success and ret_val

            # Power on the board under test
            instruction_dialog_func("CONNECT the Test Jig FILL DEVICE RJ45 cable to power up the board under test.\n\n"
                                    "Click OK to proceed.")
            time.sleep(3.0)

            # Grab the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, True) and ret_val

            # Disable the tamper channel and check its status is reported correctly
            ret_val = fmti.set_anti_tamper_channel_enable(FdTamperChannels.CHANNEL_1, False) and ret_val

            cmd_success, status = fmti.get_tamper_channel_status(FdTamperChannels.CHANNEL_1)
            ret_val = cmd_success and status == FdTamperChannelStatus.DISABLED and ret_val

            # Check that the IRQ_TAMPER_N signal is NOT asserted
            # TODO: Can't do this because of hardware bug
            # cmd_success, asserted = dmti.get_gpi_signal_asserted(DrcuGpiSignals.IRQ_TAMPER_N)
            # ret_val = cmd_success and not asserted and ret_val

            # Release the shared I2C bus
            ret_val = fmti.set_gpo_signal(FdGpoSignals.MICRO_I2C_EN, False) and ret_val

        log.info("{} - Board Light Sensor (Q4) Test".format(self._pass_fail_string(ret_val)))
        return ret_val


class FdProdTestInfo:
    """
    Utility class used to define the test info to be executed by the test thread class
    """
    # Test Cases:
    program_micro_test_fw: bool = False
    poe_pd_pse_type_test: bool = False
    set_hw_config_info: bool = False
    unit_set_config_info: bool = False
    batt_temp_sensor_test: bool = False
    pvbat_monitor_test: bool = False
    board_case_switch_test: bool = False
    board_light_sensor_test: bool = False
    program_micro_operational_fw: bool = False
    som_bring_up: bool = False
    unit_som_bring_up: bool = False
    enable_som: bool = False
    disable_som: bool = False
    copy_test_scripts_to_som: bool = False
    remove_test_scripts: bool = False
    som_supply_rail_test: bool = False
    som_ad7415_temp_sensor_test: bool = False
    som_nvme_test: bool = False
    gbe_bandwidth_test: bool = False
    fd_uart_test: bool = False
    unit_tamper_test: bool = False
    rtc_test: bool = False
    keypad_button_test: bool = False
    check_for_sd_card: bool = False
    keypad_led_test: bool = False
    # Test Parameters:
    micro_test_fw: str = ""
    micro_operational_fw: str = ""
    platform_test_scripts: str = ""
    assy_type: str = ""
    assy_rev_no: str = ""
    assy_serial_no: str = ""
    assy_build_batch_no: str = ""
    hostname: str = ""
    test_jig_com_port: str = ""
    fd_com_port: str = ""
    soc_console_com_port: str = ""
    segger_jlink_win32: str = ""
    segger_jlink_win64: str = ""
    flash_pro: str = ""
    iperf3: str = ""
    cygwin1_dll: str = ""
    # Test Case Lists:
    test_case_list = [
        # Tests are specified in the order needed for production
        "disable_som",
        # START - Require  Micro Test Utility
        "program_micro_test_fw",
        "poe_pd_pse_type_test",
        "set_hw_config_info",
        "batt_temp_sensor_test",
        "pvbat_monitor_test",
        "board_case_switch_test",
        "board_light_sensor_test",
        # END - Require Micro Test Utility
        # START - Require Micro Operational Fw
        "program_micro_operational_fw",
        # START - Require SoM Programmed
        "som_bring_up",
        "unit_som_bring_up",
        "unit_set_config_info",
        # START - Require Board/Unit Powered and Linux Booted with platform test scripts installed
        "enable_som",
        "copy_test_scripts_to_som",
        "som_supply_rail_test",
        "keypad_button_test",
        "keypad_led_test",
        "check_for_sd_card",
        "som_ad7415_temp_sensor_test",
        "som_nvme_test",
        "gbe_bandwidth_test",
        "fd_uart_test",
        "unit_tamper_test",
        "rtc_test",
        "remove_test_scripts",
        # END - Require Board/Unit Powered and Linux Booted with platform test scripts installed
        "disable_som",
        # END - Require SoM Programmed
        # END - Require Micro Operational Fw
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
