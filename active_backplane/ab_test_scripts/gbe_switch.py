#!/usr/bin/env python3
"""
Module for accessing VSC7512 GbE switch registers using the Active Backplane
Telnet server
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-t/--telnet_server required argument specifies Telnet Server IP address
-p/--port specifies Telnet Server IP address (default 31)
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
from dataclasses import dataclass
from enum import Enum
import logging
from os import popen
import platform
import re
from telnetlib import Telnet

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
class GbeSwitchLinkState(Enum):
    UNKNOWN = -1
    DOWN = 0
    UP_FAST = 2
    UP_GBE = 3


@dataclass
class GbeSwitchPortStats:
    """
    Utility class to represent port statistics read from the switch.
    """
    rx_packets: int = -1
    rx_octets: int = -1
    rx_broadcast: int = -1
    rx_multicast: int = -1
    rx_pause: int = -1
    rx_error_packets: int = -1
    rx_mac_ctrl: int = -1
    rx_crc_alignment: int = -1
    rx_undersize: int = -1
    rx_oversize: int = -1
    rx_fragments: int = -1
    rx_jabbers: int = -1
    rx_drops: int = -1
    rx_classifier_drops: int = -1
    tx_packets: int = -1
    tx_octets: int = -1
    tx_broadcast: int = -1
    tx_multicast: int = -1
    tx_pause: int = -1
    tx_error_packets: int = -1
    tx_collisions: int = -1
    tx_drops: int = -1
    tx_overflow: int = -1
    tx_aged: int = -1
    rx_64_bytes: int = -1
    tx_64_bytes: int = -1
    rx_65_127_bytes: int = -1
    tx_65_127_bytes: int = -1
    rx_128_255_bytes: int = -1
    tx_128_255_bytes: int = -1
    rx_256_511_bytes: int = -1
    tx_256_511_bytes: int = -1
    rx_512_1023_bytes: int = -1
    tx_512_1023_bytes: int = -1
    rx_1024_bytes: int = -1
    tx_1024_bytes: int = -1

    def set_attr_from_resp_str(self, port_statistic_str):
        """
        Class constructor, takes the response to a Get Port Statistics
        command as input and extracts attributes
        @param port_statistic_str:
        """
        if not isinstance(port_statistic_str, str):
            raise ValueError("port_statistic_str must be a string!")

        for line in port_statistic_str.splitlines():
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

    def __init__(self):
        """ Class constructor """
        pass

    def read_until(self, expected):
        """
        Virtual base read method, must be implemented by concrete classes.
        Read until an expected sequence is found or until timeout occurs.
        :param expected: string to search for
        :return: Read string up until ezpected sequence is found or timeout occurred
        """
        raise NotImplementedError

    def write(self, buffer):
        """
        Virtual base read method, must be implemented by concrete classes.
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
        :return: read temperaturein deg C or -255.0 if read fails
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
        if int(uport) not in range(self.MIN_UPORT, self.MAX_UPORT, 1):
            raise ValueError("Invalid uport value {} ({}..{})".format(uport, self.MIN_UPORT, self.MAX_UPORT))

        ret_data = GbeSwitchPortStats()

        self.synchronise_cmd_prompt()
        cmd = self.GET_PORT_STATISTICS_CMD.format(uport)
        self.write(bytes(cmd, "UTF-8"))
        ret_string = self.read_until(self.CMD_TERMINATOR)

        if self.CMD_TERMINATOR in ret_string:
            ret_data.set_attr_from_resp_str(ret_string.decode("UTF-8"))

        return ret_data

    def get_port_link_state(self, uport):
        """
        Query the specified port's link state.
        :param uport: GbE switch port no. :type Integer
        :return: GbeSwitchLinkState object representing the port's link state
        """
        if int(uport) not in range(self.MIN_UPORT, self.MAX_UPORT, 1):
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
                    print(split_line)
                    sw_part_no = split_line[-4 if "4-port" in line or "10-port" in line else -3]
                    sw_version_no = split_line[-2 if "4-port" in line or "10-port" in line else-1]

        return sw_part_no, sw_version_no

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
            # Default LWIP AUTOIP address is built using MAC address values 4 and 5 (0 index)
            return "169.254.{}.{}".format(int(values[5], base=16) + 1, int(values[4], base=16))
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

                if "unreachable" in output or "0 packets received" or "could not find" in output:
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
        Opens the specified serial port
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
def main(telnet_server, telnet_port):
    """
    Blah...
    :return: None
    """
    gs = TelnetGbeSwitch(telnet_server, telnet_port)
    gs.get_sw_junc_temp()
    gs.find_lwip_autoip_addresses()


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Active Backplane Telnet server test")
    parser.add_argument("-t", "--telnet_server", required=True, dest="telnet_server", action="store",
                        help="Telnet Server IP address")
    parser.add_argument("-p", "--telnet_port", default=31, dest="telnet_port", action="store",
                        help="Telnet Server port number")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    main(args.telnet_server, args.telnet_port)
