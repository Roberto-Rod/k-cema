#!/usr/bin/env python3
"""
Keysight EXG X-Series (N5173B/N5183B) Signal Generator Class

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
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


class SignalGeneratorN5173B_83B():
    def __init__(self, debug = False):
        super().__init__()
        log.info("INFO - Instanciating Keysight EXG X-Series (N5173B/N5183B) Signal Generator Class!")
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sg = None
        self.debug = debug
        self.binding_success = False

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)
    
    def __del__(self):
        if self.sg:
            self.sg.close()
        
    def find_and_initialise(self):
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                if self.initialise_device():
                    log.info("INFO - Found and initialised N5173B/83B Signal Generator: {}".format(self.details()))
                    return True
                else:
                    self.resource = None
        log.info("ERROR - did not find an N5173B/83B Signal Generator")
        return False
            
    def initialise_device(self):
        try:
            self.sg = self.rm.open_resource(self.resource)            
            if ("N5173B" or "N5183B") in self.details():
                if self.send_command("*RST") and self.wait_command_complete():
                    ok = True
                else:
                    ok = False
                    self.sg.close()
            else:
                ok = False
                self.sg.close()                                 
        except:
            if self.sg:
                self.sg.close()
                log.info("ERROR - Could not open resource: {}".format(self.resource))
            else:
                log.info("ERROR - Resource busy: {}".format(self.resource))
            ok = False
        return ok     
        
    def details(self):
        return self.send_query("*IDN?")
    
    def resource_name(self):
        return self.resource
    
    def set_frequency_Hz(self, freq_Hz):
        if self.send_command("FREQ {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_frequency_Hz(self):
        return int(float(self.send_query("FREQ?").strip()))
        
    def set_output_power_dBm(self, power_dBm):
        if self.send_command("POW:AMPL {:.2f} DBM".format(power_dBm)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_output_power_dBm(self):
        return float(self.send_query("POW:AMPL?").strip())
    
    def set_output_enable(self, enable_state):
        if self.send_command("OUTP:STAT ON" if enable_state else "OUTP:STAT OFF"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_output_enable(self):
        resp = self.send_query("OUTP:STAT?").strip()
        return bool(resp == "1" or resp == "+1")
    
    def wait_command_complete(self):
        resp = self.send_query("*OPC?").strip()
        return bool(resp == "1" or resp == "+1")

    def send_command(self, cmd):
        if self.debug:
            log.info("INFO - send_command: {}".format(cmd))
        try:            
            self.sg.write(cmd)
            return True
        except:
            log.info("ERROR - could not send command")
            return False
    
    def send_query(self, query):
        if self.debug:
            log.info("INFO - send_query: {}".format(query))
        try:
            return self.sg.query(query).strip()
        except:
            log.info("ERROR - could not send query")
        return False

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    sg = SignalGeneratorN5173B_83B()
    log.info("INFO - SignalGeneratorN5173B_83B Test:")
    if sg.find_and_initialise():
        log.info("INFO - Found and initialised: {}".format(sg.details()))        
    else:
        log.info("ERROR: could not find & configure signal generator")
        exit()
        
    log.info("INFO - Set frequency to 10 MHz: ")
    if sg.set_frequency_Hz(10e6):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get frequency: {} Hz".format(sg.get_frequency_Hz()))
    
    log.info("INFO - Set output power to -10.0 dBm: ")
    if sg.set_output_power_dBm(-10.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get output power: {} dBm".format(sg.get_output_power_dBm()))
    
    log.info("INFO - Set output enable state to 'on': ")
    if sg.set_output_enable(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get output enable state: {}".format(sg.get_output_enable()))
    
    log.info("INFO - Set frequency to 20 MHz: ")
    if sg.set_frequency_Hz(20e6):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get frequency: {} Hz".format(sg.get_frequency_Hz()))
    
    log.info("INFO - Set output power to -20.0 dBm: ")
    if sg.set_output_power_dBm(-20.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get output power: {} dBm".format(sg.get_output_power_dBm()))
    
    log.info("INFO - Set output enable state to 'off': ")
    if sg.set_output_enable(False):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Get output enable state: {}".format(sg.get_output_enable()))

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()
    
    