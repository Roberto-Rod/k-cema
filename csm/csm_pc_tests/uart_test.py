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
import queue
import threading
import logging
import time
from datetime import datetime

# Third-party imports -----------------------------------------------
import serial

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
class UartTest:
    """
    Class which tests UARTs by looping a test string back on each tested port
    """
    _RX_TX_TIMEOUT = 1.0
    _SERIAL_PORTS = ["/dev/ttyPS8", "/dev/ttyUL1", "/dev/ttyUL3", "/dev/ttyUL7"]
    _BAUD_RATES = [115200, 115200, 115200, 115200]
    _TEST_STRING = b"The quick brown fox jumps over the lazy dog!"
    _TEST_TIMEOUT = 3

    def __init__(self):
        """
        Class constructor
        :param None
        :return: None
        """
        self._tx_queue = queue.Queue()
        self._rx_queue = queue.Queue()
        self._rx_thread = None
        self._tx_thread = None
        self._event = threading.Event()
        self._serial_device = None

    def __rx_thread_run(self):
        """
        Receive thread
        :return None:
        """
        try:
            log.debug("Rx Waiting...")

            while not self._event.is_set():
                # Attempt to read from the serial port
                rx_data = self._serial_device.read(1)

                # read() call will time out if nothing was read
                if len(rx_data) >= 1:
                    self._rx_queue.put(rx_data)

            log.debug("Rx __rx_thread exiting")

        except Exception as ex:
            log.critical("Rx Caught exception in __rx_thread: {}".format(ex))

    def __tx_thread_run(self):
        """
        Transmit thread, put byte arrays into _tx_queue and they will be sent...
        :return None:
        """
        try:
            log.debug("Tx Ready...")

            while not self._event.is_set():
                time.sleep(0.001)
                try:
                    data_to_send = self._tx_queue.get(timeout=self._RX_TX_TIMEOUT)
                    self._serial_device.write(data_to_send)

                except queue.Empty:
                    log.debug("Tx Queue Empty")

                except Exception as ex:
                    log.critical("Tx writeThread exception {}".format(ex))

            log.debug("Tx __tx_thread exiting")

        except Exception as ex:
            log.critical("Tx Caught exception in __tx_thread: {}".format(ex))

    def __add_to_tx_queue(self, data):
        if self._serial_device.isOpen():
            self._tx_queue.put(data)
        else:
            log.critical("Tx serial port is NOT open")

    def __get_from_rx_queue(self):
        data = None

        if self._serial_device.isOpen():
            try:
                data = self._rx_queue.get(timeout=self._RX_TX_TIMEOUT)
            except queue.Empty:
                log.debug("Rx Queue Empty")
                data = None
        else:
            log.critical("Rx serial port is NOT open")

        return data

    def __start(self, serial_port, baud_rate):
        """
        Starts the MessageHandler running
        :param serial_port:
        :param baud_rate:
        :return: None
        """
        log.debug('Starting MessageHandler...')

        try:
            self._serial_device = serial.Serial(serial_port, baud_rate, timeout=self._RX_TX_TIMEOUT,
                                                xonxoff=False, rtscts=False, dsrdtr=False)

            if self._serial_device.isOpen():
                log.debug('Serial Port Opened')

                self._event.clear()
                self._tx_queue.empty()
                self._rx_queue.empty()

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
            log.critical("Failed to start MessageHandler: {}".format(ex))

        if not self._event.is_set():
            return True
        else:
            return False

    def __stop(self):
        """
        Stop the MessageHandler from running
        :return:
        """
        self._event.set()
        time.sleep(UartTest._RX_TX_TIMEOUT * 2)
        if self._serial_device:
            self._serial_device.close()

    def run_test(self):
        """
        Run the UART test routine
        :return: True if the test passes, else False
        """
        ret_val = True

        for sp, br in zip(self._SERIAL_PORTS, self._BAUD_RATES):
            test_pass = self.test_serial_port(sp, br)
            log.info("{} - UART {}, {}".format("PASS" if test_pass else "FAIL", sp, br))
            ret_val = ret_val and test_pass

        return ret_val

    def test_serial_port(self, serial_port, baud_rate):
        """
        Run the test routine on the specified serial port.
        :param serial_port: serial port to test :type: string
        :param baud_rate: serial baud rate :type: integer
        :return: True if test passes else false
        """
        test_pass = True

        if self.__start(serial_port, baud_rate):
            self.__add_to_tx_queue(self._TEST_STRING)
            rxb = bytearray()

            test_start_time = datetime.now()
            test_timeout = False

            while rxb != self._TEST_STRING:
                data = self.__get_from_rx_queue()

                if data is not None:
                    rxb += data
                    log.debug("Rx {}".format(rxb))

                time_diff = (datetime.now() - test_start_time)
                if time_diff.seconds > self._TEST_TIMEOUT:
                    test_timeout = True
                    break

            if test_timeout:
                test_pass = False

            self.__stop()
        else:
            test_pass = False

        return test_pass


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(serial_port, baud_rate):
    """
    Enable logging, run test and report the overall test result
    :param serial_port: serial port to test :type: string
    :param baud_rate: serial baud rate :type: integer
    :return: N/A
    """
    ut = UartTest()
    log.info("{} - UART {}, {}".format("PASS" if ut.test_serial_port(serial_port, baud_rate) else "FAIL",
                                       serial_port, baud_rate))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="CSM UART Test")
    parser.add_argument("-s", "--serial_port", required=True, dest="serial_port", action="store",
                        help="Serial port to test")
    parser.add_argument("-b", "--baud_rate", required=True, dest="baud_rate", action="store",
                        help="Serial port baud rate")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.serial_port, args.baud_rate)
