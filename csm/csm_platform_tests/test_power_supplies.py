#!/usr/bin/env python3
"""
Test power supply rails
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from built_in_test import BuiltInTest, CsmAdcChannel, CsmPowerGood, XADCInternalVoltage
from test import *

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
def run_test():
    test_pass = True
    bit = BuiltInTest()

    for rail in CsmPowerGood:
        if bit.power_good(rail):
            log.info("PASS - {}".format(bit.pgood_name[rail]))
            test_pass &= True
        else:
            log.info("FAIL - {}".format(bit.pgood_name[rail]))
            test_pass &= False

    for adc_channel in CsmAdcChannel:
        val = bit.value(adc_channel)
        if Test.nom(val, bit.chan_nom[adc_channel], 10):    # Test and allow 10 % error from nominal
            log.info("PASS - {} [{:.2f} V]".format(bit.chan_name[adc_channel], val))
            test_pass &= True
        else:
            log.info("FAIL - {} [{:.2f} V]".format(bit.chan_name[adc_channel], val))
            test_pass &= False

    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCAUX)
    if Test.nom(val, 1.8, 10):  # Test and allow 10 % error from nominal
        log.info("PASS - +1V8 Rail [{:.2f} V]".format(val))
        test_pass &= True
    else:
        log.info("FAIL - +1V8 Rail [{:.2f} V]".format(val))
        test_pass &= False

    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCO_DDR)
    if Test.nom(val, 1.5, 10):  # Test and allow 10 % error from nominal
        log.info("PASS - +1V5 Rail [{:.2f} V]".format(val))
        test_pass &= True
    else:
        log.info("FAIL - +1V5 Rail [{:.2f} V]".format(val))
        test_pass &= False

    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCINT)
    if Test.nom(val, 1.0, 10):  # Test and allow 10 % error from nominal
        log.info("PASS - +1V0 SoC Core [{:.2f} V]".format(val))
        test_pass &= True
    else:
        log.info("FAIL - +1V0 SoC Core [{:.2f} V]".format(val))
        test_pass &= False

    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Run main() routine
    """
    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    log.info("Power Supply Test:")
    if run_test():
        log.info("\n*** OK - test passed ***\n")
    else:
        log.info("\n*** TEST FAILED ***\n")
