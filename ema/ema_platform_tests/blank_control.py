#!/usr/bin/env python3
from devmem import *


class BlankControl:
    REG_BLANK_CTRL = 0x40080588
    EXT_BLANK_MASK = 0x80000000
    EXT_BLANK_EN_MASK = 0x00000001

    @staticmethod
    def get_ext_blank_n_state():
        if (DevMem.read(BlankControl.REG_BLANK_CTRL) & BlankControl.EXT_BLANK_MASK) == 0:
            return 0
        else:
            return 1

    @staticmethod
    def set_ext_blank_n_enabled(state):
        if state:
            DevMem.set(BlankControl.REG_BLANK_CTRL, BlankControl.EXT_BLANK_EN_MASK)
        else:
            DevMem.clear(BlankControl.REG_BLANK_CTRL, BlankControl.EXT_BLANK_EN_MASK)


if __name__ == "__main__":
    print("State: {}".format(BlankControl.get_ext_blank_n_state()))
