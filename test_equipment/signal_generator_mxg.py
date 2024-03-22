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

# stdlib imports -------------------------------------------------------
import logging
import sys, io

# Third-party imports -----------------------------------------------
import pyvisa
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

class SignalGeneratorMXG():
    def __init__(self, debug = False):
        super().__init__()
        log.info("INFO - Instanciating MXG Signal Generator Class!")
        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)
        
    def find_and_initialise(self, debug = False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sg = None
        self.debug = debug
        self.binding_success = False
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                if self.initialise_device():
                    log.info("INFO - Found MXG/EXG Signal Generator: {}".format(res))
                    log.info("INFO - Device initialised: OK")
                    return True
                else:
                    self.resource = None
        return False
             
    def initialise_device(self):
        try:
            self.sg = self.rm.open_resource(self.resource)            
            # Searching for Sig Gen by ID string as Resource Name varies depending on physical connection type
            details = self.details()
            if "N5181A" in details or "N5173B" in details:
            # if "SDG1020" in details or "N5173B" in details:
                if self.send_command("*RST"):
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

    def __del__(self):
        if self.sg:
            self.sg.close()     
        
    def details(self):
        return self.send_query("*IDN?")   
    
    def set_frequency_Hz(self, freq_Hz):
        self.send_command("FREQ {:.0f} HZ".format(freq_Hz))
        return self.wait_command_complete()   
    
    def get_frequency_Hz(self):
        return int(float(self.send_query("FREQ:CW?").split("\n")[0]))
        
    def set_output_power_dBm(self, power_dBm):
        self.send_command("POW:AMPL {:.2f} DBM".format(power_dBm))
        return self.wait_command_complete()
        
    def get_output_power_dBm(self):
        """
        Return the output power with dBm resolution.
        :return power_dbm: output power in dBm :type Float
        """
        return float(self.send_query("POW:AMPL?").split("\n")[0])
       
    def set_output_enable(self, enable_state):
        self.send_command("OUTP ON" if enable_state else "OUTP OFF")
        return self.wait_command_complete()
    
   
    def get_output_enable(self):
        resp = self.send_query("OUTP?").split("\n")[0]
        return bool(resp == "1")
      
    def wait_command_complete(self):
        resp = self.send_query("*OPC?").split("\n")[0]
        return bool(resp == "1")
    
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
            log.info("send_query: {}".format(query))
        #try:
        return self.sg.query(query)
        #except:
        #    log.info("ERROR - could not send query")
        #return False

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    sg = SignalGeneratorMXG()
    log.info("INFO - SignalGeneratorMXG Test:")
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
    
    log.info("INFO - Set output power to -50.0 dBm: ")
    if sg.set_output_power_dBm(-50.0):
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
    
    log.info("INFO - Set output power to -60.0 dBm: ")
    if sg.set_output_power_dBm(-60.0):
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
    