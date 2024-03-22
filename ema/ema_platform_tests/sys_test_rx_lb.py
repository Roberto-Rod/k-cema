#!/usr/bin/env python3
import datetime

from ad96xx import *
from power_supplies import *
from rx_control import *
from timing_control import *

# ADC fast detect threshold, -6 dBFS = 0x1000
# Set to -20 dBFS = 0x0333
ADC_FAST_DETECT_THRESHOLD = 0x0333

MIN_MIX_DBM = -30.0
MIN_IF_ATT_DB = 6


def run_test(freq_MHz):
    freq_MHz = int(freq_MHz)
    if freq_MHz < 45:
        freq_MHz = 45
    if freq_MHz > 495:
        freq_MHz = 495

    if freq_MHz <= 45:
        preselector = 0
        rf_att_dB = 0
    elif freq_MHz <= 120:
        preselector = 1
        rf_att_dB = 6
    elif freq_MHz <= 220:
        preselector = 3
        rf_att_dB = 7
    elif freq_MHz <= 320:
        preselector = 3
        rf_att_dB = 9
    elif freq_MHz <= 420:
        preselector = 4
        rf_att_dB = 15
    elif freq_MHz <= 470:
        preselector = 5
        rf_att_dB = 15
    elif freq_MHz <= 520:
        preselector = 6
        rf_att_dB = 15

    rx = RxControl()

    # Enable Rx test mode
    tm = TimingControl()
    tm.enable_tx_in_rx_test_mode()
    tm.enable_rx_test_mode()

    # Set Rx RF attenuation
    print("Set Rx RF attenuation to {} dB: ".format(rf_att_dB), end="", flush=True)
    if rx.set_rf_attenuator(rf_att_dB):
        print("OK")
    else:
        print("FAIL")
        return False

    # Disable Rx LNA
    print("Set Rx LNA to enabled: ", end="", flush=True)
    if rx.set_lna_enable(True, Band.LOW):
        print("OK")
    else:
        print("FAIL")
        return False

    # Set Rx preselector
    print("Set Rx preselector to {}: ".format(preselector), end="", flush=True)
    if rx.set_preselector(preselector):
        print("OK")
    else:
        print("FAIL")
        return False

    # Set Rx centre frequency
    print("Set Rx centre frequency to {} MHz: ".format(freq_MHz), end="", flush=True)
    if rx.set_centre_frequency_mhz(freq_MHz):
        print("OK")
    else:
        print("FAIL")
        return False

    # Get mixer level
    mix_dbm = round(rx.get_mixer_level_dbm(), 1)
    print("Check mixer input level: ", end="", flush=True)
    if mix_dbm >= MIN_MIX_DBM:
        print("OK [{:.1f} dBm]".format(mix_dbm))
    else:
        print("FAIL [{:.1f} dBm]".format(mix_dbm))
        return False

    # Hunt for IF attenuation which toggles ADC Fast Detect
    print("Find IF attenuation level to toggle ADC Fast Detect: ", end="", flush=True)
    if_att_found = False
    for att in range(30, MIN_IF_ATT_DB-1, -1):
        # Set Rx IF attenuation
        if not rx.set_if_attenuator(att):
            print("FAIL (could not set IF attenuator)")
            return False
        if rx.fast_detect():
            print("OK [{} dB]".format(att))
            if_att_found = True
            break
    if not if_att_found:
        print("FAIL [hit minimum IF attenuation]")
        return False

    # Set Rx IF attenuation to 30 dB
    print("Set Rx IF attenuation to 30 dB: ", end="", flush=True)
    if rx.set_if_attenuator(30):
        print("OK")
    else:
        print("FAIL")
        return False

    # If we got this far then all tests passed
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EMA-LB Rx In-System Test")
    parser.add_argument("-f", "--frequency", help="frequency in MHz")
    args = parser.parse_args()
    if run_test(args.frequency):
        print("OK")
    else:
        print("FAIL")
