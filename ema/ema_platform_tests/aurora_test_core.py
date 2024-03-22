#!/usr/bin/env python3
from devmem import *


class AuroraTestCore:
    AURORA_GPIO_ADDRESS = 0x40072000

    CHANNEL_UP_MASK = 0x00002000
    FRAME_ERR_MASK = 0x00001000
    HARD_ERR_MASK = 0x00000800
    LANE_UP_MASK = 0x00000780
    LANE_UP_LSB = 7
    PLL_NOT_LOCKED_MASK = 0x00000040
    RX_RESET_DONE_MASK = 0x00000020
    SOFT_ERR_MASK = 0x00000010
    TX_LOCK_MASK = 0x00000008
    TX_RESET_DONE_MASK = 0x00000004
    QPLL_LOCK_MASK = 0x00000002
    QPLL_REF_LOST_MASK = 0x00000001
    CORE_RESET_MASK = 0x00010000
    GT_RESET_MASK = 0x00020000

    def __init__(self):
        self.reset()

    def reset(self, rst=True):
        ok = True
        if rst:
            ok = ok and DevMem.set(self.AURORA_GPIO_ADDRESS, self.CORE_RESET_MASK)
            ok = ok and DevMem.set(self.AURORA_GPIO_ADDRESS, self.GT_RESET_MASK)
        else:
            ok = ok and DevMem.clear(self.AURORA_GPIO_ADDRESS, self.GT_RESET_MASK)
            ok = ok and DevMem.clear(self.AURORA_GPIO_ADDRESS, self.CORE_RESET_MASK)
        return ok

    def is_pll_locked(self):
        return (DevMem.read(self.AURORA_GPIO_ADDRESS) & self.PLL_NOT_LOCKED_MASK) == 0

    def is_reset_done(self):
        tx_is_done = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.TX_RESET_DONE_MASK) != 0)
        rx_is_done = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.RX_RESET_DONE_MASK) != 0)
        return tx_is_done and rx_is_done

    def is_all_up(self):
        lanes_up = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.LANE_UP_MASK) == self.LANE_UP_MASK)
        channel_up = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.CHANNEL_UP_MASK) == self.CHANNEL_UP_MASK)
        return lanes_up and channel_up

    def is_no_errors(self):
        soft_err = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.SOFT_ERR_MASK) != 0)
        hard_err = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.HARD_ERR_MASK) != 0)
        frame_err = ((DevMem.read(self.AURORA_GPIO_ADDRESS) & self.FRAME_ERR_MASK) != 0)
        return not soft_err and not hard_err and not frame_err

    def lane_mask(self):
        return (DevMem.read(self.AURORA_GPIO_ADDRESS) & self.LANE_UP_MASK) >> self.LANE_UP_LSB


if __name__ == "__main__":
    print("Aurora Test Core Tests")
    aur = AuroraTestCore()
    aur.reset(False)
    print("is_pll_locked: {}".format(aur.is_pll_locked()))
    print("is_reset_done: {}".format(aur.is_reset_done()))
    print("is_all_up: {}".format(aur.is_all_up()))
    print("is_no_errors: {}".format(aur.is_no_errors()))
    print("lane_mask: 0x{:01x}".format(aur.lane_mask()))
