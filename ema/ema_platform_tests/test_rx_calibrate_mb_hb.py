#!/usr/bin/env python3
import argparse
import datetime
import os
from time import sleep

from ad9528 import *
from band import *
from dds import *
from external_attenuator import *
from hardware_unit_config import *
from ipam import *
from mcp4728 import *
from power_supplies import *
from rf_control import *
from rx_control import *
from serial_number import *
from signal_generator import *
from timing_control import *
from xcvr_control import *

FILE_ROOT = "/run/media/mmcblk0p2"
DIR_NAME = FILE_ROOT + "/calibration/"
FILE_NAME = "rx_cal.csv"

TEST_POINTS = [
    # Band, Preselector, Centre MHz, IF MHz, LNA Enabled:  (Input dBm, Min. dBFS),
    #                                        LNA Disabled: (Input dBm, Min. dBFS)
    [Band.MID,  0,  400, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  0,  525, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  0,  650, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  1,  550, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  1,  750, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  1,  950, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  1, 1050, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  2, 1100, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  2, 1200, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  2, 1450, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  3, 1350, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  3, 1600, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  3, 1850, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  3, 2100, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  3, 2250, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  4, 2150, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  4, 2400, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  4, 2650, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  4, 2900, 0, [-30, -30.0], [-20, -36.0]],
    [Band.MID,  4, 3050, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 3, 1800, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 3, 2025, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 3, 2250, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 4, 2150, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 4, 2400, 0, [-30, -31.0], [-20, -37.0]],
    [Band.HIGH, 4, 2650, 0, [-30, -31.0], [-20, -37.0]],
    [Band.HIGH, 4, 2900, 0, [-30, -31.0], [-20, -37.0]],
    [Band.HIGH, 4, 3050, 0, [-30, -30.0], [-20, -36.0]],
    [Band.HIGH, 5, 2950, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 3200, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 3450, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 3700, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 3950, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 4200, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 4450, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 5, 4650, 0, [-30, -35.0], [-20, -41.0]],
    [Band.HIGH, 6, 4550, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 4800, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 5050, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 5300, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 5550, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 5800, 0, [-20, -28.0], [-20, -44.0]],
    [Band.HIGH, 6, 6000, 0, [-20, -33.0], [-20, -49.0]],
    [Band.EXT_HIGH, 7, 5700, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 5950, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 6200, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 6450, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 6700, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 6950, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 7200, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 7450, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 7700, 0, [-30, -30.0], [-20, -41.0]],
    [Band.EXT_HIGH, 7, 8000, 0, [-30, -30.0], [-20, -41.0]]
]

BAND_NAME = {Band.LOW: "low", Band.MID: "mid", Band.HIGH: "high", Band.EXT_HIGH: "ext-high"}


