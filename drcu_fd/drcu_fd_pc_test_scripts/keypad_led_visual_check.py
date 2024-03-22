#!/usr/bin/env python3
"""
Utility module for performing a visual check that the keypad LEDs are
functioning correctly.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
-u --uart Serial UART
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
from drcu_serial_msg_intf import DrcuSerialMsgInterface

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
    WAIT_FOR_ACKS = False
    LED_PATTERN = "BLINK_HALF_HZ"
    DWELL_TIME_S = 4

    parser = argparse.ArgumentParser(description="Keypad button monitor")
    parser.add_argument("-u", "--uart", required=True, help="Serial UART")
    args = parser.parse_args()

    with DrcuSerialMsgInterface(args.uart) as drcu_smi:
        # Clear the terminal and move the cursor home
        print("\x1b[2J", end="\n\x1b[H")
        brightness = 255
        while True:
            drcu_smi.send_set_led_brightness(brightness, wait_for_ack=WAIT_FOR_ACKS)
            print("\x1b[2J\x1b[HBrightness {}".format(brightness))
            brightness -= 32
            if brightness <= 0:
                brightness = 255

            print("LEDs Green..")
            for i in range(0, 20):
                drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, 20, 2):
                drcu_smi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                drcu_smi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)

            print("LEDs Red..")
            for i in range(0, 20):
                drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(1, 20, 2):
                drcu_smi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                drcu_smi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)

            print("LEDs Yellow..")
            for i in range(0, 20):
                drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, 20):
                drcu_smi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                drcu_smi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)
