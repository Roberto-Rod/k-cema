#!/usr/bin/env python3
#!/usr/bin/env python3
# PA calibration routine based on the algorithm in:
# http://bitbucket.kirintec.local/projects/MS/repos/mercury/browse/UI/desktop/mercuryrftest/PaCalibration.cpp
# commit ID: 53443ff544d
#
# NOTE: Mercury hunts for levelled and saturated power. K-CEMA does not hunt for saturated power as the
# Power Amplifier stage output could over-power the Transmit/Receive switch which follows the PA stage
import argparse
import datetime
import math
import os

from band import *
from adf4355 import *
from ad9162 import *
from ad9528 import *
from dds import *
from external_attenuator import *
from fans import *
from hardware_unit_config import *
from ipam import *
from logger import *
from mcp4728 import *
from pcm import *
from power_meter import *
from power_supplies import *
from rf_control import *
from serial_number import *
from synth import *
from xcvr_control import *

DEBUG = False
FILE_ROOT = "/run/media/mmcblk0p2"
CAL_DIR = FILE_ROOT + "/calibration/"
LOG_DIR = FILE_ROOT + "/log/"
CAL_FILE_DDS = "pa_cal.csv"
CAL_FILE_DAC = "pa_cal_dac.csv"
LOG_FILE_DDS = "pa_cal.log"
LOG_FILE_DAC = "pa_cal_dac.log"

XCVR_ATT_MAX_MILLI_DB = 41950
ATT_MAX_DB = 52.75
ATT_STEP_MIN_DB = 0.25
COMPRESSION_FAIL_COUNT = 2
POWER_HIGH_FAIL_DB = 1.5
# Transceiver test tone amplitude (0 dBFS)
XCVR_TEST_TONE_AMP = 0x20000

fans_on_temperature = {IPAMPowerClass.VEHICLE: {Band.LOW: 55.0, Band.MID: 55.0, Band.HIGH: 45.0},
                       IPAMPowerClass.MANPACK: {Band.LOW: 50.0, Band.MID: 50.0, Band.HIGH: 50.0, Band.EXT_HIGH: 50.0}}

fans_drive_temperature = {IPAMPowerClass.VEHICLE: {Band.LOW: 60.0, Band.MID: 60.0, Band.HIGH: 50.0},
                          IPAMPowerClass.MANPACK: {Band.LOW: 55.0, Band.MID: 55.0, Band.HIGH: 50.0, Band.EXT_HIGH: 55.0}}

fan_drive_number = {IPAMPowerClass.VEHICLE: {Band.LOW: 2, Band.MID: 2, Band.HIGH: 2},
                    IPAMPowerClass.MANPACK: {Band.LOW: 1, Band.MID: 1, Band.HIGH: 1, Band.EXT_HIGH: 2}}

# The maximum change in temperature over 10 seconds to determine that IPAM has warmed up...
temperature_stabilisation_delta = 2.0

band_name = {Band.LOW: "low", Band.MID: "mid", Band.HIGH: "high", Band.EXT_HIGH: "high"}

voltage = {Band.LOW: 30, Band.MID: 32, Band.HIGH: 30, Band.EXT_HIGH: 30}

base_target_power_dBm = {IPAMPowerClass.VEHICLE: {Band.LOW: 50, Band.MID: 50, Band.HIGH: 46},
                         IPAMPowerClass.MANPACK: {Band.LOW: 41.76, Band.MID: 41.76, Band.HIGH: 41.76, Band.EXT_HIGH: 41.76}}

