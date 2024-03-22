#!/usr/bin/env python3
"""
Utility module for testing the Keypad on a Display RCU.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
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
from drcu_serial_msg_intf import DrcuSerialMsgInterface, DrcuButtonId

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
def main(kw_args):
    """
    Process command line options
    :param kw_args: command line parameters
    :return: N/A
    """
    with DrcuSerialMsgInterface(kw_args.uart) as drcu_smi:
        if vars(kw_args).get("buzzer_state", None) is not None:
            if drcu_smi.send_set_buzzer_pattern("ON" if int(kw_args.buzzer_state) else "OFF", wait_for_ack=False):
                log.info("Buzzer set to: {}".format("ON" if int(kw_args.buzzer_state) else "OFF"))
            else:
                log.info("Buzzer NOT set!")
            # Make sure the message has time to be sent, pySerial is really slow!
            time.sleep(1.0)

        if vars(kw_args).get("led_state", None) is not None:
            if kw_args.led_state == "ON":
                # Turn all the LEDs on Green
                for i in range(0, 20):
                    drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                for i in range(0, 20, 2):
                    drcu_smi.send_set_led_pattern(led=i, pattern="ON", wait_for_ack=False)
                for i in range(0, 6):
                    drcu_smi.send_ping(wait_for_ack=False)
                    time.sleep(1)
                log.info("LED state set to ON")
            elif kw_args.led_state == "BLINK":
                # Turn all the LEDs on Green
                for i in range(0, 20):
                    drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                for i in range(0, 20, 2):
                    drcu_smi.send_set_led_pattern(led=i, pattern="BLINK_ONE_HZ", wait_for_ack=False)
                for i in range(0, 6):
                    drcu_smi.send_ping(wait_for_ack=False)
                    time.sleep(1)
                log.info("LED state set to BLINK")
            elif kw_args.led_state == "OFF":
                # Turn all the LEDs off
                for i in range(0, 20):
                    drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
                for i in range(0, 6):
                    drcu_smi.send_ping(wait_for_ack=False)
                    time.sleep(1)
                log.info("LED state set to OFF")
            else:
                log.info("Invalid LED state!")

        if vars(kw_args).get("button", None) is not None:
            if kw_args.button in ["JAM", "EXCLAMATION", "X"]:
                log.info("Press the Keypad '{}' Button followed by any other button "
                         "except the Power button (within 20-seconds)...".format(kw_args.button))
                test_timeout = time.time() + 20.0
                button_pressed = False
                button_released = False
                while True:
                    rx_msg = drcu_smi.smh.get_from_rx_queue()
                    if rx_msg:
                        log.debug("Rx Msg: {}".format(rx_msg))
                        button_status_msg, button_status = drcu_smi.unpack_button_status_message(rx_msg)

                        # If a button status message was received check for pressed and released states
                        if button_status_msg:
                            for button in button_status:
                                if button.get("button_id") == getattr(DrcuButtonId, kw_args.button).value and \
                                        button.get("button_state"):
                                    log.debug("{} button pressed".format(kw_args.button))
                                    button_pressed = True

                                if button.get("button_id") == getattr(DrcuButtonId, kw_args.button).value and not\
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
    parser.add_argument("-b", "--buzzer_state", help="Buzzer state [0|1]")
    parser.add_argument("-l", "--led_state", help="Set state of all Green LEDs ['ON'|'OFF'|'BLINK']")
    parser.add_argument("-s", "--button", help="Check for button press, waits 20s ['JAM', 'EXCLAMATION', 'X']")
    parser.add_argument("-u", "--uart", help="Serial UART")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to DEBUG to see test pass/fail results and DEBUG
    # to see detailed information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args)
