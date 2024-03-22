#!/usr/bin/env python3
"""
TTi CPX400DP Power Supply Class

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
from time import sleep
# -----------------------------------------------------------------------------
# Third party library imports
# -----------------------------------------------------------------------------
import pyvisa

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

class PowerSupplyCPX400DP():
    def __init__(self, reset_device=True, debug=False):
        super().__init__()
        log.info("INFO - Instanciating TTi CPX400DP Supply Class!")
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.psu = None
        self.reset_device = reset_device
        self.debug = debug

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def __del__(self):
        if self.psu:
            self.psu.close()

    def find_and_initialise(self):
        self.resource = None
        resources = self.rm.list_resources()
        for res in resources:
            # This instrument does not fully support VXI-11, we need to use the COM port interface
            # find COM ports, open and query to look for device ID
            if res.startswith("ASRL"):
                self.resource = res
                if self.initialise_device():
                    log.info("INFO - Found and initialised CPX400DP Power Supply: {}".format(res))
                    return True
                else:
                    self.resource = None
        log.info("ERROR - did not find a CPX400DP Power Supply")
        return False

    def initialise_device(self):
        try:
            self.psu = self.rm.open_resource(self.resource)
        except:
            if self.psu:
                self.psu.close()
                log.info("INFO - Could not open resource: {}".format(self.resource))
            else:
                log.info("ERROR - Resource busy: {}".format(self.resource))
            return False
        try:
            if "CPX400DP" in self.details():
                if self.reset_device:
                    return self.send_command("*RST")
                else:
                    return True
        except:
            pass
        self.psu.close()
        return False

    def details(self):
        return self.send_query("*IDN?")
    
    def resource_name(self):
        return self.resource

    def send_command(self, cmd):
        if self.debug:
            log.info("INFO - send_command: {}".format(cmd))
        try:
            self.psu.write(cmd)
            return True
        except:
            log.info("ERROR - could not send command")
            return False

    def send_query(self, query):
        if self.debug:
            log.info("INFO - send_query: {}".format(query))
        try:
            return self.psu.query(query).strip()
        except:
            log.info("ERROR - could not send query")
            return False

    def set_enabled(self, enabled, channel=1):
        if enabled:
            return self.send_command("OP{} 1".format(channel))
        else:
            return self.send_command("OP{} 0".format(channel))

    def dc_is_enabled(self, channel=1):
        response = self.send_query("OP{}?".format(channel))
        return response == "1"

    def set_voltage(self, voltage, channel=1):
        return self.send_command("V{0} {1}".format(channel, voltage))

    def get_voltage(self, channel=1):
        response = self.send_query("V{}?".format(channel))
        return float(response.split(" ")[1])

    def get_voltage_out(self, channel=1):
        response = self.send_query("V{}O?".format(channel))
        return float(response.replace("V", ""))

    def set_current(self, current, channel=1):
        return self.send_command("I{0} {1}".format(channel, current))

    def get_current(self, channel=1):
        response = self.send_query("I{}?".format(channel))
        return float(response.split(" ")[1])

    def get_current_out(self, channel=1):
        response = self.send_query("I{}O?".format(channel))
        return float(response.replace("A", ""))

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
        return self.send_command("OVP{0} {1}".format(channel, voltage))

    def get_ovp(self, channel=1):
        response = self.send_query("OVP{}?".format(channel))
        return float(response.split(" ")[1])

    def set_ocp(self, current, channel=1):
        return self.send_command("OCP{0} {1}".format(channel, current))

    def get_ocp(self, channel=1):
        response = self.send_query("OCP{}?".format(channel))
        return float(response.split(" ")[1])

    def set_sense_remote(self, channel=1):
        return self.send_command("SENSE{} 1".format(channel))

    def set_sense_local(self, channel=1):
        return self.send_command("SENSE{} 0".format(channel))

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    psu = PowerSupplyCPX400DP()
    log.info("INFO - PowerSupplyCPX400DP Test:")
    if psu.find_and_initialise():
        psu.set_voltage(5.0, 1)
        psu.set_voltage(3.3, 2)
        psu.set_current(1, 1)
        psu.set_current(0.5, 2)
        psu.set_ovp(5.5, 1)
        psu.set_ovp(3.63, 2)
        psu.set_ocp(1.1, 1)
        psu.set_ocp(0.55, 2)
        psu.set_sense_local(1)
        psu.set_sense_local(2)
        psu.set_enabled(True, 1)
        psu.set_enabled(True, 2)
        log.info("INFO - Details:                 {}".format(psu.details()))
        log.info("INFO - Ch1 Enabled:             {}".format(psu.dc_is_enabled(1)))
        log.info("INFO - Ch2 Enabled:             {}".format(psu.dc_is_enabled(2)))
        log.info("INFO - Ch1 Voltage Setting:     {} V".format(psu.get_voltage(1)))
        log.info("INFO - Ch2 Voltage Setting:     {} V".format(psu.get_voltage(2)))
        log.info("INFO - Ch1 Voltage Out:         {} V".format(psu.get_voltage_out(1)))
        log.info("INFO - Ch2 Voltage Out:         {} V".format(psu.get_voltage_out(2)))
        log.info("INFO - Ch1 Current Setting:     {} A".format(psu.get_current(1)))
        log.info("INFO - Ch2 Current Setting:     {} A".format(psu.get_current(2)))
        log.info("INFO - Ch1 Current Out:         {} A".format(psu.get_current_out(1)))
        log.info("INFO - Ch2 Current Out:         {} A".format(psu.get_current_out(2)))
        log.info("INFO - Ch1 Power Out:           {} W".format(psu.get_power_out(1)))
        log.info("INFO - Ch2 Power Out:           {} W".format(psu.get_power_out(2)))
        log.info("INFO - Ch1 Average Power Out:   {} W".format(psu.get_average_power_out(1)))
        log.info("INFO - Ch2 Average Power Out:   {} W".format(psu.get_average_power_out(2)))
        log.info("INFO - Ch1 OVP Setting:         {} V".format(psu.get_ovp(1)))
        log.info("INFO - Ch2 OVP Setting:         {} V".format(psu.get_ovp(2)))
        log.info("INFO - Ch1 OCP Setting:         {} V".format(psu.get_ocp(1)))
        log.info("INFO - Ch2 OCP Setting:         {} V".format(psu.get_ocp(2)))
        psu.set_enabled(False, 1)
        psu.set_enabled(False, 2)

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()