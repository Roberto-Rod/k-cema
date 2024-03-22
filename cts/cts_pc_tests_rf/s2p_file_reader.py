#!/usr/bin/python3
import argparse
from math import log10

import os

# Class to read *.s2p Touchstone files and return an S-parameter data element for a given frequency
# The returned data format is: frequency units = Hz and data format = dB-angle, regardless of what's in the file 
class S2PFileReader:
    # Refer to: http://literature.cdn.keysight.com/litweb/pdf/genesys200801/sim/linear_sim/sparams/touchstone_file_format.htm
    def get_s_parameter(self, frequency_Hz, s_param_elem = 3, input_file = "/run/media/mmcblk0p2/calibration/tx_attenuation.s2p", verbose = False):
        retVal = None
        
        if s_param_elem < 0 or s_param_elem > 8:
            if verbose:
                print("Invalid S-parameter element (valid range 0-8)")
            return retVal
        
        try:
            f = open(input_file, "r")

            # Get the "options line"   
            ok = False
            options_line = []
            for line in f:
                if line.startswith("#"):
                    options_line = line.split()
                    if options_line[0] == "#":
                        f_freq_units = options_line[1].upper()
                        f_type = options_line[2].upper()
                        f_format = options_line[3].upper()
                        # check for optional "R" parameter
                        if len(options_line) == 6:
                            if options_line[4].upper() == "R":
                                f_impedance = options_line[5]
                    ok = True
                    break
            if not ok:
                if verbose:
                    print('Invalid file (no Option Line found)')
                ok = False
            
            # Check these are S-parameters
            if ok:
                if f_type != "S":
                    if verbose:
                        print("Invalid file (data not S-parameters)")
                    ok = False

            # Check impedance normalised to 50 Ohms
            if len(options_line) == 6:
                if f_impedance != "50":
                    if verbose:
                        print("Invalid file (data not normalised to 50 Ohms)")
                    ok = False  
            
            # Convert the input frequency units (Hz) to same as those in file
            if ok:
                if f_freq_units == "HZ":
                    frequency = float(frequency_Hz)
                elif f_freq_units == "KHZ":
                    frequency =  float(frequency_Hz) / 1e3
                elif f_freq_units == "MHZ":
                    frequency =  float(frequency_Hz) / 1e6
                elif f_freq_units == "GHZ":
                    frequency =  float(frequency_Hz) / 1e9
                else:
                    if verbose:
                        print("Invalid file (frequency units unrecognised)")
                    return retVal
                
                # Attempt to find the two bracketing data lines and the associated requested S-parameter
                n = 0
                data_line = []
                for line in f:
                    if line[0].isdigit():
                        data_line = line.split()
                        if n == 0:
                            # First data line found
                            freq1 = float(data_line[0])
                            s_param1 = float(data_line[s_param_elem])
                            freq2 = freq1
                            s_param2 = s_param1
                        else:
                            if float(data_line[0]) >= frequency:
                                freq2 = float(data_line[0])
                                s_param2 = float(data_line[s_param_elem])
                                break
                            freq1 = float(data_line[0])
                            s_param1 = float(data_line[s_param_elem])
                        n += 1

                # No data lines were found
                if n == 0:
                    if verbose:
                        print("Invalid file (no data lines found)")
              
                # Frequency point was not found within the cal table
                elif freq1 > frequency or frequency > freq2:
                    if verbose:
                        print("File does not contain the requested frequency")
                
                # Otherwise get the S-parameter value by interpolation
                else:
                    r = (frequency - freq1) / (freq2 - freq1)
                    val = (r * (s_param2 - s_param1)) + s_param1
                    
                    # Convert frequency units to Hz
                    if s_param_elem == 0: 
                        if f_freq_units == "HZ":
                            retVal = int(val)
                        elif f_freq_units == "KHZ":
                            retVal = int(val * 1e3)
                        elif f_freq_units == "MHZ":
                            retVal = int(val * 1e6)
                        elif f_freq_units == "GHZ":
                            retVal = int(val * 1e9)
                    
                    # Convert data to dB-angle (this is the "dB" bit of that)
                    elif s_param_elem in [1, 3, 5, 7]: 
                        if f_format == "DB":
                            retVal = val # Already in the right format
                        elif f_format == "MA":
                            retVal = 20 * log10(val) # Convert to dB
                        else:
                            if verbose:
                                print('Data format not supported (must be "DB" or "MA")')
                        
                    # Convert data to dB-angle (this is the "angle" bit of that)    
                    elif s_param_elem in [2, 4, 6, 8]: 
                        if f_format == "DB":
                            retVal = val # Already in the right format
                        elif f_format == "MA":
                            retVal = val # Already in the right format
                        else:
                            if verbose:
                                print('Data format not supported (must be "DB" or "MA")')
            f.close()
            
        except:
            if verbose:
                print("Unable to open file: " + input_file)        
          
        return retVal
    
if __name__ == '__main__':    
    s_param_name = {}
    s_param_name[0] = "FREQ"
    s_param_name[1] = "20log10|S11|"
    s_param_name[2] = "<S11"
    s_param_name[3] = "20log10|S21|"
    s_param_name[4] = "<S21"
    s_param_name[5] = "20log10|S12|"
    s_param_name[6] = "<S12"
    s_param_name[7] = "20log10|S22|"
    s_param_name[8] = "<S22"   

    o = S2PFileReader()
    parser = argparse.ArgumentParser(description="Get an s2p file element for a given frequency")
    parser.add_argument("frequency", help="frequency in Hz", type=int)
    parser.add_argument("-s", "--s_param", help="S-parameter element: 0 = FREQ, 1 = 20log10|S11|, 2 = <S11, 3 = 20log10|S21|, 4 = <S21, \
                        5 = 20log10|S12|, 6 = <S12, 7 = 20log10|S22|, 8 = <S22. Default is 3 20log10|S21|)", type=int, default=3) 
    parser.add_argument("-i", "--input_file", help="Input *.s2p file. Default is /run/media/mmcblk0p2/calibration/tx_attenuation.s2p",
                        default="/run/media/mmcblk0p2/calibration/tx_attenuation.s2p")
    parser.add_argument("-v", "--verbose", help="print useful information to the console", action="store_true")
    args = parser.parse_args()
    
    value = o.get_s_parameter(args.frequency, args.s_param, args.input_file, args.verbose)
    if value != -999.0:
        print("OK: Frequency [{0}]: S-parameter [{1}]: Value [{2}]".format(args.frequency, s_param_name[args.s_param], value))
    else:
        print("Error")    
    