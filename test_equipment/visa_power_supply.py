#!/usr/bin/env python3
"""
POwer Supply Base Class

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
# -----------------------------------------------------------------------------
# Standard library imports
# -----------------------------------------------------------------------------
import sys
import logging
# -----------------------------------------------------------------------------
# Third party library imports
# -----------------------------------------------------------------------------
import pyvisa

# -----------------------------------------------------------------------------
# Our own imports
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Test Equipment imports
# -----------------------------------------------------------------------------
# Power Supplies
# -----------------------------------------------------------------------------
from power_supply_cpx400dp import *
from power_supply_72_xxxx import *
from power_supply_qpx import *

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
SUPPORTED_MODELS = [
    {"manufacturer": "Tenma", "model": "72-2940"},
    {"manufacturer": "THURLBY THANDAR", "model": "CPX400DP"},
    {"manufacturer": "THURLBY THANDAR", "model": "QPX750SP"}
]

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class VisaPowerSupply:
    def __init__(self, debug = False):
        """
        Class constructor
        :param : None
        """
        super().__init__()
        log.info("INFO - Instanciating Power Supply Base Class!")
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.psu = None
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
        This method finds the supported power supply models and initializes whichever supported model is connected
        :return: True if successful, else False
        """
        self.resource = None
        log.info("INFO - Found connected resources\n: {}".format(self.rm.list_resources()))
        for res in self.rm.list_resources():
            if res and res.startswith("ASRL"):
                power_supply = res
                # There are connected devices, get the model and try to initialize if it is a supported device
                try:
                    power_supply = self.rm.open_resource(res)
                    power_supply_query_str = power_supply.query('*IDN?')
                    # Close the resource 
                    power_supply.close()

                    if "TENMA" not in power_supply_query_str:
                        # Not a Tenma PSU
                        self.manufacturer = power_supply_query_str.split(", ")[0]
                        self.model = power_supply_query_str.split(", ")[1]
                        self.serial_no = power_supply_query_str.split(", ")[2]
                        self.revision = power_supply_query_str.split(", ")[3]
                    else:
                        # Tenma PSU
                        self.manufacturer = power_supply_query_str.split(" ")[0]
                        self.model = power_supply_query_str.split(" ")[1]
                        self.serial_no = power_supply_query_str.split(" ")[2]
                        self.revision = power_supply_query_str.split(" ")[3]
                except:
                    log.info("ERROR - Resource could not be opened: {}".format(power_supply))
                    self.resource = None
                
                if self.debug:
                    log.info("DEBUG - power_meter_query_str : {}".format(power_supply_query_str))
                    log.info("DEBUG - Manufacturer : {}".format(self.manufacturer))
                    log.info("DEBUG - Model : {}".format(self.model))
                    log.info("DEBUG - Serial Number : {}".format(self.serial_no))
                    log.info("DEBUG - Revision : {}".format(self.revision))

                log.info("INFO - Checking if {} is a supported power supply...".format(self.model))

                for model in SUPPORTED_MODELS:
                    if self.model == model.get("model"):
                        log.info ("INFO - Found a supported Power Supply Serial Number: {}, Model: {}".format(self.serial_no, self.model))
                        self.resource = res
                        # Check the model and create the correct power supply object
                        if self.model == "QPX750SP":
                            self.psu = PowerSupplyQPX()
                        elif self.model == "CPX400DP":
                            self.psu = PowerSupplyCPX400DP()
                        elif self.model == "72-2940":
                            self.psu = PowerSupply72_XXXX()
                        try:
                            if self.psu.find_and_initialise():
                                return True, self.model
                            else:
                                self.resource = None
                        except:
                            self.resource = None
                    # else:
                log.info("ERROR - This is not a supported power supply: {}".format(self.model))
        log.info("ERROR: did not find a Power Supply")
        return False, None

    def find_and_initialise(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")
    
    def initialise_device(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def details(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def send_command(self, cmd):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def send_query(self, query):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_enabled(self, enabled):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def dc_is_enabled(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_voltage(self, voltage):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_voltage(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_voltage_out(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_current(self, voltage):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_current(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_current_out(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_average_current_out(self, nr_readings=16, delay_s=0):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_power_out(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_average_power_out(self, nr_readings=16, delay_s=0.1):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_ovp(self, voltage):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_ovp(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_ocp(self, voltage):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def get_ocp(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_sense_remote(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

    def set_sense_local(self):
        """
        This method must be implemented by concrete class implementations.
        :return: True if successful, else False
        """
        raise NotImplementedError("This method should be implemented by concrete classes")

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

    psu = VisaPowerSupply()
    
    # log.info("SignalGeneratorMXG Test:")
    [is_device_initalized, model] = psu.device_specific_initialisation()
    if is_device_initalized:
        log.info("INFO - Successfully initialized power supply {}".format(model))
    else:
        log.info("ERROR: could not find & configure power supply")
        exit()

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()
    
