#!/usr/bin/env python3
"""
Utility module for driving the keypad LEDs with a given colour and state.
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
import time

# Third-party imports ---------------------------------------------------------

# Our own imports -------------------------------------------------------------
from zm_serial_msg_intf import ZmSerialMsgInterface

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
DEFAULT_SERIAL_INTERFACE = "/dev/ttyZerMicro"
DEFAULT_BLINK_PATTERN = "BLINK_HALF_HZ"
ALL_LED_ID = "A"
RED_COLOUR_ID = "R"
GREEN_COLOUR_ID = "G"
YELLOW_COLOUR_ID = "Y"
ALL_LED_OFF_PATTERN = ['OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF',
                       'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF']
ALL_LED_ON_PATTERN = ['ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON',
                      'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON', 'ON']
ALL_LED_BLINK_PATTERN = [DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN,
                         DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN,
                         DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN,
                         DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN,
                         DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN, DEFAULT_BLINK_PATTERN]
# Makes sure the LED order matches the panel.
LED_VISUAL_ORDER = [0, 1, 2, 3, 9, 4, 5, 6, 7, 8]
# LEDs are grouped into RED/GREEN pairs and the YELLOW is obtained by lighting
# up both the RED and GREEN.
MIN_LED = 0
MAX_LED = len(LED_VISUAL_ORDER)
# RED
RED_LED_START = 1
RED_LED_STEP = 2
# GREEN
GREEN_LED_START = 0
GREEN_LED_STEP = 2
# BRIGHTNESS
MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 255
DEFAULT_BRIGHTNESS = int(MAX_BRIGHTNESS / 2)


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def set_brightness(zsmi, brightness):
    if brightness < MIN_BRIGHTNESS:
        brightness = MIN_BRIGHTNESS
    elif brightness > MAX_BRIGHTNESS:
        brightness = MAX_BRIGHTNESS
    zsmi.send_set_led_brightness(brightness)


def set_red_led_state(zsmi, led, state, wait=True):
    led = RED_LED_START + (led * RED_LED_STEP)
    if state == "BLINK":
        state = DEFAULT_BLINK_PATTERN
    zsmi.send_set_led_pattern(led, state, wait_for_ack=wait)


def set_green_led_state(zsmi, led, state, wait=True):
    led = GREEN_LED_START + (led * GREEN_LED_STEP)
    if state == "BLINK":
        state = DEFAULT_BLINK_PATTERN
    zsmi.send_set_led_pattern(led, state, wait_for_ack=wait)


def set_yellow_led_state(zsmi, led, state):
    set_red_led_state(zsmi, led, state, False)
    set_green_led_state(zsmi, led, state, False)
    time.sleep(0.1)


def set_all_led_off(zsmi):
    zsmi.send_set_all_leds(ALL_LED_OFF_PATTERN)


def set_all_led_on(zsmi, colour):
    if colour == YELLOW_COLOUR_ID:
        zsmi.send_set_all_leds(ALL_LED_ON_PATTERN)
    elif colour == RED_COLOUR_ID:
        set_all_led_off(zsmi)
        for i in range(MIN_LED, MAX_LED):
            set_red_led_state(zsmi, i, "ON", False)
        time.sleep(0.1)
    elif colour == GREEN_COLOUR_ID:
        set_all_led_off(zsmi)
        for i in range(MIN_LED, MAX_LED):
            set_green_led_state(zsmi, i, "ON", False)
        time.sleep(0.1)


def set_all_led_blink(zsmi, colour):
    if colour == YELLOW_COLOUR_ID:
        zsmi.send_set_all_leds(ALL_LED_BLINK_PATTERN)
    elif colour == RED_COLOUR_ID:
        set_all_led_off(zsmi)
        for i in range(MIN_LED, MAX_LED):
            set_red_led_state(zsmi, i, "BLINK", False)
        time.sleep(0.1)
    elif colour == GREEN_COLOUR_ID:
        set_all_led_off(zsmi)
        for i in range(MIN_LED, MAX_LED):
            set_green_led_state(zsmi, i, "BLINK", False)
        time.sleep(0.1)


def set_all_led_state(zsmi, colour, state):
    if state == "ON":
        set_all_led_on(zsmi, colour)
    elif state == "OFF":
        set_all_led_off(zsmi)
    elif state == "BLINK":
        set_all_led_blink(zsmi, colour)


def set_led_state(zsmi, led, colour, state):
    led = LED_VISUAL_ORDER[int(led) % MAX_LED]
    if colour == RED_COLOUR_ID:
        set_red_led_state(zsmi, led, state)
        set_green_led_state(zsmi, led, "OFF")
    elif colour == GREEN_COLOUR_ID:
        set_green_led_state(zsmi, led, state)
        set_red_led_state(zsmi, led, "OFF")
    elif colour == YELLOW_COLOUR_ID:
        set_yellow_led_state(zsmi, led, state)


def main(args):
    """
    Process command line options
    :param args: command line parameters
    :return: N/A
    """
    serial = DEFAULT_SERIAL_INTERFACE
    brightness = DEFAULT_BRIGHTNESS
    if vars(args).get("serial", None) is not None:
        serial = args.serial
    if vars(args).get("brightness", None) is not None:
        brightness = int(args.brightness)
    with ZmSerialMsgInterface(serial) as zsmi:
        set_brightness(zsmi, brightness)
        if args.led == ALL_LED_ID:
            set_all_led_state(zsmi, args.colour, args.state)
        else:
            set_led_state(zsmi, args.led, args.colour, args.state)


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LED Driver Utility")

    parser.add_argument("-b", "--brightness", required=False, dest="brightness", action="store",
                        help="LED brightness [" + str(MIN_BRIGHTNESS) + ".." + str(MAX_BRIGHTNESS) + "], (Default: " +
                             str(DEFAULT_BRIGHTNESS) + ")")
    parser.add_argument("-c", "--colour", required=True, dest="colour", action="store",
                        help="LED colour ['R'|'G'|'Y']")
    parser.add_argument("-l", "--led", required=True, dest="led", action="store",
                        help="LED number ['A'|" + str(MIN_LED) + ".." + str(MAX_LED - 1) + "]")
    parser.add_argument("-s", "--state", required=True, dest="state", action="store",
                        help="LED state ['ON'|'OFF'|'BLINK']")
    parser.add_argument("-u", "--uart", required=False, dest="serial", action="store",
                        help="Serial UART, (Default: " + DEFAULT_SERIAL_INTERFACE + ")")
    arguments = parser.parse_args()

    main(arguments)
