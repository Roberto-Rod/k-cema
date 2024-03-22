#!/usr/bin/env python3
"""
Base class for VISA compatible test equipment
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

# stdlib imports --------------------------------------------------------------
import logging

# Third-party imports ---------------------------------------------------------
import pyvisa

# Our own imports -------------------------------------------------------------
from visa_signal_generator import *
from visa_power_meter import *
from visa_power_supply import *
from visa_spectrum_analyser import *

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
class VisaTestEquipment:
    """" Base class for a piece of VISA compatible test equipment. """
    # Concrete class implementations should override parameters with appropriate values
    MANUFACTURER = ""
    MODEL = ""

    def __init__(self, resource_type):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        self.resource_manager = pyvisa.ResourceManager()
        self.resource_type = resource_type
        self.visa_te = None
        self.resource = None
        self.manufacturer = ""
        self.model = ""
        log.info("INFO - Instanciating Visa Test Equipment Base Class!")

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)


    def __del__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self):
        pass

    # @abstractmethod
    def find_and_initialise(self, resource_type):
        """
        Looks for resource name specified during object creation in available resources and initialises device if it is
        found.
        Concrete class implementations must define the parameter SUPPORTED_MODELS which is a List of Dictionaries, e.g.
        [{"manufacturer": "HP", "model "abc"}, {"manufacturer": "HP", "model "abc"}, ... ]
        :return: True if the resource is found and initialised, else False
        """
        pass

    # @abstractmethod
    def initialise_device(self, model_string_list):
        """
        Initialises the device, only successful if the resource is in the list of supported models.
        :param model_string_list: list of models supported by the concrete class implementation :type List of Strings
        :return: True if the resource is found and initialised, else False
        """
        pass

    # @abstractmethod
    def device_specific_initialisation(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        if self.resource_type == "Signal Generator":
            self.visa_te = VisaSignalGenerator()
            [is_device_initalized, model] = self.visa_te.device_specific_initialisation()
            if is_device_initalized:
                log.info("INFO - Found and initialised: {}".format(model)) 
                self.resource = self.visa_te
                return is_device_initalized, model     
            else:
                log.info("ERROR: Could not find & configure signal generator")
                return False, None
        elif self.resource_type == "Power Meter":
            self.visa_te = VisaPowerMeter()
            [is_device_initalized, model] = self.visa_te.device_specific_initialisation()
            if is_device_initalized:
                log.info("INFO - Found and initialised: {}".format(model))  
                self.resource = self.visa_te
                return is_device_initalized, model     
            else:
                log.info("ERROR: Could not find & configure power meter")
                return False, None
        elif self.resource_type == "Power Supply":
            self.visa_te = VisaPowerSupply()
            [is_device_initalized, model] = self.visa_te.device_specific_initialisation()
            if is_device_initalized:
                log.info("INFO - Found and initialised: {}".format(model))  
                self.resource = self.visa_te
                return is_device_initalized, model     
            else:
                log.info("ERROR: Could not find & configure power supply")
                return False, None
        elif self.resource_type == "Spectrum Analyser":
            self.visa_te = VisaSpectrumAnalyser()
            [is_device_initalized, model] = self.visa_te.device_specific_initialisation()
            if is_device_initalized:
                log.info("INFO - Found and initialised: {}".format(model))  
                self.resource = self.visa_te
                return is_device_initalized, model     
            else:
                log.info("ERROR: Could not find & configure spectrum analyser")
                return False, None
        else:
            log.info("ERROR: Unknown Resource Type string. Available options are:\n 1 - Signal Generator\n 2 - Power Meter\n 3 - Power Supply\n 4 - Spectrum Analyser")
            return False, None

    def set_frequency_Hz(self, freq_hz):
        """
        Set the carrier frequency with Hz resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        pass

    # @abstractmethod
    def get_frequency_Hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return frequency with Hz resolution :type Float
        """
        pass
   
    # @abstractmethod
    def set_output_power_dBm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        pass
    
    # @abstractmethod
    def get_output_power_dBm(self):
        """
        Return the output power with dBm resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return power_dbm: output power in dBm :type Float
        """
        pass

    # @abstractmethod
    def wait_command_complete(self):
        pass

    # @abstractmethod
    def send_command(self, cmd):
        pass

    # @abstractmethod
    def send_query(self, query, delay=None):
        pass


# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    """ List the available PyVISA resources. """
    log.info("Module is NOT intended to be executed stand-alone")

def test():
    """ List the available PyVISA resources. """
    log.info("Checking for available PyVISA resources:")

    log.info("INFO - Testing for invalid PyVISA resources:")
    sg = VisaTestEquipment(resource_type="Signal ")
    sg.device_specific_initialisation()

    log.info("INFO - Searching for signal generators...")
    sg = VisaTestEquipment(resource_type="Signal Generator")
    sg.device_specific_initialisation()

    log.info("INFO - Searching for power meters...") 
    pm = VisaTestEquipment(resource_type="Power Meter")
    pm.device_specific_initialisation()

    log.info("INFO - Searching for power supplies...") 
    ps = VisaTestEquipment(resource_type="Power Supply")
    ps.device_specific_initialisation()

    log.info("INFO - Searching for spectrum analysers...") 
    sa = VisaTestEquipment(resource_type="Spectrum Analyser")
    sa.device_specific_initialisation()


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run-time procedure """
    main()
    test()