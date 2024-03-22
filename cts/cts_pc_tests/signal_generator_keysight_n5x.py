#!/usr/bin/env python3
"""
VISA signal generator driver classes for Keysight N5xxxx devices.
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
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from signal_generator import VisaSignalGenerator

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Agilent Technologies", "model": "N5181A"}
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class SignalGeneratorKeysightN5181A(VisaSignalGenerator):
    MANUFACTURER = "Agilent Technologies"
    MODEL = "N5181A"

    def __init__(self, resource_name):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        super().__init__(resource_name)

    def device_specific_initialisation(self):
        """
        Concrete class implementation of device specific initialisation, sets capability parameters based on model type.
        :return: True if successful, else False
        """
        ret_val = False
        idn_dict = self.ieee4882_idn_query()
        option_string = self.ieee4882_opt_query()
        # Check we haven't got an empty Dictionary
        if len(idn_dict) != 0:
            if idn_dict.get("manufacturer", "") == self.MANUFACTURER and idn_dict.get("model", "") == self.MODEL:
                self.MIN_FREQUENCY_HZ = 250000.0
                self.MAX_FREQUENCY_HZ = 6000.0E6
                if "1EQ" in option_string:
                    self.MIN_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": 250, "freq_hi_khz": 6000000, "power_dbm": -127.0}
                    ]
                else:
                    self.MIN_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": 250, "freq_hi_khz": 6000000, "power_dbm": -110.0}
                    ]
                if "1EA" in option_string:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": 250, "freq_hi_khz": 50000, "power_dbm": 15.0},
                        {"freq_lo_khz": 50000, "freq_hi_khz": 3000000, "power_dbm": 23.0},
                        {"freq_lo_khz": 3000000, "freq_hi_khz": 5000000, "power_dbm": 17.0},
                        {"freq_lo_khz": 5000000, "freq_hi_khz": 6000000, "power_dbm": 16.0}
                    ]
                else:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": 250, "freq_hi_khz": 5000000, "power_dbm": 13.0},
                        {"freq_lo_khz": 5000000, "freq_hi_khz": 6000000, "power_dbm": 11.0}
                    ]
                ret_val = True

        # Ensure the output is disabled
        self.set_output_enable(False)
        return ret_val

    def set_carrier_freq_hz(self, freq_hz):
        """
        Set the carrier frequency with Hz resolution.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        if self.send_command(":FREQ:CW {:.0f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_carrier_freq_hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        :return frequency with Hz resolution :type Integer
        """
        return float(self.send_query(":FREQ:CW?").strip())

    def set_output_power_dbm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        if self.send_command(":POW:LEV {:.1f} DBM".format(power_dbm)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_power_dbm(self):
        """
        Return the output power with dBm resolution.
        :return power_dbm: output power in dBm :type Float
        """
        return float(self.send_query(":POW:LEV?").strip())

    def set_output_enable(self, enable_state):
        """
        Enable/disable the RF output
        :param enable_state: True to enable output, False to disable :type Boolean
        """
        if self.send_command(":OUTP:STAT {}".format("ON" if enable_state else "OFF")):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_enable(self):
        """
        Return the RF output enable state
        :return True if output enabled, False if disabled :type Boolean
        """
        return True if "ON" in self.send_query(":OUTP:STAT?").strip() else False


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