TEST_POINTS = {
"DDS": [
    # Band,     Path, Start Freq., Stop Freq., Step, Start Att, Att Step per, Power Monitor, Min Pass,  Target
    #                       (MHz)       (MHz) (MHz)       (dB)  per Freq (dB)    Range (dB)  Power (dB) Offset (dB)
    [Band.LOW,    0,          20,        520,   25,      40.0,         15.0,           30,       -0.5,     0.0],

    [Band.MID,    0,         400,        500,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    0,         525,        525,   25,      30.0,         15.0,           30,       -1.0,     0.0],
    [Band.MID,    0,         550,       1450,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    0,        1475,       1500,   25,      30.0,         15.0,           30,       -1.0,     0.0],
    [Band.MID,    1,        1480,       1555,   25,      30.0,         15.0,           30,       -1.0,     0.0],
    [Band.MID,    1,        1580,       1880,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    2,        1850,       1925,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    2,        1950,       2000,   25,      30.0,         15.0,           30,       -1.0,     0.0],
    [Band.MID,    2,        2025,       2100,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    2,        2125,       2200,   25,      30.0,         15.0,           30,       -1.0,     0.0],
    [Band.MID,    2,        2225,       2250,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    3,        2250,       2500,   25,      30.0,         15.0,           30,       -0.5,     0.0],
    [Band.MID,    4,        2500,       2700,   25,      30.0,         15.0,           30,       -0.5,     0.0],

    [Band.HIGH,   0,        1800,       1880,   20,      50.0,         30.0,           30,       -0.5,     0.0],  # MB 1 (1)
    [Band.HIGH,   1,        1850,       2250,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # MB 2 (2)
    [Band.HIGH,   2,        2250,       2500,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # MB 3 (3)
    [Band.HIGH,   3,        2400,       3400,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # HB 1 (9)
    [Band.HIGH,   4,        3400,       4600,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # HB 2 (10)
    [Band.HIGH,   5,        4600,       5375,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # HB 3 (11)
    [Band.HIGH,   5,        5400,       6000,   25,      50.0,         30.0,           30,       -0.5,     0.0],  # HB 3 (11)

    [Band.EXT_HIGH, 6,      5700,       5700,    1,      50.0,         30.0,           30,       -0.5,    -1.76], # 10 Watts
    [Band.EXT_HIGH, 6,      5725,       5725,    1,      50.0,         30.0,           30,       -0.5,    -1.58], # These are single points
    [Band.EXT_HIGH, 6,      5750,       5750,    1,      50.0,         30.0,           30,       -0.5,    -1.41], # range doesn't allow a step of 0
    [Band.EXT_HIGH, 6,      5775,       5775,    1,      50.0,         30.0,           30,       -0.5,    -1.25], # so step beyond the end frequency
    [Band.EXT_HIGH, 6,      5800,       5800,    1,      50.0,         30.0,           30,       -0.5,    -1.09], # only one point will be tested
    [Band.EXT_HIGH, 6,      5825,       5825,    1,      50.0,         30.0,           30,       -0.5,    -0.94],
    [Band.EXT_HIGH, 6,      5850,       5850,    1,      50.0,         30.0,           30,       -0.5,    -0.79],
    [Band.EXT_HIGH, 6,      5875,       5875,    1,      50.0,         30.0,           30,       -0.5,    -0.65],
    [Band.EXT_HIGH, 6,      5900,       5900,    1,      50.0,         30.0,           30,       -0.5,    -0.51],
    [Band.EXT_HIGH, 6,      5925,       5925,    1,      50.0,         30.0,           30,       -0.5,    -0.38],
    [Band.EXT_HIGH, 6,      5950,       5950,    1,      50.0,         30.0,           30,       -0.5,    -0.25],
    [Band.EXT_HIGH, 6,      5975,       5975,    1,      50.0,         30.0,           30,       -0.5,    -0.12],
    [Band.EXT_HIGH, 6,      6000,       8000,   25,      50.0,         30.0,           30,       -0.5,     0.0]   # 15 Watts
],
"DAC": [
    # Band,     Path, Start Freq., Stop Freq., Step, Start Att, Att Step per, Power Monitor, Min Pass,  Target
    #                       (MHz)       (MHz) (MHz)       (dB)  per Freq (dB)    Range (dB)  Power (dB) Offset (dB)
    [Band.LOW, 0, 20, 520, 25, 40.0, 15.0, 30, -0.5, 0.0],

    [Band.MID, 0, 400, 825, 25, 30.0, 15.0, 30, -1.0, 0.0],
    [Band.MID, 1, 625, 1485, 25, 30.0, 15.0, 30, -1.0, 0.0],
    [Band.MID, 2, 1285, 2600, 25, 30.0, 15.0, 30, -1.0, 0.0],
    [Band.MID, 3, 2400, 2700, 25, 30.0, 15.0, 30, -1.0, 0.0],

    [Band.HIGH, 2, 1800, 2600, 20, 50.0, 30.0, 30, -0.5, 0.0],
    [Band.HIGH, 3, 2400, 6000, 25, 50.0, 30.0, 30, -0.5, 0.0],

    [Band.EXT_HIGH, 4, 5700, 5700, 1, 50.0, 30.0, 30, -0.5, -1.76],  # 10 Watts
    [Band.EXT_HIGH, 4, 5725, 5725, 1, 50.0, 30.0, 30, -0.5, -1.58],  # These are single points
    [Band.EXT_HIGH, 4, 5750, 5750, 1, 50.0, 30.0, 30, -0.5, -1.41],  # range doesn't allow a step of 0
    [Band.EXT_HIGH, 4, 5775, 5775, 1, 50.0, 30.0, 30, -0.5, -1.25],  # so step beyond the end frequency
    [Band.EXT_HIGH, 4, 5800, 5800, 1, 50.0, 30.0, 30, -0.5, -1.09],  # only one point will be tested
    [Band.EXT_HIGH, 4, 5825, 5825, 1, 50.0, 30.0, 30, -0.5, -0.94],
    [Band.EXT_HIGH, 4, 5850, 5850, 1, 50.0, 30.0, 30, -0.5, -0.79],
    [Band.EXT_HIGH, 4, 5875, 5875, 1, 50.0, 30.0, 30, -0.5, -0.65],
    [Band.EXT_HIGH, 4, 5900, 5900, 1, 50.0, 30.0, 30, -0.5, -0.51],
    [Band.EXT_HIGH, 4, 5925, 5925, 1, 50.0, 30.0, 30, -0.5, -0.38],
    [Band.EXT_HIGH, 4, 5950, 5950, 1, 50.0, 30.0, 30, -0.5, -0.25],
    [Band.EXT_HIGH, 4, 5975, 5975, 1, 50.0, 30.0, 30, -0.5, -0.12],
    [Band.EXT_HIGH, 4, 6000, 8000, 25, 50.0, 30.0, 30, -0.5, 0.0]  # 15 Watts
]}
# Note that Power Monitor Range is used to define the minimum power below the target power that
# is used to calculate the power monitor slope and offset.


def run_test(extended_high, use_dac, pms_ip_addr=None):
    ok = True
    include_temperature = use_dac
    if include_temperature:
        cal_file_version = "0.4"
    else:
        cal_file_version = "0.3"
    serial = SerialNumber.get_serial(Module.EMA)
    ehb_ntm = False
    xcvr = None
    start = time.process_time()
    fans = Fans()
    fans.initialise()
    print()
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if use_dac:
        log_file = LOG_DIR + LOG_FILE_DAC
    else:
        log_file = LOG_DIR + LOG_FILE_DDS
    sys.stdout = Logger(log_file)
    print("test_pa_calibrate")
    print("-----------------")
    print("Serial number: {}".format(serial))
    print("Writing file version: {}".format(cal_file_version))
    print("Disable Tx power supplies: ", end="")
    IPAM.enable_power(False)
    DDS.enable_power(False)
    PowerSupplies.tx_en(False)
    PowerSupplies.rail_3v6_en(False)
    PowerSupplies.rail_5v5_en(False)
    time.sleep(2)
    print("OK")
    PowerSupplies.rail_3v6_en(True)  # Enable +3V6 so that we can read NTM RF Board ID
    time.sleep(0.5)
    status, config = get_config_info(AssemblyType.NTM_RF_LB)
    if status:
        try:
            if "Assembly Part Number" in config.keys():
                assy_nr = config["Assembly Part Number"]
                if assy_nr.startswith("KT-000-0202"):
                    ehb_ntm = True
        except Exception:
            print("Could not get NTM RF Board Part Number")
    print("Using eHB NTM: {}".format(ehb_ntm))
    print("Using DAC: {}".format(use_dac))

    pm = PowerMeter()
    print("Searching for Power Meter Service: ", end="", flush=True)
    if pm.find(pms_ip_addr):
        print("Power Meter Service found at {}:{}".format(pm.address,str(pm.port)))
        print("Connect to power meter: ", end="", flush=True)
        if pm.connect():
            print("OK")
            print("Power meter details: {}".format(pm.description))
            # Zero power meter
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

    print("Enable IPAM: ", end="", flush=True)
    IPAM.enable_power(True)
    if IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S) and IPAM.prepare_power_monitor():
        print("OK")
    else:
        print("FAIL - IPAM did not become ready")
        terminate_test()
        return False

    print("Get IPAM band: ", end="", flush=True)
    band = IPAM.get_rf_band()
    if band != Band.UNKNOWN:
        print("OK [{}]".format(band))
    else:
        print("FAIL [{}]".format(band))
        terminate_test()
        return False

    if use_dac and band != Band.LOW:
        xcvr = XcvrControl()
        print("Connect to transceiver driver...")
        if not xcvr.connect():
            print("ERROR: Failed to connect to transceiver driver")
            return False

    print("Get IPAM power class: ", end="", flush=True)
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

    if use_dac:
        cal_file_name = CAL_FILE_DAC
    else:
        cal_file_name = CAL_FILE_DDS
    print("Open {}{} for writing: ".format(CAL_DIR, cal_file_name), end="")
    try:
        # Test if file already exists
        cal_file = CAL_DIR + cal_file_name
        cal_file_exists = os.path.isfile(cal_file)
        if not cal_file_exists:
            # Create directory if it does not exist
            os.makedirs(CAL_DIR, exist_ok=True)
        lines = []

        # If performing extended high-band calibration and cal file already exists then read in existing cal lines
        if extended_high and cal_file_exists:
            found_header = False
            f = open(cal_file, "r")
            for line in f.readlines():
                # Store all the calibration lines which do not start with path 4 when using DAC / path 6 when using DDS
                ehb_line = (use_dac and line.startswith("4,")) or line.startswith("6,")
                if found_header and not ehb_line:
                    lines.append(line)
                if line.startswith("path,"):
                    found_header = True
            f.close()
        # Open file for writing
        f = open(cal_file, "w")
        # Write header
        f.write("file_version,{}\n".format(cal_file_version))
        f.write("serial,{}\n".format(serial))
        f.write("band,{}\n".format(band_name[band]))
        f.write("power,{:.2f}\n".format(round(base_target_power_dBm[power_class][band], 2)))
        f.write("voltage,{}\n".format(voltage[band]))
        f.write("\n")
        if include_temperature:
            f.write("path,freq_Hz,att_sat,att_level,pm_slope,pm_offset,temperature\n")
        else:
            f.write("path,freq_Hz,att_sat,att_level,pm_slope,pm_offset\n")
        # Write the previously stored lines if there are any
        f.writelines(lines)
        print("OK")
    except:
        print("FAIL")
        terminate_test()
        return False

    # File opened, Power Meter connected now initialise the hardware
    print("Set PCM to +{} V: ".format(voltage[band]), end="", flush=True)
    if PCM.set_voltage(voltage[band]):
        print("OK")
    else:
        print("FAIL")
        terminate_test()
        return False

    print("Enable Tx power supplies: ", end="")
    if use_dac and Band != Band.LOW:
        PowerSupplies.rail_1v3_en()
        PowerSupplies.rail_2v1_en()
    PowerSupplies.rail_3v6_en()
    PowerSupplies.rail_5v5_en()
    PowerSupplies.tx_en()
    print("OK")
    dac = None
    dds = None
    if use_dac:
        if band == Band.LOW:
            print("Enable DAC power supplies: ", end="", flush=True)
            PowerSupplies.rail_neg_1v8_en()
            PowerSupplies.tx_dac_en()
            for attempts in range(10):
                print(".", end="", flush=True)
                time.sleep(1)
                if PowerSupplies.tx_dac_pgood():
                    print("OK")
                    break
            if not PowerSupplies.tx_dac_pgood():
                print("FAIL - PGOOD not asserted")
                terminate_test()
                return False
            print("Initialise DAC synth: ", end="")
            dac_synth = ADF4355()
            dac_synth.enable_device()
            dac_synth.set_synth_5000_megahertz()
            print("OK")
            print("Initialise DAC: ", end="")
            dac = AD9162()
            dac.initialise()
            print("OK")
        elif xcvr is not None:
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
            # Run the transceiver initialisation
            print("Initialise transceiver device (typ. 45 seconds)...", flush=True)
            if not xcvr.initialise():
                print("ERROR: Failed to initialise transceiver")
                terminate_test()
                return False
            print("Enable Tx mode: ", end="", flush=True)
            if not xcvr.enable_tx_mode():
                print("ERROR: Failed to enter Tx mode")
                terminate_test()
                return False
            print("OK")
            print("Set Tx attenuation: ", end="", flush=True)
            if not xcvr.set_tx_att(XCVR_ATT_MAX_MILLI_DB):
                print("ERROR: Failed to set Tx attenuation")
                terminate_test()
                return False
            print("OK")
            print("Enable NTM RF Tx path: ", end="", flush=True)
            if not xcvr.tx_en():
                print("ERROR: Failed to enable NTM RF Tx")
                terminate_test()
                return False
            print("OK")
            print("Enable test tone JESD204B source: ", end="", flush=True)
            if not xcvr.jesd204b_stream_select(JESD204BSource.Tone):
                print("ERROR")
                terminate_test()
                return False
            print("OK")
            print("Set test tone amplitude: ", end="", flush=True)
            if not xcvr.set_test_tone_amplitude(XCVR_TEST_TONE_AMP):
                print("ERROR")
                terminate_test()
                return False
            print("OK")
        else:
            print("ERROR - transceiver not initialised")
            terminate_test()
            return False
    else:
        print("Initialise DDS synth: ", end="", flush=True)
        Synth.initialise()
        if Synth.is_locked():
            print("OK")
        else:
            print("FAIL - not locked")
            terminate_test()
            return False
        print("Initialise DDS: ", end="")
        dds = DDS()
        dds.initialise()
        print("OK")

    print("Set source att to 0 dB: ", end="", flush=True)
    RFControl.set_source_att(0)
    print("OK")

    print("Set Tx Att to 0 dB: ", end="", flush=True)
    RFControl.enable_tx_att_override()
    RFControl.set_tx_att(0)
    print("OK")

    print("Set doubler att to {} dB: ".format(ATT_MAX_DB), end="", flush=True)
    RFControl.set_doubler_att(ATT_MAX_DB)
    RFControl.en_doubler_att_20_dB(False)
    print("OK")

    print("Unmute IPAM: ", end="", flush=True)
    IPAM.force_mute(False)
    print("OK")

    target_power_W = (10 ** (base_target_power_dBm[power_class][band]/10)) / 1000
    print("Target Power: {:.2f} dBm ({:.1f} W)".format(base_target_power_dBm[power_class][band], target_power_W))

    min_achieved_power_dBm = 100
    max_achieved_power_dBm = -100
    min_power_freq_MHz = 0
    max_power_freq_MHz = 0
    if use_dac and Band != Band.LOW:
        att_max_dB = XCVR_ATT_MAX_MILLI_DB / 1000
    else:
        att_max_dB = ATT_MAX_DB
    
    warmed_up = False
    fans_on = False

    # Loop through test points
    first_point = True
    test_set = "DAC" if use_dac else "DDS"
    for test_point in TEST_POINTS[test_set]:
        # Skip this test point if it is not in the band we are calibrating
        if test_point[0] != band:
            continue
        path = test_point[1]
        start_MHz = test_point[2]
        stop_MHz = test_point[3]
        step_MHz = test_point[4]
        att_dB = test_point[5]
        if att_dB > att_max_dB:
            att_dB = att_max_dB
        att_step_per_freq_dB = test_point[6]
        power_monitor_range_dB = test_point[7]
        min_pass_power_dBm = base_target_power_dBm[power_class][band] + test_point[8]
        target_power_dBm = base_target_power_dBm[power_class][band] + test_point[9]  # Apply target power offset
        att_step_dB = 0

        # Loop through the frequencies
        for freq_MHz in range(start_MHz, stop_MHz + step_MHz, step_MHz):
            # Skip this frequency if it is beyond the stop frequency (the table shouldn't be configured like this
            # as it means that there are not a whole number of steps between the start and stop frequencies)
            if freq_MHz > stop_MHz:
                continue
            freq_Hz = int(freq_MHz * 1e6)
            dds_freq_Hz = freq_Hz / RFControl.get_multiplier(path, band, ehb_ntm)

            if band == Band.EXT_HIGH:
                if_mhz = 5000
                lo_mhz = (freq_Hz/1e6) + if_mhz
                xcvr_mhz = if_mhz
            else:
                xcvr_mhz = freq_Hz/1e6

            # Set Power Meter offset
            power_meter_offset_dB = ExternalAttenuator.get_att(band, freq_MHz)
            print("Set power meter offset to {:.2f} dB: ".format(power_meter_offset_dB), end="", flush=True)
            if pm.set_offset(power_meter_offset_dB) and pm.set_average_count(1):
                print("OK")
                power_meter_average_enabled = False
            else:
                print("FAIL")
                terminate_test()
                return False

            if use_dac:
                if band == Band.LOW:
                    # Set DAC frequency
                    dac.set_frequency(freq_Hz)
                else:
                    # Set transceiver Rx centre frequency
                    if (band != Band.EXT_HIGH) or first_point:
                        print("Set XCVR centre frequency to {} MHz: ".format(xcvr_mhz), end="", flush=True)
                        if xcvr.set_frequency(xcvr_mhz):
                            print("OK")
                            first_point = False
                        else:
                            print("FAIL")
                            terminate_test()
                            return False

                    # Set synth frequency in eHB case
                    if band == Band.EXT_HIGH:
                        print("Set synth frequency to {} MHz: ".format(lo_mhz), end="", flush=True)
                        if xcvr.set_synth(lo_mhz):
                            print("OK")
                        else:
                            print("FAIL")
                            terminate_test()
                            return False

                    # Set XCVR Tx path
                    print("Set XCVR Tx path to {}: ".format(path), end="", flush=True)
                    if xcvr.set_tx_path(path):
                        print("OK")
                    else:
                        print("FAIL")
                        terminate_test()
                        return False

                    # Set LO path
                    if path == 4:
                        print("Set XCVR LO path to 1: ", end="", flush=True)
                        RFControl.set_xcvr_path(1)
                    else:
                        print("Set XCVR LO path to 0: ", end="", flush=True)
                        RFControl.set_xcvr_path(0)
                    print("OK")
            else:
                # Set DDS frequency
                dds.set_frequency(dds_freq_Hz)
                # Set ASF to calibrated DDS output for mid/high band
                if band == Band.MID or band == band.HIGH or band == band.EXT_HIGH:
                    asf = dds.get_calibrated_asf(dds_freq_Hz)
                    print("f {} MHz, ASF {}, {}, path {}: ".format(freq_MHz, asf, band, path))
                    dds.set_asf(asf, True)
                    RFControl.set_tx_path(path, band, ehb_ntm)

            cal_point_found = False
            compression_fail = 0
            last_power_dBm = -100.0
            min_error_dB = 100.0
            final_narrowing = False
            narrowing_error_dB = 100.0

            # Storage for power monitor cal points
            pm_point = []

            while not cal_point_found and compression_fail < COMPRESSION_FAIL_COUNT:
                # Set attenuation, for low band set DDS/DAC ASF, for mid/high-band
                # set post-doubler/multiplier attenuator
                if band == Band.LOW:
                    if use_dac:
                        dac.set_att_dB(att_dB)
                    else:
                        dds.set_att_dB(att_dB, True)
                else:
                    if use_dac:
                        att_milli_dB = att_dB * 1000
                        # http://jira.kirintec.local/browse/KCEMA-1310 work-around write Tx att twice...
                        if not (xcvr.set_tx_att(att_milli_dB) and xcvr.set_tx_att(att_milli_dB)):
                            print("ERROR - failed to set transceiver Tx attenuation")
                            terminate_test()
                            return False
                        time.sleep(0.1)
                    else:
                        RFControl.set_doubler_att(att_dB)
                # Read power
                pm.frequency_Hz = freq_Hz
                power_dBm = pm.get_reading_dBm()
                error_dB = abs(power_dBm - target_power_dBm)
                delta_dBm = power_dBm - last_power_dBm
                
                print("p {:.2f}, t {:.2f}, e {:.2f}, a {:.2f}".format(power_dBm, target_power_dBm, error_dB, att_dB), flush=True)

                # Do we have the first power monitor reading yet?
                # Use the first point we find that is at an output power within x dB of the target
                if len(pm_point) == 0 and warmed_up and error_dB <= power_monitor_range_dB:
                    # Read and store IPAM forward/reverse power
                    pm_values = IPAM.get_power_monitor_readings()
                    print("pm point 0: {}".format(pm_values["fwd"]))
                    pm_point.append({"dBm": power_dBm, "mV": pm_values["fwd"] * 5000.0 / 4096.0})

                # If the point we are on is the closest to target that we have seen then store the values.
                # If we are in the final narrowing phase then continue for as long as we are finding smaller errors
                # as soon as the error is growing again, stop searching, we have found the cal point and
                # it will already be stored in min_error_dB / att_lev_dB / power_lev_dBm
                if error_dB < min_error_dB:
                    min_error_dB = error_dB
                    att_lev_dB = att_dB
                    power_lev_dBm = power_dBm
                if final_narrowing:
                    if error_dB > narrowing_error_dB:
                        cal_point_found = True
                    else:
                        narrowing_error_dB = error_dB
                # If we have hit or exceeded the target power then enter final narrowing phase:
                # change direction, use minimum attenuator step and reset stored minimum error
                elif power_dBm >= target_power_dBm:
                    narrowing_error_dB = error_dB
                    final_narrowing = True
                # Check for compression, when we are using 1.0 dB steps a <= 0.1 dB change indicates compression
                # check that power is high enough to ensure we are not just at low power and in a non-linear
                # part of the NTM attenuator range
                elif att_step_dB == 1.0 and delta_dBm <= 0.1:
                    if power_dBm > min_pass_power_dBm:
                        cal_point_found = True
                    elif att_dB < 21.0:
                        compression_fail += 1
                else:
                    compression_fail = 0
                # Check for max. attenuation - if we have hit maximum attenuation and are achieving power then
                # set cal point found to true
                if att_dB == att_max_dB and power_dBm > min_pass_power_dBm:
                    cal_point_found = True

                # We have hit target power, have we warmed up yet?
                if cal_point_found and not warmed_up:
                    # Wind back to the start conditions so that the first point is calibrated whilst warm
                    cal_point_found = False
                    att_dB = test_point[5]
                    if att_dB > att_max_dB:
                        att_dB = att_max_dB
                    att_step_dB = 0
                    last_power_dBm = -100.0
                    min_error_dB = 100.0
                    final_narrowing = False
                    narrowing_error_dB = 100.0

                    # Having got to full power, wait for warm up, monitor temperature change every 10 seconds
                    # and wait for this to stablisie to within 0.15 degrees
                    # Print reading every 1 second so that user can see the process is active and use the average
                    # over ten seconds
                    print("Wait for warm up...", flush=True)
                    t_prev = -100
                    t_acc = 0
                    count = 1
                    while not warmed_up:
                        t = IPAM.get_temperature()
                        print("Temperature: {:.2f} degC".format(t), flush=True)
                        if t >= fans_on_temperature[power_class][band]:
                            # Set fans based on a fixed expected temperature
                            # do this as the calibration routine causes power to go up and down and we don't
                            # want fans hunting
                            single_fan = (fan_drive_number[power_class][band] == 1)
                            fans.set_temperature(fans_drive_temperature[power_class][band], single_fan)
                            fans_on = True
                        t_acc += t
                        if count == 10:
                            count = 1
                            t = t_acc / 10
                            t_acc = 0
                            t_delta = abs(t - t_prev)
                            print("Ten Second Average: {:.2f} degC".format(t), end="", flush=True)
                            if t_prev != -100:
                                print(" (change: {:.2f} degC)".format(t_delta), flush=True)
                            else:
                                print("")
                            if fans_on and t_delta <= temperature_stabilisation_delta:
                                warmed_up = True
                                print("*** WARMED UP ***", flush=True)
                            t_prev = t
                            t = 0
                        else:
                            count += 1
                        time.sleep(1.0)
                    continue

                # If we are about to leave the loop due to PA compression but we have already seen minimum power
                # then set cal point found to True
                if compression_fail == COMPRESSION_FAIL_COUNT and power_lev_dBm >= min_pass_power_dBm:
                    cal_point_found = True
                    # Set attenuation back to the "cal point" before the power monitor reading is taken
                    if band == Band.LOW:
                        if use_dac:
                            dac.set_att_dB(att_lev_dB)
                        else:
                            dds.set_att_dB(att_lev_dB, True)
                    else:
                        if use_dac:
                            att_milli_dB = att_lev_dB * 1000
                            # http://jira.kirintec.local/browse/KCEMA-1310 work-around write Tx att twice...
                            if not (xcvr.set_tx_att(att_milli_dB) and xcvr.set_tx_att(att_milli_dB)):
                                print("ERROR - failed to set transceiver Tx attenuation {}".format(att_milli_dB))
                                terminate_test()
                                return False
                        else:
                            RFControl.set_doubler_att(att_lev_dB)

                if cal_point_found:
                    # Read and store IPAM forward/reverse power
                    pm_values = IPAM.get_power_monitor_readings()
                    print("pm point 1: {}".format(pm_values["fwd"]))
                    pm_point.append({"dBm": power_dBm, "mV": pm_values["fwd"] * 5000.0 / 4096.0})
                    break

                # If we are in the final narrowing-in phase then step attenuator up (input power down)
                # by the smallest step
                if final_narrowing:
                    att_dB += ATT_STEP_MIN_DB
                    compression_check = False
                    if att_dB > att_max_dB:
                        # Attenuator reached maximum, this should never happen and it will cause the test to fail
                        break
                else:
                    # If we have run out of input power then just stop, this should never happen
                    # and it will cause the test to fail
                    if att_dB == 0:
                        break

                    # Pick nearest step to 1.0 dB and use 1.0 dB steps once we are within 3.0 dB of the target
                    # to facilitate the compression check.
                    att_step_dB = round(error_dB, 0)
                    att_step_dB -= 3
                    if att_step_dB <= 3.0:
                        att_step_dB = 1.0
                        
                    # On High Band don't make any steps bigger than 6 dB
                    if band == Band.HIGH or band == Band.EXT_HIGH:
                        if att_step_dB > 6.0:
                            att_step_dB = 6.0

                    # Input power heading up, reduce attenuation
                    att_dB -= att_step_dB
                    if att_dB < 0:
                        att_dB = 0
                    
                    if not power_meter_average_enabled and error_dB <= 1.0:
                        pm.set_average_count(8)
                        power_meter_average_enabled = True

                last_power_dBm = power_dBm
            # end while not cal_point_found and compression_fail < COMPRESSION_FAIL_COUNT

            if cal_point_found:
                delta_dB = pm_point[1]["dBm"] - pm_point[0]["dBm"]
                delta_mV = pm_point[1]["mV"] - pm_point[0]["mV"]
                # Avoid divide by zero
                if delta_dB == 0:
                    delta_dB = 0.001
                slope_mv_per_dB = delta_mV / delta_dB
                if slope_mv_per_dB != 0:
                    offset_dBm = pm_point[0]["dBm"] - (pm_point[0]["mV"] / slope_mv_per_dB)
                else:
                    offset_dBm = pm_point[0]["dBm"]
                if power_lev_dBm < min_achieved_power_dBm:
                    min_achieved_power_dBm = power_lev_dBm
                    min_power_freq_MHz = freq_MHz
                if power_lev_dBm > max_achieved_power_dBm:
                    max_achieved_power_dBm = power_lev_dBm
                    max_power_freq_MHz = freq_MHz

                # Read IPAM DC current, DC power and temperature
                manpack = (power_class == IPAMPowerClass.MANPACK)
                curr_A = IPAM.get_input_current(manpack)
                dc_power_W = IPAM.get_input_power(manpack)
                rf_power_W = (10 ** (power_dBm/10)) / 1000
                eff = (rf_power_W / dc_power_W) * 100
                temp_C = IPAM.get_temperature()
                    
                print("> path {}, freq {} MHz, att {:.2f} dB, power {:.2f} dBm, slope {:.2f} mV/dB, offset {:.2f} dBm, "
                      "temp {:.1f} C, curr {:.1f} A, eff {:.1f} %".format(path, freq_MHz, att_lev_dB, power_lev_dBm,
                                                                          slope_mv_per_dB, offset_dBm, temp_C, curr_A,
                                                                          eff), flush=True)
                if power_lev_dBm > target_power_dBm + POWER_HIGH_FAIL_DB:
                    print("FAIL - overpower")
                    terminate_test()
                    return False
                try:
                    # Write line to file
                    pm_slope = int(round(slope_mv_per_dB * 1000.0, 0))
                    pm_offset = int(round(offset_dBm * 1000.0, 0))
                    if include_temperature:
                        f.write("{},{},{},{},{},{},{:.1f}\n".format(path, freq_Hz, int(att_lev_dB * 4),
                                                                    int(att_lev_dB * 4), pm_slope, pm_offset, temp_C))
                    else:
                        f.write("{},{},{},{},{},{}\n".format(path, freq_Hz, int(att_lev_dB * 4),
                                                             int(att_lev_dB * 4), pm_slope, pm_offset))
                except:
                    print("FAIL - file write error")
                    terminate_test()
                    return False
            else:
                print("FAIL - could not find calibration point (PA may not be achieving minimum power)")
                if not DEBUG:
                    terminate_test()
                    return False

            # Increase attenuation before moving to next frequency point and set to nearest whole dB
            att_dB += att_step_per_freq_dB
            att_dB = round(att_dB, 0)
            if att_dB > att_max_dB:
                att_dB = math.floor(att_max_dB)

    # If we got this far then all tests passed
    print("\nMinimum achieved power: {:.2f} dBm (at {} MHz)".format(min_achieved_power_dBm, min_power_freq_MHz))
    print("Maximum achieved power: {:.2f} dBm (at {} MHz)".format(max_achieved_power_dBm, max_power_freq_MHz))
    terminate_test()
    return ok


def terminate_test():
    IPAM.enable_power(False)
    DDS.enable_power(False)
    PowerSupplies.disable_all()
    fans = Fans()
    fans.initialise()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control timing register")
    parser.add_argument("-n", "--no_kill_no_duration", help="Don't kill apps and don't log test duration", action="store_true")
    parser.add_argument("-e", "--extended_high", help="Calibrate Extended High Band port", action="store_true")
    parser.add_argument("-d", "--use_dac", help="Calibrate using DAC", action="store_true")
    parser.add_argument("-i", "--pms_ip_addr", help="Find Power Meter Service at specified IP address", default=None)
    args = parser.parse_args()
    if not args.no_kill_no_duration:
        os.system("/usr/bin/killall fetchandlaunchema")
        os.system("/usr/bin/killall KCemaEMAApp")
        os.system("/usr/bin/killall ema_app.bin")
        start_time = time.time()
    pm = PowerMeter()
    if not pm.find(args.pms_ip_addr):
        print("Could not find Power Meter Service, terminating test...")
    elif run_test(args.extended_high, args.use_dac, args.pms_ip_addr):
        print("\n*** OK - PA calibration passed ***\n")
        if not args.no_kill_no_duration:
            print("\n(PA calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds=round(time.time() - start_time, 0)))))
            print("\n*** Unmount mmcblk0p2 to ensure calibration and log files are saved ***\n")
    else:
        if not args.no_kill_no_duration:
            print("\n(PA calibration duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds=round(time.time() - start_time, 0)))))
        print("\n*** TEST FAILED ***\n")
