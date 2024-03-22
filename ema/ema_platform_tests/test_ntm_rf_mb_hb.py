#!/usr/bin/env python3
from logger import *
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from power_meter import *
from band import *
from serial_number import *

import os


TEST_POINTS = [
#    Band,     Path, Frequency,  Min Power
#                        (MHz)   Out (dBm)
    [Band.MID,    0,       400,        8.0],
    [Band.MID,    0,       950,        8.0],
    [Band.MID,    0,      1500,        8.0],

    [Band.MID,    1,      1490,        8.0],
    [Band.MID,    1,      1685,        8.0],
    [Band.MID,    1,      1880,        8.0],

    [Band.MID,    2,      1850,        8.0],
    [Band.MID,    2,      2050,        8.0],
    [Band.MID,    2,      2250,        8.0],

    [Band.MID,    3,      2250,        8.0],
    [Band.MID,    3,      2375,        8.0],
    [Band.MID,    3,      2500,        8.0],

    [Band.MID,    4,      2500,        8.0],
    [Band.MID,    4,      2600,        8.0],
    [Band.MID,    4,      2700,        8.0],

    [Band.MID,    5,      2700,        8.0],
    [Band.MID,    5,      2850,        8.0],
    [Band.MID,    5,      3000,        8.0],

#    Band,     Path, Frequency,  Min Power
#                        (MHz)   Out (dBm)
    [Band.HIGH,   3,      2400,        8.0],
    [Band.HIGH,   3,      2850,        8.0],
    [Band.HIGH,   3,      3400,        7.0],

    [Band.HIGH,   4,      3400,        8.0],
    [Band.HIGH,   4,      4000,        8.0],
    [Band.HIGH,   4,      4600,        6.0],

    [Band.HIGH,   5,      4600,        6.0],
    [Band.HIGH,   5,      5400,        8.0],
    [Band.HIGH,   5,      6000,        5.0],
]

def run_test():
    ok = True
    serial = SerialNumber.get_serial(Module.NTM_DIGITAL)
    sys.stdout = Logger("ntm_mb_hb_rf_test_{}.log".format(serial))
    start = time.process_time()
    print("")
    print("test_ntm_rf_mb_hb")
    print("-----------------")
    print("Serial number: {}".format(serial))
    print("Disable Tx power supplies: ", end = "")
    DDS.enable_power(False)
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

    # Power Meter connected now enable DDS
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

    print("Set source att to 0 dB: ", end = "", flush = True)
    RFControl.set_source_att(0)
    print("OK")

    print("Set doubler att to 0 dB: ", end = "", flush = True)
    RFControl.set_doubler_att(0)
    RFControl.en_doubler_att_20_dB(False)
    print("OK")

    for line in TEST_POINTS:
        band = line[0]
        path = line[1]
        freq_MHz = line[2]
        power_min_dBm = line[3]
        freq_Hz = freq_MHz * 1e6
        dds_freq_Hz = freq_Hz / RFControl.get_multiplier(path, band)

        # Set frequency/ASF
        asf = d.get_calibrated_asf(dds_freq_Hz)
        print("f {} MHz, ASF {}, {}, path {}: ".format(freq_MHz, asf, band, path), end = "", flush = True)
        d.set_frequency(dds_freq_Hz)
        d.set_asf(asf, True)
        RFControl.set_tx_path(path, band)

        # Read power
        pm.frequency_Hz = freq_Hz
        power_dBm = pm.get_reading_dBm()

        if power_dBm >= power_min_dBm:
            print("OK ({:.2f} dBm)".format(power_dBm))
        else:
            print("FAIL ({:.2f} dBm)".format(power_dBm))
            ok = False

    # If we got this far then all tests passed
    terminate_test()
    return ok

def terminate_test():
    DDS.enable_power(False)
    PowerSupplies.disable_all()


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

