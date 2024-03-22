#!/usr/bin/env python3
from devmem import *
from band import *
from ltc2991 import *
from power_supplies import *
from time import sleep
import sys

BIT_CHANNELS = [
    [Band.LOW, "+5V5", 1, 3.7, 5.5 * 0.9, 5.5 * 1.1],
    [Band.LOW, "+7V3", 0, 3.7, 7.3 * 0.9, 7.3 * 1.1],
    [Band.MID_HIGH, "+1V3", 1, 1.0, 1.3 * 0.9, 1.3 * 1.1],
    [Band.MID_HIGH, "+2V1", 0, 1.0, 2.1 * 0.9, 2.1 * 1.1],
    [Band.MID_HIGH, "+3V6", 2, 3.7, 3.6 * 0.9, 3.6 * 1.1],
    [Band.MID_HIGH, "+5V3", 3, 3.7, 5.3 * 0.9, 5.3 * 1.1]
]


def run_test(band):
    '''
    Test the RF board voltages using the LTC2991 ADC on the KT-000-0161-00 RF interface board
    :param band: the band the NTM under test is associated with must be Band.LOW or Band.MID_HIGH
    :return: True if all tests pass, otherwise False
    '''
    ok = True
    print("")
    print("test_rf_board_voltages")
    print("----------------------")
    if band == Band.LOW:
        PowerSupplies.rail_5v5_en(True)
        PowerSupplies.rail_7v3_en(True)
    elif band == Band.MID_HIGH:
        PowerSupplies.rail_1v3_en(True)
        PowerSupplies.rail_2v1_en(True)
        PowerSupplies.rail_5v3_en(True)
        PowerSupplies.rail_3v6_en(True)
    else:
        print("FAIL - band not supported")
        return False

    ltc = LTC2991(1, 4)
    for ch in BIT_CHANNELS:
        if ch[0] == band:
            v = ltc.read_channel_volts(ch[2]) * ch[3]
            print("{} channel ({:.2f} V): ".format(ch[1], v), end="")
            if (v >= ch[4]) and (v <= ch[5]):
                print("PASS")
            else:
                print("FAIL")
                PowerSupplies.disable_all()
                return False
    PowerSupplies.disable_all()
    return True


if __name__ == "__main__":
    if run_test(get_band_opt(sys.argv, ntm_digital=True)):
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
