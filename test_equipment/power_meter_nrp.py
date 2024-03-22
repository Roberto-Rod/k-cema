#!/usr/bin/env python3
"""
ROHDE & SCHWARZ NRP Power Meter Class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec+
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
import sys, math

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

class PowerMeterNRP:
    """
    Class for the  ROHDE & SCHWARZ power meters, currently supporting NRP18S and NRP-Z21
    """
    def __init__(self, debug = False):
        """
        Class constructor
        :param debug: Debug flag : Type Boolean
        """
        super().__init__()
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.pm = None
        self.debug = debug
        self.binding_success = False

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def find_and_initialise(self):
        self.resource = None

        for res in self.rm.list_resources():
            if res:
                self.resource = res
                if self.initialise_device():
                    log.info("INFO - Found NRP Power Meter: {}".format(res))
                    log.info("INFO - Device initialised: OK")
                    return True
                else:
                    self.resource = None
        return False
        
          
    def initialise_device(self):
        try:
            self.pm = self.rm.open_resource(self.resource)
        except:
            if self.pm:
                self.pm.close()
                log.info("ERROR - Could not open resource: {}".format(self.resource))
            else:
                log.info("ERROR - Resource busy: {}".format(self.resource))
            return False
            
        ok = True
        ok = ok and self.send_command("*RST")
        ok = ok and self.send_command("INIT:CONT OFF")
        ok = ok and self.send_command("SENS:FUNC \"POW:AVG\"")
        ok = ok and self.send_command("SENS:FREQ 1000000000")      # Default to 1GHz
        ok = ok and self.send_command("SENS:AVER:COUN:AUTO OFF")
        ok = ok and self.send_command("SENS:AVER:COUN 16")
        ok = ok and self.send_command("SENS:AVER:STAT ON")
        ok = ok and self.send_command("SENS:AVER:TCON REP")
        ok = ok and self.send_command("SENS:POW:AVG:APER 5e-3")
        ok = ok and self.send_command("FORMAT ASCII")
        return ok

    def __del__(self):
        if self.pm:
            self.pm.close()
        
    def details(self):
        return self.send_query("*IDN?")
           
    def zero(self):
        return self.send_command("CAL:ZERO:AUTO ONCE")
        
    def set_offset(self, offset):
        ok = True
        if offset == 0:
            ok = ok and self.send_command("SENS:CORR:OFFS:STAT OFF")
        else:
            ok = ok and self.send_command("SENS:CORR:OFFS {:.1f}".format(offset))
            ok = ok and self.send_command("SENS:CORR:OFFS:STAT ON")
        return ok
      
    def set_average_count(self, count):
        return self.send_command("SENS:AVER:COUN {}".format(int(count)))
      
    def get_reading_dBm(self):
        ret_val = -999
        for i in range(5):
            if self.send_command("INIT:IMM"):
                # pyvisa appears to not support sending the query "STAT:OPER:COND?" (raises exception)
                # sleeping here does not change the reading, there is a short delay before FETCH? responds
                # and this delay is longer if the number of averages is increased, so wait for completion not required
                try:
                    reading = abs(float(self.send_query("FETCH?").split(",")[0]))
                except pyvisa.errors.VisaIOError:
                    continue
                if reading > 0:
                    ret_val = (10 * math.log10(abs(reading))) + 30
                    break
        return ret_val

    def set_frequency_Hz(self, freq_Hz):
        return self.send_command("SENS:FREQ {:.0f}".format(freq_Hz))

    def send_command(self, cmd):
        if self.debug:
            log.info("INFO - send_command: {}".format(cmd))
        try:            
            self.pm.write(cmd)
            return True
        except:
            log.info("ERROR - could not send command")
            return False
       
    def send_query(self, query):
        if self.debug:
            log.info("INFO - send_query: {}".format(query))
        # try:
        return self.pm.query(query)
        # except:
        #     log.info("ERROR - could not send query")
        #     return False

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    pm = PowerMeterNRP()
    log.info("PowerMeterNRP Test:")
    if pm.find_and_initialise():
        log.info("INFO - Found and initialised: {}".format(pm.details()))        
    else:
        log.info("ERROR: could not find & configure power meter")
        exit()
       
    log.info("INFO - Set averages: ")
    if pm.set_average_count(8):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Zero power meter: ")
    if pm.zero():
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Set offset to 0 dB: ")
    if pm.set_offset(0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Set offset to 10 dB: ")
    if pm.set_offset(10):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Set offset to 30.5 dB: ")
    if pm.set_offset(30.5):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Set frequency to 10 MHz: ")
    if pm.set_frequency_Hz(10e6):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
  
    log.info("INFO - Set frequency to 1 GHz: ")
    if pm.set_frequency_Hz(1e9):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
   
    log.info("INFO - Get reading: {}".format(pm.get_reading_dBm()))

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """ This module is NOT intended to be executed stand-alone """
    main()
    test()
    