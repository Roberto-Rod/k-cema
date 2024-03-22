#!/usr/bin/env python3
from power_supplies import *
from built_in_test import *
from test import *

from time import sleep

# rev_num is the PCB revision code where 0 = A, 1 = B etc.
def run_test(rev_num = 0):
    all_ok = True
    bit = BuiltInTest()
    print("")
    print("test_power_supplies")
    print("-------------------")
    print("Disable switchable supplies: ", end = "")
    PowerSupplies.disable_all()
    sleep(1)
    print("OK")

    print("Test DC In: ", end = "", flush = True)
    val = bit.value(NTMADCChannel.XADC_CHAN_DC_IN)
    ok = "OK"
    if not Test.nom(val, 24, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Turn Bench PSU voltage down to +15 V: ", end = "", flush = True)
    if wait_dc_input_lte(15.0):
        print("OK")
    else:
        ok = "FAIL"
        all_ok = False

    print("Turn Bench PSU voltage up to +33 V: ", end= "", flush = True)
    # Allow for some voltage drop from bench PSU to DUT
    if wait_dc_input_gte(32.5):
        print("OK")
    else:
        ok = "FAIL"
        all_ok = False

    print("Turn Bench PSU down to +24 V: ", end="", flush=True)
    if wait_dc_input_lte(24.1):
        print("OK")
    else:
        ok = "FAIL"
        all_ok = False

    print("Test +3V3: ", end = "")
    val = bit.value(NTMADCChannel.XADC_CHAN_3V3)
    ok = "OK"
    if not Test.nom(val, 3.3, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Test DDS_CLK_3V3: ", end = "")
    val = bit.value(NTMADCChannel.XADC_CHAN_DDS_CLK_3V3)
    ok = "OK"
    if not Test.nom(val, 3.3, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Test +1V8 Rail: ", end = "", flush = True)
    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCAUX)
    ok = "OK"
    if not Test.nom(val, 1.8, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Test +1V5 Rail: ", end = "", flush = True)
    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCO_DDR)
    ok = "OK"
    if not Test.nom(val, 1.5, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Test +1V0 SoC Core Voltage: ", end = "", flush = True)
    val = bit.xadc.get_internal_voltage(XADCInternalVoltage.VCCINT)
    ok = "OK"
    if not Test.nom(val, 1.0, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Test MGT +1V0 Power Good: ", end = "", flush = True)
    if bit.power_good(NTMPowerGood.PGD_MGT_1V0):
        print("OK")
    else:
        print("FAIL")
        all_ok = False

    print("Test MGT +1V2 Power Good: ", end = "", flush = True)
    if bit.power_good(NTMPowerGood.PGD_MGT_1V2):
        print("OK")
    else:
        print("FAIL")
        all_ok = False

    print("Test MGT Clock Power Good: ", end = "", flush = True)
    if bit.power_good(NTMPowerGood.PGD_MGT_CLK):
        print("OK")
    else:
        print("FAIL")
        all_ok = False

    print("Test ETH +1V2 Power Good: ", end = "", flush = True)
    if bit.power_good(NTMPowerGood.PGD_ETH_1V2):
        print("OK")
    else:
        print("FAIL")
        all_ok = False

    print("Enable and test +3V6: ", end = "", flush = True)
    PowerSupplies.rail_3v6_en()
    sleep(1)
    ok = "OK"
    val = bit.value(NTMADCChannel.XADC_CHAN_3V6)
    if not Test.nom(val, 3.6, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Enable and test +5V3: ", end = "", flush = True)
    PowerSupplies.rail_5v3_en()
    sleep(1)
    val = bit.value(NTMADCChannel.XADC_CHAN_5V5_5V3)
    ok = "OK"
    if not Test.nom(val, 5.3, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Enable and test +2V1: ", end = "", flush = True)
    PowerSupplies.rail_2v1_en()
    sleep(1)
    val = bit.value(NTMADCChannel.XADC_CHAN_IF_ADC_3V3A_XCVR_2V1)
    ok = "OK"
    if not Test.nom(val, 2.1, 10): # Test and allow 10 % error from nominal
        ok = "FAIL"
        all_ok = False
    print("{} [{:.2f} V]".format(ok, val))

    print("Enable and test +1V3 Power Good: ", end = "", flush = True)
    PowerSupplies.rail_1v3_en()
    sleep(1)
    if bit.power_good(NTMPowerGood.PGD_XCVR_1V3):
        print("OK")
    else:
        print("FAIL")
        all_ok = False

    PowerSupplies.disable_all()
    return all_ok


def wait_dc_input_lte(voltage):
    bit = BuiltInTest()
    val = 1000
    val_str = ""
    while (val > voltage):
        sleep(0.2)
        val = bit.value(NTMADCChannel.XADC_CHAN_DC_IN)
        # Delete previous string
        for i in range(len(val_str)):
            print("\b \b", end = "", flush = True)
        val_str = ("{:.2f} V".format(val)).rstrip()
        print(val_str, end = "", flush = True)
    # Delete previous string
    for i in range(len(val_str)):
        print("\b \b", end = "", flush = True)
    return True


def wait_dc_input_gte(voltage):
    bit = BuiltInTest()
    val = 0
    val_str = ""
    while (val < voltage):
        sleep(0.2)
        val = bit.value(NTMADCChannel.XADC_CHAN_DC_IN)
        # Delete previous string
        for i in range(len(val_str)):
            print("\b \b", end = "", flush = True)
        val_str = ("{:.2f} V".format(val)).rstrip()
        print(val_str, end = "", flush = True)
    # Delete previous string
    for i in range(len(val_str)):
        print("\b \b", end = "", flush = True)
    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")

