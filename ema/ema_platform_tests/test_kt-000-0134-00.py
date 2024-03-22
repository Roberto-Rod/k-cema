#!/usr/bin/env python3
import datetime
import os

import get_time_and_date
import test_adc
import test_dds_calibrate
import test_dds_clock
import test_dds_power
import test_ext_gpio
import test_fpga_version
import test_hardware_config
import test_jig_details
import test_leds
import test_mac_address
import test_nvme_ssd
import test_phy_speed
import test_power_supplies_lb
import test_rf_board_voltages
import test_tamper
import test_tx_attenuator
from band import *
from logger import *
from power_meter import *
from signal_generator import *


def run_test():
    if not os.path.exists("../log"):
        os.makedirs("../log")
    sys.stdout = Logger("../log/test.log")
    print("test_kt-000-0134-00")
    print("-------------------")
    if not test_fpga_version.run_test():
        return False
    if not test_jig_details.run_test():
        return False
    if not test_mac_address.run_test():
        return False
    if not test_phy_speed.run_test():
        return False
    if not test_power_supplies_lb.run_test(rev_num=1):
        return False
    if not test_ext_gpio.run_test(Band.LOW):
        return False
    if not test_rf_board_voltages.run_test(Band.LOW):
        return False
    if not test_dds_clock.run_test():
        return False
    if not test_dds_power.run_test(Band.LOW, zero_power_meter=True):
        return False
    if not test_tx_attenuator.run_test(zero_power_meter=False):
        return False
    if not test_dds_calibrate.run_test(Band.LOW, zero_power_meter=False):
        return False
    if not test_adc.run_test():
        return False
    if not test_tamper.run_test():
        return False
    if not test_leds.run_test():
        return False
    if not test_hardware_config.run_test(test_hardware_config.AssemblyType.NTM_DIGITAL_LB):
        return False
    if not test_hardware_config.run_test(test_hardware_config.AssemblyType.EMA_LB_A, True):
        return False
    if not test_nvme_ssd.run_test():
        return False

    # If we got this far then all tests passed
    return True


if __name__ == "__main__":
    os.system("/usr/bin/killall fetchandlaunchema")
    os.system("/usr/bin/killall KCemaEMAApp")
    os.system("/usr/bin/killall ema_app.bin")
    get_time_and_date.run_test()
    start_time = time.time()
    pm = PowerMeter()
    sg = SignalGenerator()
    if not pm.find():
        print("Could not find Power Meter Service, terminating test...")
    elif not sg.find():
        print("Could not find Signal Generator Service, terminating test...")
    elif run_test():
        print("\n*** OK - test passed ***\n")
        print("\n(test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** Unmount mmcblk0p2 to ensure calibration and log files are saved ***\n")
    else:
        print("\n(test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** TEST FAILED ***\n")
