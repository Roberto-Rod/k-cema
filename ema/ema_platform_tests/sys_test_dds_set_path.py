#!/usr/bin/env python3
from ipam import *
from serial_number import *
from rf_control import *
import time
import argparse

# Class provided to update the IPAM mute state using a command line argument
class SysTestIPAMSetMute:
    IPAM_REG_ADDR_PA_CONTROL_AND_STATUS = 0x005A

    ATT_MAX_DB = 52.75
    ATT_STEP_DB = -1.00
    STEP_TIME_SEC = 0.0005

    def set_mute(self, mute):
        ok = True        
        error_msg = ""
        serial = SerialNumber.get_serial(Module.EMA)
        print("Setting EMA-{0} IPAM mute state to {1}...".format(serial, mute))
        if mute == "true" or mute == "True":
            b = True            
        elif mute == "false" or mute == "False":
            b = False              
        else:
            error_msg = ": invalid argument: {} - must be 'true' or 'false'".format(mute)
            ok = False 
        if ok:
            if not b:
                att_target_dB = RFControl.get_doubler_att()
                att_dB = self.ATT_MAX_DB
                RFControl.set_doubler_att(att_dB)
            try:
                IPAM.force_mute(b)
                #if b:
                #    ok = self.get_mute()
                #else:
                #    ok = not self.get_mute()
                #if not ok:
                #    error_msg = ": IPAM read and write worked but mute state failed to update"
            except:
                error_msg = ": IPAM read and/or write failed"
                ok = False
            if not b:
                while att_dB != att_target_dB:
                    att_dB += self.ATT_STEP_DB
                    if att_dB < att_target_dB:
                        att_dB = att_target_dB
                    time.sleep(self.STEP_TIME_SEC)
                    RFControl.set_doubler_att(att_dB)
        return ok, error_msg
    
    # Get the state of TX_EN_COMP from the IPAM directly
    # '0' means mute = true     
    def get_mute(self):
        reg = IPAM.reg_read(self.IPAM_REG_ADDR_PA_CONTROL_AND_STATUS)
        return not (reg >> 9) & 0x1        


if __name__ == "__main__":
    o = SysTestIPAMSetMute()
    parser = argparse.ArgumentParser(description = "Update the IPAM mute state")
    parser.add_argument("mute", help="'true' for mute, 'false' for no mute", default="True")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()    
    ok, error_msg = o.set_mute(args.mute)
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")