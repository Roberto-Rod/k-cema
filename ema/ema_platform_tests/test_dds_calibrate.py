#!/usr/bin/env python3
from power_supplies import *
from synth import *
from dds import *
from rf_control import *
from power_meter import *
from band import *

import os

SERIAL = 1234
DIR_NAME = "../calibration/"
FILE_NAME = "dds_cal.csv"
ERROR_THRESHOLD = 0.1 # dB
ATT_MAX_DB = 63.75

target_power_dBm = {}
target_power_dBm[Band.LOW] = 0.0
target_power_dBm[Band.MID_HIGH] = -9.0

freq_start_MHz = {}
freq_stop_MHz = {}
freq_step_MHz = {}
freq_start_MHz[Band.LOW] = 20
freq_stop_MHz[Band.LOW] = 1500
freq_step_MHz[Band.LOW] = 20
freq_start_MHz[Band.MID_HIGH] = 400
freq_stop_MHz[Band.MID_HIGH] = 1500
freq_step_MHz[Band.MID_HIGH] = 20

def run_test(band, zero_power_meter=True):
    if not isinstance(band, Band):
        raise TypeError("band must be an instance of Band Enum")
    start = time.process_time()
    print("")
    print("test_dds_calibrate")
    print("------------------")
    print("Disable Tx power supplies: ", end="")
    DDS.enable_power(False)
    PowerSupplies.tx_en(False)
    PowerSupplies.rail_5v5_en(False)
    print("OK")
    pm = PowerMeter()
    print("Searching for Power Meter Service: ", end="", flush=True)
    if (pm.find()):
        print("Power Meter Service found at {}:{}".format(pm.address,str(pm.port)))
        print("Connect to power meter: ", end="", flush=True)
        if pm.connect():
            print("OK")
            print("Power meter details: {}".format(pm.description))
            # Zero power meter
            if zero_power_meter:
                print("Zero power meter: ", end="", flush=True)
                if pm.zero():
                    print("OK")
                else:
                    print("FAIL")
                    terminate_test()
                    return False
            # Set power meter offset
            print("Set offset to 0.0 dB: ", end="", flush=True)
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

    print("Open {}{} for writing: ".format(DIR_NAME, FILE_NAME), end="")
    try:
        # Create directory if it does not exist
        os.makedirs(DIR_NAME, exist_ok = True)

        # Open file for writing
        f = open(DIR_NAME + FILE_NAME, "w")

        # Write header (v0.1)
        f.write("file_version,0.1\n")
        f.write("serial,{}\n".format(SERIAL))
        f.write("\n")
        f.write("freq_Hz,asf\n")
        print("OK")
    except:
        print("FAIL")
        terminate_test()
        return False

    # File opened, Power Meter connected now enable DDS
    print("Enable Tx power supplies: ", end="")
    PowerSupplies.rail_5v5_en()
    PowerSupplies.tx_en()
    print("OK")
    print("Initialise synth: ", end="")
    Synth.initialise()
    if Synth.is_locked():
        print("OK")
    else:
        print("FAIL - not locked")
        terminate_test()
        return False

    d = DDS()
    print("Initialise DDS: ", end="")
    print("Initialise DDS: ", end="")
    d.initialise()
    print("OK")

    print("Set source_att to 0 dB: ", end="", flush=True)
    RFControl.set_source_att(0)
    print("OK")

    # Start at 30 dB
    att_dB = 30

    # Loop through DDS frequencies
    for freq in range(freq_start_MHz[band], freq_stop_MHz[band] + freq_step_MHz[band], freq_step_MHz[band]):
        # Set frequency
        print("Set DDS to {} MHz: ".format(freq), end="")
        d.set_frequency(freq * 1e6)
        print("OK")

        # Prime last error at 0 on each frequency point - prevents direction change on first step
        last_error = 0

        # Prime step size at 0.25 dB on each frequency point - prevents large steps on first step
        step_size_dB = 0.25
        last_att_dB = att_dB
        decrease_att = True
        flip_count = 0
        cal_point_found = False
        error = 0

        print("Finding attenuation level", end="", flush=True)
        while not cal_point_found:
            print(".", end="", flush=True)
            d.set_att_dB(att_dB ,True)

            # Read power
            pm.frequency_Hz = freq * 1e6
            power_dBm = pm.get_reading_dBm()
            error_dB = float(target_power_dBm[band]) - float(power_dBm)
            abs_error_dB = abs(error_dB)
            if abs_error_dB < ERROR_THRESHOLD:
                cal_point_found = True
            else:
                if att_dB == 0:
                    print("FAIL - reached minimum attenuation")
                    terminate_test()
                    return False
                elif abs_error_dB < 2.0:
                    step_size_dB = 0.25
                elif abs_error_dB < 6.0:
                    step_size_dB = 1
                else:
                    step_size_dB = 3

            # Determine direction
            direction_changed = False
            if error_dB > 0:
                if not decrease_att:
                    direction_changed = True
                decrease_att = True
            else:
                if decrease_att:
                    direction_changed = True
                decrease_att = False

            # Was direction changed?
            if direction_changed:
                flip_count += 5
                if flip_count > 5:
                    if abs(last_error_dB) < abs_error_dB:
                        att_dB = last_att_dB
                    cal_point_found = True
            else:
                flip_count = 0

            # Increment/decrement attenuation depending on sign of error
            if decrease_att:
                att_dB -= step_size_dB
                if att_dB < 0:
                    att_dB = 0
            else:
                att_dB += step_size_dB
                if att_dB > ATT_MAX_DB:
                    att_dB = ATT_MAX_DB

            last_error_dB = error_dB
            last_att_dB = att_dB

        if cal_point_found:
            asf = d.get_asf()
            print("OK [att = {} dB, ASF = {}]".format(att_dB, asf))
            try:
                # Write to file, frequency in Hz
                f.write("{:.0f},{}\n".format(freq * 1e6, asf))
            except:
                print("FAIL - file write error")
                terminate_test()
                return False

    # If we got this far then all tests passed
    terminate_test()
    return True

def terminate_test():
    DDS.enable_power(False)
    PowerSupplies.disable_all()


if __name__ == "__main__":
    if run_test(Band.MID_HIGH):
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

