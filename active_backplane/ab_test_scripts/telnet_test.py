#!/usr/bin/env python3
"""
Test script for Active Backplane Telnet Server, sends test string and checks
for response on Telnet ports: 23, 26, 27, 28, 29, 30.

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
class AbTelnetTest:
    """
    Active Backplane Telnet  test, provides functionality to quickely test the
    different Telnet server ports implemented in the Active Backplane firmware,
    KT-956-0194-00.
    """
    def __init__(self):
        """
        Class constructor
        """
        self.TELNET_PORTS = [23, 26, 27, 28, 29, 30]
        self.TEST_STRING = b"The quick brown fox jumped over the lazy dog!"
        self.TEST_TIMEOUT_SEC = 2
        
    def test_telnet_server(self, ip_address, telnet_ports=None):
        """
        Performs a simple tx/rx test on each Telnet server port in turn. Sends
        a test string and checks that it is correctly echoed back.
        :param ip_address: IP address or hostname for Active Backplane microcontroller
        :param telnet_ports: list of port numbers to test, default None, use
        ports defined in self.TELNET_PORTS. :type: Integer List
        :return: True if the test passes, else False :type Boolean
        """
        test_pass = True

        try:
            if telnet_ports is None:
                test_ports = self.TELNET_PORTS
            else:
                test_ports = telnet_ports

            for port in test_ports:
                with Telnet(ip_address, port) as tn:
                    tn.write(self.TEST_STRING)
                    ret_string = tn.read_until(self.TEST_STRING, self.TEST_TIMEOUT_SEC)
                    tn.close()
                    result = " - {}:{} - {}".format(ip_address, port, ret_string)
                    
                    if ret_string == self.TEST_STRING:
                        result = "PASS" + result
                        test_pass &= True
                    else:
                        result = "FAIL" + result
                        test_pass &= False
                        
                    log.info(result)
        
        except Exception as ex:
            log.critical("Something went wrong testing the Active Backplane Telnet Server\t" 
                         "{} - {}".format(ip_address, ex))
            test_pass &= False
        
        return test_pass


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(ip_address):
    """
    Runtime procedure called when the the module is executed standalone or
    by a function call if the module is imported into another module.

    Create a test object, execute the test and report the test result.
    :param ip_address: IP address or hostname for Active Backplane microcontroller
    Telnet server :type string
    :return: None
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.DEBUG, datefmt="%H:%M:%S")

    att = AbTelnetTest()
    if att.test_telnet_server(ip_address):
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
    parser = argparse.ArgumentParser(description="Active Backplane Telnet server test")
    parser.add_argument("-t", "--telnet_server", required=True, dest="telnet_server", action="store",
                        help="Telnet Server IP address")
    args = parser.parse_args()
    
    main(args.telnet_server)
