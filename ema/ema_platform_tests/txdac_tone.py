#!/usr/bin/env python3
from power_supplies import *
from synth import *
from dds import *
from adf4355 import *
from ad9162 import *
from rf_control import *
from band import *
from ipam import *
from enum import Enum

import os
import csv
import argparse
import math


# Class provided to generate a full power CW tone at the frequency passed in as command line argument
# IMPORTANT: assumes the EMA has been initialised first by running initialise.py
# Also the IPAM mute control is deliberately not done in here, use IPAMMute.py for this
class TxDACTone:
    CAL_DIR_NAME = "/run/media/mmcblk0p2/calibration/"
    CAL_FILE_NAME = "pa_cal_dac.csv"

    def initialise(self):
        # Set Tx attenuator to 6 dB
        RFControl.enable_tx_att_override()
        RFControl.set_tx_att(6)

        # Enable Tx power supplies
        PowerSupplies.rail_3v6_en()
        PowerSupplies.rail_5v5_en()
        PowerSupplies.tx_en()
        PowerSupplies.tx_dac_en()

        # Initialise synth
        synth = ADF4355()
        synth.enable_device()
        synth.set_synth_5000_megahertz()

    def disable(self):
        dac = AD9162()
        synth = ADF4355()
        synth.disable_device()
        dac.disable()
        RFControl.disable_tx_att_override()

    def set_tone(self, frequency_Hz):
        error_msg = ""

        # Get the PA cal (att) setting
        get_att_dB = self.get_calibrated_att(frequency_Hz)
        if get_att_dB[1]:
            att_dB = get_att_dB[0]
        else:
            error_msg = ": Calibration Point for the requested frequency was not found]"     
            return False, error_msg
        
        # Set the DAC frequency
        dac = AD9162()
        # Set DAC to safe level before setting frequency
        dac.set_att_dB(60)
        dac.set_frequency(frequency_Hz)
        # Set DAC to calibrated level
        dac.set_att_dB(att_dB)
        
        # If we got this far then everything worked    
        return True, error_msg

    def get_calibrated_att(self, frequency_Hz):
        att = 63.75
        with open(self.CAL_DIR_NAME + self.CAL_FILE_NAME, mode = 'r') as csv_file:
            # Discard first two rows
            for i in range(2):
                csv_file.readline()
            
            # Next row contains the band
            # Validate the cal file band against what has been requested
            row_band = next(csv_file)
            if "low" not in str(row_band.split(",")[1]):
                return att, False          
            # Discard next 4 rows
            for i in range(4):
                csv_file.readline()            
            csv_reader = csv.reader(csv_file)
            n = 0
            for row in csv_reader:
                if float(row[0]) == 0:  # path 0
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
    tone = TxDACTone()
    parser = argparse.ArgumentParser(description="Generate a full power CW tone using the TxDAC")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("-i", "--initialise",
                        help="Initialise the AD9162 TxDAC",
                        action="store_true")
    action.add_argument("-d", "--disable",
                        help="Disable the AD9162 TxDAC",
                        action="store_true")
    parser.add_argument("-f", "--frequency", help="Frequency in MHz", type=int, default="200")
    parser.add_argument("-v", "--verbose", help="Increase error message verbosity", action="store_true")
    args = parser.parse_args()
    dac = AD9162()
    if args.initialise:
        print("Initialise Synth: ", end="", flush=True)
        tone.initialise()
        print("OK")
        print("Initialise TxDAC: ", end="", flush=True)
        if dac.initialise():
            print("OK")
        else:
            print("FAIL")
    elif args.disable:
        print("Disable TxDAC")
        tone.disable()
        exit(1)

    if args.frequency:
        freq_MHz = int(args.frequency) * 1e6
        print("Configuring TxDAC for {} MHz: ".format(freq_MHz/1e6), end="", flush=True)
        ok, error_msg = tone.set_tone(freq_MHz)
        if ok:
            print("OK")
        else:
            if args.verbose:
                print("Error" + error_msg)
            else:
                print("Error")
