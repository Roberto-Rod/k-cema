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
import sys, io

# Third-party imports -----------------------------------------------
import pyvisa

# Our own imports ---------------------------------------------------
from signal_generator_hp83752a import *
from signal_generator_mxg import *
from signal_generator_n5173b_83b import *

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Agilent Technologies", "model": " N5181A"},
    {"manufacturer": "Agilent Technologies", "model": " N5173B"},
    {"manufacturer": "Keysight Technologies", "model": " N5173B"},
    {"manufacturer": "Keysight Technologies", "model": " N5183B"},
    {"manufacturer": "Agilent Technologies", "model": "83752A"}
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class VisaSignalGenerator:
    # Concrete class implementations should override these capability parameters with appropriate values
    MIN_FREQUENCY_HZ = 0.0
    MAX_FREQUENCY_HZ = 0.0
    MIN_OUTPUT_POWER_DBM = -200.0
    MAX_OUTPUT_POWER_DBM = -200.0

    def __init__(self, debug = False):
        """
        Class constructor
        :param resource_name: VISA resource name for the piece of TE :type String
        """
        super().__init__()
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sg = None
        self.debug = debug
        self.binding_success = False
        self.resource = None
        self.manufacturer = ""
        self.model = ""
        self.serial_no = ""
        self.revision = ""
        log.info("INFO - Instanciating Signal Generator Base Class!")

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def device_specific_initialisation(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        # self.resource = None
        log.info("INFO - Found connected resources:\n {}".format(self.rm.list_resources()))
        for res in self.rm.list_resources():
            if res and res.startswith("TCPIP0"):
                signal_gen = res
                # There are connected devices, get the model and try to initialize if it is a supported device
                try:
                    signal_gen = self.rm.open_resource(res)
                    signal_gen_query_str = signal_gen.query('*IDN?')
                    # Close the resource 
                    signal_gen.close()
                    self.manufacturer = signal_gen_query_str.split(",")[0]
                    self.model = signal_gen_query_str.split(",")[1]
                    self.serial_no = signal_gen_query_str.split(",")[2]
                    self.revision = signal_gen_query_str.split(",")[3]
                except:
                    log.info("ERROR - Resource could not be opened: {}".format(res))
                    self.model = None
                    self.resource = None
                
                if self.debug:
                    log.info("DEBUG - power_meter_query_str : {}".format(signal_gen_query_str))
                    log.info("DEBUG - Manufacturer : {}".format(self.manufacturer))
                    log.info("DEBUG - Model : {}".format(self.model))
                    log.info("DEBUG - Serial Number : {}".format(self.serial_no))
                    log.info("DEBUG - Revision : {}".format(self.revision))

                log.info("INFO - Checking if {} is a supported signal generator...".format(self.model))

                for model in SUPPORTED_MODELS:
                    if self.model == model.get("model"):
                        log.info("INFO - Found a supported Signal Generator Serial Number: {}, Model: {}".format(self.serial_no, self.model))
                        self.resource = res
                        # Check the model and create the correct signal generator object
                        if self.model == "83752A":
                            self.sg = SignalGeneratorHP83752A()
                        elif self.model == " N5181A" or self.model == " N5173B":
                            self.sg = SignalGeneratorMXG()
                        elif self.model == " N5173B" or self.model == "N5183B":
                            self.sg = SignalGeneratorN5173B_83B()
                            
                        try:
                            if self.sg.find_and_initialise():
                                return True, self.model
                            else:
                                self.resource = None
                        except:
                            self.resource = None
                    # else:
                log.info("ERROR - This is not a supported signal generator: {}".format(self.model))
        log.info("ERROR: did not find a signal generator")
        return False, None
        
        

    def find_and_initialise(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")
    
    def initialise_device(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_frequency_Hz(self, freq_hz):
        """
        Set the carrier frequency with Hz resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_frequency_Hz(self):
        """
        Return the current carrier frequency with Hz resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return frequency with Hz resolution :type Float
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_output_power_dBm(self, power_dbm):
        """
        Set the output power with dBm resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param power_dbm: required output power in dBm :type Integer, Float or String
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_output_power_dBm(self):
        """
        Return the output power with dBm resolution.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return power_dbm: output power in dBm :type Float
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_output_enable(self, enable_state):
        """
        Enable/disable the RF output
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param enable_state: True to enable output, False to disable :type Boolean
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_output_enable(self):
        """
        Return the RF output enable state
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return True if output enabled, False if disabled :type Boolean
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def wait_command_complete(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def send_command(self, cmd):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        """
        raise NotImplementedError("This method should be implemented by concrete classes")
    
    def send_query(self, query):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        """
        raise NotImplementedError("This method should be implemented by concrete classes")


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
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    sg = VisaSignalGenerator()
    
    # log.info("SignalGeneratorMXG Test:")
    [is_device_initalized, model] = sg.device_specific_initialisation()
    if is_device_initalized:
        log.info("INFO - Found and initialised: {}".format(model))      
    else:
        log.info("ERROR: could not find & configure signal generator")
        exit()