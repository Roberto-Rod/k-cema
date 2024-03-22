#!/usr/bin/env python3
"""
Power Meter Base Class
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
class VisaPowerMeter(VisaTestEquipment):
    # Concrete class implementations should override these capability parameters with appropriate values
    MIN_FREQUENCY_HZ = 0.0
    MAX_FREQUENCY_HZ = 0.0
    MIN_INPUT_POWER_DBM = -200.0
    MAX_INPUT_POWER_DBM = -200.0

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

    def zero_sensor(self):
        """
        Zero the sensor.
        :return: True if successful, else False
        """
        raise NotImplementedError

    def set_freq_hz(self, freq_hz):
        """
        Set the frequency with Hz resolution used for frequency dependent offset-corrections.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        :return: True if successful, else False
        """
        raise NotImplementedError

    def get_freq_hz(self):
        """
        Return the current frequency with Hz resolution used for frequency dependent offset-corrections.
        :return frequency with Hz resolution :type Float
        """
        raise NotImplementedError

    def get_power_dbm(self):
        """
        Return the measured power with dBm resolution.
        :return power_dbm: power in dBm :type Float
        """
        raise NotImplementedError

    def set_offset(self, offset_db):
        """
        Enable/disable the RF output
        :param offset_db: required offset in dB :type Float
        :return: True if successful, else False
        """
        raise NotImplementedError

    def get_offset(self):
        """
        Return the RF output enable state
        :return current offset in dB :type Float
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
    for cls in VisaPowerMeter.__subclasses__():
        s = cls(resource_name)
        if s.find_and_initialise():
            return s

    raise RuntimeError("Could not detect Power Meter resource - '{}'".format(resource_name))


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    print("Module is NOT intended to be executed stand-alone")
