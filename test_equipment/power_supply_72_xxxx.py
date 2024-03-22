#!/usr/bin/env python3
"""
Tenma 72XXX Power Supply Class

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
import logging
import sys, os
from time import sleep
import serial.tools.list_ports

sys.path.append(os.path.join(sys.path[0],'test_equipment'))
from tenmaDcLib import Tenma72Base

# -----------------------------------------------------------------------------
# Our own imports
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class PowerSupply72_XXXX():
    def __init__(self, debug=False):
        super().__init__()
        log.info("INFO - Instanciating Tenma 72-XXXX Power Supply Class!")
        self.psu_com_port = None
        self.psu = None
        self.debug = debug
        self.ovp = 0.0
        self.ocp = 0.0

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def __del__(self):
        if self.psu:
            self.psu.close()
    
    def get_tenma_psu_instance(self):
        """
        Get a proper Tenma PSU subclass depending on the *IDN? response from the unit.
        The subclasses mainly deal with the limit checks for each PSU type.
        """
        # Try each available COM port and use the first one that succeeds
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            try:
                self.psu_com_port = port.name
                
                # Instantiate base to retrieve ID information
                psu = Tenma72Base(self.psu_com_port, debug=self.debug)
                ver = psu.getVersion()
        
                # Need to close the serial port otherwise call to create specific device instance will fail
                psu.close()
                for cls in Tenma72Base.__subclasses__():
                    for match_str in cls.MATCH_STR:
                        if match_str in ver:
                            return cls(self.psu_com_port, debug=self.debug)
            except:
                self.psu_com_port = None

        return None

    def find_and_initialise(self):
        # Attempt to find the PSU
        self.psu = self.get_tenma_psu_instance()
        if self.psu is not None:
            self.psu.OFF()
            log.info("INFO - Found and initialised 72-XXXX Power Supply: {}".format(self.psu.getVersion()))
            return True
        else:
            log.info("ERROR - did not find a Tenma 72-XXXX Power Supply")
            return False

    def initialise_device(self):
        # Unsupported
        return True

    def details(self):
        return self.psu.getVersion()

    def set_enabled(self, enabled, channel=1):
        if enabled:
            try:
                self.psu.ON()
                return True
            except:
                return False
        else:
            try:
                self.psu.OFF()
            except:
                return False

    def dc_is_enabled(self, channel=1):
        # Unsupported - for now, as we can get this info using self.psu.getStatus()
        return True

    def set_voltage(self, voltage, channel=1):
        # Voltage setting is in mV but returns it in V
        v = self.psu.setVoltage(channel, voltage * 1e3)
        return v == voltage

    def get_voltage(self, channel=1):
        # Voltage reading is in V
        return self.psu.readVoltage(channel)

    def get_voltage_out(self, channel=1):
        # Voltage reading is in V
        return self.psu.runningVoltage(channel)

    def set_current(self, current, channel=1):
        # Current setting is in mA but returns it in A
        a = self.psu.setCurrent(channel, current * 1e3)
        return a == current

    def get_current(self, channel=1):
        # Current reading is in A
        return self.psu.readCurrent(channel)

    def get_current_out(self, channel=1):
        # Current reading is in A
        return self.psu.runningCurrent(channel)

    def get_average_current_out(self, nr_readings=16, delay_s=0, channel=1):
        readings = []
        for i in range(0, nr_readings):
            sleep(delay_s)
            readings.append(self.get_current_out(channel))
        return round(sum(readings) / len(readings), 4)

    def get_power_out(self, channel=1):
        return round(self.get_voltage_out(channel) * self.get_current_out(channel), 4)

    def get_average_power_out(self, nr_readings=16, delay_s=0.1, channel=1):
        # Use average current and an instantaneous voltage measurement as voltage
        # is stabilised by the PSU whilst current varies
        return round(self.get_voltage_out(channel) * self.get_average_current_out(nr_readings, delay_s, channel), 4)

    def set_ovp(self, voltage, channel=1):
        # PSU takes a boolean input rather than a voltage...
        self.ovp = voltage
        enable = True if self.ovp > 0.0 else False
        self.psu.setOVP(enable)
        return True

    def get_ovp(self, channel=1):
        # Unsupported, so just return the saved setting
        return self.ovp

    def set_ocp(self, current, channel=1):
        # PSU takes a boolean input rather than a current...
        self.ocp = current
        enable = True if self.ocp > 0.0 else False
        self.psu.setOCP(enable)
        return True

    def get_ocp(self, channel=1):
        # Unsupported, so just return the saved setting
        return self.ocp

    def set_sense_remote(self, channel=1):
        # Unsupported
        return True

    def set_sense_local(self, channel=1):
        # Unsupported
        return True

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    psu = PowerSupply72_XXXX()
    log.info("INFO - PowerSupply72_XXXX Test:")
    if psu.find_and_initialise():
        psu.set_voltage(5.0, 1)
        psu.set_current(1, 1)
        psu.set_ovp(5.5, 1)
        psu.set_ocp(1.1, 1)
        psu.set_sense_local(1)
        psu.set_enabled(True, 1)
        log.info("INFO - Details:                 {}".format(psu.details()))
        log.info("INFO - Ch1 Enabled:             {}".format(psu.dc_is_enabled(1)))
        log.info("INFO - Ch1 Voltage Setting:     {} V".format(psu.get_voltage(1)))
        log.info("INFO - Ch1 Voltage Out:         {} V".format(psu.get_voltage_out(1)))
        log.info("INFO - Ch1 Current Setting:     {} A".format(psu.get_current(1)))
        log.info("INFO - Ch1 Current Out:         {} A".format(psu.get_current_out(1)))
        log.info("INFO - Ch1 Power Out:           {} W".format(psu.get_power_out(1)))
        log.info("INFO - Ch1 Average Power Out:   {} W".format(psu.get_average_power_out(1)))
        log.info("INFO - Ch1 OVP Setting:         {} V".format(psu.get_ovp(1)))
        log.info("INFO - Ch1 OCP Setting:         {} V".format(psu.get_ocp(1)))
        psu.set_enabled(False, 1)

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":   
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()