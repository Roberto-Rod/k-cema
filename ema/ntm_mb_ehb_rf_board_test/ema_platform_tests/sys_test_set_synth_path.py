#!/usr/bin/env python3
from serial_number import *
from rf_control import *
import argparse


# Class provided to update the NTM RF Board synth path using a command line argument
class SysTestSetSynthPath:
    def set_path(self, path):
        ok = True        
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Setting EMA-{} synth path to {}...".format(serial, path))

        if ok:
            try:
                path_i = int(path)
                if not 0 <= path_i <= 1:
                    error_msg = ": invalid argument: {} - must be in range 0 to 1".format(path)
                    ok = False
            except Exception as e:
                error_msg = ": {}".format(e)
                ok = False
            if ok:
                RFControl.set_synth_path(path_i)
        return ok, error_msg


if __name__ == "__main__":
    o = SysTestSetSynthPath()
    parser = argparse.ArgumentParser(description="Update the NTM RF Board synth path")
    parser.add_argument("path", help="Tx Path, range 0 to 1")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_path(args.path)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
