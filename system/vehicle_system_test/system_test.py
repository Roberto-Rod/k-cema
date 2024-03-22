#!/usr/bin/env python3
from power_meter_nrp import *
from s2p_file_reader import *
from band import *
from enum import Enum
from logger import *
from find_service import *
from ip_tools import *

import argparse
import enum
import ssh
import signal
import sys
import os
import time
import datetime

password_dict = {}


class AssemblyType(enum.Enum):
    UNKNOWN = 0,
    VEHICLE = 1,
    MANPACK = 2


# Class provided to run the final production test on a K-CEMA vehicle system
class SystemTest:
    TEST_VERSION = "1.3.2"
    TEST_DURATION_MINS = 20
    MANUAL_RX_TEST = False
    TEST_LOG_REL_DIR = "./test_logs/"
    TEST_CAL_REL_DIR = "./calibration/"

    ASSEMBLIES = [["KT-950-0424-00", AssemblyType.MANPACK],
                  ["KT-950-0472-00", AssemblyType.MANPACK],
                  ["KT-950-0345-00", AssemblyType.VEHICLE],
                  ["KT-950-0404-00", AssemblyType.VEHICLE]]

    ema_ssh_to_slot = []

    slot_name = {}
    slot_name[0] = "Slot 1"
    slot_name[1] = "Slot 2"
    slot_name[2] = "Slot 3"
    slot_name[3] = "Slot 4"
    slot_name[4] = "Slot 5"

    tx_attenuation_s2p_file = {}
    tx_attenuation_s2p_file[0] = [TEST_CAL_REL_DIR + "tx_attenuation_1.s2p"]
    tx_attenuation_s2p_file[1] = [TEST_CAL_REL_DIR + "tx_attenuation_2.s2p", TEST_CAL_REL_DIR + "tx_attenuation_2b.s2p"]
    tx_attenuation_s2p_file[2] = [TEST_CAL_REL_DIR + "tx_attenuation_3.s2p"]
    tx_attenuation_s2p_file[3] = [TEST_CAL_REL_DIR + "tx_attenuation_4.s2p"]
    tx_attenuation_s2p_file[4] = [TEST_CAL_REL_DIR + "tx_attenuation_5.s2p"]

    SANITY_CHECK_DBM = 40.0

    min_power_dBm = {AssemblyType.VEHICLE: {Band.LOW: 48.0, Band.MID: 47.0, Band.HIGH: 43.0},
                     AssemblyType.MANPACK: {Band.LOW: 39.8, Band.MID: 39.8, Band.HIGH: 39.8, Band.EXT_HIGH: 39.8}}

    min_hot_delta_dB = {AssemblyType.VEHICLE: {Band.LOW: -0.5, Band.MID: -0.5, Band.HIGH: -0.5},
                        AssemblyType.MANPACK: {Band.LOW: -0.5, Band.MID: -0.5, Band.HIGH: -0.5, Band.EXT_HIGH: -0.5}}

    hot_threshold_degrees_c = {AssemblyType.VEHICLE: {Band.LOW: 70, Band.MID: 70, Band.HIGH: 55},
                               AssemblyType.MANPACK: {Band.LOW: 70, Band.MID: 70, Band.HIGH: 70, Band.EXT_HIGH: 70}}

    RUN_FILE_ROOT = "/run/media/mmcblk1p2/run.sh"
    RUN_FILE_LAUNCHER = "/run/media/mmcblk1p2/app_launchers/01_csm_app/run.sh"

    # CSM channel 0 (case switch) tamper normally-closed configuration:
    # TEB=1, TIE=1, TCM=0, TPM=1, TDS=1, TCHI=0, CLR1_EXT=0, CLR1=1

    # CSM channel 1 (light sensor) & EMA (both channels) normally-open configuration:
    # TEB=1, TIE=1, TCM=1, TPM=0, TDS=0, TCHI=0, CLR1_EXT=0, CLR1=1

    CSM_GENERATE_RUN_FILE_CMD = "cd /tmp/test;python3 ./generate_run_file.py"
    CSM_READ_RUN_FILE_CMD = "cat {}"
    CSM_DISARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x14 0;/usr/sbin/i2cset -f -y 1 0x68 0x15 0"
    CSM_ARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x14 0xD1;/usr/sbin/i2cset -f -y 1 0x68 0x15 0xE1"
    CSM_SET_TAMPER_ABE_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x0A 0x20"
    CSM_GET_TAMPER_FLAGS = "/usr/sbin/i2cget -f -y 1 0x68 0xF"
    EMA_DISARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x14 0;/usr/sbin/i2cset -f -y 0 0x68 0x15 0"
    EMA_ARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x14 0xE1;/usr/sbin/i2cset -f -y 0 0x68 0x15 0xE1"
    EMA_SET_TAMPER_ABE_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x0A 0x20"
    EMA_GET_TAMPER_FLAGS = "/usr/sbin/i2cget -f -y 0 0x68 0xF"
    EMA_TEST_FULL_POWER_TONE_CMD = "cd /tmp/test;python3 ./sys_test_full_power_tone.py -v "
    EMA_TEST_INITIALISE_CMD = "cd /tmp/test;python3 ./sys_test_initialise.py -v"
    EMA_TEST_TERMINATE_CMD = "cd /tmp/test;python3 ./sys_test_terminate.py -v"
    EMA_TEST_IPAM_GET_TEMPERATURE_CMD = "cd /tmp/test;python3 ./sys_test_ipam_get_temperature.py -v"
    EMA_TEST_IPAM_SET_MUTE_CMD = "cd /tmp/test;python3 ./sys_test_ipam_set_mute.py -v "
    EMA_SET_DUMMY_PCM_CONFIG_CMD = "cd /tmp/test;python3 ./pcm_set_dummy_hw_config.py -v "
    EMA_TEST_PPS_CMD = "cd /tmp/test;python3 ./pps.py"
    EMA_IPAM_GET_BIT_CMD = "cd /tmp/test;python3 ./ipam.py -f"
    EMA_TEST_RX_LB_CMD = "cd /tmp/test;python3 ./sys_test_rx_lb.py -f {}"
    SET_CLOCK_CMD = "/bin/date +%Y%m%d%T -s '{:04d}{:02d}{:02d} {:02d}:{:02d}:{:02d}';/sbin/hwclock -w"

    SCRIPT_SUBDIR_NAME_EMA = "./platform_scripts/ema"
    SCRIPT_TARGET_NAME_EMA = "/tmp/test_scripts.tgz"
    EXTRACT_CMD_EMA = "cd /tmp;rm -rf test;/bin/tar -xzf {}".format(SCRIPT_TARGET_NAME_EMA)
    BINARY_SUBDIR_NAME = "./binaries"
    FPGA_IMAGE_EMA = "KT-956-0189-01_v1.2.0-1-e1286583.bin"
    FPGA_TARGET_NAME_EMA = "/run/media/mmcblk0p1/system.bin"
    REBOOT_CMD = "/sbin/reboot"
    SCRIPT_SUBDIR_NAME_CSM = "./platform_scripts/csm"
    SCRIPT_TARGET_NAME_CSM = "/tmp/test_scripts.tgz"
    EXTRACT_CMD_CSM = "cd /tmp;rm -rf test;/bin/tar -xzf {}".format(SCRIPT_TARGET_NAME_CSM)

    EHB_CROSSOVER_FREQ_MHZ = 6000

