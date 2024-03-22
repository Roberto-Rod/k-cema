#!/usr/bin/env python3
"""
Utility module for testing the Keypad on a Fill Device
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
See argparse definition in the Runtime Procedure

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
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
from fd_serial_msg_intf import FdSerialMsgInterface, FdButtonId

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
LED_ON_TIME_S = 1

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
def main(kw_args):
    """
    Process command line options
    :param kw_args: command line parameters
    :return: N/A
    """
    with FdSerialMsgInterface(kw_args.uart) as fd_smi:

        if vars(kw_args).get("led_state", None) is not None:
            led_colour = vars(kw_args).get("led_colour", "GREEN")
            if led_colour not in ["GREEN", "RED", "YELLOW"]:
                log.info("Colour must be 'GREEN', 'RED', or 'YELLOW', defaulting to 'GREEN'")
                led_colour = "GREEN"

            if kw_args.led_state == "ON":
                # Turn all the LEDs on specified colour
                if led_colour == "GREEN":
                    for i in range(0, 6):
                        fd_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                    for i in range(0, 6, 2):
                        fd_smi.send_set_led_pattern(led=i, pattern="ON", wait_for_ack=False)
                    for i in range(0, LED_ON_TIME_S):
                        fd_smi.send_ping(wait_for_ack=False)
                        time.sleep(1)
                elif led_colour == "RED":
                    for i in range(0, 6):
                        fd_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                    for i in range(1, 6, 2):
                        fd_smi.send_set_led_pattern(led=i, pattern="ON", wait_for_ack=False)
                    for i in range(0, LED_ON_TIME_S):
                        fd_smi.send_ping(wait_for_ack=False)
                        time.sleep(1)
                else:   # Must be "YELLOW"
                    for i in range(0, 6):
                        fd_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                    for i in range(0, 6, 1):
                        fd_smi.send_set_led_pattern(led=i, pattern="ON", wait_for_ack=False)
                    for i in range(0, LED_ON_TIME_S):
                        fd_smi.send_ping(wait_for_ack=False)
                        time.sleep(1)
                log.info("LED state set to ON - {}".format(led_colour))
            elif kw_args.led_state == "BLINK":
                # Turn all the LEDs on Green
                for i in range(0, 20):
                    fd_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                for i in range(0, 20, 2):
                    fd_smi.send_set_led_pattern(led=i, pattern="BLINK_ONE_HZ", wait_for_ack=False)
                for i in range(0, 6):
                    fd_smi.send_ping(wait_for_ack=False)
                    time.sleep(1)
                log.info("LED state set to BLINK")
            elif kw_args.led_state == "OFF":
                # Turn all the LEDs off
                for i in range(0, 20):
                    fd_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                for i in range(0, 6):
                    fd_smi.send_ping(wait_for_ack=False)
                    time.sleep(1)
                log.info("LED state set to OFF")
            else:
                log.info("Invalid LED state!")

        if vars(kw_args).get("button", None) is not None:
            if kw_args.button in ["UP_ARROW", "X", "DOWN_ARROW"]:
                log.info("Press the Keypad '{}' Button followed by any other button "
                         "except the Power button (within 20-seconds)...".format(kw_args.button))
                test_timeout = time.time() + 10.0
                ping_timeout = 0.0
                button_pressed = False
                button_released = False
                while True:
                    if time.time() > ping_timeout:
                        fd_smi.send_ping(wait_for_ack=False)
                        ping_timeout = time.time() + 1.0

                    rx_msg = fd_smi.smh.get_from_rx_queue()
                    if rx_msg:
                        log.debug("Rx Msg: {}".format(rx_msg))
                        button_status_msg, button_status = fd_smi.unpack_button_status_message(rx_msg)

                        # If a button status message was received check for pressed and released states
                        if button_status_msg:
                            for button in button_status:
                                if button.get("button_id") == getattr(FdButtonId, kw_args.button).value and \
                                        button.get("button_state"):
                                    log.debug("{} button pressed".format(kw_args.button))
                                    button_pressed = True

                                if button.get("button_id") == getattr(FdButtonId, kw_args.button).value and not\
                                        button.get("button_state"):
                                    log.debug("{} button released".format(kw_args.button))
                                    button_released = True

                    if (button_pressed and button_released) or (time.time() > test_timeout):
                        break

                log.info("{} - '{}' Keypad Button Pressed".format(
                    "PASS" if button_pressed and button_released else "FAIL", kw_args.button))

            else:
                log.info("Invalid button!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Process arguments, setup logging and call runtime procedure
    """
    parser = argparse.ArgumentParser(description="Keypad test utility")
    parser.add_argument("-l", "--led_state", help="Set state of all LEDs ['ON'|'OFF'|'BLINK'], "
                                                  "use -c / --led_colour to select colour, default GREEN")
    parser.add_argument("-c", "--led_colour", default="GREEN", help="Set LED colour ['GREEN', 'RED', 'YELLOW']")
    parser.add_argument("-s", "--button", help="Check for button press, waits 10s ['UP_ARROW', 'X', 'DOWN_ARROW']")
    parser.add_argument("-u", "--uart", help="Serial UART")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args)
