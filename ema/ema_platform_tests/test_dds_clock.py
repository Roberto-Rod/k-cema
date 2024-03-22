#!/usr/bin/env python3
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from test import *

from time import sleep

def run_test():
    print("")
    print("test_dds_clock")
    print("--------------")
    print("Enable Tx power supplies: ", end = "")
    PowerSupplies.tx_en()
    print("OK")
    print("Initialise synth: ", end = "")
    Synth.initialise()
    if Synth.is_locked():
        print("OK")
    else:
        print("FAIL - not locked")
        terminate_test()
        return False
    print("Initialise DDS: ", end = "")
    DDS.initialise()
    print("OK")
    print("Test DDS clock count: ", end = "")
    sleep(2)
    clk_count = DDS.clock_count()
    if Test.nom(clk_count, 135e6, 1):
        print("OK")
    else:
        print("FAIL [count = {}]".format(clk_count))
        terminate_test()
        return False

    # If we got this far then all tests passed
    return True

def terminate_test():
    DDS.enable_power(False)
    PowerSupplies.disable_all()


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

