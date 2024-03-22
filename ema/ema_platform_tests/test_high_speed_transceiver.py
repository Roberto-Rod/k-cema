#!/usr/bin/env python3
from power_supplies import *
from xcvr_control import *
from aurora_test_core import *
from mcp4728 import *
from ad9528 import *


def run_test():
    print("")
    print("test_high_speed_transceiver")
    print("---------------------------")
    ok = True
    dac = MCP4728()
    gen = AD9528()
    aur = AuroraTestCore()
    xcvr = XcvrControl()
    xcvr.reset(True)
    PowerSupplies.disable_all()
    PowerSupplies.rail_3v6_en(True)
    xcvr.reset(False)

    print("Set Trim DAC to mid-scale: ", end="", flush=True)
    if dac.set_dac_midscale():
        print("OK")
    else:
        ok = False
        print("FAIL")

    print("Check Clock Generator Vendor ID: ", end="", flush=True)
    if gen.check_vendor_id():
        print("OK")
    else:
        ok = False
        print("FAIL")

    print("Initialise Clock Generator: ", end="", flush=True)
    if gen.initialise(validate=True):
        print("OK")
    else:
        ok = False
        print("FAIL")

    if ok:
        print("Initialise Aurora Loopback Module: ", end="", flush=True)
        aur.reset(False)
        if aur.is_reset_done():
            print("OK")
        else:
            ok = False
            print("FAIL")

    if ok:
        print("Aurora PLL Lock: ", end="", flush=True)
        if aur.is_pll_locked():
            print("OK")
        else:
            ok = False
            print("FAIL")

    if ok:
        print("Aurora Lanes All Up: ", end="", flush=True)
        if aur.is_all_up():
            print("OK")
        else:
            ok = False
            print("FAIL")

    if ok:
        print("Aurora Check Errors: ", end="", flush=True)
        if aur.is_no_errors():
            print("OK")
        else:
            ok = False
            print("FAIL")
        
    xcvr.reset(True)
    PowerSupplies.disable_all()
    return ok


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
