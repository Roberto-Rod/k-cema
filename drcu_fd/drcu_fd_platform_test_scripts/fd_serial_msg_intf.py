#!/usr/bin/env python3
"""
Module for handling serial messages using the K-CEMA serial protocol
specified in KT-957-0143-00. Implements the Fill Device Microcontroller command set
for communicating with the Fill Device Microcontroller Firmware, KT-956-0377-00.
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
FD_SERIAL_TIMEOUT = 2.0

FD_LED_PATTERNS = {
    "OFF": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    "BLINK_HALF_HZ": [0xF0, 0xF0, 0xF0, 0xF0, 0xF0, 0xF0],
    "BLINK_ONE_HZ": [0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00],
    "BLINK_ONE_HALF_HZ": [0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00],
    "BLINK_SYNC_START": [0xFF, 0x00, 0x00, 0x00, 0x00, 0x00],
    "ON": [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
}

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class FdMsgId(Enum):
    """ Enumeration for message identifiers """
    PING = 0x00
    GET_SOFTWARE_VERSION_NUMBER = 0x01
    SET_LED_PATTERN = 0x02
    BUTTON_STATUS = 0x05


class FdMsgPayloadLen(Enum):
    """ Enumeration for payload lengths """
    PING = 0
    GET_SOFTWARE_VERSION_NUMBER = 11
    GET_BIT_INFO = 5


class FdButtonId(Enum):
    """ Enumeration for button index """
    UP_ARROW = 4
    X = 5
    DOWN_ARROW = 6


class FdButtonState(Enum):
    """ Enumeration for button state """
    NO_EVENT = 0
    PRESSED = 1
    HELD = 2
    RELEASED = 3


class FdButtonStatusOffset(Enum):
    """ Enumeration for button status message offsets """
    BUTTON_ID = 0
    BUTTON_STATE = 1
    BUTTON_HOLD_TIME = 2


class FdLedPattern:
    led_pattern: int = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]


class FdSerialMsgInterface:
    """
    Class for handling serial messages to the Fill Device microcontroller firmware
    firmware KT-956-0377-00.  The serial message ICD is defined in document KT-957-0413-00.
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
        :return: True if the ack received before FD_SERIAL_TIMEOUT, else False
        """
        ret_val = False
        rx_timeout = time.time() + FD_SERIAL_TIMEOUT
        while True:
            time.sleep(0.001)
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

    def send_ping(self, wait_for_ack=True):
        """
        Sends a Ping message, waits for the response and processes it
        :param wait_for_ack: wait for command to be acknowledged, default is True, wait for Ack :type: Boolean
        :return: True if Ping is successfully acked, else False :type Boolean
        """
        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=FdMsgId.PING.value,
            pl_len=0)  # No payload

        log.debug("Tx Ping: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self.smh.send_to_tx_queue(header_bytes)

        if wait_for_ack:
            return self.wait_for_ack(seq_no, FdMsgId.PING.value)
        else:
            return True

    def get_command(self, get_cmd, resp_payload_len, wait_for_ack=True):
        """
        Sends a command that expects a response, processes ACK response and returns response message
        :return: [0] True if response received, else False; [1] the received message
        """
        if get_cmd not in FdMsgId:
            raise ValueError("get_cmd must be one of ZmMsgId enumerated values")
        if resp_payload_len not in FdMsgPayloadLen:
            raise ValueError("get_cmd must be one of ZmMsgPayloadLen enumerated values")

        seq_no = self.smh.get_next_sequence_number()
        header_bytes = self.smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=get_cmd.value,
            pl_len=0)  # No payload

        log.debug("Tx Get Cmd: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self.smh.send_to_tx_queue(header_bytes)

        if wait_for_ack:
            # Wait for Ack, if it's successful wait for response
            if not self.wait_for_ack(seq_no, get_cmd.value):
                log.debug("No Ack")
                return False, None

        ret_val = False
        rx_timeout = time.time() + FD_SERIAL_TIMEOUT
        while True:
            time.sleep(0.001)
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

    def send_set_led_pattern(self, led=0, pattern="OFF", wait_for_ack=True):
        """
        Constructs and sends a SetLedPattern message
        :param wait_for_ack: wait for command to be acknowledged, default is True, wait for Ack :type: Boolean
        :param led: index of LED to set
        :param pattern: dictionary key for FD_LED_PATTERNS :type: string
        :return: True if command sent and Ack received, else False
        """
        if pattern not in FD_LED_PATTERNS.keys():
            return False
        # Build the message header
        seq_no = self.smh.get_next_sequence_number()
        message_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                      ack_no=0,
                                                      status=smh.MessageStatus.NEW_MESSAGE.value,
                                                      msg_id=FdMsgId.SET_LED_PATTERN.value,
                                                      pl_len=9)

        # Build payload to set LED to required pattern
        message_bytes.append(0)                                 # Payload Format Version
        message_bytes.append(1)                                 # Number of Patterns, 1 single LED
        message_bytes.append(led)                               # Number of Patterns, 1 single LED
        for entry in FD_LED_PATTERNS.get(pattern):            # Pattern data
            message_bytes.append(entry)
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[smh.TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])              # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])              # Payload CRC MSB

        log.debug("Tx SetLedPattern: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        self.smh.send_to_tx_queue(message_bytes)
        if wait_for_ack:
            return self.wait_for_ack(seq_no, FdMsgId.SET_LED_PATTERN.value)
        else:
            return True

    def send_set_all_leds(self, led_patterns, wait_for_ack=True):
        """
        Constructs and sends a SetLedPattern that sets all 6x LEDs
        :param wait_for_ack: wait for command to be acknowledged, default is True, wait for Ack :type: Boolean
        :param led_patterns: 20-element List of dictionary keys from FD_LED_PATTERNS :type: list of 20 Strings
        :return: True if command sent and Ack received, else False
        """
        if len(led_patterns) != 6:
            return False
        for pattern in led_patterns:
            if pattern not in FD_LED_PATTERNS:
                return False
        # Build the message header
        seq_no = self.smh.get_next_sequence_number()
        message_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                      ack_no=0,
                                                      status=smh.MessageStatus.NEW_MESSAGE.value,
                                                      msg_id=FdMsgId.SET_LED_PATTERN.value,
                                                      pl_len=142)

        # Build payload to set LED to required pattern
        message_bytes.append(0)     # Payload Format Version
        message_bytes.append(6)    # Number of Patterns, 9 all LEDs
        for led, pattern in enumerate(led_patterns):
            message_bytes.append(led)
            for entry in FD_LED_PATTERNS.get(pattern):  # Pattern data
                message_bytes.append(entry)
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[smh.TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])  # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])  # Payload CRC MSB

        log.debug("Tx SetLedPattern: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        self.smh.send_to_tx_queue(message_bytes)
        if wait_for_ack:
            return self.wait_for_ack(seq_no, FdMsgId.SET_LED_PATTERN.value)
        else:
            return True

    def send_set_led_brightness(self, brightness, wait_for_ack=True):
        """
        Constructs and sends a SetLedBrightness message
        :param wait_for_ack: wait for command to be acknowledged, default is True, wait for Ack :type: Boolean
        :param brightness: valid range 0..255 :type: Integer
        :return: True if command sent and Ack received, else False
        """
        if brightness < 0 or brightness > 255:
            brightness = 255
        # Build the message header
        seq_no = self.smh.get_next_sequence_number()
        message_bytes = self.smh.build_message_header(seq_no=seq_no,
                                                      ack_no=0,
                                                      status=smh.MessageStatus.NEW_MESSAGE.value,
                                                      msg_id=FdMsgId.SET_LED_BRIGHTNESS.value,
                                                      pl_len=FdMsgPayloadLen.SET_LED_BRIGHTNESS.value)

        # Build payload to set buzzer to required pattern
        message_bytes.append(0)             # Payload Format Version
        message_bytes.append(brightness)    # LED brightness
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[smh.TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])              # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])              # Payload CRC MSB

        log.debug("Tx SetLedBrightness: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        self.smh.send_to_tx_queue(message_bytes)
        if wait_for_ack:
            return self.wait_for_ack(seq_no, FdMsgId.SET_LED_BRIGHTNESS.value)
        else:
            return True

    @staticmethod
    def unpack_button_status_message(ba):
        """
        Utility method to unpack a button status message, assuming all CRC checks have passed for message
        param ba: ByteArray payload of response message to unpack
        :return: ret_val True, if data unpacked, else False; button_status, dictionary of returned button status
        """
        button_status = []
        return_val = False
        payload_start_idx = smh.TOTAL_HEADER_LENGTH

        if ba[smh.HeaderOffset.MESSAGE_ID.value] == FdMsgId.BUTTON_STATUS.value:
            for btn_idx in range(0, ba[payload_start_idx + 1]):
                button_id = ba[payload_start_idx + 2 + (btn_idx * 3) + FdButtonStatusOffset.BUTTON_ID.value]
                button_state = ba[payload_start_idx + 2 + (btn_idx * 3) + FdButtonStatusOffset.BUTTON_STATE.value]
                button_hold_time = ba[payload_start_idx + 2 + (btn_idx * 3) + FdButtonStatusOffset.BUTTON_HOLD_TIME.value]
                button_status.append({"button_id": button_id,
                                      "button_state": button_state,
                                      "button_hold_time": button_hold_time})

            return_val = True

        return return_val, button_status

    @staticmethod
    def unpack_get_software_version_number_response(ba):
        """
        Utility method to unpack the payload of a GetSoftwareVersionNumber Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else 5x unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + FdMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER.value + smh.CRC_LENGTH:
            log.critical("Unpack GetSoftwareVersionNumber Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + FdMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER.value + smh.CRC_LENGTH))
            return None
        else:
            payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                struct.unpack("<BHHHI", ba[smh.TOTAL_HEADER_LENGTH:len(ba) - smh.CRC_LENGTH])
            return payload_version, sw_major, sw_minor, sw_patch, sw_build


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
