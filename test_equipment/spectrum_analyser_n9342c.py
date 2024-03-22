#!/usr/bin/env python3
"""
VISA spectrum analyser drivers class for Agilent/Keysight N9342C devices.
Device datasheet: K:\Engineering\Project Files\Project_K-CEMA\Reference\Test Equipment Datasheets\Agilent-Keysight\Agilent N9342C Programming Guide.pdf
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
import sys, io

from enum import Enum

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

class DbPerDiv(Enum):
    UNKNOWN = 0
    DIV1    = 1       # 1 dB per division
    DIV2    = 2       # 2 dB per division
    DIV5    = 5       # 5 dB per division
    DIV10   = 10      # 10 dB per division

class SpectrumAnalyserN9342C:
    def __init__(self, debug=False):
        self.rm = pyvisa.ResourceManager()
        self.resource = None
        self.sa = None
        self.debug = debug
        self.binding_success = False
        log.info("INFO - Creating an instance of SpectrumAnalyserN9342C")

        # Set logging level to INFO initially
        self._logging_fmt = "%(asctime)s: %(message)s"
        self._logging_level = logging.INFO
        logging.basicConfig(format=self._logging_fmt, datefmt="%H:%M:%S", stream=sys.stdout, level=self._logging_level)

    def __del__(self):
        if self.sa:
            self.sa.close()

    def find_and_initialise(self):
        """
        Finds connected devices and attempts to initialize them by calling the initialise_device function.
        :return: True if successfull, else False
        """
        self.resource = None
        for res in self.rm.list_resources():
            if res:
                self.resource = res
                try:
                    if self.initialise_device():
                        log.info("INFO - Found and initialised N9342C Spectrum Analyser: {}".format(self.details()))
                        return True
                    else:
                        self.resource = None
                except:
                    self.resource = None
        log.info("ERROR: did not find a N9342C Spectrum Analyser")
        return False

    def initialise_device(self):
        """
        Initializes the N9342C Spectrum Analyser.
        :return: True if successfull, else False
        """
        try:
            self.sa = self.rm.open_resource(self.resource)            
            str = self.details()
            if "N9342C" in self.details():
                # Set 5 second timeout since Preset takes ~3 seconds
                self.sa.timeout = 5000
                if self.send_command("*RST") and self.wait_command_complete():
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
                log.info("INFO - Could not open resource: {}".format(self.resource))
            else:
                log.info("INFO - Resource busy: {}".format(self.resource))
            ok = False
        return ok

    def details(self):
        """
        Sends a query requesting device details.
        :return: Device details: Type: String
        """
        return self.send_query("*IDN?")

    def resource_name(self):
        """
        Gets the device name.
        :return: Device name: Type: String
        """
        return self.resource

    def set_centre_frequency_Hz(self, freq_Hz):
        """
        Set the spectrum analyser's centre frequency with Hz resolution.
        :param freq_hz: required centre frequency in Hz :type Integer or Float 
        :return: True if successfull, else False
        """
        if self.send_command("FREQ:CENT {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False

    def get_centre_frequency_Hz(self):
        """
        Get the spectrum analyser's centre frequency with Hz resolution.
        :return centre frequency with Hz resolution :type Integer
        """
        return int(float(self.send_query("FREQ:CENT?").strip()))
    
    def set_span_Hz(self, freq_Hz):
        """
        Set the spectrum analyser's frequency span with Hz resolution.
        :param span_hz: required frequency span in Hz :type Integer or Float
        :return: True if successfull, else False
        """
        if self.send_command("FREQ:SPAN {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_span_Hz(self):
        """
        Get the spectrum analyser's frequency span with Hz resolution.
        :return frequency span with Hz resolution :type Integer
        """
        return int(float(self.send_query("FREQ:SPAN?").strip()))
    
    def set_resolution_BW_Hz(self, freq_Hz):
        """
        Set the spectrum analyser's resolution bandwidth with Hz resolution.
        :param res_bw_hz: required resolution bandwidth in Hz :type Integer or Float 
        :return: True if successfull, else False
        """
        if self.send_command("BAND:RES {:.0f} HZ".format(freq_Hz)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_resolution_BW_Hz(self):
        """
        Get the spectrum analyser's resolution bandwidthwith Hz resolution.
        :return resolution bandwidth with Hz resolution :type Integer
        """
        return int(float(self.send_query("BAND:RES?").strip()))
    
    def set_reference_level_dBm(self, level_dBm):
        """
        Set the spectrum analyser's reference level with dBm resolution.
        :param ref_level_dbm: required reference level in dBm :type Integer or Float
        :return: True if successfull, else False
        """
        if self.send_command("DISP:WIND:TRAC:Y:RLEV {:.2f} DBM".format(level_dBm)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_reference_level_dBm(self):  
        """
        Get the spectrum analyser's reference level with dBm resolution.
        :return reference level in dBm :type Float
        """
        return float(self.send_query("DISP:WIND:TRAC:Y:RLEV?"))
    
    def set_dB_per_division(self, dB_per_div):
        """
        Set the spectrum analyser's vertical scale (dB/div).
        :param dB_per_div: type Integer: Options are: 1=DIV1; 2=DIV2; 5=DIV5; 10=DIV10
        :return: True if successfull, else False
        """
        if self.send_command("DISP:WIND:TRAC:Y:PDIVision {}".format(DbPerDiv(dB_per_div).name)):
            return self.wait_command_complete()
        else:
            return False
    
    def set_max_hold_mode(self, enabled):
        """
        Sets the display mode for trace 1 to either the Maximum Hold, or to Write
        param enabled: Type: Boolean
        :return: True if successfull, else False
        """
        if self.send_command("TRAC1:MODE MAXH" if enabled else "TRAC1:MODE WRIT"):
            return self.wait_command_complete()
        else:
            return False

    def get_dB_per_division(self): 
        """
        Get the spectrum analyser's vertical scale (dB/div).
        :return enumerated DbPerDiv value :type Integer
        """
        resp = self.send_query(":DISP:WIND:TRAC:Y:PDIV?").strip()
        return int((DbPerDiv[resp].value))
    
    def set_continuous_sweep(self, continuous):
        """
        Enable/disable the spectrum analyser's continuous sweep.
        :param continuous: True to enable continuous sweep, False to disable :type Boolean
        :return: True if successfull, else False
        """
        if self.send_command("INIT:CONT ON" if continuous else "INIT:CONT OFF"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_peak_Hz_dBm(self):
        """
        Get the peak marker reading.

        Executes marker->peak and returns the marker frequency and power readings.
        :return: [0] freq_hz :type Integer
                 [1] ampl_dBm :type Float
        """
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return freq_Hz, ampl_dBm
        else:
            return 0, -999.0

    def get_peak_amplitude_dBm(self):
        """
        Get the amplitude peak marker reading. Executes marker->peak and returns the marker frequency and power readings.
        :return: ampl_dBm :type Float
        """
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return ampl_dBm
        else:
            return -999.0

    def get_peak_frequency_Hz(self):
        """
        Get the frequency peak marker reading. Executes marker->peak and returns the marker frequency and power readings.
        :return: freq_hz :type Integer
        """
        # Perform the peak search       
        if self.marker_find_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            return freq_Hz
        else:
            return 0

    last_freq_Hz = 0
    def get_next_peak_Hz_dBm(self):
        """
        Get the next peak marker reading.
        Executes marker->next peak and returns the marker frequency and amplitude readings.
        :return: [0] freq_hz :type Integer
                 [1] power_dbm :type Float
                 [3] valid: type Boolean
        """
        # Perform the next peak search
        if self.marker_find_next_peak():
            # Read the marker frequency
            freq_Hz = int(float(self.send_query("CALC:MARK1:X?").strip()))
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            valid = freq_Hz != self.last_freq_Hz
            # Remember the last marker frequency
            self.last_freq_Hz = freq_Hz
            return freq_Hz, ampl_dBm, valid
        else:
            return 0, -999.0, False

    def set_attenuation_mode(self, auto):
        """
        Select the input port attenuator range to be set either automatically (ON) or manually (OFF).
        :param auto: True to enable continuous AUTO, False to disable :type Boolean
        :return: True if successfull, else False
        """
        if self.send_command("POW:ATT:AUTO ON" if auto else "POW:ATT:AUTO OFF"):
            return self.wait_command_complete()
        else:
            return False
    
    def get_amplitude_dBm(self, freq_Hz):
        """
        Gets the amplitude in dBm for a given frequency marker
        :param freq_Hz: Frequency marker value in Hz
        :return: ampl_dBm: Value of amplitude marker: Type: Float
        """
        # Set the marker frequency first
        if self.send_command("CALC:MARK1:X {:.0f} HZ".format(freq_Hz)) and self.wait_command_complete():
            # Read the marker amplitude
            ampl_dBm = float(self.send_query("CALC:MARK1:Y?").strip())
            return ampl_dBm
        else:
            return -999.0

    def set_attenuation_dB(self, atten_dB):
        """
        Set the input attenuator level in dB
        :param atten_dB: Attenuator value: Range 0 to 50 dB: Type: Integer
        :return: True if successfull, else False
        """
        if self.send_command("POW:ATT {:.2f} DB".format(atten_dB)):
            return self.wait_command_complete()
        else:
            return False
        
    def marker_find_peak(self):  
        """
        Trigger a sweep and then set marker 1 to the peak.
        :return: True if successful, else False
        """      
        # Trigger a sweep
        if self.send_command("INIT:IMM") and self.wait_command_complete():
            # Set marker 1 to peak
            if self.send_command("CALC:MARK1:MAX") and self.wait_command_complete():
                return True
            else:
                return False
        else:
            return False
    
    def marker_find_next_peak(self):
        """
        Send the next peak command marker search command.
        :return: True if successful, else False
        """
        # Set marker 1 to next peak
        if self.send_command("CALC:MARK1:MAX:NEXT") and self.wait_command_complete():
            return True
        else:
            return False
    
    def set_peak_excursion_dB(self, excursion_dB):
        """
        Sets the peak excursion value in dB
        :param excursion_dB: Type: Float
        :return: True if successfull, else False
        """
        if self.send_command("CALC:MARK:PEAK:EXC {:.1f}".format(excursion_dB)):
            return self.wait_command_complete()
        else:
            return False
    
    def set_peak_threshold_dBm(self, threshold_dBm):
        """
        Sets the peak threshold value in dB
        :param threshold_dBm: Type: Float
        :return: True if successfull, else False
        """
        if self.send_command("CALC:MARK:PEAK:THR {:.1f}".format(threshold_dBm)):
            return self.wait_command_complete()
        else:
            return False

    # I am unsure if this meets the intent of of the original named function, or is related to video
    def set_video_average_mode(self, enabled):
        """
        This command toggles averaging off and on. Averaging combines
        the value of successive measurements to average out measurement variations.
        Note: See device datasheet page 74
        :param enabled: Type: Boolean
        :return: True if successful, else False
        """
        if enabled:
            self.send_command("AVER:TRAC1:STAT ON")
            return True
        else:
            self.send_command("AVER:TRAC1:STAT OFF")
            return self.wait_command_complete()

    # I am unsure if this meets the intent of of the original named function, or is related to video
    def set_video_average_sweeps(self, sweeps):
        """
        Specifies the number of measurements that are combined. 
        Note: See device datasheet page 74
        :param sweeps: Type: Integer
        :return: True if successful, else False
        """
        # Number of sweeps must be between 1 and 8192, reset value is 100
        if sweeps >= 1 and sweeps <= 8192:
            if self.send_command("AVER:TRAC1:COUN {:.0f}".format(sweeps)):
                return True
            else:
                return False
        else:
            log.info("ERROR - Invalid number of sweeps selected. Please select a number between 1 and 8192!")
            return False
    
    def set_video_bandwidth_freq(self, vd_bw_frequency):
        """
        Specifies the video bandwidth frequency.
        :param vd_bw_frequency: Type Integer: Range: 1 Hz to 3 MHz
        :return: True if successful, else False
        """
        if self.send_command("BWID:VID {:.0f}".format(vd_bw_frequency)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_video_bandwidth_freq(self):
        """
        Gets the video bandwidth frequency.
        :return video bandwidth frequency: Type: Integer
        """
        return int(float(self.send_query("BWID:VID?").strip()))

    def set_video_auto_mode(self, enable):
        """
        Sets the video auto mode enabled/disabled. Couples the video bandwidth to the resolution bandwidth when enabled.
        :param enable: Type Boolean
        :return: True if successful, else False
        """
        if enable:
            self.send_command("BWID:VID:AUTO ON")
            return self.wait_command_complete()
        else:
            self.send_command("BWID:VID:AUTO OFF")
            return self.wait_command_complete()

    def set_video_resolution_to_bandwidth_ratio(self, vd_bw_freq_ratio):
        """"
        Specifies the ratio of the video bandwidth to the resolution bandwidth.
        :param vd_bw_freq_ratio: Type Float: Range: 0.001 to 1.0e3 
        :return: True if successful, else False
        """
        if self.send_command("BWID:VID:RAT {:.3f}".format(vd_bw_freq_ratio)):
            return self.wait_command_complete()
        else:
            return False
    
    def get_video_resolution_to_bandwidth_ratio(self):
        """
        Gets the ratio of the video bandwidth to the resolution bandwidth.
        :return ratio of the video bandwidth to the resolution bandwidth: Type: Float
        :return: True if successful, else False
        """
        return int(float(self.send_query("BWID:VID:RAT?").strip()))

    def set_video_res_to_bandw_ratio_auto_mode(self, enable):
        """"
        Selects auto or manual mode for video bandwidth to resolution bandwidth ratio.
        :param enable: Type Boolean
        :return: True if successful, else False
        """
        if enable:
            self.send_command("BWID:VID:RAT:AUTO ON")
            return self.wait_command_complete()
        else:
            self.send_command("BWID:VID:RAT:AUTO OFF")
            return self.wait_command_complete()

    def set_marker_noise_mode(self, mk_noise_mode):
        """
        Sets the marker function for marker 1.
        :param mk_noise_mode: Type: True for noise mode, False for normal function (OFF), or Type: String FCO for frequency counter
        :return: True if successful, else False
        """
        if str(mk_noise_mode) == "True":
            self.send_command("CALC:MARK1:FUNC {}".format("NOIS"))
            return self.wait_command_complete()
        elif str(mk_noise_mode) == "False":
            self.send_command("CALC:MARK1:FUNC {}".format("OFF"))
            return self.wait_command_complete()
        elif mk_noise_mode == "FCO":
            self.send_command("CALC:MARK1:FUNC {}".format("FCO"))
            return self.wait_command_complete()
        else:
            log.info("ERROR - Invalid selection of marker function.")
            return False

    def wait_command_complete(self):
        """
        Sends a query to the device and reads the response
        :return: True if successful, else False
        """
        resp = self.send_query("*OPC?").strip()
        return bool(resp == "1" or resp == "+1")

    def send_command(self, cmd):
        """
        Sends a command to the device
        :param cmd: Command to be sent: Type: String
        :return: True if successful, else False
        """
        if self.debug:
            log.info("INFO - send_command: {}".format(cmd))
        try:
            self.sa.write(cmd)
            return True
        except:
            log.info("ERROR - could not send command")
            return False

    def send_query(self, query):
        """
        Sends a query to the device and reads the response
        :param query: Query to be sent: Type: String
        :return: The device response if query is successful, else False
        """
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
    sa = SpectrumAnalyserN9342C(debug=False)
    log.info("INFO - SpectrumAnalyserN9342C Test:")
    if sa.find_and_initialise():
        log.info("INFO - Found and initialised: {}".format(sa.details()))
    else:
        log.info("ERROR: could not find & configure spectrum analyser")
        exit()

    log.info("INFO - Set centre frequency to 1 GHz: ")
    if sa.set_centre_frequency_Hz(3.33e9):
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

    log.info("INFO - Set dB per division to 10 dB/div: ")
    if sa.set_dB_per_division(10):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
        
    log.info("INFO - Get dB per division: {} dB/div".format(sa.get_dB_per_division()))

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
    log.info("INFO - Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
    log.info("INFO - Get next peak: {0[0]} Hz, {0[1]} dBm, {0[2]}".format(sa.get_next_peak_Hz_dBm()))
        
    log.info("INFO - Get amplitude at 1 GHz: {} dBm".format(sa.get_amplitude_dBm(1e9)))

    log.info("INFO - Set attenuation to 10 dB: ")
    if sa.set_attenuation_dB(10.0):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Set video bandwidth frequency to 3 MHz: ")
    if sa.set_video_bandwidth_freq(3e6):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Get video bandwidth frequency: {} Hz".format(sa.get_video_bandwidth_freq()))

    log.info("INFO - Set the ratio of the video bandwidth to the resolution bandwidth to 1 KHz: ")
    if sa.set_video_resolution_to_bandwidth_ratio(1e3):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()
    
    log.info("INFO - Get the ratio of the video bandwidth to the resolution bandwidth: {} Hz".format(sa.get_video_resolution_to_bandwidth_ratio()))
    
    log.info("Selecting auto mode for video bandwidth to resolution bandwidth ratio (on): ")
    if sa.set_video_res_to_bandw_ratio_auto_mode(True):
        log.info("OK")
    else:
        log.info("ERROR")
        exit()

    log.info("INFO - Set video auto mode (on): ")
    if sa.set_video_auto_mode(True):
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

    log.info("INFO - Set video average mode (off): ")
    if sa.set_video_average_mode("OFF"):
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
    