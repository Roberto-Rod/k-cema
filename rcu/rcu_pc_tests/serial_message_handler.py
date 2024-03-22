#!/usr/bin/env python3
"""
Module for handling serial messages using the K-CEMA serial protocol
specified in KT-957-0143-00
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
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
import queue
import threading
from threading import Lock
from enum import Enum, auto, unique
import logging
import struct
import collections
import time

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT
import serial

# Our own imports ---------------------------------------------------


# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SERIAL_TIMEOUT = 1.0
HEADER_LENGTH = 6
CRC_LENGTH = 2
TOTAL_HEADER_LENGTH = HEADER_LENGTH + CRC_LENGTH
START_OF_FRAME = 0xA5
MESSAGE_ID_TEXT = ['Ping',
                   'GetSoftwareVersionNumber',
                   'SetLedPattern',
                   'SetBuzzerPattern',
                   'Synchronize',
                   'ButtonStatus',
                   'Zeroise']
MESSAGE_STATUS_TEXT = ['NewMessage',
                       'Retransmit',
                       'Acknowledge',
                       'NotAcknowledge',
                       'ResponseOk',
                       'ResponseNotOk',
                       'Invalid (0x6)',
                       'Invalid (0x7)']

LED_PATTERNS = {
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
@unique
class MessageHandlerRxState(Enum):
    """
    Enumeration class for rx state machine
    """
    IDLE = auto()
    RECEIVING_HEADER = auto()
    AWAITING_HEADER_CRC = auto()
    RECEIVING_PAYLOAD = auto()
    AWAITING_PAYLOAD_CRC = auto()
    MESSAGE_COMPLETE = auto()


class MessageStatus(Enum):
    """
    Enumeration class for message status
    """
    NEW_MESSAGE = 0x0
    RETRANSMIT = 0x1
    ACKNOWLEDGE = 0x2
    NOT_ACKNOWLEDGE = 0x3
    RESPONSE_OK = 0x4
    RESPONSE_NOT_OK = 0x5
    INVALID6 = 0x6
    INVALID7 = 0x7


class MessageId(Enum):
    """
    Enumeration for message identifiers
    """
    PING = 0x0
    GET_SOFTWARE_VERSION_NUMBER = 0x1
    SET_LED_PATTERN = 0x2
    SET_BUZZER_PATTERN = 0x3
    SYNCHRONISE = 0x4
    BUTTON_STATUS = 0x5
    ZEROISE = 0x6
    SET_LED_BRIGHTNESS = 0x0D


class HeaderOffset(Enum):
    """
    Offsets for bytes in header
    """
    START_OF_FRAME = 0
    MESSAGE_SEQUENCE_NO = 1
    ACKNOWLEDGEMENT_NO = 2
    MESSAGE_STATUS_PROTOCOL_VERSION = 3
    MESSAGE_ID = 4
    PAYLOAD_LENGTH = 5
    CRC_LSB = 6
    CRC_MSB = 7


class ButtonId(Enum):
    """
    Enumeration for button index
    """
    POWER = 0
    JAM = 1
    EXCLAMATION = 2
    X = 3


class ButtonStatusOffset(Enum):
    BUTTON_ID = 0
    BUTTON_STATE = 1
    BUTTON_HOLD_TIME = 2


class MessageHandler:
    """
    Class for handling serial messages using the K-CEMA serial protocol
    specified in KT-957-0143-00, sets up tx/rx threads which use
    queues to pass messages between application and serial port
    """
    def __init__(self):
        """
        Class constructor
        :param None
        :return: None
        """
        self._next_sequence_number = 255
        self._tx_queue = collections.deque()
        self._rx_queue = collections.deque()
        self._rx_thread = None
        self._rx_thread_lock = Lock()
        self._tx_thread = None
        self._tx_thread_lock = Lock()
        self._event = threading.Event()
        self._serial_device = None

        self._message_statuses_to_acknowledge = [MessageStatus.NEW_MESSAGE.value,
                                                 MessageStatus.RETRANSMIT.value,
                                                 MessageStatus.RESPONSE_OK.value,
                                                 MessageStatus.RESPONSE_NOT_OK.value]

    def get_from_rx_queue(self):
        if len(self._rx_queue) > 0:
            with self._rx_thread_lock:
                return self._rx_queue.popleft()
        else:
            return None

    def clear_rx_queue(self):
        with self._rx_thread_lock:
            self._rx_queue.clear()

    def get_next_sequence_number(self):
        """
        Get the serial tx sequence number
        :return: Next sequence number
        """
        self._next_sequence_number = (self._next_sequence_number + 1) % 256
        return self._next_sequence_number

    @staticmethod
    def build_message_header(sequence_no, ack_no, status, msg_id, payload_length):
        header_bytes = bytearray()
        header_bytes.append(START_OF_FRAME)             # Start of Frame
        header_bytes.append(sequence_no)                # Message Sequence Number
        header_bytes.append(ack_no)                     # Acknowledgment Number
        header_bytes.append((status << 5) & 0xE0)       # Status and Protocol
        header_bytes.append(msg_id)                     # Message ID
        header_bytes.append(payload_length)             # Payload Length
        header_crc = CRCCCITT(version="FFFF").calculate(bytes(header_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        header_bytes.append(header_crc_bytes[0])        # CRC LSB
        header_bytes.append(header_crc_bytes[1])        # CRC MSB
        return header_bytes

    def send_ping(self):
        """
        Sends a Ping message
        :return:
        """
        header_bytes = bytearray()
        header_bytes.append(START_OF_FRAME)                    # Start of Frame
        header_bytes.append(self.get_next_sequence_number())   # Message Sequence Number
        header_bytes.append(0)                                 # Acknowledgment Number
        header_bytes.append(0)                                 # Status and Protocol
        header_bytes.append(MessageId.PING.value)              # Message ID
        header_bytes.append(0)                                 # Payload Length
        header_crc = CRCCCITT(version="FFFF").calculate(bytes(header_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        header_bytes.append(header_crc_bytes[0])  # CRC LSB
        header_bytes.append(header_crc_bytes[1])  # CRC MSB

        log.debug("Tx Ping: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(header_bytes)

    def send_get_software_version_number(self):
        """
        Sends a GetSoftwareVersionNumber message
        :return:
        """
        message_bytes = bytearray()
        message_bytes.append(START_OF_FRAME)                    # Start of Frame
        message_bytes.append(self.get_next_sequence_number())   # Message Sequence Number
        message_bytes.append(0)                                 # Acknowledgment Number, '0' for new message
        message_bytes.append(0)                                 # Status = '0' for new message and Protocol = '0'
        message_bytes.append(MessageId.GET_SOFTWARE_VERSION_NUMBER.value)   # Message ID
        message_bytes.append(0)                                 # Payload Length

        header_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        message_bytes.append(header_crc_bytes[0])  # CRC LSB
        message_bytes.append(header_crc_bytes[1])  # CRC MSB

        log.debug("Tx GetSoftwareVersionNumber: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(message_bytes)

    def send_get_software_version_number_response(self, acknowledgment_number, payload_version=0, sw_major=0,
                                                  sw_minor=0, sw_build=0):
        """
        Sends a GetSoftwareVersionNumber Response message
        :return:
        """
        # Build the message header
        message_bytes = bytearray()
        message_bytes.append(START_OF_FRAME)                    # Start of Frame
        message_bytes.append(self.get_next_sequence_number())   # Message Sequence Number
        message_bytes.append(acknowledgment_number)             # Acknowledgment Number
        message_bytes.append(MessageStatus.RESPONSE_OK.value << 5)   # Status (3 bits) plus Protocol Version (5 bits)
        message_bytes.append(MessageId.GET_SOFTWARE_VERSION_NUMBER.value)    # Message ID
        message_bytes.append(7)                                  # Payload Length

        header_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        message_bytes.append(header_crc_bytes[0])  # CRC LSB
        message_bytes.append(header_crc_bytes[1])  # CRC MSB

        # Add the payload
        message_bytes.append(payload_version)   # Protocol Version
        sw_ver_param = sw_major.to_bytes(2, byteorder="little")
        message_bytes.append(sw_ver_param[0])   # Software Major Version
        message_bytes.append(sw_ver_param[1])
        sw_ver_param = sw_minor.to_bytes(2, byteorder="little")
        message_bytes.append(sw_ver_param[0])  # Software Minor Version
        message_bytes.append(sw_ver_param[1])
        sw_ver_param = sw_build.to_bytes(2, byteorder="little")
        message_bytes.append(sw_ver_param[0])  # Software Build Version
        message_bytes.append(sw_ver_param[1])

        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])  # CRC LSB
        message_bytes.append(payload_crc_bytes[1])  # CRC MSB

        log.debug("Tx GetSoftwareVersionNumber Response: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(message_bytes)

    @staticmethod
    def unpack_get_software_version_number_response(ba):
        """
        Utility method to unpack the payload of a GetSoftwareVersionNumber Response
        :param ba: ByteArray payload of response message to unpack, expected length is 7
        :return: None if ba is wrong type or length, else 4x unpacked values
        """
        if ba is not bytearray or len(ba) != 7:
            log.critical("Unpack GetSoftwareVersionNumber Response expecting 7-byte array")
            return None
        else:
            payload_version, sw_major, sw_minor, sw_build = struct.unpack("BHHH", ba)
            return payload_version, sw_major, sw_minor, sw_build

    def send_set_buzzer_pattern(self, pattern="OFF"):
        """
        Constructs and sends a SetBuzzerPattern message
        :param pattern:
        :return:
        """
        if pattern not in LED_PATTERNS.keys():
            return
        # Build the message header
        message_bytes = self.build_message_header(sequence_no=self.get_next_sequence_number(),
                                                  ack_no=0,
                                                  status=MessageStatus.NEW_MESSAGE.value,
                                                  msg_id=MessageId.SET_BUZZER_PATTERN.value,
                                                  payload_length=7)

        # Build payload to set buzzer to required pattern
        message_bytes.append(0)                                 # Payload Format Version
        for entry in LED_PATTERNS.get(pattern):                 # Pattern data
            message_bytes.append(entry)
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])              # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])              # Payload CRC MSB

        log.debug("Tx SetLedPattern: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(message_bytes)

    def send_set_led_pattern(self, led=0, pattern="OFF"):
        """
        Constructs and sends a SetLedPattern message
        :param led:
        :param pattern:
        :return:
        """
        if pattern not in LED_PATTERNS.keys():
            log.debug("Valid patterns: {}".format(LED_PATTERNS.keys()))
            return
        # Build the message header
        message_bytes = self.build_message_header(sequence_no=self.get_next_sequence_number(),
                                                  ack_no=0,
                                                  status=MessageStatus.NEW_MESSAGE.value,
                                                  msg_id=MessageId.SET_LED_PATTERN.value,
                                                  payload_length=9)     # Payload Length, 9 for single LED

        # Build payload to set all the LEDs blinking yellow
        message_bytes.append(0)                         # Payload Format Version
        message_bytes.append(1)                         # Number of Patterns, 1 single LED
        message_bytes.append(led)
        for entry in LED_PATTERNS.get(pattern):
            message_bytes.append(entry)
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])      # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])      # Payload CRC MSB

        log.debug("Tx SetLedPattern: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(message_bytes)

    def send_set_led_brightness(self, brightness):
        """
        Constructs and sends a SetLedBrightness message
        :param brightness: valid range 0..255 :type: Integer
        :return: True if command sent and Ack received, else False
        """
        if brightness < 0 or brightness > 255:
            brightness = 255
        # Build the message header
        seq_no = self.get_next_sequence_number()
        message_bytes = self.build_message_header(sequence_no=seq_no,
                                                  ack_no=0,
                                                  status=MessageStatus.NEW_MESSAGE.value,
                                                  msg_id=MessageId.SET_LED_BRIGHTNESS.value,
                                                  payload_length=2)

        # Build payload to set buzzer to required pattern
        message_bytes.append(0)             # Payload Format Version
        message_bytes.append(brightness)    # LED brightness
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(message_bytes[TOTAL_HEADER_LENGTH:]))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        message_bytes.append(payload_crc_bytes[0])              # Payload CRC LSB
        message_bytes.append(payload_crc_bytes[1])              # Payload CRC MSB

        log.debug("Tx SetLedBrightness: {}".format(" ".join(format(x, '02x') for x in message_bytes)))
        with self._tx_thread_lock:
            self._tx_queue.append(message_bytes)

    @staticmethod
    def unpack_button_status_message(ba):
        """
        Utility method to unpack a button status message, assuming all CRC checks have passed for message
        :param ba:
        :return: ret_val True, if data unpacked, else False; button_status, dictionary of returned button status
        """
        button_status = []
        return_val = False
        payload_start_idx = TOTAL_HEADER_LENGTH

        if ba[HeaderOffset.MESSAGE_ID.value] == MessageId.BUTTON_STATUS.value:
            for btn_idx in range(0, ba[payload_start_idx + 1]):
                button_id = ba[payload_start_idx + 2 + (btn_idx * 3) + ButtonStatusOffset.BUTTON_ID.value]
                button_state = ba[payload_start_idx + 2 + (btn_idx * 3) + ButtonStatusOffset.BUTTON_STATE.value]
                button_hold_time = ba[payload_start_idx + 2 + (btn_idx * 3) + ButtonStatusOffset.BUTTON_HOLD_TIME.value]
                button_status.append({"button_id": button_id,
                                      "button_state": button_state,
                                      "button_hold_time": button_hold_time})

            return_val = True

        return return_val, button_status

    def send_acknowledge(self, acknowledgment_number, message_id, ack=True):
        """
        Send acknowledge to message
        :param acknowledgment_number
        :param message_id
        :param ack set to False to send a Not Acknowledge
        :return: None
        """
        header_bytes = bytearray()
        header_bytes.append(START_OF_FRAME)                     # Start Of Frame
        header_bytes.append(self.get_next_sequence_number())    # Message Sequence Number
        header_bytes.append(acknowledgment_number)              # Acknowledgment Number
        if ack:                                                 # Status (3 bits) plus Protocol Version (5 bits)
            header_bytes.append(MessageStatus.ACKNOWLEDGE.value << 5)
        else:
            header_bytes.append(MessageStatus.NOT_ACKNOWLEDGE.value << 5)
        header_bytes.append(message_id)                         # Message ID
        header_bytes.append(0)                                  # Payload Length

        header_crc = CRCCCITT(version="FFFF").calculate(bytes(header_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        header_bytes.append(header_crc_bytes[0])  # CRC LSB
        header_bytes.append(header_crc_bytes[1])  # CRC MSB

        log.debug("Tx Ack: {}".format(" ".join(format(x, '02x') for x in header_bytes)))

        with self._tx_thread_lock:
            self._tx_queue.append(header_bytes)

    def __rx_thread_run(self):
        """
        Receive thread
        :return None:
        """
        try:
            log.debug("Rx Waiting...")

            crc_bytes_read = 0
            bytes_to_process = 0
            current_state = MessageHandlerRxState.IDLE

            message_buffer = bytearray()
            read_position = -1

            next_acknowledge_number = 0

            while not self._event.is_set():
                # Attempt to read from the serial port
                data = self._serial_device.read(1)

                # read() call will time out if nothing was read
                if len(data) >= 1:
                    message_buffer += data

                    processed_all_data = False
                    while not processed_all_data:
                        if current_state == MessageHandlerRxState.IDLE:
                            log.debug("Rx Idle State")
                            if message_buffer[HeaderOffset.START_OF_FRAME.value] != START_OF_FRAME:
                                message_buffer = message_buffer[1:]
                            else:
                                log.debug("Rx Start of Message Detected")
                                read_position = 1
                                bytes_to_process = HEADER_LENGTH - 1
                                current_state = MessageHandlerRxState.RECEIVING_HEADER

                        elif current_state == MessageHandlerRxState.RECEIVING_HEADER:
                            read_position += 1
                            bytes_to_process -= 1

                            if bytes_to_process == 0:
                                log.debug("Rx All Non-CRC Header Bytes Received")
                                crc_bytes_read = 0
                                current_state = MessageHandlerRxState.AWAITING_HEADER_CRC

                        elif current_state == MessageHandlerRxState.AWAITING_HEADER_CRC:
                            read_position += 1
                            crc_bytes_read += 1

                            if crc_bytes_read == CRC_LENGTH:
                                calculated_crc = CRCCCITT(version="FFFF").calculate(
                                    bytes(message_buffer[0:HEADER_LENGTH]))
                                log.debug("Rx Header Calculated CRC = {}".format(hex(calculated_crc)))

                                header_crc = int.from_bytes(
                                    bytes(message_buffer[HEADER_LENGTH: TOTAL_HEADER_LENGTH]), byteorder="little")
                                log.debug("Rx Header CRC = {}".format(hex(header_crc)))

                                if calculated_crc == header_crc:
                                    payload_length = int(message_buffer[HeaderOffset.PAYLOAD_LENGTH.value])
                                    log.debug("Rx Payload Length: {}".format(payload_length))

                                    if payload_length == 0:
                                        current_state = MessageHandlerRxState.MESSAGE_COMPLETE
                                    else:
                                        bytes_to_process = payload_length
                                        current_state = MessageHandlerRxState.RECEIVING_PAYLOAD

                                else:
                                    # Need to go back to idle and find the start again
                                    log.error("Header CRC: calculated {}; received {}".format(
                                        hex(calculated_crc), hex(header_crc)))
                                    message_buffer = message_buffer[1:]
                                    read_position = -1
                                    current_state = MessageHandlerRxState.IDLE

                        elif current_state == MessageHandlerRxState.RECEIVING_PAYLOAD:
                            read_position += 1
                            bytes_to_process -= 1

                            if bytes_to_process == 0:
                                log.debug('Rx All Non-CRC Payload Bytes Received')
                                crc_bytes_read = 0
                                current_state = MessageHandlerRxState.AWAITING_PAYLOAD_CRC

                        elif current_state == MessageHandlerRxState.AWAITING_PAYLOAD_CRC:
                            read_position += 1
                            crc_bytes_read += 1

                            if crc_bytes_read == CRC_LENGTH:
                                calculated_crc = CRCCCITT(version="FFFF").calculate(
                                    bytes(message_buffer[TOTAL_HEADER_LENGTH: read_position - 2]))
                                log.debug("Rx Header Calculated CRC = {}".format(hex(calculated_crc)))

                                payload_crc = int.from_bytes(
                                    bytes(message_buffer[read_position - 2: read_position]), byteorder="little")
                                log.debug("Rx Header CRC = {}".format(hex(payload_crc)))

                                if calculated_crc == payload_crc:
                                    current_state = MessageHandlerRxState.MESSAGE_COMPLETE
                                else:
                                    # Generate a not acknowledge structure and send it off
                                    # MAGIC NUMBERS!
                                    self.send_acknowledge(message_buffer[1], message_buffer[4], ack=False)

                                    # Need to go back to idle and find the start again
                                    log.error("Payload CRC: calculated {}; received {}".format(
                                        hex(calculated_crc), hex(payload_crc)))
                                    message_buffer = message_buffer[1:]
                                    read_position = -1
                                    current_state = MessageHandlerRxState.IDLE

                        elif current_state == MessageHandlerRxState.MESSAGE_COMPLETE:
                            start_of_frame, message_sequence_number, acknowledge_number, blah, message_id, \
                                payload_length, header_crc = \
                                struct.unpack('BBBBBBH', message_buffer[:TOTAL_HEADER_LENGTH])
                            message_status = blah >> 5
                            protocol_version = blah & 0x1F

                            if message_status in self._message_statuses_to_acknowledge:
                                # Generate an acknowledge structure and send it off
                                self.send_acknowledge(message_sequence_number, message_id)

                            elif message_status == MessageStatus.ACKNOWLEDGE or \
                                    message_status == MessageStatus.NOT_ACKNOWLEDGE:
                                if acknowledge_number != next_acknowledge_number:
                                    log.error("Rx Sequence Number Error: Expected {}, Received {}".format(
                                        next_acknowledge_number, acknowledge_number))
                                next_acknowledge_number = acknowledge_number + 1

                            with self._rx_thread_lock:
                                self._rx_queue.append(message_buffer[:read_position-1])

                            # Finished with the message; back to the start now
                            message_buffer = message_buffer[read_position:]
                            read_position = -1
                            current_state = MessageHandlerRxState.IDLE

                        # Only dealing with headers at the moment, payload is managed by the calling application
                        processed_all_data = (current_state != MessageHandlerRxState.MESSAGE_COMPLETE) and \
                                             ((len(message_buffer) == 0) or
                                              ((read_position > 0) and
                                               (read_position == len(message_buffer))))

            log.debug("Rx __rx_thread exiting")

        except Exception as ex:
            log.critical("Rx Caught exception in __rx_thread: {}".format(ex))

    def __tx_thread_run(self):
        """
        Transmit thread
        :return None:
        """
        try:
            log.debug("Tx Ready...")

            while not self._event.is_set():
                time.sleep(0.001)
                try:
                    with self._tx_thread_lock:
                        if len(self._tx_queue) > 0:
                            message_to_send = self._tx_queue.popleft()
                            self._serial_device.write(message_to_send)

                except queue.Empty:
                    log.debug("Tx Queue Empty")

                except Exception as ex:
                    log.critical("Tx writeThread exception {}".format(ex))

            log.debug("Tx __tx_thread exiting")

        except Exception as ex:
            log.critical("Tx Caught exception in __tx_thread: {}".format(ex))

    def start(self, serial_port, baud_rate):
        """
        Starts the MessageHandler running
        :param serial_port:
        :param baud_rate:
        :return: None
        """
        log.debug('Starting MessageHandler...')

        try:
            self._serial_device = serial.Serial(serial_port, baud_rate, timeout=1.0,
                                                xonxoff=False, rtscts=False, dsrdtr=False)

            if self._serial_device.isOpen():
                log.debug('Serial Port Opened')

                self._serial_device.timeout = SERIAL_TIMEOUT
                self._event.clear()
                self._next_sequence_number = 255
                with self._tx_thread_lock:
                    self._tx_queue.clear()
                self.clear_rx_queue()

                self._rx_thread = threading.Thread(target=self.__rx_thread_run)
                self._rx_thread.start()

                self._tx_thread = threading.Thread(target=self.__tx_thread_run)
                self._tx_thread.start()

            else:
                log.critical('Failed to open the serial port')

        except Exception as ex:
            self._event.set()
            if self._serial_device:
                self._serial_device.close()
            log.critical("*** Failed to start MessageHandler: {} ***".format(ex))

        if not self._event.is_set():
            return True
        else:
            return False

    def stop(self):
        """
        Stop the MessageHandler from running
        :return:
        """
        self._event.set()
        # Allow setting the event to be detected by the tx/rx threads before closing the serial port
        time.sleep(SERIAL_TIMEOUT)
        if self._serial_device:
            self._serial_device.close()

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Module is not intended to be executed stand-alone, print warning message
    """
    print("Module is not intended to be executed stand-alone")
