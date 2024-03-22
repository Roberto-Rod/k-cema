#!/usr/bin/env python3
"""
Class that provides an interface for executing CSM Platform Test scripts,
KT-956-0234-00 test scripts via SSH.

Prerequisites:
- CSM Platform Test Script installed in folder "/run/media/mmcblk1p2/test/" on
  the KT-000-0140/0180-00 board.

Software compatibility:
- KT-956-0234-00 K-CEMA CSM Platform Test Scripts V2.0.10
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
import json
import logging
from os import popen
import platform
import time

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
class CsmPlatformTest:
    PYTHON_PATH = "python3"
    CSM_TEST_SCRIPT_PATH = "/run/media/mmcblk1p2/test/"
    ASSERT_RF_MUTE_CMD = "ext_rf_mute.py -b 1"
    ASSERT_RF_MUTE_CMD_SUCCESS = "Both RF_MUTE - Asserted"
    DEASSERT_RF_MUTE_CMD = "ext_rf_mute.py -b 0"
    DEASSERT_RF_MUTE_CMD_SUCCESS = "Both RF_MUTE - De-asserted"
    ASSERT_MASTER_RF_MUTE_CMD = "ext_rf_mute.py -m 1"
    ASSERT_MASTER_RF_MUTE_CMD_SUCCESS = "Master RF_MUTE - Asserted"
    DEASSERT_MASTER_RF_MUTE_CMD = "ext_rf_mute.py -m 0"
    DEASSERT_MASTER_RF_MUTE_CMD_SUCCESS = "Master RF_MUTE - De-asserted"
    ASSERT_SLAVE_RF_MUTE_CMD = "ext_rf_mute.py -s 1"
    ASSERT_SLAVE_RF_MUTE_CMD_SUCCESS = "Slave RF_MUTE - Asserted"
    DEASSERT_SLAVE_RF_MUTE_CMD = "ext_rf_mute.py -s 0"
    DEASSERT_SLAVE_RF_MUTE_CMD_SUCCESS = "Slave RF_MUTE - De-asserted"
    SET_RF_MUTE_DIR_IP_CMD = "ext_rf_mute.py -d 0"
    SET_RF_MUTE_DIR_IP_CMD_SUCCESS = "RF_MUTE_DIR - Input"
    SET_RF_MUTE_DIR_OP_CMD = "ext_rf_mute.py -d 1"
    SET_RF_MUTE_DIR_OP_CMD_SUCCESS = "RF_MUTE_DIR - Output"
    ASSERT_PWR_OFF_OVR_CMD = "ext_power_off_over.py 1"
    ASSERT_PWR_OFF_OVR_CMD_SUCCESS = "POWER_OFF_OVR - Asserted"
    DEASSERT_PWR_OFF_OVR_CMD = "ext_power_off_over.py 0"
    DEASSERT_PWR_OFF_OVR_CMD_SUCCESS = "POWER_OFF_OVR - De-asserted"
    UART_TEST_EXECUTE = "uart_test.py"
    UART_TEST_SUCCESS = "PASS - UART {}, {}"    # serial_port, baud_rate
    READ_TMP442_TEMPS_CMD = "tmp442_temp_sensor.py"
    READ_TMP442_INTERNAL_TEMP_LINE = "Internal"
    READ_TMP442_REMOTE1_TEMP_LINE = "Remote 1"
    READ_TMP442_REMOTE2_TEMP_LINE = "Remote 2"
    READ_AD7415_TEMP_CMD = "ad7415_temp_sensor.py"
    READ_EUI48_IDS_CMD = "eui48_ic.py"
    READ_EUI48_IDS_DEV1_NAME = "dev1"
    READ_EUI48_IDS_DEV2_NAME = "dev2"
    READ_EUI48_IDS_OUI_VALID = "OUI valid"
    TCXO_ADJUST_TEST_CMD = "tcxo_adjust.py"
    TCXO_ADJUST_TEST_SUCCESS = "PASS - SoM 1PPS & TCXO Input Test"
    READ_GPS_LOCK_CMD = "gps_nmea_decode.py -l -s {}"
    READ_GPS_LOCK_SUCCESS = "INFO - GPS is locked"
    READ_SOM_BIT_CH_CMD = "built_in_test.py -c {}"
    READ_SOM_TEMPERATURE_CMD = "xadc.py"
    READ_GBE_PORT_LINK_STATE_CMD = "gbe_switch.py -c {} -p {}"
    READ_GBE_PORT_STATISTICS_CMD = "gbe_switch.py -c {} -s {}"
    READ_GBE_SWITCH_TEMPS_CMD = "gbe_switch.py -c /dev/ttyEthSw -t"
    SET_CONFIG_INFO_CMD = "hardware_unit_config.py -st \"{}\" -sn \"{}\" -sr \"{}\" -sb \"{}\" -td"
    SET_CONFIG_SUCCESS = "Programmed config info"
    GET_ASSEMBLY_CONFIG_INFO_CMD = "hardware_unit_config.py -u"
    GET_MBOARD_CONFIG_INFO_CMD = "hardware_unit_config.py -b"
    GET_PB_CTRL_IRQ_CMD = "pb_ctrl_irq.py"
    KILL_POWER_CMD = "kill_power.py"
    SET_BUZZER_STATE_CMD = "keypad.py -b {} -u {}"
    SET_LED_STATE_CMD = "keypad.py -l {} -u {}"
    CHECK_BUTTON_PRESS_CMD = "keypad.py -s {} -u {}"
    ARM_TAMPER_SENSORS_CMD = "tamper.py -a"
    INACTIVE_TAMPER_SENSORS_CMD = "tamper.py -i"
    READ_TAMPER_SENSORS_STATUS_CMD = "tamper.py -s"
    UNIT_TAMPER_BIT_TEST_CMD = "tamper.py -b"
    UNIT_TAMPER_BIT_TEST_EXPECTED_RESPONSE = "PASS - Micro-switch Test\nPASS - Light Sensor Test"
    READ_LTC2991_TEMP_CMD = "ltc2991_adc.py"
    SET_EXTERNAL_1PPS_DIRECTION_CMD = "/sbin/devmem 0x4000D004 32 {}"
    CSM_MOTHERBOARD_NO = "KT-000-0140-00"
    CSM_ASSEMBLY_NO = "KT-950-0351-00"
    CSM_MOTHERBOARD_MP_NO = "KT-000-0180-00"
    CSM_MOTHERBOARD_MP_KBAN_NO = "KT-000-0180-01"

    def __init__(self, username, hostname=None):
        """
        Class constructor
        :param username: User name for SSH login :type String
        :param hostname: Hostname of the board/unit :type String
        """
        self._ssh_conn = None
        self._username = username
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

    def assert_rf_mute(self, assert_val):
        """
        Assert the RF Mute signals
        :return: True if the command is successfully executed, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.ASSERT_RF_MUTE_CMD if assert_val else self.DEASSERT_RF_MUTE_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            ret_val = (assert_val and self.ASSERT_RF_MUTE_CMD_SUCCESS in resp.stdout) or \
                      (not assert_val and self.DEASSERT_RF_MUTE_CMD_SUCCESS in resp.stdout)

        return ret_val

    def assert_master_rf_mute(self, assert_val):
        """
        Assert the RF Mute signals
        :return: True if the command is successfully executed, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.ASSERT_MASTER_RF_MUTE_CMD if assert_val else
                                       self.DEASSERT_MASTER_RF_MUTE_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            ret_val = (assert_val and self.ASSERT_MASTER_RF_MUTE_CMD_SUCCESS in resp.stdout) or \
                      (not assert_val and self.DEASSERT_MASTER_RF_MUTE_CMD_SUCCESS in resp.stdout)

        return ret_val

    def assert_slave_rf_mute(self, assert_val):
        """
        Assert the RF Mute signals
        :return: True if the command is successfully executed, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.ASSERT_SLAVE_RF_MUTE_CMD if assert_val else self.DEASSERT_SLAVE_RF_MUTE_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            ret_val = (assert_val and self.ASSERT_SLAVE_RF_MUTE_CMD_SUCCESS in resp.stdout) or \
                      (not assert_val and self.DEASSERT_SLAVE_RF_MUTE_CMD_SUCCESS in resp.stdout)

        return ret_val

    def set_rf_mute_direction(self, assert_val):
        """
        Set the Control port RF Mute direction
        :param assert_val: True, to set as output, False input :type Boolean
        :return: True if the command is successfully executed, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.SET_RF_MUTE_DIR_OP_CMD if assert_val else self.SET_RF_MUTE_DIR_IP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            ret_val = (assert_val and self.SET_RF_MUTE_DIR_OP_CMD_SUCCESS in resp.stdout) or \
                      (not assert_val and self.SET_RF_MUTE_DIR_IP_CMD_SUCCESS in resp.stdout)

        return ret_val

    def assert_power_off_override(self, assert_val):
        """
        Assert the Power Off Override signal
        :return: True if the command is successfully executed, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.ASSERT_PWR_OFF_OVR_CMD if assert_val else self.DEASSERT_PWR_OFF_OVR_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            ret_val = (assert_val and self.ASSERT_PWR_OFF_OVR_CMD_SUCCESS in resp.stdout) or \
                      (not assert_val and self.DEASSERT_PWR_OFF_OVR_CMD_SUCCESS in resp.stdout)

        return ret_val

    def uart_test(self, serial_port, baud_rate):
        """
        Execute UART loopback test and return the result.
        :param serial_port: serial port to test :type: string
        :param baud_rate: serial baud rate :type: integer
        :return: True if test executes and passes, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{} -s {} -b {}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.UART_TEST_EXECUTE,
                                                   serial_port, baud_rate)
            resp = self._ssh_conn.send_command(cmd_str)
            success_string = self.UART_TEST_SUCCESS.format(serial_port, baud_rate)
            ret_val = success_string in resp.stderr or success_string in resp.stdout

        return ret_val

    def get_ad7415_temperature(self):
        """
        Read the AD7415 temperature sensor and return the value.
        :return: temperature in deg C :type: Float
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_AD7415_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "Temperature" in a_line:
                    temperature = float(a_line.split()[-3])
                    break

        return temperature

    def get_tmp442_temperatures(self):
        """
        Read the TMP442 temperature sensor and return the values.
        :return: Dictionary of temperature sensor readings :type: Dictionary {channel_name, temp_dec_c}
        where channel_name is a string and temp_deg_c is an integer.
        """
        ret_vals = {}
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_TMP442_TEMPS_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if self.READ_TMP442_INTERNAL_TEMP_LINE in a_line:
                    ret_vals[self.READ_TMP442_INTERNAL_TEMP_LINE] = int(a_line.split()[-3])
                elif self.READ_TMP442_REMOTE1_TEMP_LINE in a_line:
                    ret_vals[self.READ_TMP442_REMOTE1_TEMP_LINE] = int(a_line.split()[-3])
                elif self.READ_TMP442_REMOTE2_TEMP_LINE in a_line:
                    ret_vals[self.READ_TMP442_REMOTE2_TEMP_LINE] = int(a_line.split()[-3])
                else:
                    pass

        return ret_vals

    def read_eui48_ids(self):
        """
        Read the EUI48 IDs from the board/unit under test.
        :return: Dictionary of EUI48 values and validity :type Dictionary {dev_name, {dev_id, dev_id_valid}}
        where dev_name and dev_id are strings and devi_id_valid is a Boolean.
        """
        ret_vals = {self.READ_EUI48_IDS_DEV1_NAME: {}, self.READ_EUI48_IDS_DEV2_NAME: {}}
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_EUI48_IDS_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "{} EUI48".format(self.READ_EUI48_IDS_DEV1_NAME) in a_line:
                    ret_vals[self.READ_EUI48_IDS_DEV1_NAME]["dev_id"] = a_line.split()[-1].upper()
                elif "{} EUI48".format(self.READ_EUI48_IDS_DEV2_NAME) in a_line:
                    ret_vals[self.READ_EUI48_IDS_DEV2_NAME]["dev_id"] = a_line.split()[-1].upper()
                elif "{} OUI".format(self.READ_EUI48_IDS_DEV1_NAME) in a_line:
                    ret_vals[self.READ_EUI48_IDS_DEV1_NAME]["dev_id_valid"] = self.READ_EUI48_IDS_OUI_VALID in a_line
                elif "{} OUI".format(self.READ_EUI48_IDS_DEV2_NAME) in a_line:
                    ret_vals[self.READ_EUI48_IDS_DEV2_NAME]["dev_id_valid"] = self.READ_EUI48_IDS_OUI_VALID in a_line
                else:
                    pass

        return ret_vals

    def read_som_mac_ipv4_address(self):
        """
        Read and return the SOM MAC and IPv4 address
        :return: tuple of strings mac_address, ipv4_address
        """
        ipv4_address = ""
        mac_address = ""

        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command("/sbin/ifconfig")
            ifconfig_string = resp.stdout

            # Find the lines with the eth0 MAC aannd IPV4 addresses and extract them
            found_avahi = False
            for a_line in ifconfig_string.splitlines():
                if found_avahi:
                    ipv4_address = a_line[a_line.find("inet addr:") + len("inet addr:"):a_line.find(" Bcast:")].rstrip()
                    break

                if "eth0:avahi Link encap:Ethernet  HWaddr " in a_line:
                    mac_address = a_line[a_line.find("HWaddr ") + len("HWaddr "):].rstrip()
                    found_avahi = True

        return mac_address, ipv4_address

    def read_mount_cmd_response(self):
        """
        Return the standard output of the Linux mount command
        :return: standard output response to mount command :type: string
        """
        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command("mount")
            return resp.stdout

    def tcxo_adjust_test(self):
        """
        Execute TCXO adjust test and return the result.
        :return: True if test executes and passes, else False :type Boolean
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.TCXO_ADJUST_TEST_CMD)
            # This command may take longer than the standard default timeout of 15.0 secs, typically 15.0-17.0 secs
            resp = self._ssh_conn.send_command(cmd_str, timeout=20.0)
            ret_val = self.TCXO_ADJUST_TEST_SUCCESS in resp.stderr or self.TCXO_ADJUST_TEST_SUCCESS in resp.stdout

        return ret_val

    def read_gps_lock(self, serial_port):
        """
        Read if the GPS is locked and return the result, will timeout after 30-seconds if there is no GPS lock
        :param serial_port: CSM GPS serial port :type String
        :return: True if GPS locked, else False
        """
        ret_val = True

        if self.check_ssh_connection():
            cmd = self.READ_GPS_LOCK_CMD.format(serial_port)
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd)
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = self.READ_GPS_LOCK_SUCCESS in resp.stderr or self.READ_GPS_LOCK_SUCCESS in resp.stdout

        return ret_val

    def read_som_bit_adc(self, channel):
        """
        Read the specified SoM built-in test channel ADC value
        :param channel: name of channel to read :type: string
        :return: BIT channel value :type: float
        """
        ret_val = -1.0

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.READ_SOM_BIT_CH_CMD.format(channel))
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = float(resp.stderr.split()[-2])

        return ret_val

    def get_som_temperature(self):
        """
        Read the SoM temperature sensor and return the value.
        :return: temperature in deg C :type: Float
        """
        temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_SOM_TEMPERATURE_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stdout.splitlines():
                if "Internal temperature:" in a_line:
                    temperature = float(a_line.split()[-2])
                    break

        return temperature

    def read_som_bit_pgood(self, channel):
        """
        Read the specified SoM built-in test channel Power Good signal
        :param channel: name of channel to read :type: string
        :return: BIT channel Power Good state :type: boolean
        """
        ret_val = ""

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.READ_SOM_BIT_CH_CMD.format(channel))
            resp = self._ssh_conn.send_command(cmd_str)
            ret_val = True if resp.stderr.split()[-1] == "True" else False

        return ret_val

    def get_gbe_sw_port_link_state(self, serial_port, u_port):
        """
        Get the link state of the specified GbE Switch port.
        :param serial_port: GbE Switch serial port :type string
        :param u_port: uPort to check :type integer
        :return: string representing the link state UNKNOWN/DOWN/UP_FAST/UP_GBE :type string
        """
        ret_val = "UNKNOWN"

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.READ_GBE_PORT_LINK_STATE_CMD.format(serial_port, u_port))
            resp = self._ssh_conn.send_command(cmd_str)
            for a_line in resp.stderr.splitlines():
                if "Link State" in a_line:
                    ret_val = a_line.split(".")[-1]
                    break

            if ret_val != "DOWN" and ret_val != "UP_FAST" and ret_val != "UP_GBE":
                ret_val = "UNKNOWN"

        return ret_val

    def get_gbe_sw_port_statistics(self, serial_port, u_port):
        """
        Get the statistics for the specified GbE Switch port.
        :param serial_port: GbE Switch serial port :type string
        :param u_port: uPort to check :type integer
        :return: dictionary representing the port statistics :type dictionary
        """
        ret_val = {}

        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                       self.READ_GBE_PORT_STATISTICS_CMD.format(serial_port, u_port))
            resp = self._ssh_conn.send_command(cmd_str)
            # log.debug(resp.stderr)
            lines = resp.stderr.splitlines()
            for i, a_line in enumerate(lines):
                if "Statistics:" in a_line:
                    try:
                        ret_val = json.loads(lines[i + 1])
                    except Exception as ex:
                        log.info("{}".format(ex))
                        ret_val = {}
                    break

        return ret_val

    def get_gbe_sw_temperatures(self):
        """
        Get the Gbe Switch (VSC7512) and GbE Switch PHY (VSC8514) junction temperatures.
        :return: tuple of temperatures in deg C :type tuple of floats
        """
        sw_temperature = -128
        phy_temperature = -128
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_GBE_SWITCH_TEMPS_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "VSC7512 junction temperature (deg C):" in a_line:
                    sw_temperature = float(a_line.split()[-1])
                elif "VSC8514 junction temperature (deg C):" in a_line:
                    phy_temperature = float(a_line.split()[-1])

        return sw_temperature, phy_temperature

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
        ret_val = True

        if self.check_ssh_connection():
            if assy_type == self.CSM_ASSEMBLY_NO or assy_type == self.CSM_MOTHERBOARD_NO or \
                    assy_type == self.CSM_MOTHERBOARD_MP_NO or assy_type == self.CSM_MOTHERBOARD_MP_KBAN_NO:

                if assy_type == self.CSM_ASSEMBLY_NO:
                    at = "CSM_ASSEMBLY"
                elif assy_type == self.CSM_MOTHERBOARD_NO:
                    at = "CSM_MOTHERBOARD"
                elif assy_type == self.CSM_MOTHERBOARD_MP_NO:
                    at = "CSM_MOTHERBOARD_MP"
                else:
                    at = "CSM_MOTHERBOARD_MP_KBAN"

                cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                           self.SET_CONFIG_INFO_CMD.format(at, assy_serial_no,
                                                                           assy_rev_no, assy_batch_no))
                resp = self._ssh_conn.send_command(cmd_str)
                if self.SET_CONFIG_SUCCESS not in resp.stderr:
                    ret_val = False
            else:
                log.info("FAIL - Invalid assembly type!")
                ret_val = False

        return ret_val

    def get_config_info(self, assy_type):
        """
        Reads the board or unit configuration information and return it in a dictionary
        :param assy_type: board/unit assembly type "KT-000-0140-00" or "KT-950-0351-00" :type String
        :return: board or unit configuration information dictionary :type: dictionary
        """
        ret_val = {}

        if self.check_ssh_connection():
            if assy_type == self.CSM_ASSEMBLY_NO or assy_type == self.CSM_MOTHERBOARD_NO or \
                    assy_type == self.CSM_MOTHERBOARD_MP_NO or assy_type == self.CSM_MOTHERBOARD_MP_KBAN_NO:
                at_cmd = self.GET_ASSEMBLY_CONFIG_INFO_CMD if assy_type == self.CSM_ASSEMBLY_NO \
                    else self.GET_MBOARD_CONFIG_INFO_CMD
                resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                                                    at_cmd))
                try:
                    ret_val = json.loads(resp.stdout)
                except json.JSONDecodeError:
                    ret_val = {}

        return ret_val

    def read_i2c_device_detect_string(self):
        """
        :return: Returns the response string to I2C tools i2cdetect command on the SoM I2C bus :type: string
        """
        ret_val = ""
        if self.check_ssh_connection():
            ret_val = self._ssh_conn.send_command("/usr/sbin/i2cdetect -y -r 1").stdout
        return ret_val

    def get_pb_ctrl_irq(self):
        """
        Read and return the state of the push-button controller interrupt signal
        :return: True if interrupt asserted, else False :type: boolean
        """
        ret_val = False

        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                                                self.GET_PB_CTRL_IRQ_CMD))
            ret_val = "De-asserted" not in resp.stdout
        return ret_val

    def power_kill(self):
        """
        Asserts the Power Kill signal to the push-button controller.
        :return: True if command executed, else False
        """
        if self.check_ssh_connection():
            self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH,
                                                         self.KILL_POWER_CMD))
            return True
        else:
            return False

    def set_buzzer_state(self, serial_port, set_state):
        """
        Execute unit level command to set the buzzer state
        :param serial_port: Board/Unit Zeroise Micro serial port :type String
        :param set_state: True to turn buzzer on, False to turn buzzer off
        :return: True if buzzer state set, else False
        """
        if self.check_ssh_connection():
            cmd = self.SET_BUZZER_STATE_CMD.format('1' if set_state else '0', serial_port)
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd))
            return True if "Buzzer set to" in resp.stderr else False
        else:
            return False

    def check_for_sd_card(self):
        """
        Checks if the SD Card is present
        :return: True if SD Card present, else False
        """
        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command("ls /run/media")
            return True if "mmcblk0p1" in resp.stdout else False
        else:
            return True

    def set_all_keypad_green_leds(self, serial_port, mode):
        """
        Set all of the Keypad LEDS to the specified state, mode is applied for 6-seconds
        :param serial_port: Board/Unit Zeroise Micro serial port :type String
        :param mode: "ON"|"OFF"|"BLINK" :type string
        :return: True if LED set, else False
        """
        if self.check_ssh_connection() and mode in ["ON", "OFF", "BLINK"]:
            cmd = self.SET_LED_STATE_CMD.format(mode, serial_port)
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd))
            return True if "LED state set to {}".format(mode) in resp.stderr else False
        else:
            return False

    def check_for_keypad_button_press(self, serial_port, button):
        """
        Check that the requested button is pressed within a 20-second period.
        Must also press any other button except the Power button.
        :param serial_port: Board/Unit Zeroise Micro serial port :type String
        :param button: "JAM"|"X"|"EXCLAMATION" :typ string
        :return: True if button pressed, else False
        """
        if self.check_ssh_connection() and button in ["JAM", "X", "EXCLAMATION"]:
            cmd = self.CHECK_BUTTON_PRESS_CMD.format(button, serial_port)
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd))
            return True if "PASS - '{}' Keypad Button Pressed".format(button) in resp.stderr else False
        else:
            return False

    def arm_tamper_channels(self, arm_state):
        """
        Arm both the tamper detection sensors.
        :param arm_state: True to arm, False to disarm :type Boolean
        :return: True if tamper detection sensors armed/disarmed, else False
        """
        if self.check_ssh_connection():
            cmd = self.ARM_TAMPER_SENSORS_CMD if arm_state else self.INACTIVE_TAMPER_SENSORS_CMD
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd))
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
            resp = self._ssh_conn.send_command("{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, cmd))
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
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.UNIT_TAMPER_BIT_TEST_CMD)
            resp = self._ssh_conn.send_command(cmd_str)
            if self.UNIT_TAMPER_BIT_TEST_EXPECTED_RESPONSE in resp.stderr:
                ret_val = True

        return ret_val

    def remove_test_scripts(self):
        """
        Check for the presence of the test scripts archive, "csm_p2.tgz" and folder "test" on mmcblk1p2,
        if they are present remove them.
        :return: True if successful, else False
        """
        ret_val = True

        if self.check_ssh_connection():
            remove_test_script_cmds = [
                # (command, response1, response2)
                ("rm -fv /run/media/mmcblk1p2/csm_p2.tgz;", "removed '/run/media/mmcblk1p2/csm_p2.tgz'", ""),
                ("rm -rfv /run/media/mmcblk1p2/test;rm -d /run/media/mmcblk1p2/test",
                 "removed directory '/run/media/mmcblk1p2/test'", "")
            ]

            for cmd, resp1, resp2 in remove_test_script_cmds:
                resp = self._ssh_conn.send_command(cmd)
                ret_val = (resp1 in resp.stdout) or (resp2 == resp.stdout)
            try:
                self._ssh_conn.send_command("/sbin/reboot -f", retries=1)
            except Exception as ex:
                log.debug(ex)
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
                ("cd /run/media/mmcblk1p2;ls;rm -rf test;/bin/tar -xvzf csm_p2.tgz;cd /;umount /run/media/mmcblk1p2;"
                 "mount /dev/mmcblk1p2 /run/media/mmcblk1p2", "test/", "")
            ]

            self._ssh_conn.send_file(test_script_archive, "/run/media/mmcblk1p2/csm_p2.tgz")
            for cmd, resp1, resp2 in copy_test_script_cmds:
                resp = self._ssh_conn.send_command(cmd)
                ret_val = (resp1 in resp.stdout) or (resp2 == resp.stdout)
        else:
            ret_val = False

        return ret_val

    def get_ltc2991_temperature(self):
        """
        Read the LTC2991 ADC temperature sensor and return the value.
        :return: temperature in deg C, -255.0 for invalid read :type: Float
        """
        temperature = -255.0
        if self.check_ssh_connection():
            cmd_str = "{} {}{}".format(self.PYTHON_PATH, self.CSM_TEST_SCRIPT_PATH, self.READ_LTC2991_TEMP_CMD)
            resp = self._ssh_conn.send_command(cmd_str)

            for a_line in resp.stderr.splitlines():
                if "Temperature (deg C)" in a_line:
                    temperature = float(a_line.split()[1])
                    break

        return temperature

    def set_external_1pps_direction(self, output):
        """
        Set the External 1PPS Direction
        :param output: True to set as output, False to set as input :type Boolean
        :return: True if External 1PPS direction set else False
        """
        if self.check_ssh_connection():
            resp = self._ssh_conn.send_command(self.SET_EXTERNAL_1PPS_DIRECTION_CMD.format('0' if input else '1'))
            return True if resp.exited == 0 else False
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
            log.debug("Ping {}:".format(i))
            log.debug(output)

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
