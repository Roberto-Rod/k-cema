#!/usr/bin/env python3
"""
Utility module for driving the front panel LEDs with a given colour and state.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS -----------------------------------------------------------------------
None

ARGUMENTS ---------------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports --------------------------------------------------------------
import argparse
import os

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
# The values in the dictionary represent the 48 bits sequence to program the
# AXI LED Controller however we will use 64 bits whereby the top 16 bits will
# be ignored by the hardware and more convenient when using 'devmem' tool.
# ref:
#    http://confluence.kirintec.local/display/KEW/AXI+LED+Controller
LED_PATTERNS = { "OFF":               0x0000000000000000,
                 "BLINK_QUARTER_HZ":  0x0000CCCCCCCCCCCC,
                 "BLINK_HALF_HZ":     0x0000F0F0F0F0F0F0,
                 "BLINK_ONE_HZ":      0x0000FF00FF00FF00,
                 "BLINK_ONE_HALF_HZ": 0x0000FFFFFF000000,
                 "BLINK_SYNC_START":  0x0000FF0000000000,
                 "ON":                0x0000FFFFFFFFFFFF }
ALL_LED_ID = "A"
# EMA's LED range
MIN_LED = 0
MAX_LED = 3
# BRIGHTNESS
SCALE_BRIGHTNESS = 257
MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 255
DEFAULT_BRIGHTNESS = int(MAX_BRIGHTNESS / 2)
BRIGHTNESS_MULTIPLIER = 257
# MEMORY ADDRESS
BASE_LED_ADDRESS = 0x40030000
LED_ADDRESS_SIZE = 64
BRIGHTNESS_ADDRESS = BASE_LED_ADDRESS + 0x18
BRIGHTNESS_ADDRESS_SIZE = 32

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def write_dev_mem(address, size, data):
    cmd = '/sbin/devmem ' + hex(address) + ' ' + str(size) + ' ' + hex(data)
    os.popen(cmd).read()

def get_pattern(state):
    if state not in LED_PATTERNS.keys():
        return LED_PATTERNS.get("OFF")
    else:
        return LED_PATTERNS.get(state)

def set_brightness(brightness):
    if brightness < MIN_BRIGHTNESS:
        brightness = MIN_BRIGHTNESS
    elif brightness > MAX_BRIGHTNESS:
        brightness = MAX_BRIGHTNESS
    write_dev_mem(BRIGHTNESS_ADDRESS,
                  BRIGHTNESS_ADDRESS_SIZE,
                  brightness * SCALE_BRIGHTNESS)

def set_led_pattern(led, pattern):
    write_dev_mem(BASE_LED_ADDRESS + (led * int(LED_ADDRESS_SIZE / 8)),
                  LED_ADDRESS_SIZE,
                  pattern)

def set_all_led_state(state):
    for led in range(MIN_LED, MAX_LED):
        set_led_pattern(led, get_pattern(state))

def set_led_state(led, state):
    set_led_pattern(led, get_pattern(state))

def main(args):
    """
    Process command line options
    :param args: command line parameters
    :return: N/A
    """
    brightness = DEFAULT_BRIGHTNESS
    if vars(args).get("brightness", None) is not None:
        brightness = int(args.brightness)
    set_brightness(brightness)
    if args.led == ALL_LED_ID:
        set_all_led_state(args.state)
    else:
        set_led_state(int(args.led), args.state)

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LED Driver Utility")

    parser.add_argument("-b", "--brightness", required=False, dest="brightness", action="store",
                        help="LED brightness [" + str(MIN_BRIGHTNESS) + ".." + str(MAX_BRIGHTNESS) + "], (Default: " + str(DEFAULT_BRIGHTNESS) + ")")
    parser.add_argument("-l", "--led", required=True, dest="led", action="store",
                        help="LED number ['A'|" + str(MIN_LED) + ".." + str(MAX_LED - 1) +"]")
    parser.add_argument("-s", "--state", required=True, dest="state", action="store",
                        help="LED state ['ON'|'OFF'|'BLINK_QUARTER_HZ'|'BLINK_HALF_HZ'|'BLINK_ONE_HZ'|'BLINK_ONE_HALF_HZ'|'BLINK_SYNC_START']")
    args = parser.parse_args()

    main(args)
