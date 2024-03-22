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

# stdlib imports --------------------------------------------------------------
import logging
import sys, io

# Third-party imports ---------------------------------------------------------
import pyvisa


# Our own imports -------------------------------------------------------------
# from visa_test_equipment import *
from spectrum_analyser_fsw import *
from spectrum_analyser_hp8563e import *
from spectrum_analyser_n9342c import *
from signal_generator_mxg import * # for testing RR WFH setup only

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Keysight Technologies", "model": "N9342C"},
    {"manufacturer": "Keysight Technologies", "model": "FSW"},
    {"manufacturer": "Agilent Technologies", "model": "HP8563E"}
]


# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class VisaSpectrumAnalyser():
    # Concrete class implementations should override these capability parameters with appropriate values
    MIN_FREQUENCY_HZ = 0.0
    MAX_FREQUENCY_HZ = 0.0
    MIN_OUTPUT_POWER_DBM = -200.0
    MAX_OUTPUT_POWER_DBM = -200.0

    def __init__(self, debug = False):
        """
        Class constructor
        :param : None
        """
        super().__init__()
        log.info("Instanciating a Spectrum Analyser base class!")
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sa = None
        self.debug = debug
        self.binding_success = False
        self.resource = None
        self.manufacturer = ""
        self.model = ""
        self.serial_no = ""
        self.revision = ""

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def device_specific_initialisation(self):
        """
        :return: True if successful, else False
        """
        self.resource = None
        log.info("INFO - Found connected resources\n: {}".format(self.rm.list_resources()))
        for res in self.rm.list_resources():
            if res and res.startswith("TCPIP0"):
                spectrum_analyser = res
                # There are connected devices, get the model and try to initialize if it is a supported device
                try:
                    spectrum_analyser = self.rm.open_resource(res)
                    spectrum_analyser_query_str = spectrum_analyser.query('*IDN?')
                    # Close the resource 
                    spectrum_analyser.close()
                    self.manufacturer = spectrum_analyser_query_str.split(",")[0]
                    self.model = spectrum_analyser_query_str.split(",")[1]
                    self.serial_no = spectrum_analyser_query_str.split(",")[2]
                    self.revision = spectrum_analyser_query_str.split(",")[3]
                except:
                    log.info("ERROR - Resource could not be opened: {}".format(spectrum_analyser))
                    self.resource = None
                
                if self.debug:
                    log.info("DEBUG - power_meter_query_str : {}".format(spectrum_analyser_query_str))
                    log.info("DEBUG - Manufacturer : {}".format(self.manufacturer))
                    log.info("DEBUG - Model : {}".format(self.model))
                    log.info("DEBUG - Serial Number : {}".format(self.serial_no))
                    log.info("DEBUG - Revision : {}".format(self.revision))

                log.info("INFO - Checking if {} is a supported spectrum analyser...".format(self.model))

                for model in SUPPORTED_MODELS:
                    if self.model == model.get("model"):
                        log.info("INFO - Found a supported Spectrum Analyser Serial Number: {}, Model: {}".format(self.serial_no, self.model))
                        self.resource = res
                        # Check the self.model and create the correct spectrum analyser object
                        if self.model == "N9342C":
                            self.sa = SpectrumAnalyserN9342C()
                        elif self.model == "FSW":
                            self.sa = SpectrumAnalyserFSW()
                        elif self.model == "HP8563E":
                            self.sa = SpectrumAnalyserHP8563E()
                        try:
                            if self.sa.find_and_initialise():
                                # log.info("Found and initialised N9342C Spectrum Analyser: {}".format(res))
                                return True, self.model
                            else:
                                self.resource = None
                        except:
                            self.resource = None
                    # else:
                log.info("ERROR - This is not a supported spectrum analyser: {}".format(self.model))
        log.info("ERROR - Did not find a Spectrum Analyser")
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

    def details(self):
        """
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    log.info("INFO - Module is NOT intended to be executed stand-alone")
    sa = VisaSpectrumAnalyser()

    [is_device_initalized, model] = sa.device_specific_initialisation()
    if is_device_initalized:
        log.info("INFO - Successfully initialized spectrum analyser {}".format(model))
    else:
        log.info("ERROR - could not find & configure signal generator")
        exit()
    