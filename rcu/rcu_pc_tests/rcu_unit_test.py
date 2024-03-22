#!/usr/bin/env python3
"""
Test script for the KT-950-0362-00 K-CEMA RCU unit
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2020, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See the __main__ runtime procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
from datetime import datetime
import logging
import time

# Third-party imports -----------------------------------------------
from serial import Serial, SerialException

# Our own imports ---------------------------------------------------
from serial_message_handler import MessageHandler, ButtonId

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SERIAL_TIMEOUT = 20.0
BAUD_RATE = 115200

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
def test_led_1pps(serial_message_handler):
    """
    Set all 10x LEDs to be ON, colour green at the start of 1PPS driven 6-second display synchronisation frame,
    ask the tester to confirm that the display is synchronised with the test interface baord
    :param serial_message_handler: to use for talking to RCU :type: MessageHandler
    :return: True if test, passes, else False :type: boolean
    """
    print("All 10x Keypad LEDs will now BLINK ON GREEN->RED->YELLOW at 6-seconds interval synchronised to ")
    input("KT-000-0151-00 LED LD3, following this the Power LED will FLASH RED at 2 Hz, press <ENTER> to continue")

    # Set LEDs to full brightness
    serial_message_handler.send_set_led_brightness(255)

    for i in range(0, 20):
        serial_message_handler.send_set_led_pattern(led=i, pattern="OFF")
    for i in range(0, 20, 2):
        serial_message_handler.send_set_led_pattern(led=i, pattern="BLINK_SYNC_START")

    for i in range(0, 6):
        serial_message_handler.send_ping()
        time.sleep(1)

    for i in range(0, 20):
        serial_message_handler.send_set_led_pattern(led=i, pattern="OFF")
    for i in range(1, 20, 2):
        serial_message_handler.send_set_led_pattern(led=i, pattern="BLINK_SYNC_START")

    for i in range(0, 6):
        serial_message_handler.send_ping()
        time.sleep(1)

    for i in range(0, 20):
        serial_message_handler.send_set_led_pattern(led=i, pattern="OFF")
    for i in range(0, 20):
        serial_message_handler.send_set_led_pattern(led=i, pattern="BLINK_SYNC_START")

    for i in range(0, 6):
        serial_message_handler.send_ping()
        time.sleep(1)

    log_str = " - LED and 1PPS Test"
    if input("Did all 10x Keypad LEDs flash once every 6-seconds synchronised to KT-000-0151-00 LED LD3? "
             "(y/n <ENTER>): ") == "Y" or "y":
        log.info("PASS" + log_str)
        return True
    else:
        log.info("FAIL" + log_str)
        return False


def test_buzzer(serial_message_handler):
    """
    Turn the buzzer on for 1-second, turn it off and prompt the tester to confirm it was audible
    :param serial_message_handler: to use for talking to RCU :type: MessageHandler
    :return: True if test passes, else False :type: boolean
    """
    serial_message_handler.send_set_buzzer_pattern(pattern="ON")
    time.sleep(1)
    serial_message_handler.send_set_buzzer_pattern(pattern="OFF")

    log_str = "- Case Buzzer Test"
    if input("Did the case buzzer sound? (y/n <ENTER>): ") == ("y" or "Y"):
        log.info("PASS" + log_str)
        return True
    else:
        log.info("FAIL" + log_str)
        return False


def test_push_button_inputs(serial_message_handler):
    """
    Ask the tester to press each of the keypad buttons in turn and use the serial interface to detect that the
    correct button has been pressed
    :param serial_message_handler: to use for talking to RCU :type: MessageHandler
    :return: True if test passes, else False :type: boolean
    """
    test_pass = True

    log.info("Press the Keypad 'Jamming' Button (within 20-seconds)...")
    test_timeout = time.time() + 20.0
    serial_message_handler.clear_rx_queue()
    while True:
        time.sleep(0.001)
        button_pressed = False
        rx_msg = serial_message_handler.get_from_rx_queue()
        if rx_msg:
            log.debug("Rx Msg: {}".format(rx_msg))
            button_status_msg, button_status = serial_message_handler.unpack_button_status_message(rx_msg)

            # If a button status message was received, check if the 'Jamming' button is held
            if button_status_msg:
                for button in button_status:
                    if button.get("button_id") == ButtonId.JAM.value and button.get("button_state"):
                        button_pressed = True

        if button_pressed or time.time() > test_timeout:
            break

    log_str = " - 'Jamming' Keypad Button Test"
    if button_pressed:
        log.info("PASS" + log_str)
        test_pass &= True
    else:
        log.info("FAIL" + log_str)
        test_pass &= False

    log.info("Press the Keypad '!' Button (within 20-seconds)...")
    test_timeout = time.time() + 20.0
    serial_message_handler.clear_rx_queue()
    while True:
        time.sleep(0.001)
        button_pressed = False
        rx_msg = serial_message_handler.get_from_rx_queue()
        if rx_msg:
            log.debug("Rx Msg: {}".format(rx_msg))
            button_status_msg, button_status = serial_message_handler.unpack_button_status_message(rx_msg)

            # If a button status message was received, check if the 'Jamming' button is held
            if button_status_msg:
                for button in button_status:
                    if button.get("button_id") == ButtonId.EXCLAMATION.value and button.get("button_state"):
                        button_pressed = True

        if button_pressed or time.time() > test_timeout:
            break

    log_str = " - '!' Keypad Button Test"
    if button_pressed:
        log.info("PASS" + log_str)
        test_pass &= True
    else:
        log.info("FAIL" + log_str)
        test_pass &= False

    log.info("Press the Keypad 'X' Button (within 20-seconds)...")
    test_timeout = time.time() + 20.0
    serial_message_handler.clear_rx_queue()
    while True:
        time.sleep(0.001)
        button_pressed = False
        rx_msg = serial_message_handler.get_from_rx_queue()
        if rx_msg:
            log.debug("Rx Msg: {}".format(rx_msg))
            button_status_msg, button_status = serial_message_handler.unpack_button_status_message(rx_msg)

            # If a button status message was received, check if the 'Jamming' button is held
            if button_status_msg:
                for button in button_status:
                    if button.get("button_id") == ButtonId.X.value and button.get("button_state"):
                        button_pressed = True

        if button_pressed or time.time() > test_timeout:
            break

    log_str = " - 'X' Keypad Button Test"
    if button_pressed:
        log.info("PASS" + log_str)
        test_pass &= True
    else:
        log.info("FAIL" + log_str)
        test_pass &= False

    return test_pass


def test_push_button_outputs(test_jig_serial_port):
    """
    Test the Power Button and Power Enable discrete outputs
    :param test_jig_serial_port: name of test jig serial port :type: string
    :return: True if tests all pass, else False
    """
    try:
        sp = Serial(test_jig_serial_port, BAUD_RATE, timeout=SERIAL_TIMEOUT, xonxoff=False, rtscts=False, dsrdtr=False)
        log.debug("Opened COM port {}".format(test_jig_serial_port))

        sp.flushInput()
        print("Press the Keypad 'Power' Button (within 20-seconds)...")
        test_pass = (b"0 - PWR_BTN" and b"1 - PWR_EN_ZERO") in sp.read_until(b"PWR_EN_ZERO")
        test_pass = (b"1 - PWR_BTN" and b"1 - PWR_EN_ZERO") in sp.read_until(b"PWR_EN_ZERO") and test_pass

        log_str = " - 'Power' Button Output Signal Test"
        if test_pass:
            log.info("PASS" + log_str)
        else:
            log.info("FAIL" + log_str)

        time.sleep(1)
        sp.flushInput()
        print("Press the Keypad 'X' Button (within 20-seconds)...")
        test_pass = (b"1 - PWR_BTN" and b"0 - PWR_EN_ZERO") in sp.read_until(b"PWR_EN_ZERO") and test_pass
        test_pass = (b"1 - PWR_BTN" and b"1 - PWR_EN_ZERO") in sp.read_until(b"PWR_EN_ZERO") and test_pass

        log_str = " - 'X' Button Output Signal Test"
        if test_pass:
            log.info("PASS" + log_str)
        else:
            log.info("FAIL" + log_str)

        sp.close()

    except ValueError or SerialException as ex:
        log.debug("Failed to open COM port {}: {}".format(test_jig_serial_port, ex))
        raise SystemExit(-1)

    return test_pass


def run_test(rcu_serial_port, test_jig_serial_port):
    """
    Execute the test and return the cumulative result of all tests
    :param rcu_serial_port: name of RCU serial port :type: string
    :param test_jig_serial_port: name of test jig serial port :type: string
    :return: True if tests all pass, else False
    """
    test_pass = False
    input("Confirm the required COM ports are disconnected <ENTER>")
    log.debug("Starting Serial Message Handler...")
    smh = MessageHandler()

    if smh.start(rcu_serial_port, 115200):
        test_pass = test_led_1pps(smh)
        test_pass = test_buzzer(smh) and test_pass
        test_pass = test_push_button_inputs(smh) and test_pass
        test_pass = test_push_button_outputs(test_jig_serial_port) and test_pass

        log.debug("Stopping Serial Message Handler...")
        smh.stop()

    else:
        log.critical("*** Error Starting Serial Handler! ***")

    return test_pass


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    parser = argparse.ArgumentParser(description="K-CEMA Serial Message Test Utility")
    parser.add_argument("-p", "--rcu_serial_port", required=True, dest="rcu_serial_port", action="store",
                        help="Name of RCU serial COM port")
    parser.add_argument("-t", "--test_jig_serial_port", required=True, dest="test_jig_serial_port", action="store",
                        help="Name of Test Jig serial COM port")
    parser.add_argument("-s", "--serial_no", required=True, dest="serial_no", action="store",
                        help="Serial number of board under test, max length 15 characters")
    parser.add_argument("-r", "--rev_no", required=True, dest="rev_no", action="store",
                        help="Revision number of board under test, max length 15 characters")
    parser.add_argument("-b", "--batch_no", required=True, dest="batch_no", action="store",
                        help="Batch number of board under test, max length 15 characters")
    args = parser.parse_args()

    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    fmt = "%(asctime)s: %(message)s"
    log_file_name = "KT-950-0362-00_{}_{}_{}.txt".format(args.serial_no, args.batch_no,
                                                         datetime.now().strftime("%Y%m%d%H%M%S"))
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

    log.info("KT-950-0362-00 RCU Unit Production Test Script")
    log.info("Serial No:\t{}".format(args.serial_no))
    log.info("Revision No:\t{}".format(args.rev_no))
    log.info("Batch No:\t{}".format(args.batch_no))

    log_result_str = " - Overall test result"
    if run_test(args.rcu_serial_port, args.test_jig_serial_port):
        log.info("PASS" + log_result_str)
    else:
        log.info("FAIL" + log_result_str)