def run_test(extended_high, sgs_ip_addr=None):
    print("test_rx_calibrate")
    print("-----------------")
    serial = SerialNumber.get_serial(Module.EMA)
    ehb_ntm = False
    status, config = get_config_info(AssemblyType.EMA_LB_R)
    if status:
        try:
            if "Assembly Part Number" in config.keys():
                assy_nr = config["Assembly Part Number"]
                if assy_nr.startswith("KT-950-0505"):
                    ehb_ntm = True
        except Exception:
            print("Could not get Assembly Part Number")
    print("Using eHB NTM: {}".format(ehb_ntm))
    tm = TimingControl()
    rx = RxControl()
    xcvr = XcvrControl()
    sg = SignalGenerator()
    print("Connect to transceiver driver...")
    if not xcvr.connect():
        print("ERROR: Failed to connect to transceiver driver")
        return False
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
        print("ERROR: Could not find SGS")
        return terminate_test(False)

    # Disable signal generator RF output
    print("Disable signal generator RF output: ", end="", flush=True)
    if sg.set_output_enable(False):
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Power cycle and enable Rx supplies
    print("Disable power supplies: ", end="", flush=True)
    IPAM.enable_power(False)
    DDS.enable_power(False)
    xcvr.reset(True)
    PowerSupplies.disable_all()
    sleep(2)
    print("OK")
    print("Enable Rx power supplies: ", end="", flush=True)
    PowerSupplies.rail_1v3_en(True)
    PowerSupplies.rail_2v1_en(True)
    PowerSupplies.rail_3v6_en(True)
    PowerSupplies.rail_5v3_en(True)
    PowerSupplies.rx_en(True)
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

    print("Get IPAM power class: ", end = "", flush = True)
    power_class = IPAM.get_power_class()
    if power_class != IPAMPowerClass.UNKNOWN:
        print("OK [{}]".format(power_class))
    else:
        print("FAIL [{}]".format(power_class))
        terminate_test()
        return False

    print("Using PA port: ", end="", flush=True)
    if extended_high:
        if band != Band.HIGH or power_class != IPAMPowerClass.MANPACK or not ehb_ntm:
            print("ERROR - Extended High Band calibration not supported in this device")
            print("  PA band: {}".format(band))
            print("  PA type: {}".format(power_class))
            print("  eHB NTM: {}".format(ehb_ntm))
            terminate_test()
            return False
        # Switch the IPAM to extended high band port and change the band that we are going to calibrate
        IPAM.set_pa_port(IPAM.PA_PORT_EXT)
        band = Band.EXT_HIGH
        print("extended")
    else:
        IPAM.set_pa_port(IPAM.PA_PORT_PRI)
        print("primary")

    if band != Band.MID and band != Band.HIGH and band != Band.EXT_HIGH:
        print("ERROR - test does not currently support {}".format(band()))
        return terminate_test(False)

    # Enable test mode to put IPAM into Rx
    print("Enable Tx/Rx Switch Rx Test Mode: ", end="", flush=True)
    if tm.enable_rx_test_mode():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    if band == Band.EXT_HIGH:
        # On eHB path, set xcvr path to 0 (this is the 400 MHz to 6000 MHz Tx path) to divert the LO to the Rx path
        RFControl.set_xcvr_path(0)

    # Trim Clock DAC to mid-rail
    print("Set Trim DAC to Mid-Rail: ", end="", flush=True)
    trim = MCP4728()
    if trim.set_dac_midscale():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Initialise Clock Generator
    print("Initialise Clock Generator: ", end="", flush=True)
    xcvr.reset(False)
    clk = AD9528()
    if clk.initialise():
        print("OK")
    else:
        print("FAIL")
        return terminate_test(False)

    # Set Rx preselector to band 7 = isolation
    print("Set Rx preselector to 7 (isolation): ", end="", flush=True)
    if rx.set_preselector(7):
        print("OK", flush=True)
    else:
        print("FAIL", flush=True)
        return terminate_test(False)

    # Run the transceiver initialisation
    print("Initialise transceiver device (typ. 45 seconds)...", flush=True)
    if not xcvr.initialise():
        print("ERROR: Failed to initialise transceiver")
        return terminate_test(False)

    sg_rf_prev_mhz = 0

    print("Open {}{} for writing: ".format(DIR_NAME, FILE_NAME), end="")

    try:
        # Test if file already exists
        cal_file = DIR_NAME + FILE_NAME
        cal_file_exists = os.path.isfile(cal_file)
        if not cal_file_exists:
            # Create directory if it does not exist
            os.makedirs(DIR_NAME, exist_ok=True)
        lines = []

        # If performing extended high-band calibration and cal file already exists then read in existing cal lines
        if extended_high and cal_file_exists:
            found_header = False
            f = open(cal_file, "r")
            for line in f.readlines():
                # Store all the calibration lines which do not start with preselector 7
                if found_header and not line.startswith("7,"):
                    lines.append(line)
                if line.startswith("presel,"):
                    found_header = True
            f.close()
        # Open file for writing
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
        # Write the previously stored lines if there are any
        f.writelines(lines)
        print("OK")
    except:
        print("FAIL")
        terminate_test(False)

    # Track the overall test result
    result = True
    first_point = True

    # Loop through test points
    for test_point in TEST_POINTS:
        if band == test_point[0]:
            print()
            preselector = test_point[1]
            centre_mhz = test_point[2]
            if_mhz = test_point[3]
            sg_rf_mhz = centre_mhz + if_mhz

            if band == Band.EXT_HIGH:
                if_mhz = 5000
                lo_mhz = centre_mhz + if_mhz
                xcvr_mhz = if_mhz
            else:
                xcvr_mhz = centre_mhz

            for lna_en in [True, False]:
                if lna_en:
                    param = test_point[4]
                else:
                    param = test_point[5]

                rf_in_dbm = param[0]
                sg_pwr_dbm = round(rf_in_dbm + ExternalAttenuator.get_att(band, sg_rf_mhz, Path.RX), 2)
                min_dbfs = param[1]

                # Set Rx LNA
                print("Set Rx LNA to {}: ".format("Enabled" if lna_en else "Disabled"), end="", flush=True)
                if rx.set_lna_enable(lna_en, band):
                    print("OK")
                else:
                    print("FAIL")
                    return terminate_test(False)

                # Set signal generator frequency
                if sg_rf_prev_mhz != sg_rf_mhz:
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

                # Enable signal generator RF output
                print("Enable signal generator RF output: ", end="", flush=True)
                if sg.set_output_enable(True):
                    print("OK")
                else:
                    print("FAIL")
                    return terminate_test(False)

                # Set transceiver Rx centre frequency
                if (band != Band.EXT_HIGH) or first_point:
                    print("Set XCVR centre frequency to {} MHz: ".format(xcvr_mhz), end="", flush=True)
                    if xcvr.set_frequency(xcvr_mhz):
                        print("OK")
                    else:
                        print("FAIL")
                        return terminate_test(False)

                # Set synth frequency in eHB case
                if band == Band.EXT_HIGH:
                    print("Set synth frequency to {} MHz: ".format(lo_mhz), end="", flush=True)
                    if xcvr.set_synth(lo_mhz):
                        print("OK")
                    else:
                        print("FAIL")
                        return terminate_test(False)

                # Get transceiver level
                print("Check transceiver received power", end="", flush=True)
                for i in range(10):
                    print(".", end="", flush=True)
                    sleep(1)
                xcvr_dbfs = xcvr.read_power()
                if xcvr_dbfs >= min_dbfs:
                    print("OK [{:.1f} dBFS]".format(xcvr_dbfs))
                else:
                    print("FAIL [{:.1f} dBFS]".format(xcvr_dbfs))
                    result = False

                # Disable signal generator output
                print("Disable signal generator RF output: ", end="", flush=True)
                if sg.set_output_enable(False):
                    print("OK")
                else:
                    print("FAIL")
                    return terminate_test(False)

                # Write cal point to file
                try:
                    rf_offset_dB = xcvr_dbfs - rf_in_dbm
                    if_offset_dB = 0
                    f.write("{},{},{},{},{:.1f},{:.1f}\n".format(preselector, centre_mhz, if_mhz, lna_en, rf_offset_dB, if_offset_dB))
                except:
                    print("FAIL - file write error")
                    terminate_test(False)

                first_point = False

    # End the test with result indicating pass or fail
    return terminate_test(result)


def terminate_test(ret_val):
    tm = TimingControl()
    tm.disable()
    IPAM.enable_power(False)
    PowerSupplies.disable_all()
    return ret_val


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control timing register")
    parser.add_argument("-n", "--no_kill_no_duration", help="Don't kill apps and don't log test duration", action="store_true")
    parser.add_argument("-e", "--extended_high", help="Calibrate Extended High Band port", action="store_true")
    parser.add_argument("-i", "--sgs_ip_addr", help="Find Signal Generator Service at specified IP address", default=None)
    args = parser.parse_args()
    if not args.no_kill_no_duration:
        os.system("/usr/bin/killall fetchandlaunchema")
        os.system("/usr/bin/killall KCemaEMAApp")
        os.system("/usr/bin/killall ema_app.bin")
        start_time = time.time()
    if run_test(args.extended_high, args.sgs_ip_addr):
        print("\n*** OK - Rx calibration passed ***\n")
        if not args.no_kill_no_duration:
            print("\n(Rx calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
            print("\n*** Unmount mmcblk0p2 to ensure calibration and log files are saved ***\n")
    else:
        if not args.no_kill_no_duration:
            print("\n(Rx calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** TEST FAILED ***\n")
