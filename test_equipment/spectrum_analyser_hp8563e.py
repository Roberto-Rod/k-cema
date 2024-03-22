#!/usr/bin/env python3
"""
VISA spectrum analyser drivers class for Agilent/Keysight HP8563E devices.
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2023, Kirintec
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Third-party imports -----------------------------------------------
import pyvisa

# stdlib imports -------------------------------------------------------
import logging
import sys

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class SpectrumAnalyserHP8563E:
    def __init__(self, debug=False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sa = None
        self.debug = debug
        log.info("Creating an instance of SpectrumAnalyserHP8563E")

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)


    def __del__(self):
        if self.sa:
            self.sa.close()

    def find_and_initialise(self):
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                try:
                    if self.initialise_device():
                        log.info("INFO - Found and initialised HP8563E Spectrum Analyser: {}".format(self.details()))
                        return True
                    else:
                        self.resource = None
                except:
                    self.resource = None
        log.info("ERROR - did not find an HP8563E Spectrum Analyser")
        return False

    def initialise_device(self):
        try:
            self.sa = self.rm.open_resource(self.resource)            
            # This instrument needs the REN assert
            self.sa.control_ren(pyvisa.constants.VI_GPIB_REN_ASSERT)
            if "HP8563E" in self.details():
                # Set 5 second timeout since Preset takes ~3 seconds
                self.sa.timeout = 5000
                if self.send_command("IP") and self.wait_command_complete():
                    ok = True
                else:
                    ok = False
                    self.sa.close()
            else:
                ok = False
                self.sa.close()
        except:
            if self.sa:
                self.sa.close()
                log.info("ERROR - Could not open resource: {}".format(self.resource))
            else:
                log.info("ERROR - Resource busy: {}".format(self.resource))
            ok = False
        return ok

    def details(self):
        return self.send_query("ID?")

    def resource_name(self):
        return self.resource

    def set_centre_frequency_Hz(self, freq_Hz):
        if self.send_command("CF {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False

    def get_centre_frequency_Hz(self):
        return int(float(self.send_query("CF?").strip()))
    
    def set_span_Hz(self, freq_Hz):
        if self.send_command("SP {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_span_Hz(self):
        return int(float(self.send_query("SP?").strip()))
    
    def set_resolution_BW_Hz(self, freq_Hz):
        if self.send_command("RB {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_resolution_BW_Hz(self):
        return int(float(self.send_query("RB?").strip()))
    
    def set_reference_level_dBm(self, level_dBm):
        if self.send_command("RL {:.2f} DB".format(level_dBm)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_reference_level_dBm(self):
        return float(self.send_query("RL?").strip())
    
    def set_dB_per_division(self, division_dB):
        if self.send_command("LG {:.2f} DB".format(division_dB)):
            return self.wait_command_complete()
        else:
            return False

    def get_dB_per_division(self):
        return float(self.send_query("LG?").strip())
    
    def set_continuous_sweep(self, continuous):
        if self.send_command("CONTS" if continuous else "SNGLS"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_peak_Hz_dBm(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("MKF?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("MKA?").strip())
            return freq_Hz, ampl_dBm
        else:
            return 0, -999.0

    def get_peak_amplitude_dBm(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("MKA?").strip())
            return ampl_dBm
        else:
            return -999.0

    def get_peak_frequency_Hz(self):
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("MKF?").strip()))
            return freq_Hz
        else:
            return 0

    last_freq_Hz = 0
    def get_next_peak_Hz_dBm(self):
        # Perform the next peak search
        if self.marker_find_next_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("MKF?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("MKA?").strip())
            valid = freq_Hz != self.last_freq_Hz
            # Remember the last marker frequency
            self.last_freq_Hz = freq_Hz
            return freq_Hz, ampl_dBm, valid
        else:
            return 0, -999.0, False

    def set_attenuation_mode(self, auto):
        if self.send_command("AT {}".format("AUTO" if auto else "MAN")):
            return self.wait_command_complete()
        else:
            return False

    def set_attenuation_dB(self, atten_dB):
        if self.send_command("AT {:.2f} DB".format(atten_dB)):
            return self.wait_command_complete()
        else:
            return False

    def set_video_average_mode(self, enabled):
        if self.send_command("VAVG {}".format("ON" if enabled else "OFF")):
            return self.wait_command_complete()
        else:
            return False

    def set_video_average_sweeps(self, sweeps):
        # Number of sweeps must be between 1 and 999
        if sweeps >= 1 and sweeps <= 999:
            if self.send_command("VAVG {:.0f}".format(sweeps)):
                return self.wait_command_complete()
            else:
                return False
        else:
                return False

    def set_marker_noise_mode(self, enabled):
        if self.send_command("MKNOISE {}".format("ON" if enabled else "OFF")):
            return self.wait_command_complete()
        else:
            return False

    def get_amplitude_dBm(self, freq_Hz):
        # Set the marker frequency first
        if self.send_command("MKF {:.0f} HZ".format(freq_Hz)) and self.wait_command_complete():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("MKA?").strip())
            return ampl_dBm
        else:
            return -999.0

    def set_peak_excursion_dB(self, excursion_dB):
        if self.send_command("MKPX {:.2f} DB".format(excursion_dB)):
            return self.wait_command_complete()
        else:
            return False
        
    def set_peak_threshold_dBm(self, threshold_dBm):
        if self.send_command("MKPT {:.2f} DBM".format(threshold_dBm)):
            return self.wait_command_complete()
        else:
            return False

    def set_max_hold_mode(self, enabled):
        if self.send_command("MXMH TRA" if enabled else "CLRW TRA"):
            return self.wait_command_complete()
        else:
            return False
        
    def marker_find_peak(self):
        # Trigger a sweep
        if self.send_command("TS") and self.wait_command_complete():
            # Set marker 1 to peak
            if self.send_command("MKPK HI") and self.wait_command_complete():
                return True
            else:
                return False
        else:
            return False
    
    def marker_find_next_peak(self):
        # Set marker 1 to next peak
        if self.send_command("MKPK NH") and self.wait_command_complete():
            return True
        else:
            return False

    def wait_command_complete(self):
        resp = self.send_query("DONE?").strip()
        # The DONE command sends a "1" to the controller when all commands
        # in a command string entered before DONE have been completed
        return bool(resp == "1")

    def send_command(self, cmd):
        if self.debug:
            log.info("INFO - send_command: {}".format(cmd))
        try:
            self.sa.write(cmd)
            return True
        except:
            log.info("ERROR - could not send command")
            return False

    def send_query(self, query):
        if self.debug:
            log.info("INFO - send_query: {}".format(query))
        try:
            return self.sa.query(query).strip()
        except:
            log.info("ERROR - could not send query")
        return False

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    log.info("INFO - Module is NOT intended to be executed stand-alone")

def test():
    sa = SpectrumAnalyserHP8563E(debug=False)
    log.info("INFO - SpectrumAnalyserHP8563E Test:")
    if sa.find_and_initialise():
        log.info("INFO - Found and initialised: {}".format(sa.details()))
    else:
        log.info("ERROR - could not find & configure spectrum analyser")
        exit()

    log.info("INFO - Set centre frequency to 1 GHz: ")
    if sa.set_centre_frequency_Hz(1e9):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get centre frequency: {} Hz".format(sa.get_centre_frequency_Hz()))

    log.info("INFO - Set span to 10 MHz: ")
    if sa.set_span_Hz(10e6):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get span: {} Hz".format(sa.get_span_Hz()))

    log.info("INFO - Set resolution bandwidth to 10 kHz: ")
    if sa.set_resolution_BW_Hz(10e3):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get resolution bandwidth: {} Hz".format(sa.get_resolution_BW_Hz()))

    log.info("INFO - Set reference level to 10.0 dBm: ")
    if sa.set_reference_level_dBm(10.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get reference level: {} dBm".format(sa.get_reference_level_dBm()))

    log.info("INFO - Set dB per division to 10.0 dB: ")
    if sa.set_dB_per_division(10.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get dB per division: {} dB".format(sa.get_dB_per_division()))

    log.info("INFO - Set continous sweep (on): ")
    if sa.set_continuous_sweep(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Set peak excursion to 5 dB: ")
    if sa.set_peak_excursion_dB(5.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Set peak threshold to -65 dBm: ")
    if sa.set_peak_threshold_dBm(-65.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Get peak: {0[0]} Hz, {0[1]} dBm".format(sa.get_peak_Hz_dBm()))

    log.info("INFO - Get peak amplitude: {} dBm".format(sa.get_peak_amplitude_dBm()))

    log.info("INFO - Get peak frequency: {} Hz".format(sa.get_peak_frequency_Hz()))

    log.info("INFO - Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
    log.info("Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
    log.info("INFO - Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
        
    log.info("INFO - Get amplitude at 1 GHz: {} dBm".format(sa.get_amplitude_dBm(1e9)))

    log.info("INFO - Set attenuation to 10 dB: ")
    if sa.set_attenuation_dB(10.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Set video average mode (on): ")
    if sa.set_video_average_mode(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Set video averaging to 10 sweeps: ")
    if sa.set_video_average_sweeps(10):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Set marker noise mode (on): ")
    if sa.set_marker_noise_mode(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()    

    log.info("INFO - Set max hold mode (on): ")
    if sa.set_max_hold_mode(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """ This module is NOT intended to be executed stand-alone """

    main()
    test()
    