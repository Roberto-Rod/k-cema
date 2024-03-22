#!/usr/bin/env python3
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from power_meter import *
from test import *

import os

TEST_FREQ_MHZ = 100
ATT_ALLOWED_ERR_DB = 3


def att_decibels_to_asf(decibels):
    ratio = 10 ** (decibels / 20)
    return int(round(4095 / ratio, 0))


def run_test(zero_power_meter=True):
    print("")
    print("test_tx_attenuator")
    print("------------------")
    print("Disable Tx power supplies: ", end = "")
    PowerSupplies.tx_en(False)
    PowerSupplies.rail_5v5_en(False)
    print("OK")
    pm = PowerMeter()
    print("Searching for Power Meter Service: ", end = "", flush = True)
    if (pm.find()):
        print("Power Meter Service found at {}:{}".format(pm.address,str(pm.port)))
        print("Connect to power meter: ", end = "", flush = True)
        if pm.connect():
            print("OK")
            print("Power meter details: {}".format(pm.description))
            # Zero power meter
            if zero_power_meter:
                print("Zero power meter: ", end = "", flush = True)
                if pm.zero():
                    print("OK")
                else:
                    print("FAIL")
                    terminate_test()
                    return False
            # Set power meter offset
            print("Set offset to 0.0 dB: ", end = "", flush = True)
            if pm.set_offset(0):
                print("OK")
            else:
                print("FAIL")
                terminate_test()
                return False
        else:
            print("FAIL")
            terminate_test()
            return False
    else:
        print("FAIL - could not find PMS")
        terminate_test()
        return False

    # File opened, Power Meter connected now enable DDS
    print("Enable Tx power supplies: ", end = "")
    PowerSupplies.rail_5v5_en()
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

    d = DDS()
    print("Initialise DDS: ", end = "")
    d.initialise()
    print("OK")

    print("Set source_att to 0 dB: ", end = "", flush = True)
    RFControl.set_source_att(0)
    print("OK")

    # Set ASF to full-scale
    asf = att_decibels_to_asf(10)
    print("Set DDS to 10 dB below F.S. (ASF = {}): ".format(asf), end = "", flush = True)
    d.set_asf(asf)
    print("OK")

    # Set frequency
    print("Set DDS to {} MHz: ".format(TEST_FREQ_MHZ), end = "")
    d.set_frequency(TEST_FREQ_MHZ * 1e6, True)
    print("OK")
    pm.frequency_Hz = TEST_FREQ_MHZ * 1e6

    # Loop through attenuation levels
    for att in range(0, 40, 10):
        # Set attenuator
        print("Set attenuation to {} dB: ".format(att), end = "", flush = True)
        RFControl.set_source_att(att)
        print("OK")

        # Read power
        read_power_dBm = pm.get_reading_dBm()

        # Target power
        if att == 0:
            fs_power_dBm = read_power_dBm
            print("Reference power: {:.2f} dBm".format(fs_power_dBm))
        else:
            target_power_dBm = fs_power_dBm - att
            if Test.lim(read_power_dBm, target_power_dBm - ATT_ALLOWED_ERR_DB, target_power_dBm + ATT_ALLOWED_ERR_DB):
                status = "PASS"
            else:
                status = "FAIL"

            print("Output power: {} (read {:.2f} dBm, target {:.2f} +/- {:.2f} dBm)".format(status, read_power_dBm, target_power_dBm, ATT_ALLOWED_ERR_DB))

            if status == "FAIL":
                terminate_test()
                return False

    # If we got this far then all tests passed
    return True

def terminate_test():
    PowerSupplies.disable_all()


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

