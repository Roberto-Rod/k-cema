#!/usr/bin/env python3
"""
Test script for Active Backplane Telnet Server, sends test string and checks
for response on Telnet ports: 23, 26, 27, 28, 29, 30

To use the test script loop the UART TXD output for each port back to its
RXD signal so that the UART is operating in a physical loopback mode.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-t/--telnet_server required argument specifies Telnet Server IP address or hostname
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
from telnetlib import Telnet
import random
import time
from concurrent.futures import ThreadPoolExecutor

# Third-party imports -----------------------------------------------


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
class AbTelnetStressTest:
    """
    Active Backplane Telnet stress test, provides functionality to stress test the
    different Telnet server ports implemented in the Active Backplane firmware,
    KT-956-0194-00.
    """
    # Port 23 is CSM Master SerialInterface
    #TELNET_PORTS = {23, 26, 27, 28, 29, 30}
    TELNET_PORTS = {26, 27, 28, 29, 30}
    TEST_STRING = b"The quick brown fox jumped over the lazy dog!"
    TEST_TIMEOUT_SEC = 2

    def __init__(self, ip_address):
        """
        Class constructor
        :param ip_address: IP address or hostname for Active Backplane microcontroller
        Telnet server :type string
        """
        self.ip_address = ip_address

    def str_test_telnet_server(self, port=23, test_string=None):
        """
        Perform an ASCII string based tx/rx test
        :param port: Telnet server port :type Integer
        :param test_string: ASCII text string to send, if this parameter is set to None
        or left out then self.TEST_STRING is used :type ByteArray
        :return: True if the string is successfully echoed, else False :type Boolean
        """
        if test_string is None:
            test_string = self.TEST_STRING
        return self._tx_rx_test(port, test_string)

    def bin_test_telnet_server(self, port=23, data_len=1024):
        """
        Generates an array of random bytes, data_len in length then performs
        a tx/rx test using the random data
        :param port: Telnet server port :type Integer
        :param data_len: required length of random-bytes array :type Integer
        :return: True if the data is successfully echoed, else False :type Boolean
        """
        # Limit random data to ASCII character codes as control
        # codes may be handled differently by the Telnet server
        test_data = bytes([random.randint(0x20, 0x7F) for x in range(0, data_len)])
        return self._tx_rx_test(port, test_data)

    def _tx_rx_test(self, port, data):
        """
        Private function performs the tx/rx test, i.e. sends data and
        checks that it is echoed back
        :param port: Telnet server port :type Integer
        :param data: data array to tx/rx :type ByteArray
        :return: True if the data is successfully echoed, else False :type Boolean
        """
        test_pass = True

        try:
            with Telnet(self.ip_address, port) as tn:
                tn.write(data)
                ret_data = tn.read_until(data, self.TEST_TIMEOUT_SEC)
                tn.close()
                # result = "{}:{} - {} ".format(self.ip_address, port, ret_data)
                result = "{}:{} - ".format(self.ip_address, port)

                if ret_data == data:
                    result += "PASS"
                    test_pass &= True
                else:
                    result += "FAIL"
                    test_pass &= False

                log.info(result)

        except Exception as ex:
            log.critical("{}:{} - {}".format(self.ip_address, port, ex))
            test_pass = False

        return test_pass


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(ip_address):
    """
    Runtime procedure called when the the module is executed standalone or
    by a function call if the module is imported into another module.

    The Telnet ports are tested in parallel using the ThreadPoolExecutor
    class from  the concurrent.futures library.
    :param ip_address: IP address or hostname for Active Backplane microcontroller
    Telnet server :type string
    :return: None
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    overall_pass = True
    no_loops = 100

    # start = time.time()
    # for _ in range(0, no_loops):
    #     for port in AbTelnetStressTest.TELNET_PORTS:
    #         att = AbTelnetStressTest(ip_address)
    #         overall_pass = overall_pass and att.str_test_telnet_server(port)
    #         overall_pass = overall_pass and att.bin_test_telnet_server(port)
    # end = time.time()
    # log.info("That took: {:3f} seconds".format(end - start))

    start = time.time()
    no_fails = 0
    for _ in range(0, no_loops):
        att = AbTelnetStressTest(ip_address)
        pool = ThreadPoolExecutor(max_workers=len(att.TELNET_PORTS))

        results = list(pool.map(att.str_test_telnet_server, AbTelnetStressTest.TELNET_PORTS))
        test1_pass = all(x is True for x in results) and len(results) > 0

        results = list(pool.map(att.bin_test_telnet_server, AbTelnetStressTest.TELNET_PORTS))
        test2_pass = all(x is True for x in results) and len(results) > 0

        overall_pass = overall_pass and test1_pass and test2_pass
        if not (test1_pass and test2_pass):
            no_fails += 1

    end = time.time()
    log.info("Pass rate: {} of {}".format((no_loops - no_fails), no_loops))
    log.info("That took: {:3f} seconds".format(end - start))

    if overall_pass:
        log.info("Test PASSED")
    else:
        log.info("Test FAILED!")

    return None


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="Active Backplane Telnet Server Stress Test")
    parser.add_argument("-t", "--telnet_server", required=True, dest="telnet_server", action="store",
                        help="Telnet Server IP address")
    args = parser.parse_args()

    main(args.telnet_server)
