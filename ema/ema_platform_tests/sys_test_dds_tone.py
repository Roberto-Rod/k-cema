#!/usr/bin/env python3
from dds import *
from ipam import *
from serial_number import *

import argparse


# Class provided to generate a DDS CW tone at the frequency passed in as command line argument
# IMPORTANT: assumes the EMA has been initialised first by running initialise.py
class SysTestDDSTone:
    def set_tone(self, frequency_Hz):
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Configuring EMA-{} for {} Hz at full power...".format(serial, frequency_Hz))

        # Get IPAM band
        band = IPAM.get_rf_band()
        if band == Band.UNKNOWN:
            error_msg = ": IPAM band is unknown"
            return False, error_msg

        # Set the DDS frequency
        d = DDS()
        d.set_frequency(frequency_Hz)
        
        # Set ASF to calibrated DDS output for mid/high band
        if band == Band.MID or band == band.HIGH:
            asf = d.get_calibrated_asf(frequency_Hz)
            d.set_asf(asf, True)
        
        # If we got this far then everything worked    
        return True, error_msg


if __name__ == "__main__":
    o = SysTestDDSTone()
    parser = argparse.ArgumentParser(description="Generate a DDS tone")
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
