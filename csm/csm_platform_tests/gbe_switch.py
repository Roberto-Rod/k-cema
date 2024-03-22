#!/usr/bin/env python3
"""
Module for accessing VSC7512 GbE switch registers using the Active Backplane
Telnet server
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-b"/"--baud_rate", default=115200, Serial baud rate
-c"/"--com_port", required, Serial COM port
-l"/"--lwip_addr", Print lwIP IPV4 addresses
-p"/"--port_link_state", default=0, Print port link state
-s"/"--port_stats", default=0, Print port statistics as JSON string
-si/ "--si_mode", default="", Set SI mode: SLAVE, BOOT_MASTER, MASTER
-t"/"--temp", action="store_true", Print junction temperatures
-v"/"--version", action="store_true", Print software version
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
# from dataclasses import dataclass
from enum import Enum
import json
import logging
from os import popen
import platform
import re
from telnetlib import Telnet

# Third-party imports -----------------------------------------------
from serial import Serial

# Our own imports ---------------------------------------------------
from dev_mem import DevMem

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
GBE_SWITCH_CSM_UART = "/dev/ttyEthSw"
GPIO0_REG_ADDRESS = 0x4000A000
GPIO0_ETH_SW_RESET_N_BIT = 0x10

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class GbeSwitchLinkState(Enum):
    UNKNOWN = -1
    DOWN = 0
    UP_FAST = 2
    UP_GBE = 3


# @dataclass
class GbeSwitchPortStats:
    """
    Utility class to represent port statistics read from the switch.
    """
    def __init__(self):
        """ Class constructor, set initial data values """
        self.rx_packets = -1
        self.rx_octets = -1
        self.rx_broadcast = -1
        self.rx_multicast = -1
        self.rx_pause = -1
        self.rx_error_packets = -1
        self.rx_mac_ctrl = -1
        self.rx_crc_alignment = -1
        self.rx_undersize = -1
        self.rx_oversize = -1
        self.rx_fragments = -1
        self.rx_jabbers = -1
        self.rx_drops = -1
        self.rx_classifier_drops = -1
        self.tx_packets = -1
        self.tx_octets = -1
        self.tx_broadcast = -1
        self.tx_multicast = -1
        self.tx_pause = -1
        self.tx_error_packets = -1
        self.tx_collisions = -1
        self.tx_drops = -1
        self.tx_overflow = -1
        self.tx_aged = -1
        self.rx_64_bytes = -1
        self.tx_64_bytes = -1
        self.rx_65_127_bytes = -1
        self.tx_65_127_bytes = -1
        self.rx_128_255_bytes = -1
        self.tx_128_255_bytes = -1
        self.rx_256_511_bytes = -1
        self.tx_256_511_bytes = -1
        self.rx_512_1023_bytes = -1
        self.tx_512_1023_bytes = -1
        self.rx_1024_bytes = -1
        self.tx_1024_bytes = -1

    def set_attr_from_resp_str(self, port_statistic_str):
        """
        Class constructor, takes the response to a Get Port Statistics
        command as input and extracts attributes
        @param port_statistic_str:
        """
        if not isinstance(port_statistic_str, str):
            raise ValueError("port_statistic_str must be a string!")

        for line in port_statistic_str.splitlines():
            try:
                split_line = line.split()

                if len(split_line) == 6 and split_line[0] == "Rx":   # Line containing some statistics
                    rx_attr = "{}_{}".format(split_line[0].lower().replace('/', '_').strip(':'),
                                             split_line[1].lower().replace('/', '_').strip(':'))
                    rx_val = int(split_line[2])
                    tx_attr = "{}_{}".format(split_line[3].lower().replace('/', '_').strip(':'),
                                             split_line[4].lower().replace('/', '_').strip(':'))
                    if tx_attr != "tx_-":
                        tx_val = int(split_line[5])
                    else:
                        tx_val = -1
                elif len(split_line) == 7 and split_line[0] == "Rx":   # Line containing some statistics
                    rx_attr = "{}_{}_{}".format(split_line[0].lower().replace('/', '_').strip(':'),
                                                split_line[1].lower().replace('/', '_').strip(':'),
                                                split_line[2].lower().replace('/', '_').strip(':'))
                    rx_val = int(split_line[3])
                    tx_attr = ""
                    tx_val = -1
                elif len(split_line) == 8 and split_line[0] == "Rx":   # Line containing some statistics
                    rx_attr = "{}_{}_{}".format(split_line[0].lower().replace('/', '_').replace('-', '_').strip(':'),
                                                split_line[1].lower().replace('/', '_').replace('-', '_').strip(':'),
                                                split_line[2].lower().replace('/', '_').replace('-', '_').strip(':'))
                    rx_attr = rx_attr.replace("__", '_')
                    rx_val = int(split_line[3])
                    tx_attr = "{}_{}_{}".format(split_line[4].lower().replace('/', '_').replace('-', '_').strip(':'),
                                                split_line[5].lower().replace('/', '_').replace('-', '_').strip(':'),
                                                split_line[6].lower().replace('/', '_').replace('-', '_').strip(':'))
                    tx_attr = tx_attr.replace("__", '_')
                    tx_val = int(split_line[7])
                else:
                    rx_attr = ""
                    rx_val = -1
                    tx_attr = ""
                    tx_val = -1

                # Try to update the member attributes with read values
                if hasattr(self, rx_attr):
                    self.__setattr__(rx_attr, rx_val)

                if hasattr(self, tx_attr):
                    self.__setattr__(tx_attr, tx_val)
            except Exception as ex:
                # Just print the error then try the next line
                log.debug(ex)


class GbeSwitchSiMode(Enum):
    SLAVE = 0
    BOOT_MASTER = 1
    MASTER = 2


class GbeSwitch:
    MIN_UPORT = 1
    MAX_UPORT = 10
    TIMEOUT_SEC = 2
    SOFTWARE_PART_NO_10_PORT = "KT-956-0195-00"
    SOFTWARE_PART_NO_4_PORT = "KT-956-0195-01"
    CMD_TERMINATOR = b">"
    CMD_SEND = b"\r"
    GET_MAC_ADDRESS_CMD = b"m\r"
    ENABLE_TEMP_SENSOR_CMD = b"w 0x710d0000 0x11C 0x0 1\r"
    ENABLE_SW_TEMP_SENSOR_SUCCESS = b"0x00000001          1 0000.0000.0000.0000.0000.0000.0000.0001"
    GET_SW_TEMP_SENSOR_READING_CMD = b"r 0x710d0000 0x11C 0x8\r"
    TRIGGER_PHY_TEMP_SENSOR_CMD_1 = b"O 1 0x1A 0x0080 0x0010\r"
    TRIGGER_PHY_TEMP_SENSOR_CMD_2 = b"O 1 0x1A 0x00C0 0x0010\r"
    GET_PHY_TEMP_SENSOR_READING_CMD = b"i 1 0x1C 0x0010\r"
    GET_VSC7512_QSGMII_SYNC_CMD = b"r 0x710D0000 0x10C 0x0\r"
    GET_VSC8514_QSGMII_SYNC_CMD = "i {} 0x14 0x3\r"
    GET_PORT_STATISTICS_CMD = "h {}\r"
    GET_PORT_STATUS_CMD = b"p\r"
    GET_VERSION_CMD = b"v\r"
    READ_SLAVE_INTERFACE_MODE_REG = b"r 0x70000000 0x0 0x24\r"  # VSC7512 ICPU_CFG:CPU_SYSTEM_CTRL:GENERAL_CTRL register
    WRITE_SLAVE_INTERFACE_MODE_REG = "w 0x70000000 0x0 0x24 {}\r"
    SI_MODE_BIT_MASK = 0x30
    SI_MODE_BIT_LSHIFT = 4

    def __init__(self):
        """ Class constructor """
        pass

    def read_until(self, expected):
        """
        Virtual base read method, must be implemented by concrete classes.
        Read until an expected sequence is found or until timeout occurs.
        :param expected: string to search for
        :return: Read string up until expected sequence is found or timeout occurred
        """
        raise NotImplementedError

    def write(self, buffer):
        """
        Virtual base write method, must be implemented by concrete classes.
        Write data out.
        :param buffer: data to write
        :return: N/A
        """
        raise NotImplementedError

    def synchronise_cmd_prompt(self):
        """
        Sends a carriage return (send command) then reads until command terminator is
        received or timeout occurs because there was invalid command data in the buffer
        :return: N/A
        """
        self.write(b"\r")
        self.read_until(self.CMD_TERMINATOR)

    def get_sw_junc_temp(self):
        """
        Enable the switch temperature sensor ond obtain a reading from it
        :return: read temperature in deg C or -255.0 if read fails
        """
        return_temperature = -255.0

        self.synchronise_cmd_prompt()
        self.write(self.ENABLE_TEMP_SENSOR_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.ENABLE_SW_TEMP_SENSOR_SUCCESS not in ret_string:
            log.critical("Failed to enable temperature reading!")
        else:
            self.write(self.GET_SW_TEMP_SENSOR_READING_CMD)
            ret_string = self.read_until(self.CMD_TERMINATOR)

            if self.CMD_TERMINATOR in ret_string:
                values = ret_string.splitlines()[4].split(b" ")

                # Check that the temperature reading is valid
                temperature = int(values[0].decode("UTF-8"), base=16)
                if temperature & 0x100:
                    return_temperature = 177.4 - ((temperature & 0xFF) * 0.8777)
                    log.debug("GbE switch temperature: {:.3f} deg C".format(return_temperature))
                else:
                    log.debug("GbE switch temperature NOT valid")

        return return_temperature

    def get_phy_junc_temp(self):
        """
        Trigger a PHY temperature sensor reading and collect the result
        :return: read temperature in deg C or -255.0 if read fails
        """
        return_temperature = -255.0

        self.synchronise_cmd_prompt()
        self.write(self.TRIGGER_PHY_TEMP_SENSOR_CMD_1)
        self.read_until(self.CMD_TERMINATOR)

        self.write(self.TRIGGER_PHY_TEMP_SENSOR_CMD_2)
        self.read_until(self.CMD_TERMINATOR)

        self.write(self.GET_PHY_TEMP_SENSOR_READING_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            # Check that the temperature reading is valid
            reg_val = int(ret_string.splitlines()[2].decode("UTF-8"), base=16)
            if reg_val & 0x100:
                return_temperature = (13530 - (71 * (reg_val & 0xFF))) / 100
                log.debug("GbE PHY temperature: {:.3f} deg C".format(return_temperature))
            else:
                log.debug("GbE PHY temperature NOT valid")

        return return_temperature

    def get_sw_qsgmii_sync(self):
        """
        Check if the VSC7512 switch QSGMII is synced
        @return: True if synced, else False
        """
        qsgmii_sync = False

        self.synchronise_cmd_prompt()
        self.write(self.GET_VSC7512_QSGMII_SYNC_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            values = ret_string.splitlines()[4].split(b" ")
            reg_val = int(values[0].decode("UTF-8"), base=16)
            if reg_val & 0x1:
                qsgmii_sync = True

        return qsgmii_sync

    def get_phy_qsgmii_sync(self):
        """
        Check if the VSC8514 switch QSGMII is synced, check all 4x ports
        @return: True if synced, else False
        """
        self.synchronise_cmd_prompt()

        phy_uports = [1, 2, 3, 4]
        uport_sync = []

        for uport in phy_uports:
            cmd = self.GET_VSC8514_QSGMII_SYNC_CMD.format(uport)
            self.write(bytes(cmd, "UTF-8"))
            ret_string = self.read_until(self.CMD_TERMINATOR)

            if self.CMD_TERMINATOR in ret_string:
                reg_val = int(ret_string.splitlines()[2].decode("UTF-8"), base=16)
                if reg_val & 0x2000:
                    uport_sync.append(True)
                else:
                    uport_sync.append(False)

        if len(uport_sync) == len(phy_uports):
            qsgmii_sync = all(uport is True for uport in uport_sync)
        else:
            qsgmii_sync = False

        return qsgmii_sync

    def get_mac_addresses(self):
        """
        Reads MAC address table from the GbE switch
        :return: list of list value pairs [mac_address, u_port]
        """
        mac_addresses = []

        self.synchronise_cmd_prompt()
        self.write(self.GET_MAC_ADDRESS_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            for a_line in ret_string.splitlines():
                values = a_line.split(b" ")
                if len(values) >= 11:
                    mac_addresses.append([str(values[0].upper().decode("UTF-8")), int(values[10])])

        for entry in mac_addresses:
            log.debug("MAC: {}\tuPort: {}".format(entry[0], entry[1]))

        return mac_addresses

    def get_port_statistics(self, uport):
        """
        Read back statistics for the specified port.
        :param uport: GbE switch port no. :type Integer
        :return: GbeSwitchPortStats object representing the read values
        """
        if int(uport) not in range(self.MIN_UPORT, self.MAX_UPORT + 1, 1):
            raise ValueError("Invalid uport value {} ({}..{})".format(uport, self.MIN_UPORT, self.MAX_UPORT))

        ret_data = GbeSwitchPortStats()

        for retry in range(3):
            self.synchronise_cmd_prompt()
            cmd = self.GET_PORT_STATISTICS_CMD.format(uport)
            self.write(bytes(cmd, "UTF-8"))
            ret_string = self.read_until(self.CMD_TERMINATOR)

            if self.CMD_TERMINATOR in ret_string:
                ret_data.set_attr_from_resp_str(ret_string.decode("UTF-8"))
             
            missing_stat = False
            port_stats = vars(ret_data)
            for stat in port_stats.keys():
                if port_stats.get(stat, -1) == -1:
                    missing_stat = True
                    break
             
            if not missing_stat:
                break

            ret_data = GbeSwitchPortStats()

        return ret_data

    def get_port_link_state(self, uport):
        """
        Query the specified port's link state.
        :param uport: GbE switch port no. :type Integer
        :return: GbeSwitchLinkState object representing the port's link state
        """
        if int(uport) not in range(self.MIN_UPORT, self.MAX_UPORT + 1, 1):
            raise ValueError("Invalid uport value {} ({}..{})".format(uport, self.MIN_UPORT, self.MAX_UPORT))

        link_state = GbeSwitchLinkState.UNKNOWN

        self.synchronise_cmd_prompt()
        self.write(self.GET_PORT_STATUS_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            ret_string = ret_string.decode("UTF-8")
            for line in ret_string.splitlines():
                # print(line)
                split_line = line.split()
                if len(split_line) > 0 and split_line[0] == str(uport):
                    if "Down" in line:
                        link_state = GbeSwitchLinkState.DOWN
                    elif "Up" in line and "100MFDX FC(D)" in line:
                        link_state = GbeSwitchLinkState.UP_FAST
                    elif "Up" in line and "1GFDX FC(D)" in line:
                        link_state = GbeSwitchLinkState.UP_GBE
                    else:
                        link_state = GbeSwitchLinkState.UNKNOWN

        return link_state

    def get_software_version(self):
        """
        Get the Kirintec software part and version numbers from the GbE Switch
        :return: [0] software part number :type String
        :return: [1] software version number :type String
        """
        sw_part_no = ""
        sw_version_no = ""

        self.synchronise_cmd_prompt()
        self.write(self.GET_VERSION_CMD)
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            ret_string = ret_string.decode("UTF-8")
            for line in ret_string.splitlines():
                if self.SOFTWARE_PART_NO_10_PORT in line or self.SOFTWARE_PART_NO_4_PORT in line:
                    split_line = line.split()
                    sw_part_no = split_line[-4 if "4-port" in line or "10-port" in line else -3]
                    sw_version_no = split_line[-2 if "4-port" in line or "10-port" in line else-1]

        return sw_part_no, sw_version_no

    def set_si_mode(self, si_mode):
        """
        Set the Serial Interface mode
        :param si_mode: one of GbeSwitchSiMode enumerated values
        :return: True if serial interface set, else false
        """
        if si_mode not in GbeSwitchSiMode:
            raise ValueError("si_mode must be a GbeSwitchSiMode enumerated value")

        self.synchronise_cmd_prompt()
        self.write(self.READ_SLAVE_INTERFACE_MODE_REG)
        ret_string = self.read_until(self.CMD_TERMINATOR)
        log.debug(ret_string)

        if self.CMD_TERMINATOR in ret_string:
            values = ret_string.splitlines()[4].split(b" ")
            reg_val = int(values[0].decode("UTF-8"), base=16)
            reg_val &= (~self.SI_MODE_BIT_MASK)
            reg_val |= ((si_mode.value << self.SI_MODE_BIT_LSHIFT) & self.SI_MODE_BIT_MASK)
            cmd = self.WRITE_SLAVE_INTERFACE_MODE_REG.format(reg_val).encode("UTF-8")
            log.debug(cmd)
            self.write(cmd)
            ret_string = self.read_until(self.CMD_TERMINATOR)
            log.debug(ret_string)
            if self.CMD_TERMINATOR in ret_string:
                return True
            else:
                return False

    def find_lwip_autoip_addresses(self):
        """
        Reads MAC address table from the GbE switch, uses MAC addresses to compose LWIP AUTOIP addresses
        then tries to ping them
        :return: list of IP addresses that responded to LWIP AUTOIP ping
        """
        ip_address_list = []
        mac_address_list = self.get_mac_addresses()

        for mac in mac_address_list:
            ip_address = self.build_lwip_autoip_address(mac[0])
            log.debug("Pinging: {}".format(ip_address))
            if self.ping_ip(ip_address, retries=2, timeout=1):
                ip_address_list.append(ip_address)

        log.debug("Found the following LWIP AUTOIP addresses: {}".format(ip_address_list))

        return ip_address_list

    @staticmethod
    def build_lwip_autoip_address(mac_address):
        # [0 - 9a - fA - F] matches characters the used to represent hexadecimal numbers
        # :? matches an optional colon
        # (...) {12} - all of this is then grouped and repeated 12 times.   12 because a MAC address
        # consists of 6 pairs of hexadecimal numbers, separated by a - or :
        rexp = re.compile(r'(?:[0-9a-fA-F]-?:?){12}')
        mac_addresses = re.findall(rexp, mac_address)

        if len(mac_addresses) >= 1:
            values = mac_addresses[0].split("-")
            # Default LWIP AUTOIP address is built using MAC address values 4 and 5 (0 index),
            # the address will be in the range 169.254.1.0 to 169.254.254.255 compliant to RFC 3927 Section 2.1.
            autoip_range_start = 0xA9FE0100
            autoip_range_end = 0xA9FEFEFF

            autoip_address = autoip_range_start + ((int(values[5], base=16) << 8) | int(values[4], base=16))

            # autoip_address is in range 169.254.0.0 <= addr <= 169.254.255.255, trim to required range
            if autoip_address < autoip_range_start:
                autoip_address += autoip_range_end - autoip_range_start + 1

            if autoip_address > autoip_range_end:
                autoip_address -= autoip_range_end - autoip_range_start + 1

            return "169.254.{}.{}".format((autoip_address >> 8) & 0xFF, autoip_address & 0xFF)
        else:
            return "0.0.0.0"

    @staticmethod
    def ping_ip(ip_address, retries=1, timeout=3):
        """
        Calls the system ping command for the specified IP address
        :param ip_address: ip address to ping :type: string
        :param retries: number of times to retry failed ping before giving up :type: integer
        :param timeout: number of seconds to wait for ping response
        :return: True if the IP address is successfully pinged with retries attempts, else False
        """
        try:
            return_val = False

            if platform.system().lower() == "windows":
                count_param = "n"
                timeout_param = "{}".format(timeout * 1000)
            else:
                count_param = "c"
                timeout_param = "{}".format(timeout)

            for i in range(0, retries):
                output = popen("ping -w {} -{} 1 {}".format(timeout_param, count_param, ip_address)).read()
                # log.debug("Ping {}:".format(i))
                # log.debug(output)

                # If a bad address is used then the output will be an empty string
                if not output or "unreachable" in output or "0 packets received" in output \
                        or "could not find" in output or "Request timed out" in output:
                    return_val = False
                else:
                    return_val = True
                    break

            return return_val

        except Exception as ex:
            log.critical("Something went wrong with the ping! - {}".format(ex))
            return False


class TelnetGbeSwitch(GbeSwitch):
    """
    Take care when using the context manager as the Active Backplane firmware will
    close the Telnet connection if it is idle for more than 10-seconds.
    """
    def __init__(self, telnet_server=None, telnet_port=31):
        """
        Class constructor
        :param telnet_server: Telnet IP address or hostname :type: string
        :param telnet_port: Telnet port number to connect to :type: integer
        """
        self._telnet_client = None
        self._telnet_server = telnet_server
        self._telnet_port = telnet_port
        if telnet_server is not None:
            self.open_telnet_client(telnet_server, telnet_port)

        super().__init__()

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "TelnetGbeSwitch({!r}, {!r})".format(self._telnet_server, self._telnet_port)

    def __del__(self):
        """ Class destructor - close the Telnet client """
        self.close_telnet_client()

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the Telnet client """
        self.close_telnet_client()

    def open_telnet_client(self, telnet_server, telnet_port):
        """
        Opens a connection to the specified telnet server
        :param telnet_server: Telnet IP address or hostname :type: string
        :param telnet_port: Telnet port number to connect to :type: integer
        :return: N/A
        """
        self._telnet_client = Telnet(telnet_server, telnet_port)
        log.debug("Telnet Client host: {}; port {}".format(telnet_server, telnet_port))
        self._telnet_server = telnet_server
        self._telnet_port = telnet_port

    def close_telnet_client(self):
        """ Closes _telnet_client Telnet client if it is open """
        if self._telnet_client is not None:
            log.debug("Closing Telnet Client host: {}; port {}".format(self._telnet_server, self._telnet_port))
            self._telnet_client.close()
        self._telnet_server = ""
        self._telnet_port = -1

    def read_until(self, expected):
        """ Concrete implementation of virtual read_until method """
        if self._telnet_client is not None:
            return self._telnet_client.read_until(expected, self.TIMEOUT_SEC)
        else:
            raise RuntimeError("Telnet client is not open!")

    def write(self, buffer):
        """ Concrete implementation of virtual write method """
        if self._telnet_client is not None:
            self._telnet_client.write(buffer)
        else:
            raise RuntimeError("Telnet client is not open!")


