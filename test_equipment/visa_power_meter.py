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
import sys, io

# Third-party imports -----------------------------------------------
import pyvisa


# Our own imports ---------------------------------------------------
from power_meter_nrp import PowerMeterNRP
# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "ROHDE&SCHWARZ", "model": "NRP18S"},
    {"manufacturer": "ROHDE&SCHWARZ", "model": "NRP-Z21"}
]


# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class VisaPowerMeter():
    # Concrete class implementations should override these capability parameters with appropriate values

    def __init__(self, debug = False):
        """
        Class constructor
        :param: None
        """
        super().__init__()
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.pm = None
        self.debug = debug
        self.binding_success = False
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
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :return: Device model and True if successful, else False
        """

        # Check if there are any power meters connected
        if (self.rm.list_resources() != ()):
            log.info("INFO - Found connected resources\n: {}".format(self.rm.list_resources()))
            for res in self.rm.list_resources():
                # Ignore resources that are TCPIP0 and of ASRLn type. Power meters appear as USB, USB0 and/or RSNRP
                if res and res.startswith("TCPIP0"):
                    log.info("INFO - Connected device with IP address {} is NOT a power meter!".format(res.split("::")[1]))
                elif res and res.startswith("ASRL"):
                    log.info("INFO - Connected serial device {} is NOT a power meter!".format(res.split("::")[0]))
                # Check for RSNRP
                elif res and res.startswith("RSNRP"):
                    # There are connected devices, get the model and try to initialize if it is a supported device
                    try:
                        power_meter = self.rm.open_resource(res)
                        power_meter_query_str = power_meter.query('*IDN?')
                        # Close the resource 
                        power_meter.close()
                        self.manufacturer = power_meter_query_str.split(",")[0]
                        self.model = power_meter_query_str.split(",")[1]
                        self.serial_no = power_meter_query_str.split(",")[2]
                        self.revision = power_meter_query_str.split(",")[3]
                    except:
                        log.info("ERROR - Resource could not be opened: {}".format(res))
                        self.model = None
                        self.resource = None
                    
                    if self.debug:
                        log.info("DEBUG - power_meter_query_str : {}".format(power_meter_query_str))
                        log.info("DEBUG - Manufacturer : {}".format(self.manufacturer))
                        log.info("DEBUG - Model : {}".format(self.model))
                        log.info("DEBUG - Serial Number : {}".format(self.serial_no))
                        log.info("DEBUG - Revision : {}".format(self.revision))

                    log.info("INFO - Checking if {} is a supported meter...".format(self.model))

                    for model in SUPPORTED_MODELS:
                        # Check if the connected device is a supported device
                        if self.model == model.get("model"):
                            log.info ("INFO - Found a supported NRP Power Meter Serial Number: {}, Model: {}".format(self.serial_no, self.model))
                            self.resource = res
                            # Check the model and create the correct power supply object
                            if self.model == "NRP18S" or self.model == "NRP-Z21":

                                self.pm = PowerMeterNRP()
                                # log.info("INFO - Initialising device: ")

                                try:
                                    if self.pm.find_and_initialise():
                                        return True, self.model
                                    else:
                                        log.info("ERROR")
                                        self.resource = None   
                                except:
                                    self.resource = None 
                            else: 
                                log.info ("INFO - This is Not a supported NRP meter: ".format(self.model))
                        # else: 
                    log.info ("INFO - This is Not a supported NRP meter: ".format(self.model))

                # Check for USB and USB0 devices
                elif res and (res.startswith("USB0") or res.startswith("USB")):
                    # There are connected devices, get the model and try to initialize if it is a supported device
                    try:
                        power_meter = self.rm.open_resource(res)
                        power_meter_query_str = power_meter.query('*IDN?')
                        # Close the resource 
                        power_meter.close()
                        self.manufacturer = power_meter_query_str.split(",")[0]
                        self.model = power_meter_query_str.split(",")[1]
                        self.serial_no = power_meter_query_str.split(",")[2]
                        self.revision = power_meter_query_str.split(",")[3]
                    except:
                        log.info("ERROR - Resource could not be opened: {}".format(res))
                        self.model = None
                        self.resource = None
                    
                    if self.debug:
                        log.info("DEBUG - power_meter_query_str : {}".format(power_meter_query_str))
                        log.info("DEBUG - Manufacturer : {}".format(self.manufacturer))
                        log.info("DEBUG - Model : {}".format(self.model))
                        log.info("DEBUG - Serial Number : {}".format(self.serial_no))
                        log.info("DEBUG - Revision : {}".format(self.revision))
                        
                    log.info("INFO - Checking if {} is a supported meter...".format(self.model))

                    for model in SUPPORTED_MODELS:
                        # Check if the connected device is a supported device
                        if self.model == model.get("model"):
                            self.resource = res
                            # Check the model and create the correct power supply object
                            if self.model == "NRP18S" or self.model == "NRP-Z21":

                                self.pm = PowerMeterNRP()
                                try:
                                    if self.pm.find_and_initialise():
                                        return True, self.model
                                    else:
                                        log.info("ERROR")
                                        self.resource = None   
                                except:
                                    self.resource = None 
                            else: 
                                log.info ("INFO - This is Not a supported NRP meter: ".format(self.model))
                        else: 
                            log.info ("INFO - This is Not a supported NRP meter: ".format(self.model))
                else:
                    log.info("ERROR - Unknown connected resource type!".format(res))

            log.info("ERROR - Did Not find any supported connected meters!")
            return False, None
        else:
            log.info("ERROR - Did Not find any connected meters or other resources!")
            return False, None 
    
    def details(self):
        """
        Get the power meter details.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        pass

    def zero(self):
        """
        Zero the power meter.
        This method must be implemented by concrete class implementations to perform device specific initialisation.
        :param freq_hz: required carrier frequency in Hz :type Integer, Float or String
        """
        pass

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
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    pm = VisaPowerMeter()

    log.info("info - Power Meter Test:")
    [is_device_initalized, model] = pm.device_specific_initialisation()
    if is_device_initalized:
        log.info("INFO - Found and initialised: {}".format(model))      
    else:
        log.info("ERROR: could not find & configure power meter")
        exit()

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()

    