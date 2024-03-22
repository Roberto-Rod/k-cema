#!/usr/bin/env python3
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from power_meter import *
from band import *

import os

freq_start_MHz = {}
freq_stop_MHz = {}
freq_step_MHz = {}
freq_start_MHz[Band.LOW] = 20
freq_stop_MHz[Band.LOW] = 1500
freq_step_MHz[Band.LOW] = 148
freq_start_MHz[Band.MID_HIGH] = 400
freq_stop_MHz[Band.MID_HIGH] = 1500
freq_step_MHz[Band.MID_HIGH] = 110

target_power = {}
target_power[Band.LOW] = [
    # Frequency (MHz), Power (dBm)
    (520, 10),     # Require power >= 10.0dBm up to and including 520MHz
    (1500, 5)      # Require power >= 5.0dBm up to and including 1500MHz
]

target_power[Band.MID_HIGH] = [
    # Frequency (MHz), Power (dBm)
    (1500, -7)      # Require power >= -7.0dBm up to and including 1500MHz
]


def run_test(band, zero_power_meter=True):
    if not isinstance(band, Band):
        raise TypeError("band must be an instance of Band Enum")
    print("")
    print("test_dds_power")
    print("------------------")
    print("Disable Tx power supplies: ", end = "")
    DDS.enable_power(False)
    PowerSupplies.tx_en(False)
    PowerSupplies.rail_5v5_en(False)
    print("OK")
    pm = PowerMeter()
    print("Searching for Power Meter Service: ", end = "", flush = True)
    if pm.find():
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

    print("Set source_att to 0 dB", end = "", flush = True)
    RFControl.set_source_att(0)
    print("OK")

    # Set ASF to full-scale
    asf = 4095
    print("Set DDS to full-scale (ASF = {})".format(asf), end = "", flush = True)
    d.set_asf(asf)
    print("OK")

    # Loop through DDS frequencies in MHz
    for freq in range(freq_start_MHz[band], freq_stop_MHz[band] + freq_step_MHz[band], freq_step_MHz[band]):
        # Set frequency
        print("Set DDS to {} MHz: ".format(freq), end = "")
        d.set_frequency(freq * 1e6, True)
        print("OK")

        # Read power
        pm.frequency_Hz = freq * 1e6
        read_power_dBm = pm.get_reading_dBm()

        # Find target power
        for target in reversed(target_power[band]):
            if freq <= target[0]:
                target_power_dBm = target[1]

        # Test power reading against target
        if read_power_dBm >= target_power_dBm:
            status = "PASS"
        else:
            status = "FAIL"

        print("Output power: {} (read {:.2f} dBm, min. {:.2f} dBm)".format(status, read_power_dBm, target_power_dBm))

        if status == "FAIL":
            terminate_test()
            return False

    # If we got this far then all tests passed
    return True

def terminate_test():
    DDS.enable_power(False)
    PowerSupplies.disable_all()


if __name__ == "__main__":
    if run_test(Band.LOW):
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

