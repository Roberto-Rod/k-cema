#!/usr/bin/env python3
"""
Module for handling serial messages using the K-CEMA serial protocol
specified in KT-957-0413-00. Implements the NEO Battery Box command set.
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
import logging
import struct
import time

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT

# Our own imports ---------------------------------------------------
import serial_message_handler as smh

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SERIAL_TIMEOUT = 2.0

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class BbMsgId(Enum):
    """
    Enumeration for message identifiers
    """
    PING = 0x00
    GET_SOFTWARE_VERSION_NUMBER = 0x01
    GET_DYNAMIC_BATTERY_PARAMETERS = 0x80
    GET_STATIC_BATTERY_PARAMETERS = 0x81


class BbMsgPayloadLen(Enum):
    """
    Enumeration for payload lengths
    """
    PING = 0
    GET_SOFTWARE_VERSION_NUMBER = 11
    GET_DYNAMIC_BATTERY_PARAMETERS = 45
    GET_STATIC_BATTERY_PARAMETERS = 17


class BbSoftwareVersionInfo:
    payload_version: int = -1
    sw_major: int = -1
    sw_minor: int = -1
    sw_patch: int = -1
    sw_build: int = -1


class BbBatteryStatus:
    error_code: int = -1
    fully_discharged: bool = False
    fully_charged: bool = False
    discharging: bool = False
    initialised: bool = False
    remaining_time: bool = False
    remaining_capacity: bool = False
    terminate_discharge: bool = False
    over_temperature: bool = False
    terminate_charge: bool = False
    over_charged: bool = False


class BbDynamicBatteryParameters:
    payload_version: int = -1
    battery_1a_voltage: int = -32768
    battery_1a_current: int = -32768
    battery_1a_state_of_charge: int = -1
    battery_1a_temperature: int = -1
    battery_1a_status: BbBatteryStatus()
    battery_1a_remaining_energy: int = -1
    battery_1b_voltage: int = -32768
    battery_1b_current: int = -32768
    battery_1b_state_of_charge: int = -1
    battery_1b_temperature: int = -1
    battery_1b_status: BbBatteryStatus()
    battery_1b_remaining_energy: int = -1
    battery_2a_voltage: int = -32768
    battery_2a_current: int = -32768
    battery_2a_state_of_charge: int = -1
    battery_2a_temperature: int = -1
    battery_2a_status: BbBatteryStatus()
    battery_2a_remaining_energy: int = -1
    battery_2b_voltage: int = -32768
    battery_2b_current: int = -32768
    battery_2b_state_of_charge: int = -1
    battery_2b_temperature: int = -1
    battery_2b_status: BbBatteryStatus()
    battery_2b_remaining_energy: int = -1


class BbStaticBatteryParameters:
    payload_version: int = -1
    battery_1a_serial_no: int = -1
    battery_1a_design_capacity: int = -1
    battery_1b_serial_no: int = -1
    battery_1b_design_capacity: int = -1
    battery_2a_serial_no: int = -1
    battery_2a_design_capacity: int = -1
    battery_2b_serial_no: int = -1
    battery_2b_design_capacity: int = -1


class BbSerialMsgInterface:
    """
    Class for handling serial messages to the NEO Battery Box,the serial message
    ICD is defined in document KT-957-0413-00
    """

    def __init__(self, serial_port, baud_rate=115200):
        """
        Class constructor
        :param None
        :return: NA
        """
        self._serial_port = serial_port
        self._baud_rate = baud_rate
        self.smh = None

    def __enter__(self):
        if self.smh is not None:
            raise RuntimeError("Already started SMH!")
        self.smh = smh.MessageHandler()
        if not self.smh.start(self._serial_port, self._baud_rate):
            raise RuntimeError("Failed to start SMH!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.smh.stop()

    def wait_for_ack(self, ack_no, msg_id):
        """
        Wait for an ack to be received in response to a transmitted message
        :param ack_no: sequence no of message that is being acked
        :param msg_id: ID of message that is being acked
        :return: True if the ack received before SERIAL_TIMEOUT, else False
        """
        ret_val = False
        rx_timeout = time.time() + SERIAL_TIMEOUT
        while True:
            time.sleep(0.01)
            rx_msg = self.smh.get_from_rx_queue()
            if rx_msg:
                log.debug("Wait for Ack Rx Msg: {}".format(" ".join(format(x, '02x') for x in rx_msg)))

                if len(rx_msg) == smh.TOTAL_HEADER_LENGTH:
                    if rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value] == ack_no and \
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value] == msg_id and \
                            ((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x40):
                        ret_val = True
                        break
                    else:
                        log.debug("Wait for Ack Rx Msg Failed Consistency Check! {} - {}; {} - {}; {}".format(
                            rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value], ack_no,
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value], msg_id,
                            rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0))
                else:
                    log.debug("Wait for Ack Rx Msg Failed Length Check!")

            if time.time() > rx_timeout:
                log.debug("Wait for Ack Rx Msg Timed Out! - {:02x}".format(msg_id))
                break

        return ret_val

    def send_bad_ping(self, bad_id=False, bad_crc=False, short_msg=False):
        """
        Sends a Ping message, waits for the response and processes it
        :return: True if Ping is successfully acked, else False :type Boolean
        """
        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=0xF5 if bad_id else BbMsgId.PING.value,  # Invalid Msg ID
            pl_len=0)  # No payload

        if bad_crc:     # Corrupt the CRC
            header_bytes[-1] += 1

        if short_msg:   # Truncate header
            header_bytes = header_bytes[:-2]

        log.debug("Tx Ping: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self.smh.send_to_tx_queue(header_bytes)

        return self.wait_for_ack(seq_no, BbMsgId.PING.value)

    def send_ping(self):
        """
        Sends a Ping message, waits for the response and processes it
        :return: True if Ping is successfully acked, else False :type Boolean
        """
        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=BbMsgId.PING.value,
            pl_len=0)  # No payload

        log.debug("Tx Ping: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self.smh.send_to_tx_queue(header_bytes)

        return self.wait_for_ack(seq_no, BbMsgId.PING.value)

    def get_command(self, get_cmd, resp_payload_len):
        """
        Sends a command that expects a response, processes ACK response and returns response message
        :return: [0] True if response received, else False; [1] the received message
        """
        if get_cmd not in BbMsgId:
            raise ValueError("get_cmd must be one of BbMsgId enumerated values")
        if resp_payload_len not in BbMsgPayloadLen:
            raise ValueError("get_cmd must be one of BbMsgPayloadLen enumerated values")

        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=get_cmd.value,
            pl_len=0)  # No payload

        log.debug("Tx Get Cmd: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self.smh.send_to_tx_queue(header_bytes)

        # Wait for Ack, if it's successful wait for response
        if not self.wait_for_ack(seq_no, get_cmd.value):
            log.debug("No Ack")
            return False, None

        ret_val = False
        rx_timeout = time.time() + SERIAL_TIMEOUT
        while True:
            time.sleep(0.01)
            rx_msg = self.smh.get_from_rx_queue()
            if rx_msg:
                log.debug("Get Cmd Rx Msg: {}".format(" ".join(format(x, '02x') for x in rx_msg)))

                if len(rx_msg) == smh.TOTAL_HEADER_LENGTH + resp_payload_len.value + smh.CRC_LENGTH:
                    if rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value] == seq_no and \
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value] == get_cmd.value and \
                            (((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x80) or
                                ((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x00)):
                        ret_val = True
                        break
                    else:
                        log.debug("Get Cmd Rx Msg Failed Consistency Check! {} - {}; {} - {}; {}".format(
                            rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value], seq_no,
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value], get_cmd.value,
                            rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0))
                else:
                    log.debug("Get Cmd Rx Msg Failed Length Check!")

            if time.time() > rx_timeout:
                log.debug("Get Cmd Rx Msg Timed Out! - {:02x}".format(get_cmd.value))
                break

        return ret_val, rx_msg

    def get_software_version(self):
        """
        Get Software Version Information
        :return: [0] True if response received, else False;
                 [1] BbSoftwareVersionInfo instance representing the software version information
        """
        sw_info = BbSoftwareVersionInfo()
        ret_val, rx_msg = self.get_command(BbMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                           BbMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)

        if ret_val:
            sw_info.payload_version, sw_info.sw_major, sw_info.sw_minor, sw_info.sw_patch, sw_info.sw_build = \
                struct.unpack("<BHHHI", rx_msg[smh.TOTAL_HEADER_LENGTH:len(rx_msg) - smh.CRC_LENGTH])

        return ret_val, sw_info

    def send_software_version(self, sw_info, resp_seq_no):
        """
        Send a static battery parameters response message with given parameters
        then wait for the corresponding Ack to be received
        :param resp_seq_no: sequence number of message being responded to :type Integer
        :param sw_info: software version information to transmit :type BbSoftwareVersionInfo
        :return: True if response successfully sent, else False :type Boolean
        """
        if type(sw_info) != BbSoftwareVersionInfo:
            raise ValueError("sw_info must be of type BbSoftwareVersionInfo")

        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                     ack_no=resp_seq_no,
                                                     status=0,  # Status = '0' for new message and Protocol = '0'
                                                     msg_id=BbMsgId.GET_SOFTWARE_VERSION_NUMBER.value,
                                                     pl_len=BbMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER.value)

        payload_bytes = bytearray(struct.pack("<BHHHI",
                                              sw_info.payload_version, sw_info.sw_major, sw_info.sw_minor,
                                              sw_info.sw_patch, sw_info.sw_build))

        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        self.smh.send_to_tx_queue(header_bytes + payload_bytes)

        log.debug("Tx Software Version Resp: {} {}".format(" ".join(format(x, '02x') for x in header_bytes),
                                                           " ".join(format(x, '02x') for x in payload_bytes)))

        # Wait for Ack
        ret_val = self.wait_for_ack(seq_no, BbMsgId.GET_SOFTWARE_VERSION_NUMBER.value)

        if not ret_val:
            log.debug("Ack not rx'd!")

        return ret_val

    def get_dynamic_battery_parameters(self):
        """
        Get Dynamic Battery Parameters
        :return: [0] True if response received, else False;
                 [1] BbDynamicBatteryParameters instance representing the battery dynamic parameters
        """
        bdp = BbDynamicBatteryParameters()
        ret_val, rx_msg = self.get_command(BbMsgId.GET_DYNAMIC_BATTERY_PARAMETERS,
                                           BbMsgPayloadLen.GET_DYNAMIC_BATTERY_PARAMETERS)

        if ret_val:
            bdp.payload_version, \
                bdp.battery_1a_voltage, \
                bdp.battery_1a_current, \
                bdp.battery_1a_state_of_charge, \
                bdp.battery_1a_temperature, \
                battery_1a_status_word, \
                bdp.battery_1a_remaining_energy, \
                bdp.battery_1b_voltage, \
                bdp.battery_1b_current, \
                bdp.battery_1b_state_of_charge, \
                bdp.battery_1b_temperature, \
                battery_1b_status_word, \
                bdp.battery_1b_remaining_energy, \
                bdp.battery_2a_voltage, \
                bdp.battery_2a_current, \
                bdp.battery_2a_state_of_charge, \
                bdp.battery_2a_temperature, \
                battery_2a_status_word, \
                bdp.battery_2a_remaining_energy, \
                bdp.battery_2b_voltage, \
                bdp.battery_2b_current, \
                bdp.battery_2b_state_of_charge, \
                bdp.battery_2b_temperature, \
                battery_2b_status_word, \
                bdp.battery_2b_remaining_energy = \
                struct.unpack("<BhhBHHHhhBHHHhhBHHHhhBHHH",
                              rx_msg[smh.TOTAL_HEADER_LENGTH:len(rx_msg) - smh.CRC_LENGTH])

            bdp.battery_1a_status = self.unpack_battery_status(battery_1a_status_word)
            bdp.battery_1b_status = self.unpack_battery_status(battery_1b_status_word)
            bdp.battery_2a_status = self.unpack_battery_status(battery_2a_status_word)
            bdp.battery_2b_status = self.unpack_battery_status(battery_2b_status_word)

        if not ret_val:
            log.info("Get Dynamic Parameters Response Failed!")

        return ret_val, bdp

    @staticmethod
    def unpack_battery_status(battery_status_word):
        """
        Convert a 16-bit battery status word into a BbBatteryStatus instance
        :param battery_status_word: 16-bit battery status word
        :return: BbBatteryStatus representation of the battery status word
        """
        if type(battery_status_word) is not int:
            raise ValueError("battery_status must be an integer!")

        battery_status = BbBatteryStatus()
        battery_status.error_code = battery_status_word & 0x000F
        battery_status.fully_discharged = True if battery_status_word & 0x0010 else False
        battery_status.fully_charged = True if battery_status_word & 0x0020 else False
        battery_status.discharging = True if battery_status_word & 0x0040 else False
        battery_status.initialised = True if battery_status_word & 0x0080 else False
        battery_status.remaining_time = True if battery_status_word & 0x0100 else False
        battery_status.remaining_capacity = True if battery_status_word & 0x0200 else False
        battery_status.terminate_discharge = True if battery_status_word & 0x0400 else False
        battery_status.over_temperature = True if battery_status_word & 0x1000 else False
        battery_status.terminate_charge = True if battery_status_word & 0x4000 else False
        battery_status.over_charged = True if battery_status_word & 0x8000 else False

        return battery_status

    @staticmethod
    def pack_battery_status(battery_status):
        """
        Convert a BbBatteryStatus instance into a 16-bit battery status word
        :param battery_status: battery status instance type: BbBatteryStatus
        :return: battery_status_word: 16-bit battery status word
        """
        if type(battery_status) is not BbBatteryStatus:
            raise ValueError("battery_status must be type BbBatteryStatus!")

        battery_status_word = 0x0000
        battery_status_word |= (battery_status.error_code & 0x000F)
        battery_status_word |= (0x0010 if battery_status.fully_discharged else 0x0000)
        battery_status_word |= (0x0020 if battery_status.fully_charged else 0x0000)
        battery_status_word |= (0x0040 if battery_status.discharging else 0x0000)
        battery_status_word |= (0x0080 if battery_status.initialised else 0x0000)
        battery_status_word |= (0x0100 if battery_status.remaining_time else 0x0000)
        battery_status_word |= (0x0200 if battery_status.remaining_capacity else 0x0000)
        battery_status_word |= (0x0800 if battery_status.terminate_discharge else 0x0000)
        battery_status_word |= (0x1000 if battery_status.over_temperature else 0x0000)
        battery_status_word |= (0x4000 if battery_status.over_temperature else 0x0000)
        battery_status_word |= (0x8000 if battery_status.over_charged else 0x0000)

        return battery_status_word

    def send_dynamic_battery_parameters(self, bdp, resp_seq_no):
        """
        Send a static battery parameters response message with given parameters
        then wait for the corresponding Ack to be received
        :param resp_seq_no: sequence number of message being responded to :type Integer
        :param bdp: dynamic parameters to transmit :type BbDynamicBatteryParameters
        :return: True if response successfully sent, else False :type Boolean
        """
        if type(bdp) != BbDynamicBatteryParameters:
            raise ValueError("parameters must be of type BbDynamicBatteryParameters")

        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                     ack_no=resp_seq_no,
                                                     status=0,  # Status = '0' for new message and Protocol = '0'
                                                     msg_id=BbMsgId.GET_DYNAMIC_BATTERY_PARAMETERS.value,
                                                     pl_len=BbMsgPayloadLen.GET_DYNAMIC_BATTERY_PARAMETERS.value)
        battery_1a_status_word = self.pack_battery_status(bdp.battery_1a_status)
        battery_1b_status_word = self.pack_battery_status(bdp.battery_1b_status)
        battery_2b_status_word = self.pack_battery_status(bdp.battery_2b_status)
        battery_2a_status_word = self.pack_battery_status(bdp.battery_2a_status)

        payload_bytes = bytearray(struct.pack("<BhhBHHHhhBHHHhhBHHHhhBHHH",
                                              bdp.payload_version,
                                              bdp.battery_1a_voltage,
                                              bdp.battery_1a_current,
                                              bdp.battery_1a_state_of_charge,
                                              bdp.battery_1a_temperature,
                                              battery_1a_status_word,
                                              bdp.battery_1a_remaining_energy,
                                              bdp.battery_1b_voltage,
                                              bdp.battery_1b_current,
                                              bdp.battery_1b_state_of_charge,
                                              bdp.battery_1b_temperature,
                                              battery_1b_status_word,
                                              bdp.battery_1b_remaining_energy,
                                              bdp.battery_2a_voltage,
                                              bdp.battery_2a_current,
                                              bdp.battery_2a_state_of_charge,
                                              bdp.battery_2a_temperature,
                                              battery_2a_status_word,
                                              bdp.battery_2a_remaining_energy,
                                              bdp.battery_2b_voltage,
                                              bdp.battery_2b_current,
                                              bdp.battery_2b_state_of_charge,
                                              bdp.battery_2b_temperature,
                                              battery_2b_status_word,
                                              bdp.battery_2b_remaining_energy))

        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        self.smh.send_to_tx_queue(header_bytes + payload_bytes)

        log.debug("Tx Dynamic Batt Params Resp: {} {}".format(" ".join(format(x, '02x') for x in header_bytes),
                                                              " ".join(format(x, '02x') for x in payload_bytes)))

        # Wait for Ack
        ret_val = self.wait_for_ack(seq_no, BbMsgId.GET_DYNAMIC_BATTERY_PARAMETERS.value)

        if not ret_val:
            log.debug("Ack not rx'd!")

        return ret_val

    def get_static_battery_parameters(self):
        """
        Get Static Battery Parameters
        :return: [0] True if response received, else False;
                 [1] BbStaticBatteryParameters instance representing the battery static parameters
        """
        bsp = BbStaticBatteryParameters()
        ret_val, rx_msg = self.get_command(BbMsgId.GET_STATIC_BATTERY_PARAMETERS,
                                           BbMsgPayloadLen.GET_STATIC_BATTERY_PARAMETERS)

        if ret_val:
            bsp.payload_version, \
                bsp.battery_1a_serial_no, \
                bsp.battery_1a_design_capacity, \
                bsp.battery_1b_serial_no, \
                bsp.battery_1b_design_capacity, \
                bsp.battery_2a_serial_no, \
                bsp.battery_2a_design_capacity, \
                bsp.battery_2b_serial_no, \
                bsp.battery_2b_design_capacity = \
                struct.unpack("<BHHHHHHHH", rx_msg[smh.TOTAL_HEADER_LENGTH:len(rx_msg) - smh.CRC_LENGTH])

        if not ret_val:
            log.info("Get Static Parameters Response Failed!")

        return ret_val, bsp

    def send_static_battery_parameters(self, bsp, resp_seq_no):
        """
        Send a static battery parameters response message with given parameters
        then wait for the corresponding Ack to be received
        :param resp_seq_no: sequence number of message being responded to :type Integer
        :param bsp: static parameters to transmit :type BbStaticBatteryParameters
        :return: True if response successfully sent, else False :type Boolean
        """
        if type(bsp) != BbStaticBatteryParameters:
            raise ValueError("parameters must be of type BbStaticBatteryParameters")

        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                     ack_no=resp_seq_no,
                                                     status=0,  # Status = '0' for new message and Protocol = '0'
                                                     msg_id=BbMsgId.GET_STATIC_BATTERY_PARAMETERS.value,
                                                     pl_len=BbMsgPayloadLen.GET_STATIC_BATTERY_PARAMETERS.value)

        payload_bytes = bytearray(struct.pack("<BHHHHHHHH",
                                              bsp.payload_version,
                                              bsp.battery_1a_serial_no,
                                              bsp.battery_1a_design_capacity,
                                              bsp.battery_1b_serial_no,
                                              bsp.battery_1b_design_capacity,
                                              bsp.battery_2a_serial_no,
                                              bsp.battery_2a_design_capacity,
                                              bsp.battery_2b_serial_no,
                                              bsp.battery_2b_design_capacity))

        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        self.smh.send_to_tx_queue(header_bytes + payload_bytes)

        log.debug("Tx Static Batt Params Resp: {} {}".format(" ".join(format(x, '02x') for x in header_bytes),
                                                             " ".join(format(x, '02x') for x in payload_bytes)))

        # Wait for Ack
        ret_val = self.wait_for_ack(seq_no, BbMsgId.GET_STATIC_BATTERY_PARAMETERS.value)

        if not ret_val:
            log.debug("Ack not rx'd!")

        return ret_val

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Module is NOT intended to be executed stand-alone, print warning message
    """
    print("Module is NOT intended to be executed stand-alone")
