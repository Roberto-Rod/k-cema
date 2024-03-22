#!/usr/bin/env python3
from serial_number import *
from rf_control import *
import argparse


# Class provided to update NTM RF Board attenuators using a command line argument
class SysTestDoublerSetAtt:
    def set_att(self, en_20_dB, att_dB):
        ok = True
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Setting EMA-{} doubler attenuation to: 20 dB enabled ({}), output ({} dB)...".format(serial, en_20_dB, att_dB))

        if en_20_dB == "true" or en_20_dB == "True":
            b = True
        elif en_20_dB == "false" or en_20_dB == "False":
            b = False
        else:
            error_msg = ": invalid argument: {} - must be 'true' or 'false'".format(en_20_dB)
            ok = False

        if ok:
            try:
                att_dB_f = float(att_dB)
                if not 0.0 <= att_dB_f <= 51.75:
                    error_msg = ": invalid argument: {} - must be in range 0.0 to 52.75".format(att_dB)
                    ok = False
                if ok:
                    att_dB_f = round(att_dB_f * 4) / 4.0
                    RFControl.en_doubler_att_20_dB(b)   # Currently unsupported by the FPGA, is False by default...
                    RFControl.set_doubler_att(att_dB_f)
            except Exception as e:
                error_msg = ": {}".format(e)
                ok = False

        return ok, error_msg


if __name__ == "__main__":
    o = SysTestDoublerSetAtt()
    parser = argparse.ArgumentParser(description="Update NTM RF Board attenuators")
    parser.add_argument("en_20_dB", help="'true' to enable the 20 dB input attenuator, 'false' to disable")
    parser.add_argument("att_dB", help="Output attenuation in dB, range 0.0 to 51.75")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_att(args.en_20_dB, args.att_dB)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
