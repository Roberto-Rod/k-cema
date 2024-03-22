#!/usr/bin/env python3
"""
Class that provides an interface for executing DRCU Platform Test scripts,
KT-956-0258-00 test scripts via SSH.

Prerequisites:
- DRCU Platform Test Script installed in folder "/home/root/test" on
  the KT-000-0198-00 board.

Software compatibility:
- KT-956-0258-00 K-CEMA DRCU Platform Test Scripts v1.1.0 onwards
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
import json
import logging
from os import popen
import platform

# Third-party imports -----------------------------------------------
from ssh import SSH

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
class DrcuSomBitVoltages(Enum):
    VOLTAGE_12V = 0
    VOLTAGE_3V7 = 1
    VOLTAGE_3V3 = 2
    VOLTAGE_2V5 = 3
    VOLTAGE_1V8 = 4
    VOLTAGE_1V0 = 5
    VOLTAGE_VBAT = 6
    VOLTAGE_3V3_BAT = 7
    VOLTAGE_5V = 8
    VOLTAGE_6V7_DPY = 9
    VOLTAGE_15V_DPY = 10
    VOLTAGE_N6V7_DPY = 11
    VOLTAGE_N15V_DPY = 12


class FdSomBitVoltages(Enum):
    VOLTAGE_12V = 0
    VOLTAGE_3V7 = 1
    VOLTAGE_3V3 = 2
    VOLTAGE_1V8 = 3
    VOLTAGE_VBAT = 5
    VOLTAGE_3V3_BAT = 6
    VOLTAGE_5V = 7


class DrcuFunctionButtons(Enum):
    F1 = 0
    F2 = 1
    F3 = 2
    F4 = 3
    F5 = 4
    F6 = 5
    F7 = 6
    F8 = 7


class DrcuFunctionButtonState(Enum):
    UNKNOWN = 0
    HELD = 1
    RELEASED = 2


class DrcuFdKeypadLedColours(Enum):
    GREEN = 0
    RED = 1
    YELLOW = 2


class FdKeypadButtons(Enum):
    UP_ARROW = 0
    X = 1
    DOWN_ARROW = 2


class DrcuFdPlatformTest:
    PYTHON_PATH = "python3"
    DRCU_TEST_SCRIPT_PATH = "/home/root/test/"
    READ_AD7415_TEMP_CMD = "ad7415_temp_sensor.py"
    READ_SOC_TEMP_CMD = "imx8m_temp_sensor.py"
    READ_GBE_SW_TEMP_CMD = "gbe_switch.py -c {} -t"
    READ_GBE_SW_PORT_LINK_STATE_CMD = "gbe_switch.py -c {} -p {}"
    READ_GBE_SW_PORT_STATISTICS_CMD = "gbe_switch.py -c {} -s {}"
    READ_POE_PSE_TEMP_CMD = "poe_pse_report.py"
    READ_POE_PSE_STATUS_CMD = "poe_pse_report.py -j"
    READ_NVME_TEMP_CMD = "nvme_temp_sensor.py"
    GET_DRCU_BIT_VOLTAGE_CMD = "built_in_test_0198.py -c {}"
    GET_FD_BIT_VOLTAGE_CMD = "built_in_test_0199.py -c {}"
    GET_FUNCTION_BUTTON_CMD = "keypad_func_button_monitor.py -o"
    IS_NVME_MOUNTED_CMD = "dmesg | grep nvme"
    IS_NVME_MOUNTED_EXPECTED_RESPONSE = "F2FS-fs (nvme0n1p1): Mounted with checkpoint version = "
    SET_DISPLAY_BACKLIGHT_CMD = "display_backlight.py {}"
    SET_DISPLAY_BACKLIGHT_EXPECTED_RESPONSE = "INFO - Set display backlight brightness to {}"
    GET_TAMPER_DEVICE_RTC_CMD = "tamper.py -t"
    ARM_TAMPER_SENSORS_CMD = "tamper.py -a"
    INACTIVE_TAMPER_SENSORS_CMD = "tamper.py -i"
    READ_TAMPER_SENSORS_STATUS_CMD = "tamper.py -s"
    UNIT_TAMPER_BIT_TEST_CMD = "tamper.py -b"
    UNIT_TAMPER_BIT_TEST_EXPECTED_RESPONSE = "PASS - Micro-switch Test\nPASS - Light Sensor Test"
    SET_CONFIG_INFO_CMD = "hardware_unit_config.py -st '{}' -sn '{}' -sr '{}' -sb '{}'"
    SET_CONFIG_SUCCESS = "Programmed config info"
    GET_ASSEMBLY_CONFIG_INFO_CMD = "hardware_unit_config.py -u"
    FD_SET_KEYPAD_ALL_LEDS_CMD = "fd_keypad.py -u /dev/ttymxc0 -l ON -c {}"
    FD_SET_KEYPAD_ALL_LEDS_EXPECTED_RESPONSE = "LED state set to ON - {}"
    FD_CHECK_FOR_KEYPAD_BUTTON_PRESS_CMD = "fd_keypad.py -u /dev/ttymxc0 -s {}"
    FD_CHECK_FOR_KEYPAD_BUTTON_PRESS_EXPECTED_RESPONSE = "'{}' Keypad Button Pressed"
    START_STOP_APPLICATION_CMD = "systemctl {} application-setup"
    FD_ASSEMBLY_NO = "KT-950-0431-00"
    DRCU_ASSEMBLY_NO = "KT-950-0429-00"

    def __init__(self, username, hostname=None):
        """
        Class constructor
        :param username: Username for login : type String
        :param hostname: Hostname of the DRCU :type String
        """
        self._ssh_conn = None
        self._username = username
        self._ip_address = None
        self._hostname = hostname
        if hostname is not None:
            self.open_ssh_connection(hostname)

    def __repr__(self):
        """ :return: string representing the class """
        return "CsmPlatformTest({!r})".format(self._hostname)

    def __del__(self):
        """ Class destructor - close the SSH connection """
        if self._hostname != "":
            self.close_ssh_connection()

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the SSH connection """
        self.close_ssh_connection()

    def open_ssh_connection(self, hostname):
        """
        Opens the specified serial port
        :param hostname: Hostname of the KT-000-0140-00 :type string
        :return: N/A
        """
        # Perform a ping to help the test computer find the host
        self._ping(hostname, retries=4)
        self._ssh_conn = SSH(hostname, self._username)
        log.debug("Opened SSH connection {}".format(hostname))
        self._hostname = hostname

    def close_ssh_connection(self):
        """ Closes _ssh_conn if it is open """
        if self._ssh_conn is not None:
            log.debug("Closing SSH connection {}".format(self._hostname))
            self._ssh_conn.close()
        self._ssh_conn = None
        self._hostname = ""

    def check_ssh_connection(self):
        """ Raise a Runtime Error if the SSH connection is not open """
        if self._ssh_conn is None:
            raise RuntimeError("SSH Connection is not open!")
        else:
            return True

    def get_ad7415_temperature(self):
        """
        Read the AD7415 temperature sensor and return the value.
        :return: temperature in deg C :type: integer
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.READ_AD7415_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "Temperature" in a_line:
                    temperature = int(float(a_line.split()[-3]))

        return temperature

    def get_soc_temperatures(self):
        """
        Read the SoC temperature sensors and return their values.
        :return: [0] main; [1] ARM core temperature in deg C :type: integer
        """
        main_temp = -128
        arm_core_temp = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.READ_SOC_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "Main (ANAMIX) )Temperature" in a_line:
                    main_temp = int(float(a_line.split()[1]))
                if "Remote (ARM Core) Temperature" in a_line:
                    arm_core_temp = int(float(a_line.split()[1]))

        return main_temp, arm_core_temp

    def get_gbe_sw_temperature(self, serial_port):
        """
        Read the VSC7512 GbE Switch IC temperature sensor and return the value.
        :param serial_port: GbE Switch serial port :type String
        :return: temperature in deg C :type: Integer
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.READ_GBE_SW_TEMP_CMD.format(serial_port))
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "VSC7512 junction temperature " in a_line:
                    temperature = int(float(a_line.split()[-1]))

        return temperature

    def get_gbe_sw_port_link_state(self, serial_port, u_port):
        """
        Get the link state of the specified GbE Switch port.
        :param serial_port: GbE Switch serial port :type String
        :param u_port: uPort to check :type integer
        :return: string representing the link state UNKNOWN/DOWN/UP_FAST/UP_GBE :type string
        """
        ret_val = "UNKNOWN"

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.READ_GBE_SW_PORT_LINK_STATE_CMD.format(serial_port, u_port))
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = resp.stderr.split()[-1].split(".")[-1]

            if ret_val != "DOWN" and ret_val != "UP_FAST" and ret_val != "UP_GBE":
                ret_val = "UNKNOWN"

        return ret_val

    def get_gbe_sw_port_statistics(self, serial_port, u_port):
        """
        Get the statistics for the specified GbE Switch port.
        :param serial_port: GbE Switch serial port :type String
        :param u_port: uPort to check :type integer
        :return: dictionary representing the port statistics :type Dictionary
        """
        ret_val = {}

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.READ_GBE_SW_PORT_STATISTICS_CMD.format(serial_port, u_port))
            resp = self._ssh_conn.send_command(cmd_str)
            if len(resp.stderr.splitlines()) == 2:
                ret_val = json.loads(resp.stderr.splitlines()[-1])

        return ret_val

    def get_poe_pse_temperature(self):
        """
        Read the Si3474B PoE PSE IC temperature sensor and return the value.
        :return: temperature in deg C :type: Integer
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.READ_POE_PSE_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stdout.splitlines():
                if "temperature -" in a_line:
                    temperature = int(float(a_line.split()[-1]))

        return temperature

    def get_poe_pse_status(self):
        """
        Get the status information for the PoE PSE device.
        :return: dictionary representing the PoE PSE status information :type Dictionary
        """
        ret_val = {}

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.READ_POE_PSE_STATUS_CMD)
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = json.loads(resp.stdout)

        return ret_val

    def get_nvme_temperature(self):
        """
        Read the Si3474B PoE PSE IC temperature sensor and return the value.
        :return: temperature in deg C :type Integer
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.READ_NVME_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "/dev/nvme0 Temperature" in a_line:
                    temperature = int(float(a_line.split()[1]))

        return temperature

    def is_nvme_mounted(self):
        """
        Use Linux dmesg command to determine if the NVMe is mounted.
        :return: True if the NVMe is mounted, else False
        """
        ret_val = False
        if self.check_ssh_connection():
            cmd_str = "{}".format(self.IS_NVME_MOUNTED_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stdout.splitlines():
                if self.IS_NVME_MOUNTED_EXPECTED_RESPONSE in a_line:
                    ret_val = True
                    break

        return ret_val

    def get_drcu_bit_voltage(self, supply_rail):
        """
        Read and return the requested supply rail BIT voltage.
        :param supply_rail: enumerated value for the required voltage rail :type DrcuSomBitVoltages
        :return: read voltage in mV :type Integer
        """
        if not isinstance(supply_rail, DrcuSomBitVoltages):
            raise ValueError("supply_rail must be of type DrcuSomBitVoltages!")

        voltage = -100000
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.GET_DRCU_BIT_VOLTAGE_CMD.format(supply_rail.name))
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "INFO" in a_line and " V" in a_line:
                    voltage = int(float(a_line.split()[-2]) * 1000.0)

        return voltage

    def get_fd_bit_voltage(self, supply_rail):
        """
        Read and return the requested supply rail BIT voltage.
        :param supply_rail: enumerated value for the required voltage rail :type DrcuSomBitVoltages
        :return: read voltage in mV :type Integer
        """
        if not isinstance(supply_rail, FdSomBitVoltages):
            raise ValueError("supply_rail must be of type FdSomBitVoltages!")

        voltage = -100000
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.GET_FD_BIT_VOLTAGE_CMD.format(supply_rail.name))
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "INFO" in a_line and " V" in a_line:
                    voltage = int(float(a_line.split()[-2]) * 1000.0)

        return voltage

    def get_function_button_state(self, button):
        """
        Read and return the state of the specified Keypad function button.
        :param button: button to read. :type DrcuFunctionButtons
        :return: DrcuFunctionButtonState object representing requested button state, state UNKNOWN will be returned if
        the read fails
        """
        if not isinstance(button, DrcuFunctionButtons):
            raise ValueError("button must be of type DrcuFunctionButtons!")

        ret_val = DrcuFunctionButtonState.UNKNOWN

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.GET_FUNCTION_BUTTON_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stdout.splitlines():
                if button.name in a_line:
                    ret_val = DrcuFunctionButtonState.HELD if (a_line.split()[-1] == "0") else \
                        DrcuFunctionButtonState.RELEASED

        return ret_val

    def set_display_backlight(self, brightness):
        """
        Set the display backlight brightness
        :param brightness: PWM controller value [0:255] :type Integer
        :return: True if the command is successful, else False
        """
        brightness = int(brightness)
        ret_val = False

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.SET_DISPLAY_BACKLIGHT_CMD.format(brightness))
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stdout.splitlines():
                if self.SET_DISPLAY_BACKLIGHT_EXPECTED_RESPONSE.format(brightness) in a_line:
                    ret_val = True
                    break

        return ret_val

    def get_tamper_device_rtc(self):
        """
        Read and return the tamper device RTC value.
        :return: tamper RTC string value, empty string if the read fails.
        """
        ret_val = ""

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.GET_TAMPER_DEVICE_RTC_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "RTC: " in a_line:
                    ret_val = a_line.split(' ')[-1]
                    break

        return ret_val

    def arm_tamper_channels(self, arm_state):
        """
        Arm both the tamper detection sensors.
        :param arm_state: True to arm, False to disarm :type Boolean
        :return: True if tamper detection sensors armed/disarmed, else False
        """
        if self.check_ssh_connection():
            cmd = self.ARM_TAMPER_SENSORS_CMD if arm_state else self.INACTIVE_TAMPER_SENSORS_CMD
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, cmd))
            log.debug(resp)
            return True if "Arming both tamper channels" in resp.stderr or \
                           "Setting both tamper channels to inactive" in resp.stderr else False
        else:
            return False

    def check_tamper_status(self):
        """
        Check the status of the tamper detection sensors.
        :return: tuple of Booleans [0] cmd_success; [1] micro-switch armed [2] micro-switch tampered;
        [3] light sensor armed; [4] light sensor tampered
        """
        if self.check_ssh_connection():
            cmd = self.READ_TAMPER_SENSORS_STATUS_CMD
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, cmd))
            log.debug(resp)
            return True, \
                True if "Channel TamperChannel.MICROSWITCH is armed: True" in resp.stderr else False, \
                True if "Channel TamperChannel.MICROSWITCH is tampered: True" in resp.stderr else False, \
                True if "Channel TamperChannel.LIGHT_SENSOR is armed: True" in resp.stderr else False, \
                True if "Channel TamperChannel.LIGHT_SENSOR is tampered: True" in resp.stderr else False
        else:
            return False, False, False, False, False

    def unit_tamper_bit_test(self):
        """
        Perform a unit-level anti-tamper BIT test and return the result.  Expects the unit to be fully assembled with
        the micro-switch depressed and the light sensor in the dark condition.
        NOTE, following the test the tamper channels will be left in the INACTIVE state.
        :return: True, if the BIT test passes, else False
        """
        ret_val = False

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, self.UNIT_TAMPER_BIT_TEST_CMD)
            resp = self._ssh_conn.send_command(cmd_str)
            if self.UNIT_TAMPER_BIT_TEST_EXPECTED_RESPONSE in resp.stderr:
                ret_val = True

        return ret_val

    def set_config_info(self, assy_type, assy_rev_no, assy_serial_no, assy_batch_no):
        """
        Sets the board/unit under test's configuration information to the specified values then reads back
        the data to check that it has been correctly written to EEPROM.
        :param assy_type: board/unit assembly type "KT-000-0140-00" or "KT-950-0351-00" :type String
        :param assy_rev_no: board/unit assembly revision number :type String
        :param assy_serial_no: board/unit assembly serial number :type String
        :param assy_batch_no: board/unit build/batch number :type String
        :return: True if configuration information set correctly, else False :type Boolean
        """
        valid_assy_type = [self.DRCU_ASSEMBLY_NO, self.FD_ASSEMBLY_NO]
        if assy_type not in valid_assy_type:
            raise ValueError("assy_type must be one of: {}".format(valid_assy_type))

        ret_val = False

        if self.check_ssh_connection():
            at = "DRCU_ASSEMBLY" if assy_type == self.DRCU_ASSEMBLY_NO else "FD_ASSEMBLY"
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.SET_CONFIG_INFO_CMD.format(at, assy_serial_no, assy_rev_no, assy_batch_no))
            resp = self._ssh_conn.send_command(cmd_str)
            if self.SET_CONFIG_SUCCESS in resp.stdout:
                ret_val = True

        return ret_val

    def get_config_info(self, assy_type):
        """
        Reads the board or unit configuration information and return it in a dictionary
        :param assy_type: board/unit assembly type "KT-000-0140-00" or "KT-950-0351-00" :type String
        :return: board or unit configuration information dictionary :type: dictionary
        """
        valid_assy_type = [self.DRCU_ASSEMBLY_NO, self.FD_ASSEMBLY_NO]
        if assy_type not in valid_assy_type:
            raise ValueError("assy_type must be one of: {}".format(valid_assy_type))

        ret_val = {}

        if self.check_ssh_connection():
            cmd_str = self.GET_ASSEMBLY_CONFIG_INFO_CMD
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH, cmd_str))

            try:
                ret_val = json.loads(resp.stdout)
            except json.JSONDecodeError:
                ret_val = {}

        return ret_val

    def remove_test_scripts(self):
        """
        Check for the presence of the test scripts archive, "drcu_p2.tgz" and folder "test" in home folder,
        if they are present remove them.  Reboots the SoM to ensure that the SoM eMMC file tables are flushed to disk.
        :return: True if successful, else False
        """
        ret_val = True

        if self.check_ssh_connection():
            remove_test_script_cmds = [
                # (command, response1, response2)
                ("rm -fv drcu_p2.tgz;", "removed 'drcu_p2.tgz'", ""),
                ("rm -rfv test;", "removed directory: 'test'", "")
            ]

            for cmd, resp1, resp2 in remove_test_script_cmds:
                resp = self._ssh_conn.send_command(cmd)
                ret_val = (resp1 in resp.stdout) or (resp2 == resp.stdout)

            # self._ssh_conn.send_command("bash -c 'sleep 5; /sbin/reboot -f'")
        else:
            ret_val = False

        return ret_val

    def copy_test_scripts_to_som(self, test_script_archive):
        """
        Copies the specified tgz archive to the SoM eMMC and extracts it.
        :param test_script_archive: Local path of the the file to copy to the SoM, expecting tgz archive.
        :return: True if successful, else False
        """
        ret_val = True

        if self.check_ssh_connection():
            copy_test_script_cmds = [
                # (command, response1, response2)
                ("rm -rf test; /bin/tar -xvzf drcu_p2.tgz", "test/", "")
            ]

            self._ssh_conn.send_file(test_script_archive, "drcu_p2.tgz", protocol="SCP")
            for cmd, resp1, resp2 in copy_test_script_cmds:
                resp = self._ssh_conn.send_command(cmd)
                ret_val = (resp1 in resp.stdout) or (resp2 == resp.stdout)
        else:
            ret_val = False

        return ret_val

    def check_for_sd_card(self):
        """
        Checks if the SD Card is present
        :return: True if SD Card present, else False
        """
        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command("ls /dev/mmc*")
            return True if "mmcblk1p1" in resp.stdout else False
        else:
            return True     # Default to negative state, i.e. an SD Card is present.

    def fd_set_all_keypad_leds(self, led_colour):
        """
        Sets all 3x keypad LEDs to the specified colour for 6-seconds.
        :param led_colour: required LED colour :type DrcuFdKeypadLedColours
        :return: True if the command is successful, else False :type Boolean
        """
        if type(led_colour) is not DrcuFdKeypadLedColours:
            raise ValueError("led_colour must be type DrcuFdKeypadLedColours!")

        ret_val = False

        if self.check_ssh_connection():
            if led_colour is DrcuFdKeypadLedColours.RED:
                led_colour_str = "RED"
            elif led_colour is DrcuFdKeypadLedColours.YELLOW:
                led_colour_str = "YELLOW"
            else:   # Must be GREEN
                led_colour_str = "GREEN"
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.FD_SET_KEYPAD_ALL_LEDS_CMD.format(led_colour_str))
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = self.FD_SET_KEYPAD_ALL_LEDS_EXPECTED_RESPONSE.format(led_colour_str) in resp.stderr

        return ret_val

    def fd_check_for_keypad_button_press(self, button):
        """
        Checks that the specified button is pressed and released within a 10-second window.
        :param button: button to check :type FdKeypadButtons
        :return:
        """
        if type(button) is not FdKeypadButtons:
            raise ValueError("button must be type FdKeypadButtons!")

        ret_val = False

        if self.check_ssh_connection():
            if button is FdKeypadButtons.UP_ARROW:
                button_str = "UP_ARROW"
            elif button is FdKeypadButtons.X:
                button_str = "X"
            else:   # Must be DOWN_ARROW
                button_str = "DOWN_ARROW"
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.DRCU_TEST_SCRIPT_PATH,
                                       self.FD_CHECK_FOR_KEYPAD_BUTTON_PRESS_CMD.format(button_str))
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = self.FD_CHECK_FOR_KEYPAD_BUTTON_PRESS_EXPECTED_RESPONSE.format(button_str) in resp.stderr

        return ret_val

    def start_stop_application(self, start_stop):
        """
        Start or stop the DRCU/FD application from running.
        :param start_stop: True to start, False to stop :type Boolean
        :return: True if the command is successful, else False :type Boolean
        """
        if self.check_ssh_connection():
            self._ssh_conn.send_command(self.START_STOP_APPLICATION_CMD.format("start" if start_stop else "stop"))
            return True
        else:
            return False

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
            else:
                ping_type = "-4"
        else:
            count_param = "c"

        for i in range(0, retries):
            output = popen("ping {} -{} 1 {}".format(ping_type, count_param, a)).read()

            if "unreachable" in output or "0 packets received" in output or "could not find" in output:
                return_val = False
            else:
                return_val = True
                break

        return return_val

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
