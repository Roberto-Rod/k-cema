#!/usr/bin/env python3
from time import sleep

from devmem import *


class PPS:
    REG_PPS_COUNT = 0x40080014
    EXT_PPS_STROBE_MASK = 0x80000000
    PPS_COUNT_MASK = ~EXT_PPS_STROBE_MASK

    @staticmethod
    def is_ext_pps_toggling():
        '''
        :return: True if external PPS is toggling, very wide tolerance as basic test
        '''
        val1 = DevMem.read(PPS.REG_PPS_COUNT) & PPS.EXT_PPS_STROBE_MASK
        # Expect value to change within 1.0 seconds maximum; allow up to 1.5 seconds
        for i in range(15):
            sleep(0.1)
            val2 = DevMem.read(PPS.REG_PPS_COUNT) & PPS.EXT_PPS_STROBE_MASK
            if val1 != val2:
                return True
        return False

    @staticmethod
    def get_clock_count():
        '''
        :return: 10 MHz clock count if external 1PPS is valid (with 100 ppm tolerance), otherwise 0
        '''
        return DevMem.read(PPS.REG_PPS_COUNT) & PPS.PPS_COUNT_MASK


if __name__ == "__main__":
    if PPS.is_ext_pps_toggling():
        print("Toggling: 1")
    else:
        print("Toggling: 0")
    print("Count: {}".format(PPS.get_clock_count()))
