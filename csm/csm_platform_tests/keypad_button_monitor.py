#!/usr/bin/env python3
"""
Utility module for monitoring keypad button status.
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
from zm_serial_msg_intf import ZmSerialMsgInterface, ButtonId, ButtonState

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
    with ZmSerialMsgInterface("/dev/ttyZerMicro") as zsmi:
        # Clear the terminal and move the cursor home
        print("\x1b[2J", end="\n\x1b[HKeypad Button Monitor:\n")
        ping_timeout = time.time() + 1.0
        while True:
            time.sleep(0.05)
            rx_msg = zsmi.smh.get_from_rx_queue()
            if rx_msg:
                button_status_msg, button_status = zsmi.unpack_button_status_message(rx_msg)

                # If a button status message was received print pressed and released states
                if button_status_msg:
                    print("\x1b[2J\x1b[HKeypad Button Monitor:\n{:.3f}:".format(time.clock()))
                    for button in button_status:
                        print("State: {}\tHold Time: {}\t{}".format(ButtonState(button["button_state"]).name,
                                                                    button["button_hold_time"],
                                                                    ButtonId(button["button_id"]).name))
            if time.time() > ping_timeout:
                zsmi.send_ping(wait_for_ack=False)
                ping_timeout = time.time() + 1.0
