#!/usr/bin/env python3
from serial_number import *
from rf_control import *
import argparse


# Class provided to update the doubler path using a command line argument
class SysTestDoublerSetAtt:
    def set_att(self, att_dB):
        ok = True        
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        try:
            att_dB_f = float(att_dB)
            if not 0.0 <= att_dB_f <= 52.75:
                error_msg = ": invalid argument: {} - must be in range 0.0 to 52.75".format(att_dB)
                ok = False
            if ok:
                att_dB_f = round(att_dB_f * 4) / 4.0
                print("Setting EMA-{} doubler attenuation to {}...".format(serial, att_dB_f))
                RFControl.set_doubler_att(att_dB_f)
        except Exception as e:
            error_msg = ": {}".format(e)
            ok = False
        return ok, error_msg


if __name__ == "__main__":
    o = SysTestDoublerSetAtt()
    parser = argparse.ArgumentParser(description="Update the NTM doubler attenuation")
    parser.add_argument("att_dB", help="Attenuation in dB, range 0.0 to 52.75")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_att(args.att_dB)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
