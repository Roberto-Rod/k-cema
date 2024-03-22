#!/usr/bin/env python3
"""
Utility module for updating Integrated CTS firmware by serial UART.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
"-f", "--fw_file", Firmware File
"-u", "--uart", Serial UART
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
import os

# Third-party imports -----------------------------------------------
from PyCRC.CRCCCITT import CRCCCITT

# Our own imports ---------------------------------------------------
from cts_serial_msg_intf import *
import exp_power_disable

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
UART = "/dev/ttyUL8"
ERASE_LINE = "\033[2K"
CURSOR_HOME = "\033[100D"
DATA_CHUNK_SIZE_BYTES = 240

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(fw_file, uart):
    """
    Sets the CSM Motherboard GPIO1 register to assert/de-assert the
    RF_MUTE signals based on the passed command line argument
    :param fw_file: firmware file to update CTS with. :type String
    :param uart: serial UART to be used for the firmware update :type String
    :return: N/A
    """
    if not os.path.isfile(fw_file):
        raise ValueError("Invalid firmware file - {}!".format(fw_file))

    if not os.path.isfile(fw_file):
        raise ValueError("Invalid UART - {}!".format(uart))

    fw_file_size = os.path.getsize(fw_file)
    fw_file_crc16 = CRCCCITT(version="FFFF").calculate(open(fw_file, mode="rb").read())

    with CtsSerialMsgInterface(uart, response_timeout=7.0) as c:
        exp_power_disable.expansion_slot_power_disable(1, True)
        time.sleep(1.0)
        exp_power_disable.expansion_slot_power_disable(1, False)
        time.sleep(3.0)

        log.info("CTS Ping: {}".format(c.send_ping()))
        log.info("Start File Upload: {}".format(c.send_start_file_upload(fw_file_size, fw_file_crc16)))

        with open(fw_file, mode="rb") as f:
            file_transfer_success = True
            chunk_no = 1
            total_chunks = int(fw_file_size / DATA_CHUNK_SIZE_BYTES)
            chunk = bytearray(f.read(DATA_CHUNK_SIZE_BYTES))
            log.info("Data transfer Progress:")
            while chunk:
                if c.send_file_data(chunk):
                    print("{}{}{} %".format(ERASE_LINE, CURSOR_HOME, int((chunk_no / total_chunks) * 100)),
                          end="", flush=True)
                    chunk_no += 1
                    chunk = bytearray(f.read(DATA_CHUNK_SIZE_BYTES))
                else:
                    log.info("Send File Data: False")
                    file_transfer_success = False
                    break

        if file_transfer_success:
            cmd_success, resp = c.verify_file_crc(fw_file_crc16)

            if cmd_success:
                payload_version, test_msg_type, test_msg_version, file_type, crc_valid, file_crc = \
                    c.unpack_verify_file_crc_response(resp)
                log.info("Verify File CRC: valid {}; expected x{:4x}; returned x{:4x}"
                         "".format(crc_valid, fw_file_crc16, file_crc))
                log.info("Relaunch - {}".format(c.send_relaunch()))
            else:
                log.info("Verify File Crc: Command Failed")

        time.sleep(3.0)
        result, msg = c.get_command(CtsMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                    CtsMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
        if result:
            payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                c.unpack_get_software_version_number_response(msg)
            print("Sw Version: {}.{}.{}:{}".format(sw_major, sw_minor, sw_patch, sw_build))
        else:
            print("Sw Version Read Fail")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="CTS Firmware Update Utility")
    parser.add_argument("-f", "--fw_file", help="Firmware File")
    parser.add_argument("-u", "--uart", help="Serial UART")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.fw_file, args.uart)
