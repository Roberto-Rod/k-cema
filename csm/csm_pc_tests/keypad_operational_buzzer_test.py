#!/usr/bin/env python3
"""
Test script for exercising the buzzer and verifying it is in the expected state.

Sets the buzzer using CSM Platform Test Script via SSH command which sends
Binary Serial Protocol command to the Zeroise Microcontroller.

Checks the buzzer state by reading the voltage using the CSM Test Jig ASCII
serial interface.
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

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from csm_plat_test_intf import *
from csm_test_jig_intf import *

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


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    test_jig_com_port = "COM5"
    zeroise_micro_serial_port = "/dev/ttyZerMicro"
    csm_username = "root"
    csm_hostname = "csm-000000.local"
    csm_password = "gbL^58TJc"

    ctji = CsmTestJigInterface(test_jig_com_port)
    cpt = CsmPlatformTest(csm_username, csm_password, csm_hostname)

    ret_val = True

    for i in range(0, 1000):
        for assert_val in [False, True]:
            if not cpt.set_buzzer_state(zeroise_micro_serial_port, assert_val):
                print("INFO - Failed to set buzzer state")
            adc_read, adc_data = ctji.get_adc_data()
            if not adc_read:
                print("INFO - Failed to read buzzer state")
            adc_key = "(mv) Buzzer +12V Supply"
            test_pass = ((11800 <= adc_data.get(adc_key, -1) <= 12200) if assert_val else
                         (adc_data.get(adc_key, 12000) < 11800 or adc_data.get(adc_key, 12000) > 12200))

            print("{} - Buzzer Test: {} - {} - {}".format("PASS" if test_pass and ret_val else "FAIL",
                                                          adc_data.get(adc_key, -1), i, assert_val))
            ret_val = ret_val and test_pass

    print("{} - Overall result".format("PASS" if ret_val else "FAIL"))
