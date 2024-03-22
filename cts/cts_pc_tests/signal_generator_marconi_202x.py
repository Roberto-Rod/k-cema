#!/usr/bin/env python3
"""
VISA signal generator driver classes for Marconi 202x devices.
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
    {"manufacturer": "MARCONI INSTRUMENTS", "model": "2023"},
    {"manufacturer": "MARCONI INSTRUMENTS", "model": "2024"}
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class SignalGeneratorMarconi2023(VisaSignalGenerator):
    MANUFACTURER = "MARCONI INSTRUMENTS"
    MODEL = "2023"

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
                self.MIN_FREQUENCY_HZ = 10000.0
                self.MAX_FREQUENCY_HZ = 1200000000.0
                self.MIN_OUTPUT_POWER_DBM = [
                    {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": -137.0}
                ]
                if "HIGH POWER" in option_string:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": 25.0}
                    ]
                else:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": 13.0}
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
        if self.send_command("CFRQ:MODE FIXED;VALUE {:.0f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_carrier_freq_hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        :return frequency with Hz resolution :type Integer
        """
        return float(self.send_query("CFRQ:VALUE?").strip())

    def set_output_power_dbm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        if self.send_command("RFLV:VALUE {:.1f} DBM".format(power_dbm)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_power_dbm(self):
        """
        Return the output power with dBm resolution.
        :return power_dbm: output power in dBm :type Float
        """
        return float(self.send_query("RFLV:VALUE?").strip())

    def set_output_enable(self, enable_state):
        """
        Enable/disable the RF output
        :param enable_state: True to enable output, False to disable :type Boolean
        """
        if self.send_command("RFLV:{}".format("ON" if enable_state else "OFF")):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_enable(self):
        """
        Return the RF output enable state
        :return True if output enabled, False if disabled :type Boolean
        """
        return True if "ON" in self.send_query("RFLV?").strip() else False


class SignalGeneratorMarconi2024(VisaSignalGenerator):
    MANUFACTURER = "MARCONI INSTRUMENTS"
    MODEL = "2024"

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
                self.MIN_FREQUENCY_HZ = 10000.0
                self.MAX_FREQUENCY_HZ = 2400.0E6
                self.MIN_OUTPUT_POWER_DBM = [
                    {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": -137.0}
                ]
                if "HIGH POWER" in option_string:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": 1200E6, "power_dbm": 25.0},
                        {"freq_lo_khz": 1200E6, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": 19.0}
                    ]
                else:
                    self.MAX_OUTPUT_POWER_DBM = [
                        {"freq_lo_khz": self.MIN_FREQUENCY_HZ, "freq_hi_khz": self.MAX_FREQUENCY_HZ, "power_dbm": 13.0}
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
        if self.send_command("CFRQ:MODE FIXED;VALUE {:.0f} HZ".format(freq_hz)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_carrier_freq_hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        :return frequency with Hz resolution :type Integer
        """
        return float(self.send_query("CFRQ:VALUE?").strip())

    def set_output_power_dbm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        if self.send_command("RFLV:VALUE {:.1f} DBM".format(power_dbm)):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_power_dbm(self):
        """
        Return the output power with dBm resolution.
        :return power_dbm: output power in dBm :type Float
        """
        return float(self.send_query("RFLV:VALUE?").strip())

    def set_output_enable(self, enable_state):
        """
        Enable/disable the RF output
        :param enable_state: True to enable output, False to disable :type Boolean
        """
        if self.send_command("RFLV:{}".format("ON" if enable_state else "OFF")):
            return self.ieee4882_wait_cmd_complete()
        else:
            return False

    def get_output_enable(self):
        """
        Return the RF output enable state
        :return True if output enabled, False if disabled :type Boolean
        """
        return True if "ON" in self.send_query("RFLV?").strip() else False

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
