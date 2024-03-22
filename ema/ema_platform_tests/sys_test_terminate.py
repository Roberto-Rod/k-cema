#!/usr/bin/env python3
from power_supplies import *
from dds import *
from ipam import *
from fans import *

import argparse


# Class provided to de-initialise the EMA following system tests
class SysTestTerminate:
    def terminate(self):
        ok = True
        error_msg = ""
        IPAM.enable_power(False)
        DDS.enable_power(False)
        PowerSupplies.disable_all()
        fans = Fans()
        fans.set_temperature(0)
        return ok, error_msg


if __name__ == "__main__":
    o = SysTestTerminate()
    parser = argparse.ArgumentParser(description="De-initialise the EMA after system tests")
    parser.add_argument("-v", "--verbose", help="increase error message verbosity", action="store_true")
    args = parser.parse_args()
    ok, error_msg = o.terminate()
    if ok:
        print("OK")
    else:
        if args.verbose:
            print("Error" + error_msg)
        else:
            print("Error")
