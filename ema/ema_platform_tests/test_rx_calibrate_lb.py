#!/usr/bin/env python3
import argparse
import datetime
import os
from time import sleep

from ad96xx import *
from dds import *
from external_attenuator import *
from ipam import *
from power_supplies import *
from rx_control import *
from serial_number import *
from signal_generator import *
from timing_control import *

FILE_ROOT = "/run/media/mmcblk0p2"
DIR_NAME = FILE_ROOT + "/calibration/"
FILE_NAME = "rx_cal.csv"

# ADC fast detect threshold, -6 dBFS = 0x1000
# Set to -20 dBFS = 0x0333
ADC_FAST_DETECT_THRESHOLD = 0x333

TEST_POINTS = [
    # The test sets preselector, tunes synth to "Centre MHz" and tunes signal generator to "RF MHz"
    # At each point a minimum mixer level (read from RF board) is tested expected
    # and a minimum IF attenuation is allowed to get to the ADC Fast Detect threshold
    # A negative value in min. IF att column means don't test at that point. We only perform this test
    # at the first point because it proves that the IF path is good from RF Board to Digital Board
    # Preselector, Centre MHz, IF MHz, LNA Enabled:  (Input dBm, Min. Mix dBm, Min IF att dB),
    #                                  LNA Disabled: (Input dBm, Min. Mix dBm, Min IF att dB)
    [0,  45,  -25, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],  # Start IF band (cover IF band in 5 MHz steps)
    [0,  45,  -20, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,  -15, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,  -10, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,   -5, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,    0, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,    5, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,   10, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,   15, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,   20, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],
    [0,  45,   25, [-29.0, -34.0,  8], [-9.0, -34.0,  3]],  # End IF band
    [0,  80,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],  # End preselector 0
    [1,  80,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],  # Cover RF band in 25 MHz steps and hit preselector edges
    [1, 105,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [1, 130,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [2, 130,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [2, 155,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [2, 180,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [3, 180,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [3, 205,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [3, 230,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [3, 255,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [3, 280,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 280,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 305,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 330,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 355,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 380,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 405,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [4, 420,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [5, 400,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [5, 425,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [5, 450,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [5, 470,    0, [-29.0, -34.0, -1], [-9.0, -34.0, -1]],
    [6, 470,    0, [-27.0, -42.0, -1], [-7.0, -42.0, -1]],  # Allow for preselector 6 additional loss
    [6, 495,    0, [-27.0, -42.0, -1], [-7.0, -42.0, -1]],
    [6, 495,   25, [-27.0, -42.0, -1], [-7.0, -42.0, -1]]
]

BAND_NAME = {Band.LOW: "low", Band.MID: "mid", Band.HIGH: "high", Band.EXT_HIGH: "ext-high"}


def run_test(sgs_ip_addr=None):
    print("test_rx_calibrate")
    print("-----------------")
    serial = SerialNumber.get_serial(Module.EMA)
    print("Serial number: {}".format(serial))
    tm = TimingControl()
    rx = RxControl()
    sg = SignalGenerator()
    print("Searching for Signal Generator Service: ", end="", flush=True)
    if sg.find(sgs_ip_addr):
        print("Signal Generator Service found at {}:{}".format(sg.address,str(sg.port)))
        print("Connect to signal generator: ", end="", flush=True)
        if sg.connect():
            print("OK")
            print("Signal generator details: {}".format(sg.description))
        else:
            print("FAIL")
            return terminate_test(False)
    else:
        print("FAIL - could not find SGS")
        return terminate_test(False)

    # Disable signal generator RF output
    print("Disable signal generator RF output: ", end="", flush=True)
    if sg.set_output_enable(False):
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Power cycle and enable Rx + IF ADC supplies
    print("Disable power supplies: ", end="", flush=True)
    IPAM.enable_power(False)
    DDS.enable_power(False)
    PowerSupplies.disable_all()
    sleep(2)
    print("OK")
    print("Enable Rx power supplies: ", end="", flush=True)
    PowerSupplies.rail_3v6_en(True)
    PowerSupplies.rail_5v5_en(True)
    PowerSupplies.rail_7v3_en(True)
    PowerSupplies.rx_en(True)
    PowerSupplies.if_adc_en(True)
    print("OK")

    # Enable IPAM
    print("Enable IPAM: ", end="", flush=True)
    IPAM.enable_power(True)
    if IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S):
        print("OK")
    else:
        print("FAIL - IPAM did not become ready")
        return terminate_test(False)

    print("Get IPAM band: ", end="", flush=True)
    band = IPAM.get_rf_band()
    if band != Band.UNKNOWN:
        print("OK [{}]".format(band))
    else:
        print("FAIL [{}]".format(band))
        return terminate_test(False)

    if band != Band.LOW:
        print("ERROR - test does not currently support {}".format(band()))
        return terminate_test(False)

    # Enable test mode to put IPAM into Rx
    print("Enable Tx/Rx Switch Rx Test Mode: ", end="", flush=True)
    if tm.enable_rx_test_mode():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Initialise IF ADC
    print("Initialise IF ADC: ", end="", flush=True)
    if AD96xx.reset():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Set IF ADC Fast Detect threshold
    print("Set IF ADC Fast Detect threshold to 0x{:04x}: ".format(ADC_FAST_DETECT_THRESHOLD), end="", flush=True)
    if AD96xx.set_fast_detect_threshold(ADC_FAST_DETECT_THRESHOLD):
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Initialise Rx synths
    print("Initialise Rx Synths: ", end="", flush=True)
    if rx.initialise_synths():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Set selected synth to 1
    print("Set Rx active synth to Nr. 1: ", end="", flush=True)
    if rx.set_active_synth(1):
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Set Rx RF attenuation to 0 dB
    print("Set Rx RF attenuation to 0 dB: ", end="", flush=True)
    if rx.set_rf_attenuator(0):
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    sg_rf_prev_mhz = 0

    print("Open {}{} for writing: ".format(DIR_NAME, FILE_NAME), end="")
    try:
        # Create directory if it does not exist
        os.makedirs(DIR_NAME, exist_ok=True)

        # Open file for writing
        cal_file = DIR_NAME + FILE_NAME
        f = open(cal_file, "w")
        # Write header (v0.1)
        f.write("file_version,0.1\n")
        f.write("serial,{}\n".format(serial))
        f.write("band,{}\n".format(BAND_NAME[band]))
        f.write("\n")
        # Note - gain offset is the difference between RF input power and mixer reported level
        # this must be offset again to report correct FFT power.
        # rf_offset_dB = mixer_reported_power_dBm - rf_in_power_dBm
        # rf_in_power_dBm = mixer_reported_power_dBm - rf_offset_dB
        f.write("presel,fc_MHz,if_MHz,lna_en,rf_offset_dB,if_offset_dB\n")
        print("OK")
    except:
        print("FAIL")
        terminate_test(False)

    # Loop through test points
    for test_point in TEST_POINTS:
        print()
        preselector = test_point[0]
        centre_mhz = test_point[1]
        if_mhz = test_point[2]
        sg_rf_mhz = centre_mhz + if_mhz

        for lna_en in [True, False]:
            if lna_en:
                param = test_point[3]
            else:
                param = test_point[4]

            rf_in_dbm = param[0]
            sg_pwr_dbm = round(rf_in_dbm + ExternalAttenuator.get_att(band, sg_rf_mhz, Path.RX), 2)
            min_mix_dbm = param[1]
            min_if_att_db = param[2]

            # Set Rx IF attenuation to 30 dB
            print("Set Rx IF attenuation to 30 dB: ", end="", flush=True)
            if rx.set_if_attenuator(30):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Set Rx LNA
            print("Set Rx LNA to {}: ".format("Enabled" if lna_en else "Disabled"), end="", flush=True)
            if rx.set_lna_enable(lna_en, band):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Set signal generator frequency
            if sg_rf_mhz != sg_rf_prev_mhz:
                print("Set signal generator to {} MHz: ".format(sg_rf_mhz), end="", flush=True)
                if sg.set_frequency_Hz(sg_rf_mhz * 1e6):
                    print("OK")
                    sg_rf_prev_mhz = sg_rf_mhz
                else:
                    print("FAIL")
                    return terminate_test(False)

            # Set signal generator power
            print("Set signal generator to {:.2f} dBm: ".format(sg_pwr_dbm), end="", flush=True)
            if sg.set_output_power_dBm(sg_pwr_dbm):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Set Rx preselector
            print("Set Rx preselector to {}: ".format(preselector), end="", flush=True)
            if rx.set_preselector(preselector):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Set Rx centre frequency
            print("Set Rx centre frequency to {} MHz: ".format(centre_mhz), end="", flush=True)
            if rx.set_centre_frequency_mhz(centre_mhz):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Enable signal generator RF output
            print("Enable signal generator RF output: ", end="", flush=True)
            if sg.set_output_enable(True):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Get mixer level
            mix_dbm = round(rx.get_mixer_level_dbm(), 1)
            print("Check mixer input level: ", end="", flush=True)
            if mix_dbm >= min_mix_dbm:
                print("OK [{:.1f} dBm]".format(mix_dbm))
            else:
                print("FAIL [{:.1f} dBm]".format(mix_dbm))
                return terminate_test(False)

            att = None
            if min_if_att_db >= 0:
                # Hunt for IF attenuation which toggles ADC Fast Detect
                print("Find IF attenuation level to toggle ADC Fast Detect: ", end="", flush=True)
                if_att_found = False
                for att in range(30, min_if_att_db-1, -1):
                    # Set Rx IF attenuation
                    if not rx.set_if_attenuator(att):
                        print("FAIL (could not set IF attenuator)")
                        return terminate_test(False)
                    if rx.fast_detect():
                        print("OK [{} dB]".format(att))
                        if_att_found = True
                        break
                if not if_att_found:
                    print("FAIL [hit minimum IF attenuation]")
                    return terminate_test(False)

            # Disable signal generator output
            print("Disable signal generator RF output: ", end="", flush=True)
            if sg.set_output_enable(False):
                print("OK")
            else:
                print("FAIL")
                return terminate_test(False)

            # Write cal point to file
            try:
                rf_offset_dB = mix_dbm - rf_in_dbm
                if att:
                    if_offset_dB = att - rf_offset_dB
                else:
                    if_offset_dB = 0
                f.write("{},{},{},{},{:.1f},{:.1f}\n".format(preselector, centre_mhz, if_mhz, lna_en, rf_offset_dB, if_offset_dB))
            except:
                print("FAIL - file write error")
                terminate_test(False)

    # If we got this far then all tests passed
    return terminate_test(True)


def terminate_test(ret_val):
    tm = TimingControl()
    tm.disable()
    IPAM.enable_power(False)
    PowerSupplies.disable_all()
    return ret_val


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EMA-LB Rx Test")
    parser.add_argument("-n", "--no_kill_no_duration", help="Don't kill apps and don't log test duration", action="store_true")
    parser.add_argument("-i", "--sgs_ip_addr", help="Find Signal Generator Service at specified IP address", default=None)
    args = parser.parse_args()
    if not args.no_kill_no_duration:
        os.system("/usr/bin/killall fetchandlaunchema")
        os.system("/usr/bin/killall KCemaEMAApp")
        os.system("/usr/bin/killall ema_app.bin")
        start_time = time.time()
    if run_test(args.sgs_ip_addr):
        print("\n*** OK - Rx calibration passed ***\n")
        if not args.no_kill_no_duration:
            print("\n(Rx calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
            print("\n*** Unmount mmcblk0p2 to ensure calibration and log files are saved ***\n")
    else:
        if not args.no_kill_no_duration:
            print("\n(Rx calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** TEST FAILED ***\n")