class SerialGbeSwitch(GbeSwitch):
    def __init__(self, com_port=None, baud_rate=115200):
        """
        Class constructor
        :param com_port: COM port for accessing the GbE switch serial management interface :type: string
        :param baud_rate: serial baud rate, default 115200 :type: integer
        """
        self._serial_port = None
        self._com_port = com_port
        self._baud_rate = baud_rate
        if com_port is not None:
            self.open_com_port(com_port, baud_rate)

        super().__init__()

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "SerialGbeSwitch({!r}, {!r})".format(self._com_port, self._baud_rate)

    def __del__(self):
        """ Class destructor - close the serial port """
        self.close_com_port()

    def __enter__(self):
        """ Context manager entry """
        return self

    def __exit__(self, exc_ty, exc_val, tb):
        """ Context manager exit - close the serial port"""
        self.close_com_port()

    def open_com_port(self, com_port, baud_rate):
        """
        Opens the specified serial port
        :param com_port: COM port to open :type string
        :param baud_rate: serial baud rate, default 115200 :type: integer
        :return: N/A
        """
        self._serial_port = Serial(com_port, baud_rate, timeout=self.TIMEOUT_SEC,
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

    def read_until(self, expected):
        """ Concrete implementation of virtual read_until method """
        if self._serial_port is not None:
            return self._serial_port.read_until(expected)
        else:
            raise RuntimeError("Serial port is not open!")

    def write(self, buffer):
        """ Concrete implementation of virtual write method """
        if self._serial_port is not None:
            self._serial_port.write(buffer)
        else:
            raise RuntimeError("Serial port is not open!")


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(kw_args):
    """
    Blah...
    :return: None
    """
    gs = SerialGbeSwitch(kw_args.com_port, kw_args.baud_rate)

    if kw_args.lwip_addr:
        log.info("INFO - Found the following lwIP AUTOIP addresses: {}".format(gs.find_lwip_autoip_addresses()))

    if int(kw_args.port_link_state) > 0:
        u_port = int(kw_args.port_link_state)
        log.info("INFO - uPort {} Link State: {}".format(u_port, gs.get_port_link_state(u_port)))

    if int(kw_args.port_stats) > 0:
        u_port = int(kw_args.port_stats)
        log.info("INFO - uPort {} Statistics:\n{}".format(u_port, json.dumps(vars(gs.get_port_statistics(u_port)))))

    if int(kw_args.reset) >= 0:
        gpio_reg_val = DevMem.read(GPIO0_REG_ADDRESS)
        if int(kw_args.reset):
            gpio_reg_val &= (~GPIO0_ETH_SW_RESET_N_BIT)
        else:
            gpio_reg_val |= GPIO0_ETH_SW_RESET_N_BIT
        DevMem.write(GPIO0_REG_ADDRESS, gpio_reg_val)

    if kw_args.si_mode != "":
        set_si_mode = getattr(GbeSwitchSiMode, kw_args.si_mode)
        success = gs.set_si_mode(set_si_mode)
        log.info("{} - Set Serial Interface mode to: {}".format("PASS" if success else "FAIL", set_si_mode))

    if kw_args.temp:
        log.info("INFO - VSC7512 junction temperature (deg C): {:.2f}".format(gs.get_sw_junc_temp()))
        log.info("INFO - VSC8514 junction temperature (deg C): {:.2f}".format(gs.get_phy_junc_temp()))

    if kw_args.version:
        fw_part_no, fw_ver_no = gs.get_software_version()
        log.info("INFO - GbE Switch Firmware {} {}".format(fw_part_no, fw_ver_no))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="GbE Switch Interface")
    parser.add_argument("-b", "--baud_rate", default=115200, help="Serial baud rate")
    parser.add_argument("-c", "--com_port", required=True, help="Serial COM port")
    parser.add_argument("-l", "--lwip_addr", action="store_true", help="Print lwIP IPV4 addresses")
    parser.add_argument("-p", "--port_link_state", default=0, help="Print port link state")
    parser.add_argument("-r", "--reset", default=-1, help="Assert hardware reset")
    parser.add_argument("-s", "--port_stats", default=0, help="Print port statistics as JSON string")
    parser.add_argument("-si", "--si_mode", default="", help="Set SI mode: SLAVE, BOOT_MASTER, MASTER")
    parser.add_argument("-t", "--temp", action="store_true", help="Print junction temperatures")
    parser.add_argument("-v", "--version", action="store_true", help="Print software version")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args)
