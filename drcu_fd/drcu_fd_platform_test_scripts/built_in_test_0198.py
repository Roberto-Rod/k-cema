#!/usr/bin/env python3
"""
Built-in test module for the KT-000-0198-00 DRCU Motherboard.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
See argparse definition in the Runtime Procedure
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import argparse
from enum import Enum
import json
import logging
from os import popen

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------


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
class BitChannel(Enum):
    VOLTAGE_12V = 0
    VOLTAGE_3V7 = 1
    VOLTAGE_3V3 = 2
    VOLTAGE_2V5 = 3
    VOLTAGE_1V8 = 4
    VOLTAGE_1V0 = 5
    VOLTAGE_VBAT = 6
    VOLTAGE_3V3_BAT = 7
    VOLTAGE_5V = 8
    VOLTAGE_6V7_DPY = 9
    VOLTAGE_15V_DPY = 10
    VOLTAGE_N6V7_DPY = 11
    VOLTAGE_N15V_DPY = 12
    TEMP_AMBIENT = 13


class BuiltInTest:

    chan_name = {
        BitChannel.VOLTAGE_12V: "+12V",
        BitChannel.VOLTAGE_3V7: "+3V7",
        BitChannel.VOLTAGE_3V3: "+3V3",
        BitChannel.VOLTAGE_2V5: "+2V5",
        BitChannel.VOLTAGE_1V8: "+1V8",
        BitChannel.VOLTAGE_1V0: "+1V0",
        BitChannel.VOLTAGE_VBAT: "+VBAT",
        BitChannel.VOLTAGE_3V3_BAT: "+3V3_BAT",
        BitChannel.VOLTAGE_5V: "+5V",
        BitChannel.VOLTAGE_6V7_DPY: "+6V7_DPY",
        BitChannel.VOLTAGE_15V_DPY: "+15V_DPY",
        BitChannel.VOLTAGE_N6V7_DPY: "-6V7_DPY",
        BitChannel.VOLTAGE_N15V_DPY: "-15V_DPY",
        BitChannel.TEMP_AMBIENT: "Amb Temp"}

    chan_units = {
        BitChannel.VOLTAGE_12V: "V",
        BitChannel.VOLTAGE_3V7: "V",
        BitChannel.VOLTAGE_3V3: "V",
        BitChannel.VOLTAGE_2V5: "V",
        BitChannel.VOLTAGE_1V8: "V",
        BitChannel.VOLTAGE_1V0: "V",
        BitChannel.VOLTAGE_VBAT: "V",
        BitChannel.VOLTAGE_3V3_BAT: "V",
        BitChannel.VOLTAGE_5V: "V",
        BitChannel.VOLTAGE_6V7_DPY: "V",
        BitChannel.VOLTAGE_15V_DPY: "V",
        BitChannel.VOLTAGE_N6V7_DPY: "V",
        BitChannel.VOLTAGE_N15V_DPY: "V",
        BitChannel.TEMP_AMBIENT: "deg C"}

    chan_scaling = {
        BitChannel.VOLTAGE_12V: {"divider": 186.13, "offset": 0},
        BitChannel.VOLTAGE_3V7: {"divider": 682.5, "offset": 0},
        BitChannel.VOLTAGE_3V3: {"divider": 682.5, "offset": 0},
        BitChannel.VOLTAGE_2V5: {"divider": 1023.75, "offset": 0},
        BitChannel.VOLTAGE_1V8: {"divider": 1023.75, "offset": 0},
        BitChannel.VOLTAGE_1V0: {"divider": 2047.5, "offset": 0},
        BitChannel.VOLTAGE_VBAT: {"divider": 682.5, "offset": 0},
        BitChannel.VOLTAGE_3V3_BAT: {"divider": 682.5, "offset": 0},
        BitChannel.VOLTAGE_5V: {"divider": 409.5, "offset": 0},
        BitChannel.VOLTAGE_6V7_DPY: {"divider": 341.82, "offset": 0},
        BitChannel.VOLTAGE_15V_DPY: {"divider": 186.14, "offset": 0},
        BitChannel.VOLTAGE_N6V7_DPY: {"divider": 186.14, "offset": -20},
        BitChannel.VOLTAGE_N15V_DPY: {"divider": 97.5, "offset": -40},
        BitChannel.TEMP_AMBIENT: {"divider": 1.0, "offset": 0}}

    def __init__(self):
        """ Class constructor """
        system_vars_str = popen("systemctl show-environment").read()
        self.system_vars_dict = {}
        for line in system_vars_str.splitlines():
            self.system_vars_dict[line.split('=')[0]] = line.split('=')[1]
        # print(self.system_vars_dict)

    def value(self, channel):
        if not isinstance(channel, BitChannel):
            raise TypeError("channel must be an instance of BitChannel Enum")

        if channel == BitChannel.TEMP_AMBIENT:
            # Read the "TEMPERATURE_AMBIENT" environment variable
            raw_val = open(self.system_vars_dict["TEMPERATURE_AMBIENT"], "r").read().rstrip()
            val = int(raw_val)
        else:
            # Read the "ADC_STREAM" environment variable, returns JSON string
            adc_vals = json.loads(open(self.system_vars_dict["ADC_STREAM"], "r").read())
            val = adc_vals.get(str(channel.value), -32768)

        return (val / self.chan_scaling[channel]["divider"]) + self.chan_scaling[channel]["offset"]


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main(channel):
    bit = BuiltInTest()

    if hasattr(BitChannel, channel):
        log.info("INFO - {} {:.2f} {}".format(bit.chan_name[getattr(BitChannel, channel)],
                                              bit.value(getattr(BitChannel, channel)),
                                              bit.chan_units[getattr(BitChannel, channel)]))
    else:
        log.info("INFO - Invalid channel!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Call runtime procedure and print requested parameter value
    """
    parser = argparse.ArgumentParser(description="Built-in Test KT-000-0198-00")
    parser.add_argument("-c", "--channel", required=True, dest="channel", action="store",
                        help="Read a BIT channel value")
    args = parser.parse_args()

    fmt = "%(asctime)s: %(message)s"
    # Set logging level to INFO to see test pass/fail results and DEBUG
    # to see detailed serial process information
    logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

    main(args.channel)