#   Combination of frequency step and dwell time gives >2 full passes through each band in 30 mins.
    TEST_POINTS = {
        AssemblyType.VEHICLE: [
        #   Band,           Start Freq.,    Stop Freq.,    Step Freq.,    Dwell Time
        #                   (MHz)           (MHz)          (MHz)          (s)
            [Band.LOW,        20,            470,          90,             0],   # Temporarily reduced to 470 MHz
            [Band.MID,       400,           2700,         230,             0],
            [Band.HIGH,     3000,           5900,         290,             0]],  # Temporarily reduced to 3000 to 5900 MHz
        AssemblyType.MANPACK: [
            [Band.LOW,        20,            520,         100,             0],
            [Band.MID,       400,           2700,         230,             0],
            [Band.HIGH,     2000,           6000,         400,             0],
            [Band.EXT_HIGH, 2000,           8000,         600,             0],
        ]
    }

    FILTER_AVOID_BANDS = {AssemblyType.VEHICLE:
                            [[Band.MID,     1301,           1699],
                             [Band.HIGH,    1800,           2399]],
                          AssemblyType.MANPACK: None}

    def __init__(self):
        self.terminate_signal_active = False
        self.terminate = False
        self.ema_slot_test_complete = []

    def run_test(self, quick_check=False, slot_1_only=False, reload_fpga=False):
        global password_dict
        if reload_fpga:
            print("*** RELOAD FPGAs ***")
        if quick_check:
            print("*** QUICK CHECK MODE ***")
        # Set system details
        assy_type = AssemblyType.UNKNOWN
        system_assy_nr = ""
        system_serial = ""
        system_rev = ""
        ab_ip = ""
        if not reload_fpga:
            while assy_type == AssemblyType.UNKNOWN:
                system_assy_nr = "KT-950-" +\
                                 input("Enter 4-digits of system assembly number (KT-950-xxxx-00): ").strip() + "-00"
                for assy in self.ASSEMBLIES:
                    if assy[0] == system_assy_nr:
                        assy_type = assy[1]
                        break
                if assy_type == AssemblyType.UNKNOWN:
                    print("ERROR: assembly number unrecognised")

            while len(system_serial) != 6:
                system_serial = input("Enter system/rack serial number (6-digits): ")
            while len(system_rev) != 3:
                system_rev = input("Enter system/rack revision (<letter>.<number>): ")
        if not quick_check and assy_type == AssemblyType.VEHICLE:
            while len(ab_ip) < 11 or len(ab_ip) > 15:
                ab_ip = input("Enter Active Backplane IPv4 address (169.254.xxx.xxx): ")
                if not ab_ip.startswith("169.254."):
                    ab_ip = "169.254." + ab_ip

        # Create log file
        if not reload_fpga:
            if not os.path.exists(self.TEST_LOG_REL_DIR):
                os.makedirs(self.TEST_LOG_REL_DIR)
            now = datetime.datetime.now()
            log_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_{}_nnnnnn.log".\
                            format(now.year, now.month, now.day, now.hour, now.minute, now.second, system_assy_nr)
            logger = Logger(self.TEST_LOG_REL_DIR + log_file_name)
            sys.stdout = logger
        print()
        print("system_test")
        print("-----------")
        print("System test script version: {}".format(self.TEST_VERSION))
        # Get the CSM hostname (and serial number)
        try:
            csm_hostname = FindService.find_csm(True)
            csm_serial = csm_hostname.replace(".local", "").strip()
            print("Found {}".format(csm_serial))
        except:
            print("ERROR: could not get CSM hostname")
            self.terminate_test()
            return False

        # Open an SSH connection with the CSM
        print("Connecting to {}".format(csm_hostname))
        for attempt in range(10):
            if attempt != 0:
                print("Failed to connect, retry attempt {}...".format(attempt))
            csm_ssh = ssh.SSH(csm_hostname, password_dict)
            if csm_ssh.is_connected():
                print("OK")
                break

        if not csm_ssh.is_connected():
            print("ERROR: could not connect to {}".format(csm_hostname))
            self.terminate_test()
            return False

        if not reload_fpga:
            # Arm CSM tamper
            print("Arming tamper detection...")
            if str(csm_ssh.send_command(self.CSM_DISARM_TAMPER_CMD).stdout).strip() == "" and \
                    str(csm_ssh.send_command(self.CSM_ARM_TAMPER_CMD).stdout).strip() == "" and \
                    str(csm_ssh.send_command(self.CSM_SET_TAMPER_ABE_CMD).stdout).strip() == "":
                print("OK")
            else:
                print("ERROR: unexpected response")
                self.terminate_test()
                return False
            print("Checking tamper flags...")
            time.sleep(1)
            tamper_flags = str(csm_ssh.send_command(self.CSM_GET_TAMPER_FLAGS).stdout).strip()
            if tamper_flags == "0x00":
                print("OK")
            else:
                print("ERROR: tamper flags not clear (CSM)")
                if int(tamper_flags, 16) & 0x1:
                    print("  > Light sensor triggered")
                if int(tamper_flags, 16) & 0x2:
                    print("  > Case switch triggered")
                self.terminate_test()
                return False

            # Set CSM clock
            print("Set CSM clock...")
            now = datetime.datetime.now()
            cmd = self.SET_CLOCK_CMD.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
            resp = csm_ssh.send_command(cmd)

        # Generate the run.sh file on CSM
        if csm_ssh.is_connected():
            # Send and extract the platform scripts file
            script_file = ""
            for (dirpath, dirnames, filenames) in os.walk(self.SCRIPT_SUBDIR_NAME_CSM):
                if len(filenames) > 1:
                    print("WARNING: more than one file in {}".format(dir))
                elif len(filenames) == 1:
                    script_file = self.SCRIPT_SUBDIR_NAME_CSM + "/" + filenames[0]
            if script_file is not None:
                print("Sending {}...".format(script_file))
                csm_ssh.send_file(script_file, self.SCRIPT_TARGET_NAME_CSM)
                csm_ssh.send_command(self.EXTRACT_CMD_CSM)

            if not quick_check:
                cmd = self.CSM_GENERATE_RUN_FILE_CMD
                if assy_type == AssemblyType.VEHICLE:
                    cmd += " -t " + ab_ip
                resp = csm_ssh.send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
                    self.terminate_test()
                    return False
            resp = csm_ssh.send_command(self.CSM_READ_RUN_FILE_CMD.format(self.RUN_FILE_ROOT))
            f = resp.stdout.splitlines()
            resp = csm_ssh.send_command(self.CSM_READ_RUN_FILE_CMD.format(self.RUN_FILE_LAUNCHER))
            f += resp.stdout.splitlines()
        else:
            print("ERROR: lost connection to {}".format(csm_hostname))
            self.terminate_test()
            return False

        # Now get the 5 EMA MAC addresses from the run.sh file
        # and convert to IPv6 for SSH connections
        ip_address_to_slot = []
        try:
            # Get the MAC addresses
            mac_address_to_slot = []
            for line in f:
                print("LINE: {}".format(line))
                if "export SLOT_1_MAC=" in line:
                    mac_address_to_slot.append(line.replace("export SLOT_1_MAC=", "").rstrip())
                elif not slot_1_only:
                    if "export SLOT_2_MAC=" in line:
                        mac_address_to_slot.append(line.replace("export SLOT_2_MAC=", "").rstrip())
                    elif "export SLOT_3_MAC=" in line:
                        mac_address_to_slot.append(line.replace("export SLOT_3_MAC=", "").rstrip())
                    elif "export SLOT_4_MAC=" in line:
                        mac_address_to_slot.append(line.replace("export SLOT_4_MAC=", "").rstrip())
                    elif "export SLOT_5_MAC=" in line:
                        mac_address_to_slot.append(line.replace("export SLOT_5_MAC=", "").rstrip())

            # Convert each MAC address to an IPv6 address
            if len(mac_address_to_slot) > 0:
                for entry in mac_address_to_slot:
                    ip_address = IPTools.get_ipv6_from_mac(entry, "fe80::/64")
                    ip_address_to_slot.append(ip_address)
                    #os.system("netsh int ipv6 add neighbors \"Private\" \"{}\" \"{}\"".format(ip_address, entry))
            else:
                print("ERROR: not enough MAC address entries found in {}".format(self.RUN_FILE))
                self.terminate_test()
                return False

        except OSERROR:
            print("Unable to open file: " + self.RUN_FILE)

        # Open an SSH connection with each EMA
        for entry in ip_address_to_slot:
            print("Connecting to {}".format(entry))
            for attempt in range(10):
                if attempt != 0:
                    print("Failed to connect, retry attempt {}...".format(attempt))
                s = ssh.SSH(entry, password_dict)
                if s.is_connected():
                    self.ema_ssh_to_slot.append(s)
                    print("OK")
                    break

            if not s.is_connected():
                print("ERROR: could not connect to EMA {}".format(entry))
                self.terminate_test()
                return False

        # Initialise each EMA ready for the test; map serial numbers and bands to slots
        ema_serial_to_slot = []
        ema_band_to_slot = []
        curr_slot = 0
        for entry in self.ema_ssh_to_slot:
            if entry.is_connected():
                if reload_fpga:
                    # Send the EMA FPGA and reboot EMA
                    if self.FPGA_IMAGE_EMA is not None:
                        fpga_file = self.BINARY_SUBDIR_NAME + "/" + self.FPGA_IMAGE_EMA
                        print("Sending {}...".format(fpga_file))
                        entry.send_file(fpga_file, self.FPGA_TARGET_NAME_EMA)
                        entry.send_command(self.REBOOT_CMD)
                else:
                    # Send and extract the platform scripts file
                    script_file = ""
                    for (dirpath, dirnames, filenames) in os.walk(self.SCRIPT_SUBDIR_NAME_EMA):
                        if len(filenames) > 1:
                            print("WARNING: more than one file in {}".format(dir))
                        elif len(filenames) == 1:
                            script_file = self.SCRIPT_SUBDIR_NAME_EMA + "/" + filenames[0]
                    if script_file is not None:
                        print("Sending {}...".format(script_file))
                        entry.send_file(script_file, self.SCRIPT_TARGET_NAME_EMA)
                        entry.send_command(self.EXTRACT_CMD_EMA)

                    # Use the terminate command to make sure all EMAs are quiet before zeroing power meter
                    cmd = self.EMA_TEST_TERMINATE_CMD
                    resp = entry.send_command(cmd)
                    if "OK" not in str(resp):
                        print("ERROR: command failed [{}]".format(cmd))
                        self.terminate_test()
                        return False

                    if assy_type == AssemblyType.MANPACK:
                        print("Setting dummy PCM hardware configuration...")
                        resp = entry.send_command(self.EMA_SET_DUMMY_PCM_CONFIG_CMD).stdout.strip()
                        if resp.startswith("OK"):
                            print("OK")
                        else:
                            print("ERROR: unexpected response")
                            self.terminate_test()
                            return False

                    # Arm EMA tamper
                    print("Arming tamper detection...")
                    if str(entry.send_command(self.EMA_DISARM_TAMPER_CMD).stdout).strip() == "" and \
                            str(entry.send_command(self.EMA_ARM_TAMPER_CMD).stdout).strip() == "" and \
                            str(entry.send_command(self.EMA_SET_TAMPER_ABE_CMD).stdout).strip() == "":
                        print("OK")
                    else:
                        print("ERROR: unexpected response")
                        self.terminate_test()
                        return False
                    print("Checking tamper flags...")
                    time.sleep(1)
                    tamper_flags = str(entry.send_command(self.EMA_GET_TAMPER_FLAGS).stdout).strip()
                    if tamper_flags == "0x00":
                        print("OK")
                    else:
                        print("ERROR: tamper flags not clear ({} in Slot {})".format(ema_serial_to_slot[curr_slot],
                                                                                     curr_slot))
                        if int(tamper_flags, 16) & 0x1:
                            print("  > Light sensor triggered")
                        if int(tamper_flags, 16) & 0x2:
                            print("  > Case switch triggered")
                        if not quick_check:
                            self.terminate_test()
                            return False

                    # Set EMA clock
                    print("Set EMA clock...")
                    now = datetime.datetime.now()
                    cmd = self.SET_CLOCK_CMD.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
                    resp = entry.send_command(cmd)

                    # Check that EMA is receiving 1PPS
                    print("Checking EMA 1PPS...")
                    cmd = self.EMA_TEST_PPS_CMD
                    resp = entry.send_command(cmd)
                    if str(resp.stdout).splitlines()[0] != "Toggling: 1":
                        print("ERROR: 1PPS not being received by EMA module")
                        self.terminate_test()
                        return False
            else:
                print("ERROR: lost connection to {}".format(ema_serial_to_slot[curr_slot]))
                self.terminate_test()
                return False
            curr_slot += 1

        if reload_fpga:
            return True

        # Activate terminate signal so that ctrl-C causes controlled exit from this point on
        self.terminate_signal_active = True

        # Find and initialise Power Meter
        pm = PowerMeterNRP()
        print("Searching for Power Meter...")
        if pm.find_and_initialise():
            print("Found and initialised: {}".format(pm.details()))
            # Zero power meter
            print("Zero power meter: ", end = "", flush = True)
            if pm.zero():
                print("OK")
            else:
                print("FAIL")
                self.terminate_test()
                return False
            # Set power meter offset
            print("Set offset to 0.0 dB: ", end = "", flush = True)
            if pm.set_offset(0):
                print("OK")
            else:
                print("FAIL")
                self.terminate_test()
                return False
        else:
            print("Could not find Power Meter, terminating test...")
            self.terminate_test()
            return False

        # Initialise EMAs ready for test
        for entry in self.ema_ssh_to_slot:
            if entry.is_connected():
                cmd = self.EMA_TEST_INITIALISE_CMD
                resp = entry.send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
                    self.terminate_test()
                    return False
                else:
                    self.ema_slot_test_complete.append(False)
                    resp = str(resp).split()
                    # Find the list element with "Initialising" in it
                    i = resp.index("Initialising")
                    # Serial number will be in the next element
                    ema_serial_to_slot.append(resp[i+1])
                    # Band will be in the next
                    if "Low" in resp[i+2]:
                        ema_band_to_slot.append(Band.LOW)
                    elif "Mid" in resp[i+2]:
                        ema_band_to_slot.append(Band.MID)
                    elif "High" in resp[i+2]:
                        if "eHB" in resp[i+3]:
                            ema_band_to_slot.append(Band.EXT_HIGH)
                        else:
                            ema_band_to_slot.append(Band.HIGH)
                    else:
                        ema_band_to_slot.append(Band.UNKNOWN)
            else:
                print("ERROR: lost connection to {}".format(ema_serial_to_slot[i]))
                self.terminate_test()
                return False
            i += 1

        # Get the test parameters for each EMA slot
        start_freq_MHz = []
        stop_freq_MHz = []
        step_freq_MHz = []
        dwell_time_sec = []
        for band in ema_band_to_slot:
            # Loop through test points
            for test_point in self.TEST_POINTS[assy_type]:
                # Skip this row of the table if it is not the current band
                if test_point[0] != band:
                    continue
                start_freq_MHz.append(test_point[1])
                stop_freq_MHz.append(test_point[2])
                if not quick_check:
                    step_freq_MHz.append(test_point[3])
                else:
                    if band == Band.LOW:
                        step_freq_MHz.append(test_point[3])
                    if band == Band.MID:
                        step_freq_MHz.append(2300)
                    if band == Band.HIGH:
                        step_freq_MHz.append(3000)
                dwell_time_sec.append(test_point[4])

        if not self.unmute_all_ipams():
            return False

        # Run the main test routine until test duration elapsed
        s2p = S2PFileReader()
        curr_slot = 0
        new_slot = True
        rf_port = 0
        freq_MHz = start_freq_MHz[curr_slot]
        freq_Hz = int(freq_MHz * 1e6)
        last_freq_MHz = [None] * len(ema_band_to_slot)  
        start_power_dBm = []
        end_power_dBm = []
        start_test = True
        end_test = False

        while not self.terminate:
            if not start_test:
                # End after the start measurements when running quick check
                if quick_check:
                    break
                # Check if test duration has elapsed
                time_left = round((self.TEST_DURATION_MINS * 60) - (time.time() - start_time))
                if time_left <= 0:
                    if not end_test:
                        # Test ends after one more pass through all EMAs and all test frequencies
                        end_test = True
                        curr_slot = 0
                        new_slot = True
                        rf_port = 0
                        freq_MHz = start_freq_MHz[curr_slot]
                        freq_Hz = int(freq_MHz * 1e6)
                else:
                    print("Time left before final measurement run: {}".format(str(datetime.timedelta(seconds=time_left))))
                
            # Send the next test frequency to the EMA
            if self.ema_ssh_to_slot[curr_slot].is_connected():
                cmd = self.EMA_TEST_FULL_POWER_TONE_CMD + str(freq_Hz)
                resp = self.ema_ssh_to_slot[curr_slot].send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
                    self.terminate_test()
                    return False
            else:
                print("ERROR: lost connection to {}".format(ema_serial_to_slot[curr_slot]))
                self.terminate_test()
                return False

            # Get the IPAM temperature and update fans
            for entry in self.ema_ssh_to_slot:
                if entry.is_connected():
                    cmd = self.EMA_TEST_IPAM_GET_TEMPERATURE_CMD
                    resp = entry.send_command(cmd)
                    if "OK" not in str(resp):
                        print("ERROR: command failed [{}]".format(cmd))
                        self.terminate_test()
                        return False
                else:
                    print("ERROR: lost connection to {}".format(ema_serial_to_slot[curr_slot]))
                    self.terminate_test()
                    return False

            # Get power meter offset
            power_meter_offset_dB = s2p.get_s_parameter(freq_Hz, 3, self.tx_attenuation_s2p_file[curr_slot][rf_port], True) * -1
            if power_meter_offset_dB is None:
                print("ERROR: failed to get power meter offset")
                self.terminate_test()
                return False

            if pm.set_offset(power_meter_offset_dB) and pm.set_frequency(freq_Hz):
                # Mute all IPAMs except the one we want to check
                if self.mute_all_ipams_except(curr_slot):
                    # Need to make sure the power meter is on the correct slot if these are readings we're validating
                    if (start_test or end_test) and new_slot:
                        input("Move the power meter to *** {}, RF Port {} *** then press Enter to continue...".
                              format(self.slot_name[curr_slot], "A" if rf_port == 0 else "B"))
                        # Do a sanity check
                        while True:
                            power_dBm = pm.get_reading_dBm()
                            print("Get IPAM BIT flags...")
                            cmd = self.EMA_IPAM_GET_BIT_CMD
                            resp = self.ema_ssh_to_slot[curr_slot].send_command(cmd)
                            if power_dBm >= self.SANITY_CHECK_DBM:
                                break
                            # Keep offering chances to put the power meter in the right place
                            print("Low power detected: {:.2f} dBm".format(power_dBm))
                            try:
                                input("Ensure the power meter is definitely on *** {}, RF Port {} *** "
                                      "then press Enter to continue...".
                                      format(self.slot_name[curr_slot], "A" if rf_port == 0 else "B"))
                            except EOFError:
                                if self.terminate:
                                    self.terminate_test()
                                    return False
                        new_slot = False
                    else:
                        time.sleep(1)

                    # Get power reading
                    power_dBm = pm.get_reading_dBm()
                    print("Active: {}, {}, {}, {} MHz".format(self.slot_name[curr_slot], ema_serial_to_slot[curr_slot],
                                                              ema_band_to_slot[curr_slot], freq_MHz))
                    print("Measure: {:.2f} dBm [offset: {:.2f} dB]".format(power_dBm, power_meter_offset_dB))
                    if self.ema_ssh_to_slot[curr_slot].is_connected():
                        print("Get IPAM Temperature...")
                        cmd = self.EMA_TEST_IPAM_GET_TEMPERATURE_CMD
                        resp = self.ema_ssh_to_slot[curr_slot].send_command(cmd)
                        if "OK" not in str(resp):
                            print("ERROR: command failed [{}]".format(cmd))
                            self.terminate_test()
                            return False
                        ipam_temperature = float(str(resp.stdout).splitlines()[1].strip("OK: ").strip(" degC"))
                        print("Get IPAM BIT flags...")
                        cmd = self.EMA_IPAM_GET_BIT_CMD
                        resp = entry.send_command(cmd)
                    else:
                        print("ERROR: lost connection to {}".format(ema_serial_to_slot[curr_slot]))
                        self.terminate_test()
                        return False

                    # Check power in start and end phases
                    min_power_dBm = self.min_power_dBm[assy_type][ema_band_to_slot[curr_slot]]
                    if ipam_temperature >= self.hot_threshold_degrees_c[assy_type][ema_band_to_slot[curr_slot]]:
                        min_power_dBm += self.min_hot_delta_dB[assy_type][ema_band_to_slot[curr_slot]]
                    if start_test or end_test:
                        power_ok = True
                        rx_fail = False
                        if power_dBm < min_power_dBm:
                            print("FAIL - power too low")
                            print("Temperature: {:.2f} degC, measured: {:.2f} dBm, minimum: {:.2f} dBm".
                                  format(ipam_temperature, power_dBm, min_power_dBm))
                            power_ok = False
                            if not end_test:
                                self.terminate_test()
                                return False
                        if slot_1_only and ema_band_to_slot[curr_slot] == Band.LOW:
                            print("Test Rx at {} MHz...".format(freq_MHz))
                            if self.MANUAL_RX_TEST:
                                input("Press Enter to continue")
                            else:
                                cmd = self.EMA_TEST_RX_LB_CMD.format(freq_MHz)
                                resp = str(entry.send_command(cmd).stdout).splitlines()
                                if resp[-1] != "OK":
                                    print("FAIL - Rx detected power too low")
                                    rx_fail = True
                                    if not end_test:
                                        self.terminate_test()
                                        return False

                    # Get a set of reference power readings at the start
                    if start_test:
                        start_power_dBm.append([self.slot_name[curr_slot], ema_band_to_slot[curr_slot], freq_MHz,
                                                power_dBm, power_ok, rx_fail])
                    # Get another set of power readings at the end
                    elif end_test:
                        end_power_dBm.append([self.slot_name[curr_slot], ema_band_to_slot[curr_slot], freq_MHz,
                                              power_dBm, power_ok, rx_fail])
                    
                    if not end_test:
                        # Unmute all IPAMs
                        if not self.unmute_all_ipams():
                            return False
                else:
                    return False
            else:
                print("Measure: {}, {}, {}, {} MHz, --- dBm [offset: {:.2f} dB]: FAIL".format
                      (self.slot_name[curr_slot], ema_serial_to_slot[curr_slot], ema_band_to_slot[curr_slot],
                       freq_MHz, power_meter_offset_dB))
                print("ERROR: could not access power meter")
                self.terminate_test()
                return False
            
            # Dwell time
            if not (start_test or end_test):                
                sleep(dwell_time_sec[curr_slot])

            # Remember the last frequency point for the current slot
            last_freq_MHz[curr_slot] = freq_MHz
            
            # Get the next slot...
            # If this is the start or end cycle of the test, stay on the same slot for one
            # complete pass through the test frequencies before moving to next slot
            # Otherwise move to next slot after each frequency point
            if freq_MHz == stop_freq_MHz[curr_slot] and start_test:
                curr_slot += 1
                new_slot = True
                rf_port = 0
                if curr_slot == len(ema_band_to_slot):
                    curr_slot = 0
                    start_test = False
                    start_time = time.time()
            elif freq_MHz == stop_freq_MHz[curr_slot] and end_test:
                self.ema_slot_test_complete[curr_slot] = True
                curr_slot += 1
                new_slot = True
                rf_port = 0
                if curr_slot == len(ema_band_to_slot):
                    # Test is complete now
                    end_test = False
                    break                    
            elif not (start_test or end_test):
                new_slot = False
                curr_slot += 1
                if curr_slot == len(ema_band_to_slot):
                    curr_slot = 0
            
            # Get the next frequency
            freq_MHz = last_freq_MHz[curr_slot]
            prev_freq_MHz = freq_MHz
            if freq_MHz == stop_freq_MHz[curr_slot] or freq_MHz is None or new_slot:
                # Set the frequency one step back so that the first pass through the filter avoid loop moves
                # this to the start frequency
                freq_MHz = start_freq_MHz[curr_slot] - step_freq_MHz[curr_slot]
            else:
                # Let the first pass through the filter avoid loop step the frequency
                pass
            # Avoid filter bands
            avoid_this_freq = True
            while avoid_this_freq:
                freq_MHz += step_freq_MHz[curr_slot]
                avoid_this_freq = False
                if self.FILTER_AVOID_BANDS[assy_type]:
                    for avoid in self.FILTER_AVOID_BANDS[assy_type]:
                        if avoid[0] == ema_band_to_slot[curr_slot]:
                            if avoid[1] <= freq_MHz <= avoid[2]:
                                avoid_this_freq = True
            if freq_MHz > stop_freq_MHz[curr_slot]:
                freq_MHz = stop_freq_MHz[curr_slot]
            freq_Hz = int(freq_MHz * 1e6)

            # If this is a switch from HB port to eHB port then set new slot to take Power Meter measurement
            if prev_freq_MHz and (prev_freq_MHz <= SystemTest.EHB_CROSSOVER_FREQ_MHZ < freq_MHz):
                new_slot = True

            if freq_MHz <= SystemTest.EHB_CROSSOVER_FREQ_MHZ:
                rf_port = 0
            else:
                rf_port = 1

        self.terminate_test()

        if quick_check:
            ok = True
        else:
            if self.terminate:
                ok = False
            else:
                # Validate the end power readings
                ok = True
                for i in range(len(start_power_dBm)):
                    delta_dB = end_power_dBm[i][3]-start_power_dBm[i][3]
                    print("Verify: {}, {}, {} MHz, Start: {:.2f} dBm, End: {:.2f} dBm, Delta: {:.2f} dB: ".
                          format(start_power_dBm[i][0], start_power_dBm[i][1], start_power_dBm[i][2],
                                 start_power_dBm[i][3], end_power_dBm[i][3], delta_dB),
                                 end="", flush=True)
                    # Powers are verified when measured - all pass here
                    #if delta_dB >= self.min_hot_delta_dB[assy_type][start_power_dBm[i][1]]:
                    if end_power_dBm[i][4]:
                        print("OK")
                    else:
                        print("FAIL")
                        ok = False
                    if end_power_dBm[i][5]:
                        print("        > *** RX FAIL ***")
                        ok = False

        if ok:
            print("\n*** OK - system test passed ***\n")
        else:
            print("\n*** TEST FAILED ***\n")

        # Rename test log file using serial number and assembly number (if test passed)
        logger.close_file()
        sys.stdout = sys.__stdout__
        if ok:
            new_log_file_name = log_file_name.replace("nnnnnn", system_serial)
            os.rename(self.TEST_LOG_REL_DIR + log_file_name, self.TEST_LOG_REL_DIR + new_log_file_name)
        return ok

    def unmute_all_ipams(self):
        # Unmute each IPAM
        i = 0
        for entry in self.ema_ssh_to_slot:
            if not self.ema_slot_test_complete[i] and entry.is_connected():
                cmd = self.EMA_TEST_IPAM_SET_MUTE_CMD + "False"
                resp = entry.send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
                    self.terminate_test()
                    return False
            else:
                print("ERROR: lost connection to {}".format(ema_serial_to_slot[i]))
                self.terminate_test()
                return False
            i += 1
        return True

    def mute_all_ipams_except(self, slot_nr):
        # Mute each IPAM, unmute the exception
        i = 0
        for entry in self.ema_ssh_to_slot:
            if entry.is_connected():
                if i == slot_nr:
                    cmd = self.EMA_TEST_IPAM_SET_MUTE_CMD + "False"
                else:
                    cmd = self.EMA_TEST_IPAM_SET_MUTE_CMD + "True"
                resp = entry.send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
                    self.terminate_test()
                    return False
            else:
                print("ERROR: lost connection to {}".format(ema_serial_to_slot[i]))
                self.terminate_test()
                return False
            i += 1
        return True    

    def terminate_test(self):
        # De-initialise each EMA
        i = 0
        for entry in self.ema_ssh_to_slot:
            print("De-initialising EMA...")
            if entry.is_connected():
                cmd = self.EMA_TEST_TERMINATE_CMD
                # Doing this means the IPAM currently doesn't respond to comms on next attempt - sys_test_initialise
                # and sys_test_terminate need to do the exact opposite of each other!
                resp = entry.send_command(cmd)
                if "OK" not in str(resp):
                    print("ERROR: command failed [{}]".format(cmd))
            else:
                try:
                    print("ERROR: lost connection to {}".format(self.ema_serial_to_slot[i]))
                except AttributeError:
                    print("ERROR: lost connection to EMA")
            i += 1

    def signal_handler(self, *args):
        print("\n\n*** CTRL-C received, terminating test... ***\n\n")
        if self.terminate_signal_active:
            self.terminate = True
        else:
            exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vehicle System Test")
    parser.add_argument("-q", "--quick_check", help="run quick check only", action="store_true")
    parser.add_argument("-1", "--slot_1_only", help="only test low-band EMAs", action="store_true")
    parser.add_argument("-f", "--reload_fpga", help="reload FPGA only", action="store_true")
    args = parser.parse_args()
    o = SystemTest()
    start_time = time.time()
    signal.signal(signal.SIGINT, o.signal_handler)
    o.run_test(quick_check=args.quick_check, slot_1_only=args.slot_1_only, reload_fpga=args.reload_fpga)
    print("\n(test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds=round(time.time() - start_time, 0)))))
