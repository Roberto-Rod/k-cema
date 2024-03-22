#!/usr/bin/env python3
from logger import *
from power_meter import *
from band import *
import os
import datetime
import get_time_and_date
import test_fpga_version
import test_hardware_config
import test_power_supplies_mb_hb
import test_tamper
import test_dds_calibrate
import test_dds_clock
import test_dds_power
import test_mac_address
import test_nvme_ssd
import test_phy_speed
import test_leds
import test_ext_gpio
import test_rf_board_voltages
import test_high_speed_transceiver
import test_jig_details


def run_test():
    if not os.path.exists("../log"):
        os.makedirs("../log")
    sys.stdout = Logger("../log/test.log")
    print("test_kt-000-0135-00")
    print("-------------------")    
    if not test_fpga_version.run_test():
        return False
    if not test_jig_details.run_test():
        return False
    if not test_mac_address.run_test():
        return False
    if not test_phy_speed.run_test():
        return False
    if not test_power_supplies_mb_hb.run_test():
        return False
    if not test_ext_gpio.run_test(Band.MID_HIGH):
        return False
    if not test_rf_board_voltages.run_test(Band.MID_HIGH):
        return False
    if not test_high_speed_transceiver.run_test():
        return False
    if not test_dds_clock.run_test():
        return False
    if not test_dds_power.run_test(Band.MID_HIGH, zero_power_meter=True):
        return False
    if not test_dds_calibrate.run_test(Band.MID_HIGH, zero_power_meter=False):
        return False
    if not test_tamper.run_test():
        return False
    if not test_leds.run_test():
        return False
    if not test_hardware_config.run_test(test_hardware_config.AssemblyType.NTM_DIGITAL_MB_HB):
        return False
    if not test_hardware_config.run_test(test_hardware_config.AssemblyType.EMA_MB_A, True):
        return False
    if not test_nvme_ssd.run_test():
        return False

    # TODO:
    #   Add MGT clock test
    #   Add JESD204B loopback test

    # If we got this far then all tests passed
    return True


if __name__ == "__main__":
    os.system("/usr/bin/killall fetchandlaunchema")
    os.system("/usr/bin/killall KCemaEMAApp")
    os.system("/usr/bin/killall ema_app.bin")
    get_time_and_date.run_test()
    start_time = time.time()    
    pm = PowerMeter()
    if not pm.find():
        print("Could not find Power Meter Service, terminating test...")
    elif run_test():
        print("\n*** OK - test passed ***\n")
        print("\n(test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** Unmount mmcblk0p2 to ensure calibration and log files are saved ***\n")
    else:
        print("\n(test duration: {} h:m:s)\n".format(str(datetime.timedelta(seconds = round(time.time() - start_time, 0)))))
        print("\n*** TEST FAILED ***\n")
