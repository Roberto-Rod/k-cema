#!/usr/bin/env python3
"""
Test script for KT-000-0140-00 Keypad and Buzzer, call script to execute test
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
import logging
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from csm_test_jig_intf import CsmTestJigInterface
from csm_zero_micro_test_intf import CsmZeroiseMircoTestInterface

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
def buzzer_auto_test(csm_rcu_com_port, test_jig_com_port):
    """
    Tests the board/unit under test buzzer using the KT-000-0197-00 test jig.
    Prerequisites:
    - Board is powered up
    - Linux is booted
    - CSM Zeroise Microcontroller is programmed with test utility
    Uses:
    - Test jig STM32 serial interface
    - CSM RCU serial interface
    :param test_jig_com_port: test jig serial COM port :type string
    :param csm_rcu_com_port: board/unit under test RCU COM port :type string
    :return: True if test passes, else False :type Boolean
    """
    ret_val = True

    with CsmZeroiseMircoTestInterface(csm_rcu_com_port) as czm:
        with CsmTestJigInterface(test_jig_com_port) as ctji:
            # De-assert -> Assert -> De-assert the buzzer then check the ADC data
            test_pass = True
            for assert_val in [False, True, False]:
                ret_val = czm.set_buzzer_enable(assert_val) and ret_val
                time.sleep(1.0)
                adc_read, adc_data = ctji.get_adc_data()
                ret_val = ret_val and adc_read
                adc_key = "(mv) Buzzer +12V Supply"
                test_pass = test_pass and \
                    ((11800 <= adc_data.get(adc_key, -1) <= 12200) if assert_val else
                     (adc_data.get(adc_key, -1) < 11800 or adc_data.get(adc_key, -1) > 12200))

            log.info("{} - Buzzer Test".format("PASS" if test_pass and ret_val else "FAIL"))
            ret_val = ret_val and test_pass

    return ret_val


def run_test(com_port):
    """
    Run Keypad and Buzzer test using the CSM Zeroise Micro Test Utility serial command interface
    :param com_port: name of serial port for CSM Zeroise Micro test interface :type string
    :return: True if test passes, else False :type Boolean
    """
    czm = CsmZeroiseMircoTestInterface(com_port)
    test_pass = True

    time.sleep(1)
    input("Hold down Keypad Jam Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(0)
    if cmd_success and btn_held:
        log.info("PASS - Button Jam Held")
        test_pass &= True
    else:
        log.info("FAIL - Button Jam Held")
        test_pass &= False

    time.sleep(1)
    input("Release Keypad Jam Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(0)
    if cmd_success and not btn_held:
        log.info("PASS - Button Jam Released")
        test_pass &= True
    else:
        log.info("FAIL - Button Jam Released")
        test_pass &= False

    time.sleep(1)
    input("Hold down Keypad ! Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(1)
    if cmd_success and btn_held:
        log.info("PASS - Button ! Held")
        test_pass &= True
    else:
        log.info("FAIL - Button ! Held")
        test_pass &= False

    time.sleep(1)
    input("Release Keypad ! Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(1)
    if cmd_success and not btn_held:
        log.info("PASS - Button ! Released")
        test_pass &= True
    else:
        log.info("FAIL - Button ! Released")
        test_pass &= False

    time.sleep(1)
    input("Hold down Keypad X Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(2)
    if cmd_success and btn_held:
        log.info("PASS - Button X Held")
        test_pass &= True
    else:
        log.info("FAIL - Button X Held")
        test_pass &= False

    time.sleep(1)
    input("Release Keypad X Button then press <Enter>")
    cmd_success, btn_held = czm.get_keypad_button_held(2)
    if cmd_success and not btn_held:
        log.info("PASS - Button X Released")
        test_pass &= True
    else:
        log.info("FAIL - Button X Released")
        test_pass &= False

    czm.set_all_led_green(True)
    while True:
        answer = input("Are the 10x Keypad LEDs all lit GREEN? (y/n <Enter>): ")
        if answer.lower() not in ("y", "n"):
            log.critical("*** Invalid response! ***")
        else:
            break

    if answer.lower() == "y":
        log.info("PASS - Keypad LED")
        test_pass &= True
    else:
        log.info("FAIL - Keypad LED")
        test_pass &= False
    czm.set_all_led_green(False)

    czm.set_buzzer_enable(True)
    time.sleep(1)
    czm.set_buzzer_enable(False)

    while True:
        answer = input("Did the case buzzer sound? (y/n <Enter>): ")
        if answer.lower() not in ("y", "n"):
            log.critical("*** Invalid response! ***")
        else:
            break

    if answer.lower() == "y":
        log.info("PASS - Case Buzzer")
        test_pass &= True
    else:
        log.info("FAIL - Case Buzzer")
        test_pass &= False

    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="KT-000-0140-00 CSM Keypad Buzzer Production Test")
    parser.add_argument("-m", "--csm_micro_port", required=True, dest="csm_micro_port", action="store",
                        help="Name of CSM Zeroise Microcontroller COM port")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    run_test(args.csm_micro_port)
