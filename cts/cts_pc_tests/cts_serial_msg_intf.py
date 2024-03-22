#!/usr/bin/env python3
"""
Module for handling serial messages using the K-CEMA serial protocol specified
in KT-957-0143-00. Implements the CTS command set for communicating with the
CTS Firmware, KT-956-0265-00, v0.0.3 onwards.
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
DEFAULT_NETWORK_PORT = 32
DEFAULT_RESPONSE_TIMEOUT = 2.0
RX_MSG_THREAD_SLEEP_S = 0.001

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class CtsMsgId(Enum):
    """ Enumeration for message identifiers """
    PING = 0x0
    GET_SOFTWARE_VERSION_NUMBER = 0x1
    GET_BIT_INFO = 0xA
    GET_UNIT_INFO = 0xB
    SET_UNIT_INFO = 0xC
    START_SCAN = 0xD
    STOP_SCAN = 0xE
    GET_SCAN_STATUS = 0xF
    TEST = 0x10


class CtsMsgPayloadLen(Enum):
    """ Enumeration for payload lengths """
    PING = 0
    GET_SOFTWARE_VERSION_NUMBER = 11
    GET_BIT_INFO = 20
    GET_UNIT_INFO = 66
    SET_UNIT_INFO = 65
    START_SCAN_MIN = 11
    START_SCAN_MAX = 67
    STOP_SCAN = 0
    GET_SCAN_STATUS = 8
    TEST_MSG_START_FILE_UPLOAD = 10
    TEST_MSG_DATA_MIN = 4
    TEST_MSG_DATA_MAX = 244
    TEST_MSG_VERIFY_CRC = 6
    TEST_MSG_VERIFY_CRC_RESP = 7
    TEST_MSG_RELAUNCH = 2
    TEST_MSG_SET_RF_CAL_TABLE = 38
    TEST_MSG_GET_VCO_SETTINGS_CMD = 7
    TEST_MSG_GET_VCO_SETTINGS_RESP = 10


class CtsTestMsgType(Enum):
    """ Enumeration class for Test Message Types """
    START_FILE_UPLOAD = 0x00
    FILE_DATA = 0x01
    VERIFY_FILE_CRC = 0x02
    VERIFY_FILE_CRC_RESP = 0x03
    RELAUNCH = 0x04
    SET_RF_CAL_TABLE = 0x05
    GET_VCO_SETTINGS_CMD = 0x06
    GET_VCO_SETTINGS_RESP = 0x07


class CtsScanMode(Enum):
    """ Enumeration class for Scan Mode """
    ACTIVE_MONITOR = 1
    TX_ONLY = 2
    REACTIVE_MONITOR = 3


class CtsScanStatus(Enum):
    """ Enumeration class for Scan Status """
    IDLE = 0
    ACTIVE_MONITOR = 1
    TX_ONLY = 2
    REACTIVE_MONITOR = 3
    WAITING_TO_SYNC = 4
    LAST_CMD_ERROR = 5


class CtsMsgInterface:
    """
    Class for handling serial messages to the Integrated CTS board firmware
    firmware KT-956-0xxx-00.  The serial message ICD is defined in document
    KT-957-0413-00
    """
    def __init__(self, response_timeout=DEFAULT_RESPONSE_TIMEOUT):
        """
        Class constructor
        :param None
        :return: NA
        """
        self._smh = None
        self.response_timeout = response_timeout

    def __enter__(self):
        """
        Virtual base context manager entry method, must be implemented by concrete classes.
        """
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Virtual base context manager exit method, must be implemented by concrete classes.
        """
        raise NotImplementedError

    def wait_for_ack(self, ack_no, msg_id, verbose=False):
        """
        Wait for an ack to be received in response to a transmitted message
        :param ack_no: sequence no of message that is being acked
        :param msg_id: ID of message that is being acked
        :return: True if the ack received before RESPONSE_TIMEOUT, else False
        """
        ret_val = False
        rx_timeout = time.time() + self.response_timeout
        while True:
            time.sleep(RX_MSG_THREAD_SLEEP_S)
            rx_msg = self._smh.get_from_rx_queue()
            if verbose and rx_msg is not None:
                log.info(rx_msg.hex())
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

    def send_ping(self):
        """
        Sends a Ping message, waits for the response and processes it
        :return: True if Ping is successfully acked, else False :type Boolean
        """
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=CtsMsgId.PING.value,
            pl_len=0)  # No payload

        log.debug("Tx Ping: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self._smh.send_to_tx_queue(header_bytes)

        return self.wait_for_ack(seq_no, CtsMsgId.PING.value)

    def get_command(self, get_cmd, resp_payload_len):
        """
        Sends a command that expects a response, processes ACK response and returns response message
        :return: [0] True if response received, else False; [1] the received message
        """
        if get_cmd not in CtsMsgId:
            raise ValueError("get_cmd must be one of CtsMsgId enumerated values")
        if resp_payload_len not in CtsMsgPayloadLen:
            raise ValueError("get_cmd must be one of CtsMsgPayloadLen enumerated values")

        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(
            seq_no=seq_no,
            ack_no=0,  # '0' for new message
            status=0,  # Status = '0' for new message and Protocol = '0'
            msg_id=get_cmd.value,
            pl_len=0)  # No payload

        log.debug("Tx Get Cmd: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self._smh.send_to_tx_queue(header_bytes)

        # Wait for Ack, if it's successful wait for response
        if not self.wait_for_ack(seq_no, get_cmd.value):
            log.debug("No Ack")
            return False, None

        ret_val = False
        rx_timeout = time.time() + self.response_timeout
        while True:
            time.sleep(RX_MSG_THREAD_SLEEP_S)
            rx_msg = self._smh.get_from_rx_queue()
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

    @staticmethod
    def unpack_get_software_version_number_response(ba):
        """
        Utility method to unpack the payload of a GetSoftwareVersionNumber Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else 5x unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER.value + smh.CRC_LENGTH:
            log.critical("Unpack GetSoftwareVersionNumber Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER.value + smh.CRC_LENGTH))
            return None
        else:
            payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                struct.unpack("<BHHHI", ba[smh.TOTAL_HEADER_LENGTH:len(ba) - smh.CRC_LENGTH])
            return payload_version, sw_major, sw_minor, sw_patch, sw_build

    @staticmethod
    def unpack_get_unit_info_response(ba):
        """
        Utility method to unpack the payload of a GetUnitInformation Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else 8x unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_UNIT_INFO.value + smh.CRC_LENGTH:
            log.critical("Unpack GetUnitInformation Response expecting {}}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_UNIT_INFO.value + smh.CRC_LENGTH
            ))
            return None
        else:
            read_position = smh.TOTAL_HEADER_LENGTH

            payload_version, status = struct.unpack("BB", ba[read_position: read_position + 2])
            read_position += 2

            assy_part_no = ba[read_position: read_position + 16].decode("utf-8")
            read_position += 16

            assy_rev_no = ba[read_position: read_position + 16].decode("utf-8")
            read_position += 16

            assy_serial_no = ba[read_position: read_position + 16].decode("utf-8")
            read_position += 16

            assy_build_date_batch_no = ba[read_position: read_position + 16].decode("utf-8")
            read_position += 16

            return payload_version, status, assy_part_no, assy_rev_no, assy_serial_no, \
                assy_build_date_batch_no

    @staticmethod
    def unpack_get_bit_info_response(ba):
        """
        Utility method to unpack the payload of a GetBitInformation Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_BIT_INFO.value + smh.CRC_LENGTH:
            log.critical("Unpack GetBitInformation Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_BIT_INFO.value + smh.CRC_LENGTH))
            return None
        else:
            # Check the payload format version is supported
            if ba[smh.TOTAL_HEADER_LENGTH] == 5:
                payload_version, source_payload, source_payload_version, flags, voltage_12v_mv, voltage_3v3_mv, \
                    voltage_n3v3_mv, voltage_5v0_mv, voltage_3v3_if_mv, voltage_3v3_tx_mv, voltage_5v0_tx_mv, \
                    micro_temp_deg, ambient_temp_deg = \
                    struct.unpack_from("<BBBBhhhhhhhbb", ba, smh.TOTAL_HEADER_LENGTH)
                return payload_version, source_payload, source_payload_version, flags, voltage_12v_mv, voltage_3v3_mv, \
                    voltage_n3v3_mv, voltage_5v0_mv, voltage_3v3_if_mv, voltage_3v3_tx_mv, voltage_5v0_tx_mv, \
                    micro_temp_deg, ambient_temp_deg
            else:
                return None

    def send_set_unit_info(self, assy_part_no, assy_rev_no, assy_serial_no, assy_build_date_batch_no):
        """
        Utility method to pack the payload of a SetUnitInformation command and send it,
        strings are truncated to 15 characters plus Null termination
        :param assy_build_date_batch_no: :type string
        :param assy_serial_no: :type string
        :param assy_rev_no: :type string
        :param assy_part_no: :type string
        :return: True if message added to serial message handler tx queue, else False
        """
        if type(assy_part_no) is not str or type(assy_rev_no) is not str or \
           type(assy_serial_no) is not str or type(assy_build_date_batch_no) is not str:
            log.critical("One of the parameters is not of type str!")
            return False

        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      CtsMsgId.SET_UNIT_INFO.value,
                                                      CtsMsgPayloadLen.SET_UNIT_INFO.value)

        payload_bytes = bytearray(struct.pack("B16s16s16s16s",
                                  0,
                                  assy_part_no[0: 15].encode("utf-8"),
                                  assy_rev_no[0: 15].encode("utf-8"),
                                  assy_serial_no[0: 15].encode("utf-8"),
                                  assy_build_date_batch_no[0: 15].encode("utf-8")))

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        return self.wait_for_ack(seq_no, CtsMsgId.SET_UNIT_INFO.value)

    def send_start_file_upload(self, file_size_bytes, file_crc16, check_for_resp=True):
        """
        Send a Start File Upload Test Message.
        Currently the only file type supported is firmware.
        :param file_size_bytes: :type Integer
        :param file_crc16: :type Integer
        :param check_for_resp: set to False if not interested in waiting for the Response message
        :return: True if message ack'd by the receiver, else False
        """
        file_size_bytes = int(file_size_bytes)
        file_crc16 = int(file_crc16)

        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      CtsMsgPayloadLen.TEST_MSG_START_FILE_UPLOAD.value)

        payload_bytes = bytearray(struct.pack("<BBBBIH",
                                  0,                                        # Payload Format Version
                                  CtsTestMsgType.START_FILE_UPLOAD.value,   # Test Message Type
                                  0,                                        # Test Message Payload Format Version
                                  0,                                        # File Type = Firmware
                                  file_size_bytes,                          # File size bytes
                                  file_crc16))                              # File CRC-16

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        ret_val = self.wait_for_ack(seq_no, cmd_id)

        if ret_val and check_for_resp:
            ret_val = self.check_for_resp(seq_no, cmd_id, timeout_s=5.0)

        return ret_val

    def send_file_data(self, data, check_for_resp=True):
        """
        Send a File Data Test Message, a file transfer must have been started first using the Start File Upload
        command.
        :param data: :type bytearray
        :param check_for_resp: set to False if not interested in waiting for the Response message
        :return: True if message added to serial message handler tx queue, else False
        """
        if type(data) != bytearray:
            raise TypeError("data must be a bytearray!")

        data_length = len(data)
        if data_length > 240:
            raise ValueError("Maximum allowable length of data is 240!")

        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      CtsMsgPayloadLen.TEST_MSG_DATA_MIN.value + data_length)

        payload_bytes = bytearray(struct.pack("BBBB",
                                  0,                                        # Payload Format Version
                                  CtsTestMsgType.FILE_DATA.value,           # Test Message Type
                                  0,                                        # Test Message Payload Format Version
                                  data_length))                             # Data Length
        payload_bytes = bytearray().join([payload_bytes, data])

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        ret_val = self.wait_for_ack(seq_no, cmd_id)

        if ret_val and check_for_resp:
            ret_val = self.check_for_resp(seq_no, cmd_id)

        return ret_val

    def verify_file_crc(self, file_crc16):
        """
        Use the Test Message Verify File CRC command to verify a the CRC of a file that has just been transferred.
        Currently the only file type supported is firmware.
        :param file_crc16: expected CRC-16 for the file :type Integer
        :return: file_crc16 if message added to serial message handler tx queue, else False
        """
        file_crc16 = int(file_crc16)
        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      CtsMsgPayloadLen.TEST_MSG_VERIFY_CRC.value)

        payload_bytes = bytearray(struct.pack("<BBBBH",
                                  0,                                        # Payload Format Version
                                  CtsTestMsgType.VERIFY_FILE_CRC.value,     # Test Message Type
                                  0,                                        # Test Message Payload Format Version
                                  0,                                        # File Type = Firmware
                                  file_crc16))                              # CRC-16

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        # Wait for Ack, if it's successful wait for response
        if not self.wait_for_ack(seq_no, cmd_id):
            log.debug("No Ack")
            return False, None
        else:
            log.debug("Ack'd")

        ret_val = False

        rx_timeout = time.time() + self.response_timeout
        while True:
            time.sleep(RX_MSG_THREAD_SLEEP_S)
            rx_msg = self._smh.get_from_rx_queue()
            if rx_msg:
                log.debug("Verify File CRC Rx Msg: {}".format(" ".join(format(x, '02x') for x in rx_msg)))

                if len(rx_msg) == \
                        smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_VERIFY_CRC_RESP.value + smh.CRC_LENGTH:
                    if rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value] == seq_no and \
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value] == cmd_id and \
                            (((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x80) or
                             ((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x00)):
                        ret_val = True
                        break
                    else:
                        log.debug("Verify File CRC Rx Msg Failed Consistency Check! {} - {}; {} - {}; {}".format(
                            rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value], seq_no,
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value], cmd_id,
                            rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0))
                else:
                    log.debug("Verify File CRC Rx Msg Failed Length Check!")

            if time.time() > rx_timeout:
                log.debug("Verify File CRC Rx Msg Timed Out! - {:02x}".format(cmd_id))
                break

        return ret_val, rx_msg

    @staticmethod
    def unpack_verify_file_crc_response(ba):
        """
        Utility method to unpack the payload of a VerifyFileCrc Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else 5x unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_VERIFY_CRC_RESP.value + smh.CRC_LENGTH:
            log.critical("Unpack VerifyFileCrc Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_VERIFY_CRC_RESP.value + smh.CRC_LENGTH))
            return None
        else:
            payload_version, test_msg_type, test_msg_version, file_type, crc_valid, file_crc = \
                struct.unpack("<BBBBBH", ba[smh.TOTAL_HEADER_LENGTH:len(ba) - smh.CRC_LENGTH])
            return payload_version, test_msg_type, test_msg_version, file_type, \
                   True if crc_valid == 1 else False, file_crc

    def send_relaunch(self):
        """
        Send a Relaunch Test Message, relaunches with new Option Byte settings after firmware upload.
        :return: True if message ack'd by the receiver, else False
        """
        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      CtsMsgPayloadLen.TEST_MSG_RELAUNCH.value)

        payload_bytes = bytearray(struct.pack("BB",
                                              0,  # Payload Format Version
                                              CtsTestMsgType.RELAUNCH.value))

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        return self.wait_for_ack(seq_no, cmd_id)

    def send_set_rf_cal_table(self, rf_cal_power_0dbm1, slope_0dp1_points, offset_mv_points, check_for_resp=True):
        """
        Send a Set RF Calibration Table command, the K-CEMA Jupiter requires 8x cal points, one per Rx path:
            0 - 20 to 500 MHz
            1 - 500 to 800 MHz
            2 - 800 to 2000 MHz
            3 - 2000 to 2600 MHz
            4 - 2600 to 3000 MHz
            5 - 3000 to 4400 MHz
            6 - 4400 to 4670 MHz
            7 - 4670 to 6000 MHz
        :param rf_cal_power_0dbm1: the reference RF Power used for calibration
        :param offset_mv_points: ADC mV offset at reference RF Power :type list 0f 8x Integers
        :param slope_0dp1_points: slope, resolution 0.1 :type list of 8x Integers
        :param check_for_resp: set to False if not interested in waiting for the Response message
        :return: True if message ack'd by the receiver, else False
        """
        if len(slope_0dp1_points) != 8 or len(offset_mv_points) != 8:
            raise ValueError("Not enough calibration points!")

        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      CtsMsgPayloadLen.TEST_MSG_SET_RF_CAL_TABLE.value)

        payload_bytes = bytearray(struct.pack("<BBBBh",
                                              0,                            # Payload Format Version
                                              CtsTestMsgType.SET_RF_CAL_TABLE.value,    # Test message type
                                              0,                            # Test Message Payload Format Version
                                              8,                            # Number of RF calibration points
                                              int(rf_cal_power_0dbm1)))     # RF Power used for calibration (0.1dBm)

        for i in range(0, 8):
            cal_point_bytes = bytearray(struct.pack("<hh", int(slope_0dp1_points[i]), int(offset_mv_points[i])))
            payload_bytes = bytearray().join([payload_bytes, cal_point_bytes])

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        ret_val = self.wait_for_ack(seq_no, cmd_id)

        if ret_val and check_for_resp:
            ret_val = self.check_for_resp(seq_no, cmd_id)

        return ret_val

    def get_vco_settings(self, freq_khz):
        """
        Sends a GetVcoSettings Test Message, processes ACK response and returns response message
        :param freq_khz: the frequency to get VCO settings for :type Integer
        :return: [0] True if response received, else False; [1] the received message
        """
        cmd_id = CtsMsgId.TEST.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no=seq_no,
                                                      ack_no=0,  # '0' for new message
                                                      status=0,  # Status = '0' for new message and Protocol = '0'
                                                      msg_id=cmd_id,
                                                      pl_len=CtsMsgPayloadLen.TEST_MSG_GET_VCO_SETTINGS_CMD.value)

        payload_bytes = bytearray(struct.pack("<BBBI",
                                              0,                                            # Payload format ver
                                              CtsTestMsgType.GET_VCO_SETTINGS_CMD.value,    # Test msg type
                                              0,                                            # Test msg payload fmt ver
                                              int(freq_khz)))                               # Frequency, resolution kHz
        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        # Wait for Ack, if it's successful wait for response
        if not self.wait_for_ack(seq_no, msg_id=cmd_id):
            log.debug("No Ack")
            return False, None

        ret_val = False
        rx_timeout = time.time() + self.response_timeout
        while True:
            time.sleep(RX_MSG_THREAD_SLEEP_S)
            rx_msg = self._smh.get_from_rx_queue()
            if rx_msg:
                if len(rx_msg) == smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_GET_VCO_SETTINGS_RESP.value + smh.CRC_LENGTH:
                    if rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value] == seq_no and \
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value] == cmd_id and \
                            (((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x80) or
                                ((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) == 0x00)) and \
                            rx_msg[smh.TOTAL_HEADER_LENGTH + 2] == 0 and \
                            rx_msg[smh.TOTAL_HEADER_LENGTH + 1] == CtsTestMsgType.GET_VCO_SETTINGS_RESP.value:
                        ret_val = True
                        break
                    else:
                        log.debug("Get VCO Settings Cmd Rx Msg Failed Consistency Check! {} - {}; {} - {}; {}".format(
                            rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value], seq_no,
                            rx_msg[smh.HeaderOffset.MESSAGE_ID.value], cmd_id,
                            rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0))
                else:
                    log.debug("Get VCO Settings Cmd Rx Msg Failed Length Check!")

            if time.time() > rx_timeout:
                log.debug("Get VCO Settings Cmd Rx Msg Timed Out!")
                break

        return ret_val, rx_msg

    @staticmethod
    def unpack_test_msg_get_vco_settings(ba):
        """
        Utility method to unpack the payload of a TestMsgGetVcoSettings Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type or length, else unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_GET_VCO_SETTINGS_RESP.value + smh.CRC_LENGTH:
            log.critical("Unpack TestMsgGetVcoSettings Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.TEST_MSG_GET_VCO_SETTINGS_RESP.value + smh.CRC_LENGTH))
            return None
        else:
            # Check the payload format version, test message type and tet message payload format version
            if ba[smh.TOTAL_HEADER_LENGTH] == 0 and ba[smh.TOTAL_HEADER_LENGTH + 2] == 0 and \
                    ba[smh.TOTAL_HEADER_LENGTH + 1] == CtsTestMsgType.GET_VCO_SETTINGS_RESP.value:
                payload_version, test_msg_type, tst_msg_payload_version, freq_khz, vco_core, vco_band, vco_bias_code = \
                    struct.unpack_from("<BBBIBBB", ba, smh.TOTAL_HEADER_LENGTH)
                return payload_version, test_msg_type, tst_msg_payload_version, freq_khz, \
                    vco_core, vco_band, vco_bias_code
            else:
                return None

    def send_start_scan(self, mode, freq_khz, dwell_time_ms, tx_atten_0db5, rx_atten_0db5, no_blanking_transitions=0,
                        blanking_period_0us5=0, blanking_transitions_0us1=[], check_for_resp=True):
        """
        Send a StartScan Message.
        TODO: Not handling blanking patterns at the moment.
        :param check_for_resp: set to False if not interested in waiting for the Response message
        :return: True if message ack'd by the receiver, else False
        """
        if type(mode) is not CtsScanMode:
            raise TypeError("mode must be type CtsScanMode")

        seq_no = self._smh.get_next_sequence_number()
        cmd_id = CtsMsgId.START_SCAN.value
        if no_blanking_transitions > 0:
            payload_len = CtsMsgPayloadLen.START_SCAN_MIN.value + 4 + (4 * no_blanking_transitions)
        else:
            payload_len = CtsMsgPayloadLen.START_SCAN_MIN.value
        header_bytes = self._smh.build_message_header(seq_no,
                                                      0,
                                                      smh.MessageStatus.NEW_MESSAGE.value,
                                                      cmd_id,
                                                      payload_len)

        payload_bytes = bytearray(struct.pack("<BBLHBBB",
                                              0,                     # Payload Format Version
                                              int(mode.value),       # Scan mode
                                              int(freq_khz),         # Frequency, resolution kHz
                                              int(dwell_time_ms),    # Dwell time, resolution milli-seconds
                                              int(tx_atten_0db5),    # Transmit attenuation, resolution 0.5 dB
                                              int(rx_atten_0db5),    # Receive attenuation, resolution 0.5 dB
                                              int(no_blanking_transitions)))  # No blanking pattern transitions

        # Add in the timing pattern transitions
        if no_blanking_transitions > 0:
            if len(blanking_transitions_0us1) != no_blanking_transitions:
                return False

            blanking_period_0us5_int = int(blanking_period_0us5)
            for rs in [0, 8, 16, 24]:
                payload_bytes.append((blanking_period_0us5_int >> rs) & 0xFF)

            for blanking_transition_0us1 in blanking_transitions_0us1:
                blanking_transition_0us1_int = int(blanking_transition_0us1)
                for rs in [0, 8, 16, 24]:
                    payload_bytes.append((blanking_transition_0us1_int >> rs) & 0xFF)

        # Add the payload CRC
        payload_crc = CRCCCITT(version="FFFF").calculate(bytes(payload_bytes))
        payload_crc_bytes = payload_crc.to_bytes(2, byteorder="little")
        payload_bytes.append(payload_crc_bytes[0])  # CRC LSB
        payload_bytes.append(payload_crc_bytes[1])  # CRC MSB

        # Build and send the message
        msg_bytes = header_bytes + payload_bytes
        self._smh.send_to_tx_queue(msg_bytes)

        ret_val = self.wait_for_ack(seq_no, cmd_id)

        if ret_val and check_for_resp:
            ret_val = self.check_for_resp(seq_no, cmd_id)

        return ret_val

    def send_stop_scan(self):
        """
        Sends a StopScan message, waits for the response and processes it
        :return: True if StopScan message is successfully ack'd, else False :type Boolean
        """
        cmd_id = CtsMsgId.STOP_SCAN.value
        seq_no = self._smh.get_next_sequence_number()
        header_bytes = self._smh.build_message_header(seq_no=seq_no,
                                                      ack_no=0,  # '0' for new message
                                                      status=0,  # Status = '0' for new message and Protocol = '0'
                                                      msg_id=cmd_id,
                                                      pl_len=0)  # No payload

        log.debug("Tx StopScan: {}".format(" ".join(format(x, '02x') for x in header_bytes)))
        self._smh.send_to_tx_queue(header_bytes)

        return self.wait_for_ack(seq_no, cmd_id)

    @staticmethod
    def unpack_get_scan_status_response(ba):
        """
        Utility method to unpack the payload of a GetScanStatus Response
        :param ba: ByteArray payload of response message to unpack
        :return: None if ba is wrong type, length or payload format is unrecognised, else unpacked values
        """
        if type(ba) != bytearray or len(ba) != \
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_SCAN_STATUS.value + smh.CRC_LENGTH:
            log.critical("Unpack GetScanStatus Response expecting {}-byte array".format(
                smh.TOTAL_HEADER_LENGTH + CtsMsgPayloadLen.GET_SCAN_STATUS.value + smh.CRC_LENGTH))
            return None
        else:
            # Check the payload format version is supported
            if ba[smh.TOTAL_HEADER_LENGTH] == 0:
                payload_version, status, rf_detector_power_0dbm1, rf_detector_voltage_mv, remaining_dwell_time_ms = \
                    struct.unpack_from("<BBhhh", ba, smh.TOTAL_HEADER_LENGTH)
                return payload_version, status, rf_detector_power_0dbm1, rf_detector_voltage_mv, remaining_dwell_time_ms
            else:
                return None

    def check_for_resp(self, seq_no, msg_id, timeout_s=DEFAULT_RESPONSE_TIMEOUT):
        """
        Some commands will send a Response NOK after the ACK if payload processing fails.
        This method can be used to poll for Response NOK messages if required.
        :param seq_no: sequence no of message that is being checked
        :param msg_id: ID of message that is being checked
        :param timeout_s: time to wait in seconds
        :return: True if the Response OK is received before timeout, else False if Response NOK received or timeout
        """
        ret_val = False
        rx_timeout = time.time() + timeout_s
        while True:
            time.sleep(RX_MSG_THREAD_SLEEP_S)
            rx_msg = self._smh.get_from_rx_queue()
            if rx_msg:
                if rx_msg[smh.HeaderOffset.ACKNOWLEDGEMENT_NO.value] == seq_no and \
                        rx_msg[smh.HeaderOffset.MESSAGE_ID.value] == msg_id:
                    # Check for Response OK
                    ret_val = ((rx_msg[smh.HeaderOffset.MESSAGE_STATUS_PROTOCOL_VERSION.value] & 0xE0) >> 5) == \
                              smh.MessageStatus.RESPONSE_OK.value
                    break

            if time.time() > rx_timeout:
                log.debug("Looking for Resp Rx Msg Timed Out! - {:02x}".format(msg_id))
                break

        return ret_val


class CtsSerialMsgInterface(CtsMsgInterface):
    """
    Class that implements UART based implementation for CtsMsgInterface.
    """
    def __init__(self, serial_port, baud_rate=115200, response_timeout=DEFAULT_RESPONSE_TIMEOUT):
        """
        Class constructor
        :param serial_port: serial UART port to open, e.g. "COM1", "/dev/ttyACM0" :type: string
        :param baud_rate: UART baud rate, optional, default is 115200 :type: integer
        """
        self._serial_port = serial_port
        self._baud_rate = baud_rate

        super().__init__(response_timeout)

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "CtsSerialMsgInterface({!r}, {!r})".format(self._serial_port, self._baud_rate)

    def __enter__(self):
        """ Context manager entry """
        if self._smh is not None:
            raise RuntimeError("Already started SMH!")
        self._smh = smh.MessageHandler()
        if not self._smh.start(self._serial_port, self._baud_rate):
            raise RuntimeError("Failed to start SMH!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Context manager exit - stop the serial message handler """
        self._smh.stop()


class CtsSerialTcpMsgInterface(CtsMsgInterface):
    """
    Class that implements Serial TCP based implementation for CtsMsgInterface.
    """
    def __init__(self, host, port=DEFAULT_NETWORK_PORT, response_timeout=DEFAULT_RESPONSE_TIMEOUT):
        """
        Class constructor
        :param host: host IP address or hostname :type: string
        :param port: host TCP port to connect on :type: integer
        """
        self._host = host
        self._port = port

        super().__init__(response_timeout)

    def __repr__(self):
        """
        :return: string representing the class
        """
        return "CtsSerialMsgInterface({!r}, {!r})".format(self._host, self._port)

    def __enter__(self):
        """ Context manager entry """
        if self._smh is not None:
            raise RuntimeError("Already started SMH!")
        self._smh = smh.TcpMessageHandler()
        if not self._smh.start(self._host, self._port):
            raise RuntimeError("Failed to start SMH!")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Context manager exit - stop the serial message handler """
        self._smh.stop()

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
