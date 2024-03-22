#!/usr/bin/env python3
from devmem import *
import argparse


class TimingControl:
    REG_TIMING_CONTROL_BASE = 0x40080640
    REG_JAMMING_CONTROL = 0x40084004
    JAMMING_RX_TEST_MASK = 0x10
    TIMING_MODE_MASK = 0x00000003
    TX_IN_RX_TEST_MODE_MASK = 0x00000100
    MODE_DISABLED = 0x0
    MODE_ASYNC = 0x1
    MODE_SYNC = 0x2
    MODE_RX_TEST = 0x3

    def value(self):
        return DevMem.read(self.REG_TIMING_CONTROL_BASE)

    def enable_rx_test_mode(self):
        return DevMem.rmw(self.REG_TIMING_CONTROL_BASE, self.MODE_RX_TEST, self.TIMING_MODE_MASK) and\
               DevMem.rmw(self.REG_JAMMING_CONTROL, 1, self.JAMMING_RX_TEST_MASK)

    def enable_tx_in_rx_test_mode(self):
        return DevMem.rmw(self.REG_TIMING_CONTROL_BASE, 1, self.TX_IN_RX_TEST_MODE_MASK)

    def disable(self):
        return DevMem.rmw(self.REG_TIMING_CONTROL_BASE, self.MODE_DISABLED, self.TIMING_MODE_MASK) and\
               DevMem.rmw(self.REG_TIMING_CONTROL_BASE, 0, self.TX_IN_RX_TEST_MODE_MASK) and \
               DevMem.rmw(self.REG_JAMMING_CONTROL, 0, self.JAMMING_RX_TEST_MASK)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control timing register")
    parser.add_argument("-t", "--test", help="enable Rx test mode", action="store_true")
    parser.add_argument("-d", "--disable", help="disable timing modes", action="store_true")
    parser.add_argument("-x", "--enable_tx", help="enable Tx in Rx test mode", action="store_true")
    args = parser.parse_args()
    t = TimingControl()
    if args.test:
        t.enable_rx_test_mode()
    elif args.enable_tx:
        t.enable_tx_in_rx_test_mode()
    elif args.disable:
        t.disable()
    print("Register Value: 0x{:08x}".format(t.value()))
