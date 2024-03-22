#!/usr/bin/env python3
from ipam import *
import argparse


# Class provided to get the IPAM temperature and update the fan speed at the same time
class SysTestIPAMGetRFPower:
    
    def get_rf_power(self):
        ok = True
        error_msg = ""
        print("Getting IPAM RF power readings")
        try:
            rf = IPAM.get_power_monitor_readings()
        except:
            error_msg = ": IPAM read failed"
            ok = False
        return ok, error_msg, rf


if __name__ == "__main__":
    o = SysTestIPAMGetRFPower()
    parser = argparse.ArgumentParser(description="Get the IPAM RF power monitor readings")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg, rf = o.get_rf_power()
    if ok:
        print("OK: {},{}".format(rf["fwd"], rf["rev"]))
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
