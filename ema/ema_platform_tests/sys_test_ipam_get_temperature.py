#!/usr/bin/env python3
from ipam import *
from fans import *
from serial_number import *

import argparse

# Class provided to get the IPAM temperature and update the fan speed at the same time
class SysTestIPAMGetTemperature:

    def get_temperature(self):
        ok = True
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Getting EMA-{} IPAM temperature and updating fan speed...".format(serial))
        try:
            t = IPAM.get_temperature()
        except:
            error_msg = ": IPAM read failed"
            ok = False
        if ok:
            f = Fans()
            f.set_temperature(t)
        return ok, error_msg, t

if __name__ == "__main__":
    o = SysTestIPAMGetTemperature()
    parser = argparse.ArgumentParser(description = "Get the IPAM temperature and update the fan speed")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()
    ok, error_msg, t = o.get_temperature()
    if ok:
        print("OK" + ": {:.2f} degC".format(t))
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")