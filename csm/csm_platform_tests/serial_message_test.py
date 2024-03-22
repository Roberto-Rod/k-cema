#!/usr/bin/env python3
"""
Blah...
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
import sys
import time
import argparse
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from zm_serial_msg_intf import ZmSerialMsgInterface, ZmMsgId, ZmMsgPayloadLen, ButtonId

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
def main(serial_port):
    """
    Send and receive each type of serial command
    :param serial_port: COM port to use :type: string
    :return: N/A
    """
    with ZmSerialMsgInterface(serial_port) as zmsi:
        if zmsi.send_ping():
            log.info("Ping command worked")
        else:
            log.info("Ping command failed!")

        success, msg = zmsi.get_command(ZmMsgId.GET_SOFTWARE_VERSION_NUMBER,
                                        ZmMsgPayloadLen.GET_SOFTWARE_VERSION_NUMBER)
        if success:
            payload_version, sw_major, sw_minor, sw_patch, sw_build = \
                zmsi.unpack_get_software_version_number_response(msg)
            log.info("Software Version: {}.{}.{}:{}".format(sw_major, sw_minor, sw_build, sw_patch))
        else:
            log.info("Get Software Version Command Failed!")

        if zmsi.send_set_buzzer_pattern("ON"):
            log.info("Set Buzzer 'ON'")
        else:
            log.info("Failed to Set Buzzer 'ON'!")

        time.sleep(1.0)

        if zmsi.send_set_buzzer_pattern("OFF"):
            log.info("Set Buzzer 'OFF'")
        else:
            log.info("Failed to Set Buzzer 'OFF'!")

        log.info("Blinking all LEDs green at 1 Hz for 10-seconds...")
        for i in range(0, 20):
            zmsi.send_set_led_pattern(led=i, pattern="OFF", wait_for_ack=False)
        for i in range(0, 20, 2):
            zmsi.send_set_led_pattern(led=i, pattern="BLINK_ONE_HZ", wait_for_ack=False)
        for i in range(0, 10):
            time.sleep(1)
            zmsi.send_ping(wait_for_ack=False)

        button_sequence = [
            # (btn_name, btn_value)
            ("Jamming", ButtonId.JAM.value),
            ("!", ButtonId.EXCLAMATION.value),
            ("X", ButtonId.X.value)
        ]

        for btn_name, btn_value in button_sequence:
            log.info("Press the Keypad '{}' Button (within 20-seconds)...".format(btn_name))
            test_timeout = time.perf_counter() + 20.0
            ping_timeout = time.time() + 1.0

            while True:
                button_pressed = False
                rx_msg = zmsi.smh.get_from_rx_queue()

                # If a button status message was received, check if it's the one we're looking for
                if rx_msg is not None:
                    log.debug("Rx Msg: {}".format(rx_msg))
                    button_status_msg, button_status = zmsi.unpack_button_status_message(rx_msg)

                    for button in button_status:
                        if button.get("button_id") == btn_value and button.get("button_state"):
                            button_pressed = True

                if button_pressed or time.perf_counter() > test_timeout:
                    log.info("'{}' button press{}found".format(btn_name, " " if button_pressed else " NOT "))
                    break

                if time.time() > ping_timeout:
                    zmsi.send_ping(wait_for_ack=False)
                    ping_timeout = time.time() + 1.0


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Send K-CEMA RCU Messages to a serial port.")
parser.add_argument('-p', '-p1', '--port', default='COM61', help="the serial port to use for unit tests. Default COM61")

if __name__ == '__main__':
    """
    Call runtime procedure and execute test
    """
    fmt = "%(asctime)s: %(message)s"
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    parser = argparse.ArgumentParser(description="K-CEMA Serial Message Test Utility")
    parser.add_argument('-p', '--port', dest="port", default="/dev/ttyPS8",
                        help="Serial port to use for tests. Default /dev/ttyPS8")
    args = parser.parse_args()
    main(args.port)

