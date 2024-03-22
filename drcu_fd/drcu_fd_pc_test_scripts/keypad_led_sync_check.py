#!/usr/bin/env python3
"""
Utility module for performing a visual check that the keypad LEDs are sync'd
to the 1PPS input.
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
    LED_PATTERN = "BLINK_SYNC_START"
    DWELL_TIME_S = 30
    LED_BRIGHTNESS = 255

    parser = argparse.ArgumentParser(description="Keypad button monitor")
    parser.add_argument("-u", "--uart", required=True, help="Serial UART")
    args = parser.parse_args()

    with DrcuSerialMsgInterface(args.uart) as drcu_smi:
        # Clear the terminal and move the cursor home
        drcu_smi.send_set_led_brightness(LED_BRIGHTNESS, wait_for_ack=WAIT_FOR_ACKS)

        print("LEDs Green Blink At Start of 6-second sync..")
        for i in range(0, 20):
            drcu_smi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=WAIT_FOR_ACKS)

        for i in range(0, 20, 2):
            drcu_smi.send_set_led_pattern(led=i, pattern=LED_PATTERN, wait_for_ack=WAIT_FOR_ACKS)

        for i in range(0, DWELL_TIME_S):
            drcu_smi.send_ping(wait_for_ack=WAIT_FOR_ACKS)
            time.sleep(1.0)

        print("Script exiting...")
