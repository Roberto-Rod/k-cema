#!/usr/bin/env python3
from serial_number import *
from rx_control import *
import argparse


# Class provided to update the Rx LNA Bypass state using a command line argument
class SysTestRxSetLNABypass:
    def set_lna_bypass(self, bypass):
        ok = True
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Setting EMA-{} Rx LNA Bypass to {}...".format(serial, bypass))

        if bypass == "true" or bypass == "True":
            b = True
        elif bypass == "false" or bypass == "False":
            b = False
        else:
            error_msg = ": invalid argument: {} - must be 'true' or 'false'".format(bypass)
            ok = False

        if ok:
            try:
                rx = RxControl()
                ok = rx.set_lna_enable(b)
            except Exception as e:
                error_msg = ": {}".format(e)
                ok = False

        return ok, error_msg


if __name__ == "__main__":
    o = SysTestRxSetLNABypass()
    parser = argparse.ArgumentParser(description="Update the NTM RF Board Rx LNA Bypass state")
    parser.add_argument("bypass", help="'true' for bypass, 'false' for LNA", default="True")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_lna_bypass(args.bypass)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
