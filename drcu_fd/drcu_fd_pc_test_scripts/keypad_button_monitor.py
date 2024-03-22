#!/usr/bin/env python3
"""
Utility module for monitoring keypad button status.
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
from drcu_serial_msg_intf import DrcuSerialMsgInterface, DrcuButtonId, DrcuButtonState

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
    parser = argparse.ArgumentParser(description="Keypad button monitor")
    parser.add_argument("-u", "--uart", required=True, help="Serial UART")
    args = parser.parse_args()

    with DrcuSerialMsgInterface(args.uart) as drcu_smi:
        # Clear the terminal and move the cursor home
        print("\x1b[2J", end="\n\x1b[HKeypad Button Monitor:\n")
        while True:
            time.sleep(0.001)
            rx_msg = drcu_smi.smh.get_from_rx_queue()
            if rx_msg:
                button_status_msg, button_status = drcu_smi.unpack_button_status_message(rx_msg)

                # If a button status message was received print pressed and released states
                if button_status_msg:
                    print("\x1b[2J\x1b[HKeypad Button Monitor:\n{:.3f}:".format(time.time()))
                    for button in button_status:
                        print("State: {}\tHold Time: {}\t{}".format(DrcuButtonState(button["button_state"]).name,
                                                                    button["button_hold_time"],
                                                                    DrcuButtonId(button["button_id"]).name))
