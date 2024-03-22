#!/usr/bin/env python3
"""
Utility module for performing a visual check that the keypad LEDs are
functioning correctly.
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
import logging
import time

# Third-party imports -----------------------------------------------

# Our own imports ---------------------------------------------------
from zm_serial_msg_intf import ZmSerialMsgInterface

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

    with ZmSerialMsgInterface("/dev/ttyZerMicro") as zsmi:
        # Clear the terminal and move the cursor home
        print("\x1b[2J", end="\n\x1b[H")
        brightness = 255
        while True:
            zsmi.send_set_led_brightness(brightness, wait_for_ack=WAIT_FOR_ACKS)
            print("\x1b[2J\x1b[HBrightness {}".format(brightness))
            brightness -= 32
            if brightness <= 0:
                brightness = 255

            print("LEDs Green..")
            for i in range(0, 20):
                zsmi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, 20, 2):
                zsmi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                zsmi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)

            print("LEDs Red..")
            for i in range(0, 20):
                zsmi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(1, 20, 2):
                zsmi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                zsmi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)

            print("LEDs Yellow..")
            for i in range(0, 20):
                zsmi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, 20):
                zsmi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

            for i in range(0, DWELL_TIME_S):
                zsmi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
                time.sleep(1.0)
