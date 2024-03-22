#!/usr/bin/env python3
"""
Blah...
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
import argparse
from enum import Enum
import logging
import threading
import time

# Third-party imports -----------------------------------------------
import serial

# Our own imports ---------------------------------------------------

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
SERIAL_PORT = "/dev/ttyUL4"
BAUD_RATE = 9600

NMEA_START_OF_FRAME = b"$"
NMEA_END_OF_FRAME = b"\r\n"

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
class GpsNmeaDecodeRxState(Enum):
    """
    Enumeration class for rx state machine
    """
    IDLE = 1
    RECEIVING_MESSAGE = 2
    MESSAGE_COMPLETE = 3


class GpsNmeaDecode:
    _RX_TX_TIMEOUT = 1.0

    def __init__(self):
        """
        Class constructor
        :param None
        :return: None
        """
        self._rx_thread = None
        self._event = threading.Event()
        self._serial_device = None
        self._gps_locked = False

    def __rx_thread_run(self):
        """
        Receive thread
        :return None:
        """
        log.debug("Rx Waiting...")

        current_state = GpsNmeaDecodeRxState.IDLE
        message_buffer = bytearray()

        while not self._event.is_set():
            try:
                # Attempt to read from the serial port
                rx_data = self._serial_device.read(1)

                if len(rx_data) >= 1:
                    if current_state == GpsNmeaDecodeRxState.IDLE:
                        log.debug("Rx Idle State")
                        if rx_data == NMEA_START_OF_FRAME:
                            log.debug("Rx Start of Message Detected")
                            message_buffer += rx_data
                            current_state = GpsNmeaDecodeRxState.RECEIVING_MESSAGE

                    if current_state == GpsNmeaDecodeRxState.RECEIVING_MESSAGE:
                        message_buffer += rx_data
                        if message_buffer[-2:] == NMEA_END_OF_FRAME:
                            current_state = GpsNmeaDecodeRxState.MESSAGE_COMPLETE

                    if current_state == GpsNmeaDecodeRxState.MESSAGE_COMPLETE:
                        log.debug("Rx Message Complete State")
                        if message_buffer.find(b"$GNGGA") != -1:
                            nmea_string = message_buffer.decode("UTF-8")
                            nmea_params = nmea_string.split(sep=",")
                            log.debug(nmea_params)
                            if int(nmea_params[6]) == 0:
                                self._gps_locked = False
                            else:
                                self._gps_locked = True

                        message_buffer.clear()
                        current_state = GpsNmeaDecodeRxState.IDLE

            except Exception as ex:
                log.debug("Rx Caught exception in __rx_thread: {}".format(ex))

        log.debug("Rx __rx_thread exiting")

    def start(self, serial_port, baud_rate):
        """
        Starts the MessageHandler running
        :param serial_port:
        :param baud_rate:
        :return: None
        """
        log.debug('Starting MessageHandler...')

        try:
            self._serial_device = serial.Serial(serial_port, baud_rate, timeout=GpsNmeaDecode._RX_TX_TIMEOUT,
                                                xonxoff=False, rtscts=False, dsrdtr=False)

            if self._serial_device.isOpen():
                log.debug('Serial Port Opened')

                self._serial_device.timeout = GpsNmeaDecode._RX_TX_TIMEOUT
                self._event.clear()

                self._rx_thread = threading.Thread(target=self.__rx_thread_run)
                self._rx_thread.start()

            else:
                log.critical('Failed to open the serial port')

        except Exception as ex:
            self._event.set()
            if self._serial_device is not None:
                self._serial_device.close()
            log.critical("Failed to start MessageHandler: {}".format(ex))

        if not self._event.is_set():
            return True
        else:
            return False

    def stop(self):
        """
        Stop the MessageHandler from running
        :return:
        """
        if not self._event.is_set():
            self._event.set()
            time.sleep(GpsNmeaDecode._RX_TX_TIMEOUT * 2)
            if self._serial_device:
                self._serial_device.close()

    def wait_for_lock(self, timeout=10, serial_port=SERIAL_PORT):
        """
        Wait for up to timeout seconds for the GPS to become locked.
        :param timeout: how long to wait in secons :type Integer
        :param serial_port: GPS Serial port :type String
        :return: True if the GPS is locked before timeout, else False :type Boolean
        """
        gps_locked = False

        self.start(serial_port, BAUD_RATE)

        log.info("INFO - Waiting for GPS lock")
        for timeout_count in range(1, timeout + 1):
            if self._gps_locked:
                gps_locked = True
                break
            else:
                log.info("INFO - {} of {}".format(timeout_count, timeout))
                time.sleep(1)

        if gps_locked:
            log.info("INFO - GPS is locked")
        else:
            log.info("INFO - GPS is NOT locked (waited {}-seconds)".format(timeout))

        self.stop()

        return gps_locked


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(check_gps_lock, serial_port):
    """
    Blah...
    :return: None
    """
    gnd = GpsNmeaDecode()

    if check_gps_lock:
        gnd.wait_for_lock(timeout=30, serial_port=serial_port)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="CSM GPS NMEA Decoder")
    parser.add_argument("-l", "--lock_check", action="store_true", help="Check for GPS lock")
    parser.add_argument("-s", "--serial_port", default=SERIAL_PORT, help="GPS serial port")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.lock_check, args.serial_port)
