#!/usr/bin/env python3
"""
Spectrum Analyser Base Class
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
from enum import Enum
import logging

# Third-party imports -----------------------------------------------


# Our own imports ---------------------------------------------------
from visa_test_equipment import VisaTestEquipment

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
class DbPerDiv(Enum):
    UNKNOWN = 0,
    DB_1 = 1,       # 1 dB per division
    DB_2 = 2,       # 2 dB per division
    DB_5 = 5,       # 5 dB per division
    DB_10 = 10      # 10 dB per division


class VisaSpectrumAnalyser(VisaTestEquipment):
    # Concrete class implementations should override these capability parameters with appropriate values
    MIN_FREQUENCY_HZ = 0.0
    MAX_FREQUENCY_HZ = 0.0

    def __init__(self, resource_name):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        super().__init__(resource_name)

    def device_specific_initialisation(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        raise NotImplementedError

    def set_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's centre frequency with Hz resolution.
        :param freq_hz: required centre frequency in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def get_freq_hz(self):
        """
        Get the spectrum analyser's centre frequency with Hz resolution.
        :return centre frequency with Hz resolution :type Float
        """
        raise NotImplementedError

    def set_start_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's start frequency with Hz resolution.
        :param freq_hz: required start frequency in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def set_stop_freq_hz(self, freq_hz):
        """
        Set the spectrum analyser's stop frequency with Hz resolution.
        :param freq_hz: required stop frequency in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def set_span_hz(self, span_hz):
        """
        Set the spectrum analyser's frequency span with Hz resolution.
        :param span_hz: required frequency span in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def get_span_hz(self):
        """
        Get the spectrum analyser's frequency span with Hz resolution.
        :return frequency span with Hz resolution :type Float
        """
        raise NotImplementedError

    def set_res_bw_hz(self, res_bw_hz):
        """
        Set the spectrum analyser's resolution bandwidth with Hz resolution.
        :param res_bw_hz: required resolution bandwidth in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def get_res_bw_hz(self):
        """
        Get the spectrum analyser's resolution bandwidthwith Hz resolution.
        :return resolution bandwidth with Hz resolution :type Float
        """
        raise NotImplementedError

    def set_ref_level_dbm(self, ref_level_dbm):
        """
        Set the spectrum analyser's reference level with dBm resolution.
        :param ref_level_dbm: required reference level in dBm :type Integer, Float or String
        """
        raise NotImplementedError

    def get_ref_level_dbm(self):
        """
        Get the spectrum analyser's reference level with dBm resolution.
        :return reference level in dBm :type Float
        """
        raise NotImplementedError

    def set_db_per_div(self, db_per_div):
        """
        Set the spectrum analyser's vertical scale (dB/div).
        :param db_per_div: enumerated DbPerDiv value :type DbPerDiv
        """
        raise NotImplementedError

    def get_db_per_div(self):
        """
        Get the spectrum analyser's vertical scale (dB/div).
        :return enumerated DbPerDiv value :type DbPerDiv
        """
        raise NotImplementedError

    def set_cont_trigger(self, cont_trigger):
        """
        Enable/disable the spectrum analyser's continuous trigger.
        :param cont_trigger: True to enable continuous trigger, False to disable :type Boolean
        """
        raise NotImplementedError

    def get_cont_trigger(self):
        """
        Get the spectrum analyser's continuous trigger state.
        :return True if continuous trigger enabled, False if disabled :type Boolean
        """
        raise NotImplementedError

    def get_peak(self):
        """
        Get the peak marker reading.

        Executes marker->peak and returns the marker frequency and power readings.
        :return: [0] freq_hz :type Integer
                 [1] power_dbm :type Float
        """
        raise NotImplementedError

    def get_next_peak(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker frequency and power readings.
        :return: [0] freq_hz :type Integer
                 [1] power_dbm :type Float
        """
        raise NotImplementedError

    def get_peak_power_dbm(self):
        """
        Get the peak marker reading.
        Executes marker->peak and returns the marker power reading.
        :return: power_dbm :type Float
        """
        raise NotImplementedError

    def get_next_peak_power_dbm(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker power reading.
        :return: power_dbm :type Float
        """
        raise NotImplementedError

    def get_peak_freq_hz(self):
        """
        Get the peak marker reading.
        Executes marker->peak and returns the marker frequency reading.
        :return: freq_hz :type Integer
        """
        raise NotImplementedError

    def get_next_peak_freq_hz(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker frequency reading.
        :return: freq_hz :type Integer
        """
        raise NotImplementedError


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def instantiate_visa_sig_gen_class(resource_name):
    """
    Get a proper VisaSpectrumAnalyser subclass depending on the IEEE488.2 *IDN? response from the equipment.
    """
    # Fist instantiate base to retrieve version
    for cls in VisaSpectrumAnalyser.__subclasses__():
        s = cls(resource_name)
        if s.find_and_initialise():
            return s

    raise RuntimeError("Could not detect Spectrum Analyser resource - '{}'".format(resource_name))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
