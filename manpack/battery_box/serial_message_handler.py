#!/usr/bin/env python3
"""
Module for handling serial messages using the K-CEMA serial protocol
specified in KT-957-0413-00.  This is a generic module intended to be used
by composition with a higher level class implementing a module specific
command set
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
SERIAL_TIMEOUT = 0.1
HEADER_LENGTH = 6
CRC_LENGTH = 2
TOTAL_HEADER_LENGTH = HEADER_LENGTH + CRC_LENGTH
START_OF_FRAME = 0xA5
MESSAGE_STATUS_TEXT = ['NewMessage',
                       'Retransmit',
                       'Acknowledge',
                       'NotAcknowledge',
                       'ResponseOk',
                       'ResponseNotOk',
                       'Invalid (0x6)',
                       'Invalid (0x7)']

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
    """ Enumeration class for rx state machine """
    IDLE = auto()
    RECEIVING_HEADER = auto()
    AWAITING_HEADER_CRC = auto()
    RECEIVING_PAYLOAD = auto()
    AWAITING_PAYLOAD_CRC = auto()
    MESSAGE_COMPLETE = auto()


class MessageStatus(Enum):
    """ Enumeration class for message status """
    NEW_MESSAGE = 0x0
    RETRANSMIT = 0x1
    ACKNOWLEDGE = 0x2
    NOT_ACKNOWLEDGE = 0x3
    RESPONSE_OK = 0x4
    RESPONSE_NOT_OK = 0x5
    INVALID6 = 0x6
    INVALID7 = 0x7


class HeaderOffset(Enum):
    """ Offsets of bytes in header """
    START_OF_FRAME = 0
    MESSAGE_SEQUENCE_NO = 1
    ACKNOWLEDGEMENT_NO = 2
    MESSAGE_STATUS_PROTOCOL_VERSION = 3
    MESSAGE_ID = 4
    PAYLOAD_LENGTH = 5
    CRC_LSB = 6
    CRC_MSB = 7


class Header:
    """ Data representation class for a message header """
    ack_no: int = -1
    seq_no: int = -1
    status: int = -1
    msg_id: int = -1
    pl_len: int = -1
    crc:    int = -1


class MessageHandler:
    """
    Class for handling serial messages using the K-CEMA serial protocol
    specified in KT-957-0413-00, sets up tx/rx threads which use
    queues to pass messages between the application and a serial port.

    The rx thread operates as a state machine that is stepped through as
    bytes are received on te serial interface.  The rx state machine automatically
    handles sending Ack/Nacks in response to received messages.
    """
    def __init__(self):
        """ Class constructor """
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

    def __del__(self):
        """ Class destructor """
        self.stop()

    def send_to_tx_queue(self, msg):
        """
        Add a message to the tx queue, the tx thread will pop the message
        and send it on the serial interface.  This method is intended to be used
        by higher-level classes to send messages
        :param msg: message to be sent :type ByteArray
        :return: NA
        """
        with self._tx_thread_lock:
            self._tx_queue.append(msg)

    def get_from_rx_queue(self):
        """
        Pop a message from the rx queue if one is available
        :return: received message if available, else None :type ByteArray
        """
        if len(self._rx_queue) > 0:
            with self._rx_thread_lock:
                return self._rx_queue.popleft()
        else:
            return None

    def clear_rx_queue(self):
        """
        Utility method to ditch the contents of the rx queue
        :return: NA
        """
        with self._rx_thread_lock:
            self._rx_queue.clear()

    def get_next_sequence_number(self):
        """
        Get the next serial tx sequence number
        :return: Next sequence number
        """
        self._next_sequence_number = (self._next_sequence_number + 1) % 256
        return self._next_sequence_number

    def send_acknowledge(self, acknowledgment_number, message_id, ack=True):
        """
        Send acknowledge/not acknowledge message
        :param acknowledgment_number: sequence number of the message being acknowledged :type Integer
        :param message_id: ID of the message being acknowledged :type Integer
        :param ack: set to False to send a Not Acknowledge :type Boolean
        :return: NA
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

        self.send_to_tx_queue(header_bytes)

    @staticmethod
    def build_message_header(seq_no, ack_no, status, msg_id, pl_len):
        """
        Utility method for building a message header ByteArray
        :param seq_no: tx sequence number :type integer
        :param ack_no: acknowledge no :type integer
        :param status: message status :type integer
        :param msg_id: message ID :type Integer
        :param pl_len: payload length :type Integer
        :return: message header :type ByteArray
        """
        header_bytes = bytearray()
        header_bytes.append(START_OF_FRAME)  # Start of Frame
        header_bytes.append(seq_no)  # Message Sequence Number
        header_bytes.append(ack_no)  # Acknowledgment Number
        header_bytes.append((status << 5) & 0xE0)  # Status and Protocol
        header_bytes.append(msg_id)  # Message ID
        header_bytes.append(pl_len)  # Payload Length
        header_crc = CRCCCITT(version="FFFF").calculate(bytes(header_bytes))
        header_crc_bytes = header_crc.to_bytes(2, byteorder="little")
        header_bytes.append(header_crc_bytes[0])  # CRC LSB
        header_bytes.append(header_crc_bytes[1])  # CRC MSB
        return header_bytes

    @staticmethod
    def unpack_message_header(ba):
        """
        Unpack a message header from a byte array into a Header instance
        :param ba: byte array containing message header :type bytearray
        :return: Header instance representing the message header
        """
        if not type(ba) is bytearray or len(ba) < HEADER_LENGTH:
            raise RuntimeError("ba is wrong type or length!")

        msg_header = Header()

        # Check that this is a header we've been passed
        if ba[HeaderOffset.START_OF_FRAME.value] == START_OF_FRAME:
            msg_header.seq_no = ba[HeaderOffset.MESSAGE_SEQUENCE_NO.value]
            msg_header.ack_no = ba[HeaderOffset.ACKNOWLEDGEMENT_NO.value]
            msg_header.status = (ba[HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) >> 5
            msg_header.msg_id = ba[HeaderOffset.MESSAGE_ID.value]
            msg_header.pl_len = ba[HeaderOffset.PAYLOAD_LENGTH.value]
            msg_header.crc = ba[HeaderOffset.CRC_LSB.value] | ((ba[HeaderOffset.CRC_MSB.value] << 8) & 0xFF00)

        return msg_header

    def __rx_thread_run(self):
        """
        Receive thread, operates as a state machine which is stepped through
        as bytes are received on the serial interface.

        Once a complete message has been received (and validated) it is added
        to the rx queue ready to be collected by an application.
        :return NA
        """
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
                                message_buffer = message_buffer[read_position:]
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
                            log.debug("Raw Rx Msg: {}".format(" ".join(format(x, '02x') for x in message_buffer[:read_position])))
                            calculated_crc = CRCCCITT(version="FFFF").calculate(
                                bytes(message_buffer[TOTAL_HEADER_LENGTH: read_position - CRC_LENGTH]))
                            log.debug("Rx Payload Calculated CRC = {}".format(hex(calculated_crc)))

                            payload_crc = int.from_bytes(
                                bytes(message_buffer[read_position - CRC_LENGTH: read_position]), byteorder="little")
                            log.debug("Rx Payload CRC = {}".format(hex(payload_crc)))

                            if calculated_crc == payload_crc:
                                current_state = MessageHandlerRxState.MESSAGE_COMPLETE
                            else:
                                # Generate a not acknowledge structure and send it off
                                # MAGIC NUMBERS!
                                self.send_acknowledge(message_buffer[1], message_buffer[4], ack=False)

                                # Need to go back to idle and find the start again
                                log.error("Payload CRC: calculated {}; received {}".format(
                                    hex(calculated_crc), hex(payload_crc)))
                                message_buffer = message_buffer[read_position:]
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
                            self._rx_queue.append(message_buffer[:read_position])

                        # Finished with the message; back to the start now
                        message_buffer = message_buffer[read_position:]
                        read_position = -1
                        current_state = MessageHandlerRxState.IDLE

                    # Only dealing with headers here at the moment, payload is managed by the calling application
                    processed_all_data = (current_state != MessageHandlerRxState.MESSAGE_COMPLETE) and \
                                         ((len(message_buffer) == 0) or
                                          ((read_position > 0) and
                                           (read_position == len(message_buffer))))

        log.debug("Rx __rx_thread exiting")

    def __tx_thread_run(self):
        """
        Transmit thread, pops messages off the tx queue and sends them using the serial port
        :return NA
        """
        log.debug("Tx Ready...")

        while not self._event.is_set():
            time.sleep(0.01)
            try:
                with self._tx_thread_lock:
                    if len(self._tx_queue) > 0:
                        message_to_send = self._tx_queue.popleft()
                        sent = self._serial_device.write(message_to_send)
                        log.debug("Tx msg (sent {}): {}".format(
                            sent, " ".join(format(x, '02x') for x in message_to_send)))

            except queue.Empty:
                log.debug("Tx Queue Empty")

        log.debug("Tx __tx_thread exiting")

    def start(self, serial_port, baud_rate):
        """
        Starts the MessageHandler running
        :param serial_port:
        :param baud_rate:
        :return: True if started, else False :type: Boolean
        """
        log.debug('Starting MessageHandler...')

        try:
            self._serial_device = serial.Serial(serial_port, baud_rate, timeout=SERIAL_TIMEOUT,
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
                log.info('Failed to open the serial port')

        except Exception as ex:
            self._event.set()
            if self._serial_device is not None:
                self._serial_device.close()
            log.info("Failed to start SerialMessageHandler: {}".format(ex))

        if not self._event.is_set():
            return True
        else:
            return False

    def stop(self):
        """
        Stop the MessageHandler from running
        :return: NA
        """
        if not self._event.is_set():
            self._event.set()
            # Allow setting the event to be detected by the tx/rx threads before closing the serial port
            time.sleep(SERIAL_TIMEOUT)
            if self._serial_device is not None:
                self._serial_device.close()

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
