#!/usr/bin/env python3
from power_supplies import *
from ad96xx import *
from rx_control import *
from test import *
from signal_generator import *

from time import sleep


def run_test():
    print("")
    print("test_if_adc")
    print("-----------")
    sg = SignalGenerator()
    print("Searching for Signal Generator Service: ", end = "", flush = True)
    sg_ok = False
    if sg.find():
        print("Signal Generator Service found at {}:{}".format(sg.address,str(sg.port)))
        print("Connect to signal generator: ", end = "", flush = True)
        if sg.connect():
            print("OK")
            print("Signal generator details: {}".format(sg.description))
            sg_ok = True
    if not sg_ok:
        print("FAIL - could not find/connect to signal generator")
        return False

    print("Disable power supplies: ", end = "", flush = True)
    PowerSupplies.disable_all()
    sleep(1)
    print("PASS")
    print("Enable IF ADC supplies: ", end = "", flush = True)
    PowerSupplies.rail_3v6_en()
    PowerSupplies.if_adc_en()
    sleep(1)
    print("PASS")

    print("Set ADC trim DAC to mid-scale: ", end = "", flush = True)
    if AD96xx.set_adc_trim_midscale():
        print("OK")
    else:
        return terminate_test(False)

    print("Initialise ADC: ", end = "", flush = True)
    if AD96xx.reset():
        print("OK")
    else:
        return terminate_test(False)

    print("Get ADC device info: ", end = "", flush = True)
    device_info = AD96xx.get_device_info()
    if ("Chip ID" in device_info) and ("Chip Grade" in device_info):
        if device_info["Chip ID"] == "AD9690":
            print("PASS ({} {})".format(device_info["Chip ID"], device_info["Chip Grade"]))
        else:
            return terminate_test(False)

    print("Check input clock: ", end = "", flush = True)
    if AD96xx.is_input_clock_detected():
        print("PASS")
    else:
        return terminate_test(False)

    print("Bring link up: ", end = "", flush = True)
    if AD96xx.link_up():
        print("PASS")
    else:
        return terminate_test(False)

    print("Check ADC PLL lock: ", end = "", flush = True)
    if AD96xx.is_adc_pll_locked():
        print("PASS")
    else:
        return terminate_test(False)

    print("Check JESD204B PLL lock: ", end = "", flush = True)
    if AD96xx.is_jesd204b_pll_locked():
        print("PASS")
    else:
        return terminate_test(False)

    print("Check JESD204B lane sync: ", end = "", flush = True)
    if AD96xx.is_jesd204b_lane_synchronised():
        print("PASS")
    else:
        return terminate_test(False)

    print("Trigger sysref: ", end = "", flush = True)
    if AD96xx.trigger_sysref():
        print("PASS")
    else:
        return terminate_test(False)

    print("Check JESD204B link sync: ", end = "", flush = True)
    if AD96xx.is_jesd204b_link_synchronised():
        print("PASS")
    else:
        return terminate_test(False)

    print("Check ADC input...")
    print("Set signal generator RF output to 'off': ", end = "", flush = True)
    if sg.set_output_enable(False):
        print("PASS")
    else:
        return terminate_test(False)

    print("Check ADC Fast Detect is not asserted: ", end = "", flush = True)
    if not RxControl.fast_detect():
        print("PASS")
    else:
        return terminate_test(False)
        
    print("Set Signal Generator to 570 MHz, +15 dBm, RF output 'on': ", end = "", flush = True)
    if sg.set_frequency_Hz(570e6) and sg.set_output_power_dBm(15) and sg.set_output_enable(True):
        print("PASS")
    else:
        return terminate_test(False)

    print("Check ADC Fast Detect is asserted: ", end = "", flush = True)
    if RxControl.fast_detect():
        print("PASS")
    else:
        return terminate_test(False)
        
    print("Set Signal Generator to 900 MHz: ", end = "", flush = True)
    if sg.set_frequency_Hz(900e6):
        print("PASS")
    else:
        return terminate_test(False)

    print("Check ADC Fast Detect is not asserted: ", end = "", flush = True)
    if not RxControl.fast_detect():
        print("PASS")
    else:
        return terminate_test(False)

    sg.set_output_enable(False)
    return terminate_test(True)


def terminate_test(ret_val = False):
    '''
    :return: ret_val so that the test can be terminated with one line: 'return terminate_test(False)'
    '''
    if not ret_val:
        print("FAIL")
    PowerSupplies.disable_all()
    return ret_val


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

