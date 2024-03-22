#!/usr/bin/env python3
import argparse
import datetime
import os
import sys
import time

import serial.tools.list_ports
from ema_test_intf_board import *
from logger import *
from ssh import *

VERSION = "1.1.0"
EMA_CMD_PREFIX = "cd /run/media/mmcblk0p2/test/;python3 "
NVME_COMMAND_TIMEOUT_S = 60  # NVMe test may format the SSD so allow longer than default command time
RX_CAL_COMMAND_TIMEOUT_S = 120
PA_CAL_COMMAND_TIMEOUT_S = 900
TEST_LOG_REL_DIR = "./test_logs/"
ROOT_PASSWORD = "gbL^58TJc"

password_dict = {}


def login(ema, password):
    ema.uart_send_command("root")  # Send username
    resp = ema.uart_send_command(password)  # Send password
    for r in resp:
        if r[:9] == "root@EMA-":
            return True
    return False


def run_test(no_power_down=False, no_ssd=False):
    port_description_pattern = "STLink Virtual COM Port"
    print()
    if not os.path.exists(TEST_LOG_REL_DIR):
        os.makedirs(TEST_LOG_REL_DIR)
    now = datetime.datetime.now()
    log_file_name = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}_KT-950-xxxx-00_nnnnnn.log".\
                    format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    logger = Logger(TEST_LOG_REL_DIR + log_file_name)
    sys.stdout = logger
    print()
    print("ema_module_test")
    print("---------------")
    print()
    print("Test version: {}".format(VERSION))
    serial_port = None
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if port_description_pattern in p.description:
            serial_port = p.device

    if serial_port is not None:
        print("Using EMA Test Interface Board on {}".format(serial_port))
        ema = EmaTestInterfaceBoard(serial_port)
        try:
            ema.set_uart_echo(False)
            # Test Power On/Off
            if not no_power_down:
                ema.set_power_off(True)
                resp = None
                while resp != "y" and resp != "n":
                    resp = input("Confirm that bench PSU current is ≤ 0.1 A (y/n): ")
                if resp == "n":
                    return False
            ema.set_power_off(False)

            # Wait for boot
            print("Waiting for EMA to boot", end="", flush=True)
            ema.set_uart_echo(True)
            if not no_power_down:
                # Don't do anything for the first 20 seconds so that we don't interrupt autoboot
                for i in range(10):
                    time.sleep(2)
                    print(".", end="", flush=True)
            booting = True
            logged_in = False
            while booting and not logged_in:
                resp = ema.uart_send_command("")
                for r in resp:
                    if "login: " in r:
                        booting = False
                    if r[:9] == "root@EMA-":
                        logged_in = True
                print(".", end="", flush=True)

            print("")
            print("EMA has booted")
            if not logged_in:
                print("Log in to EMA...")
                attempts = 0
                while not logged_in and attempts < 10:
                    if login(ema, ROOT_PASSWORD):
                        logged_in = True
                    elif login(ema, "root"):
                        logged_in = True
                    attempts += 1

            if logged_in:
                print("Logged in to EMA")
            else:
                print("ERROR: Failed to login to EMA")
                return False

            # Kill applications on EMA module
            ema.uart_send_command("killall fetchandlaunchema")
            ema.uart_send_command("killall KCemaEMAApp")
            ema.uart_send_command("killall ema_app.bin")

            # Find IPv4 address
            inet_addr = None
            resp = ema.uart_send_command("ifconfig eth0:avahi")
            for r in resp:
                line = r.strip()
                if "169.254" in line:
                    # Split the line up into fields separated by ":" to get the inet addr out (field 1)
                    # and then by " " to separate the address from the next field name
                    inet_addr = line.split(":")[1].split(" ")[0]

            if inet_addr is None:
                print("ERROR: Failed to find IP address")
                return False

            print("Found IPv4 Address: {}".format(inet_addr))

            # Open SSH connection
            s = SSH(inet_addr, password_dict)
            if not s.is_connected():
                print("ERROR: Failed to make SSH connection")
                return False

            # Set module details
            module_serial = ""
            module_rev = ""
            module_assy_nr = "KT-950-xxxx-00"
            while len(module_serial) != 6:
                module_serial = input("Enter EMA module serial number (6-digits): ")
            while len(module_rev) != 3:
                module_rev = input("Enter EMA module revision (<letter>.<number>): ")
            resp = s.send_command(EMA_CMD_PREFIX + "./ema_rf_hw_config.py {} {} {:02d}/{:02d}/{:04d}".
                                                   format(module_rev, module_serial, now.day, now.month, now.year))
            lines = resp.stdout.splitlines()
            for line in lines:
                if "Assembly Part Number will be set to" in line:
                    assy_fields = line.split("\"")
                    if len(assy_fields) > 1:
                        module_assy_nr = assy_fields[1]

            # External 1PPS test
            print("")
            print("test_1pps")
            print("---------")
            print("Disable 1PPS...")
            ema.set_pps(False)
            time.sleep(1.1)
            resp = s.send_command(EMA_CMD_PREFIX + "pps.py")
            if resp.stdout.splitlines()[0] != "Toggling: 0":
                print("ERROR: expected \"Toggling: 0\"")
                return False
            print("Enable 1PPS...")
            ema.set_pps(True)
            resp = s.send_command(EMA_CMD_PREFIX + "pps.py")
            if resp.stdout.splitlines()[0] != "Toggling: 1":
                print("ERROR: expected \"Toggling: 1\"")
                return False
            # Disable External 1PPS
            print("Disable 1PPS...")
            ema.set_pps(False)
            print("PASS")

            # Get external blank status
            print("")
            print("test_ext_blank")
            print("--------------")
            print("De-assert external blank...")
            ema.set_rf_mute(False)
            resp = s.send_command(EMA_CMD_PREFIX + "blank_control.py")
            if resp.stdout.splitlines()[0] != "State: 1":
                print("ERROR: expected \"State: 1\"")
                return False
            print("Assert external blank...")
            ema.set_rf_mute(True)
            resp = s.send_command(EMA_CMD_PREFIX + "blank_control.py")
            if resp.stdout.splitlines()[0] != "State: 0":
                print("ERROR: expected \"State: 0\"")
                return False
            print("De-assert external blank...")
            ema.set_rf_mute(False)
            print("PASS")

            # Send an empty command to flush the test interface buffer
            ema.uart_send_command("")

            # Test NVMe SSD
            if not no_ssd:
                print()
                resp = s.send_command(EMA_CMD_PREFIX + "test_nvme_ssd.py", NVME_COMMAND_TIMEOUT_S)
                try:
                    lines = resp.stdout.strip().splitlines()
                    if lines[-1] == "*** OK - test passed ***":
                        print("PASS")
                    else:
                        print("ERROR: NVMe SSD test failed")
                        return False
                except Exception as e:
                    print(e)
                    print("ERROR: NVMe SSD test failed")
                    return False

            # Run Rx calibration if the IPAM indicates a responsive type
            print()
            print("rx_calibration")
            print("--------------")
            print("Get EMA band and type...")
            resp = s.send_command(EMA_CMD_PREFIX + "ipam.py -bd")
            resp_split = resp.stdout.strip().split(",")
            if isinstance(resp_split, list):
                band = resp_split[0]
                if resp_split[1] != "responsive":
                    print("Skipped as the IPAM indicates that this is an \"active only\" variant")
                else:
                    print("Attach signal generator to EMA module via high power attenuator")
                    while input("Enter 'y' to continue: ") != "y":
                        pass
                    if band == "Band.LOW":
                        resp = s.send_command(EMA_CMD_PREFIX + "test_rx_calibrate_lb.py -n", RX_CAL_COMMAND_TIMEOUT_S)
                    elif band == "Band.MID" or band == "Band.HIGH":
                        resp = s.send_command(EMA_CMD_PREFIX + "test_rx_calibrate_mb_hb.py -n", RX_CAL_COMMAND_TIMEOUT_S)
                    else:
                        print("ERROR - unexpected band ({})".format(band))
                        return False
                    lines = resp.stdout.splitlines()
                    # Look for the success message within the final 10 lines
                    cal_ok = False
                    line = len(lines) - 1
                    for i in range(10):
                        if line < 0:
                            break
                        if "OK - Rx calibration passed" in lines[line]:
                            cal_ok = True
                        line -= 1
                    if not cal_ok:
                        print("ERROR: Rx calibration did not complete successfully")
                        return False
            else:
                print("ERROR: unexpected response ({})".format(resp))
                return False

            # Run PA calibration
            print("")
            print("pa_calibration")
            print("--------------")
            print("Attach power meter to EMA module via high power attenuator")
            while input("Enter 'y' to continue: ") != "y":
                pass
            resp = s.send_command(EMA_CMD_PREFIX + "test_pa_calibrate.py -n", PA_CAL_COMMAND_TIMEOUT_S)
            lines = resp.stdout.splitlines()
            # Look for the success message within the final 10 lines
            cal_ok = False
            line = len(lines) - 1
            for i in range(10):
                if line < 0:
                    break
                if "OK - PA calibration passed" in lines[line]:
                    cal_ok = True
                line -= 1
            if not cal_ok:
                print("ERROR: PA calibration did not complete successfully")
                return False

            # Unmount eMMC partition 2 to ensure calibration file is saved, remount in case EMA is used
            # after this test process
            print("Unmounting and remounting EMA eMMC partition 2: ", end="", flush=True)
            s.send_command("umount /run/media/mmcblk0p2/;mount /dev/mmcblk0p2 /run/media/mmcblk0p2/")
            print("OK")

        except Exception as e:
            print("Error: {}".format(e))
            return False
    else:
        print("\nERROR: No serial port found matching description \"{}\"".format(port_description_pattern))
        return False

    print("\n*** OK - EMA module test passed ***\n")

    # Rename test log file using serial number and assembly number
    logger.close_file()
    new_log_file_name = log_file_name.replace("nnnnnn", module_serial).replace("KT-950-xxxx-00", module_assy_nr)
    os.rename(TEST_LOG_REL_DIR + log_file_name, TEST_LOG_REL_DIR + new_log_file_name)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EMA Module Test")
    parser.add_argument("--npd", help="No power-down", action="store_true")
    parser.add_argument("--no_ssd", help="No NVMe SSD test", action="store_true")
    args = parser.parse_args()
    start_time = time.time()
    if not run_test(no_power_down=args.npd, no_ssd=args.no_ssd):
        print("\n*** EMA MODULE TEST FAILED ***\n")

    print("\n(Test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds=round(time.time() - start_time, 0)))))
