#!/usr/bin/env python3
"""
Procedural test script for KT-000-0140-00 CSM Motherboard Production Test
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-m/--ema_com_port name of EMA Test Interface board COM port
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
import logging
from datetime import datetime

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
import keypad_buzzer_test
import battery_signal_test
import ptp_phy_test
import som_eia422_intf_test
import anti_tamper_prod_test
import zeroise_fpga_test

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


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(csm_micro_com_port, csm_master_port):
    """
    Executes tests and determines overall test script result
    :param csm_micro_com_port: name of serial port for CSM Zeroise Micro test interface :type: string
    :param csm_master_port: name of serial port for CSM Master test interface :type: string
    :return: None
    """
    log.info("KT-000-0140-00 CSM Motherboard PC Test Script:")
    input("Check that the required COM ports are disconnected <Enter>")
    overall_pass = True
    overall_pass = ptp_phy_test.run_test(csm_master_port) and overall_pass
    overall_pass = som_eia422_intf_test.run_test(csm_micro_com_port, csm_master_port) and overall_pass
    overall_pass = battery_signal_test.run_test(csm_micro_com_port) and overall_pass
    overall_pass = zeroise_fpga_test.run_test(csm_micro_com_port) and overall_pass
    overall_pass = keypad_buzzer_test.run_test(csm_micro_com_port) and overall_pass
    overall_pass = anti_tamper_prod_test.run_test(csm_micro_com_port) and overall_pass

    log_str = " - Overall Test Result"
    if overall_pass:
        log.info("PASS" + log_str)
    else:
        log.info("FAIL" + log_str)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM Motherboard Production Test Script")
    parser.add_argument("-m", "--csm_micro_port", required=True, dest="csm_micro_port", action="store",
                        help="Name of CSM Zeroise Microcontroller COM port")
    parser.add_argument("-c", "--csm_master_port", required=True, dest="csm_master_port", action="store",
                        help="Name of CSM Master COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    log_file_name = "KT-000-0140-00_{}.txt".format(datetime.now().strftime("%Y%m%d%H%M%S"))
    logging.basicConfig(filename=log_file_name, filemode='w', format=fmt, level=logging.INFO, datefmt="%H:%M:%S")
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger().addHandler(console)

    main(args.csm_micro_port, args.csm_master_port)
