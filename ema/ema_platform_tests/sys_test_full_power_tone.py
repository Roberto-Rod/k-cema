#!/usr/bin/env python3
from synth import *
from dds import *
from rf_control import *
from band import *
from ipam import *
from hardware_unit_config import *
from serial_number import *
from enum import Enum

import os
import csv
import argparse
import math


# Class provided to generate a full power CW tone at the frequency passed in as command line argument
# IMPORTANT: assumes the EMA has been initialised first by running initialise.py
# Also the IPAM mute control is deliberately not done in here, use IPAMMute.py for this
class SysTestFullPowerTone:
    CAL_DIR_NAME = "/run/media/mmcblk0p2/calibration/"
    CAL_FILE_NAME = "pa_cal.csv"
    
    band_name = {}
    band_name[Band.LOW] = "low"
    band_name[Band.MID] = "mid"
    band_name[Band.HIGH] = "high"
    
    FREQ_BANDS = [
#    Band,     Path, Start Freq., Stop Freq.
#                          (MHz)       (MHz)
    [Band.LOW,    0,          20,        520],
#
    [Band.MID,    0,         400,       1500],
    [Band.MID,    1,        1480,       1880],
    [Band.MID,    2,        1850,       2250],
    [Band.MID,    3,        2250,       2500],
    [Band.MID,    4,        2500,       2700],
#
    [Band.HIGH,   0,        1800,       1880],  # MB 1 (1)
    [Band.HIGH,   1,        1850,       2250],  # MB 2 (2)
    [Band.HIGH,   2,        2250,       2500],  # MB 3 (3)
    [Band.HIGH,   3,        2400,       3400],  # HB 1 (9)
    [Band.HIGH,   4,        3400,       4600],  # HB 2 (10)
    [Band.HIGH,   5,        4600,       6000],  # HB 3 (11)

    [Band.EXT_HIGH, 6,      5700,       8000],
]
    
    def set_tone(self, frequency_Hz):
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Configuring EMA-{} for {} Hz at full power...".format(serial, frequency_Hz))
        
        # Get IPAM band
        band = IPAM.get_rf_band()
        if band == Band.UNKNOWN:
            error_msg = ": IPAM band is unknown"
            return False, error_msg

        # Determine if IPAM is eHB type
        ipam_ehb = False
        if band == Band.HIGH:
            if IPAM.is_extended_high_band():
                ipam_ehb = True
                print("IPAM: eHB")

        # Determine if NTM is eHB type
        ntm_ehb = False
        status, config = get_config_info(AssemblyType.EMA_LB_R)
        if status:
            try:
                if "Assembly Part Number" in config.keys():
                    assy_nr = config["Assembly Part Number"]
                    if assy_nr.startswith("KT-950-0505"):
                        print("NTM: eHB")
                        ntm_ehb = True
            except Exception:
                error_msg = ": could not get Assembly Part Number"
                return False, error_msg
        
        # Get the Tx path from the table
        found = False
        for freq_band in self.FREQ_BANDS:
            # Find the right IPAM band first            
            if freq_band[0] == band or (freq_band[0] == Band.EXT_HIGH and ipam_ehb and ntm_ehb):
                # Now find the first Tx path that brackets the requested frequency
                # (There is a known limitation with this where two bands overlap the requested frequency)
                freq_MHz = frequency_Hz / 1e6
                if freq_MHz >= freq_band[2] and freq_MHz <= freq_band[3]:
                    path = freq_band[1]
                    found = True
                    break
        if not found:
            error_msg = ": requested frequency is invalid"      
            return False, error_msg     

        # Set the attenuator to a safe state before updating frequency
        self.set_att_dB(63.75, band)

        # Set the IPAM port
        port = IPAM.PA_PORT_PRI
        if path == 6:
            port = IPAM.PA_PORT_EXT
        if not IPAM.set_pa_port(port):
            error_msg = ": could not set PA port"
            return False, error_msg

        # Get the PA cal (att) setting
        get_att_dB = self.get_calibrated_att(self.band_name[band], path, frequency_Hz)
        if get_att_dB[1]:
            att_dB = get_att_dB[0]
        else:
            error_msg = ": Calibration Point for the requested frequency was not found]"     
            return False, error_msg  
        
        # Set the DDS frequency
        d = DDS()
        dds_freq_Hz = frequency_Hz / RFControl.get_multiplier(path, band, ntm_ehb)
        d.set_frequency(dds_freq_Hz)
        
        # Set ASF to calibrated DDS output for mid/high band
        if band == Band.MID or band == band.HIGH:
            asf = d.get_calibrated_asf(dds_freq_Hz)
            d.set_asf(asf, True)
            RFControl.set_tx_path(path, band, ntm_ehb)

        self.set_att_dB(att_dB, band)
        
        # If we got this far then everything worked    
        return True, error_msg

    def set_att_dB(self, att_dB, band):
        # Set attenuation, for low band set DDS ASF, for mid/high-band
        # set post-doubler/multiplier attenuator
        if band == Band.LOW:
            d = DDS()
            d.set_att_dB(att_dB, True)
        else:
            RFControl.set_doubler_att(att_dB)

    def get_calibrated_att(self, band_name, path, frequency_Hz):
        att = 63.75
        with open(self.CAL_DIR_NAME + self.CAL_FILE_NAME, mode = 'r') as csv_file:
            # Discard first two rows
            for i in range(2):
                csv_file.readline()
            
            # Next row contains the band
            # Validate the cal file band against what has been requested
            row_band = next(csv_file)
            if band_name not in str(row_band.split(",")[1]):
                return att, False          
            # Discard next 4 rows
            for i in range(4):
                csv_file.readline()            
            csv_reader = csv.reader(csv_file)
            n = 0
            for row in csv_reader:
                if float(row[0]) == path:
                    if n == 0:
                        freq1 = float(row[1])
                        cal1 = float(row[3])
                        freq2 = freq1
                        cal2 = cal1
                    else:
                        if float(row[1]) >= float(frequency_Hz):
                            freq2 = float(row[1])
                            cal2 = float(row[3])
                            break
                        freq1 = float(row[1])
                        cal1 = float(row[3])
                    n += 1            
            
            # No data was found
            if n == 0:
                #print(att, "not found")
                return att, False
            
            # Frequency point was not found within the cal table
            elif freq1 > float(frequency_Hz) or float(frequency_Hz) > freq2:
                #print(att, "not found")
                return att, False
            
            # Otherwise get the att value by interpolation
            else:
                r = (float(frequency_Hz) - freq1) / (freq2 - freq1)
                cal = (r * (cal2 - cal1)) + cal1
                
                # Convert cal value back to an attenuation value needed by the "set atten" methods
                att = round((cal / 4), 2)
            
            #print(att, "found")
            return att, True


if __name__ == "__main__":
    o = SysTestFullPowerTone()
    parser = argparse.ArgumentParser(description = "Generate a full power CW tone")
    parser.add_argument("frequency", help="frequency in Hz", type=int, default="20000000")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_tone(args.frequency)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")