#!/usr/bin/env python3
"""
Signal Generator Base Class
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
class VisaSignalGenerator(VisaTestEquipment):
    # Concrete class implementations should override these capability parameters with appropriate values
    MIN_FREQUENCY_HZ = 0.0
    MAX_FREQUENCY_HZ = 0.0
    MIN_OUTPUT_POWER_DBM = -200.0
    MAX_OUTPUT_POWER_DBM = -200.0

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

    def set_carrier_freq_hz(self, freq_hz):
        """
        Set the carrier frequency with Hz resolution.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        raise NotImplementedError

    def get_carrier_freq_hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        :return frequency with Hz resolution :type Float
        """
        raise NotImplementedError

    def set_output_power_dbm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        raise NotImplementedError

    def get_output_power_dbm(self):
        """
        Return the output power with dBm resolution.
        :return power_dbm: output power in dBm :type Float
        """
        raise NotImplementedError

    def set_output_enable(self, enable_state):
        """
        Enable/disable the RF output
        :param enable_state: True to enable output, False to disable :type Boolean
        """
        raise NotImplementedError

    def get_output_enable(self):
        """
        Return the RF output enable state
        :return True if output enabled, False if disabled :type Boolean
        """
        raise NotImplementedError


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def instantiate_visa_sig_gen_class(resource_name):
    """
    Get a proper VisaSignalGenerator subclass depending on the IEEE488.2 *IDN? response from the equipment.
    """
    # Fist instantiate base to retrieve version
    for cls in VisaSignalGenerator.__subclasses__():
        s = cls(resource_name)
        if s.find_and_initialise():
            return s

    raise RuntimeError("Could not detect Signal Generator resource - '{}'".format(resource_name))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
