#!/usr/bin/env python3
from tamper import *
import os

WAIT_TIMEOUT = 15 * 60


def run_test():
    print("")
    print("test_tamper")
    print("-----------")
    print("Test RTC oscillator: ", end = "", flush = True)
    t = Tamper()
    t.reset()
    if t.is_ticking():
        print("PASS")
    else:
        print("FAIL")
        return False
    print("Release microswitch", end = "", flush = True)
    if not wait_state(TamperChannel.MICROSWITCH, True):
        return False
    print("Depress microswitch", end = "", flush = True)
    if not wait_state(TamperChannel.MICROSWITCH, False):
        return False
    print("Release microswitch", end = "", flush = True)
    if not wait_state(TamperChannel.MICROSWITCH, True):
        return False
    print("Uncover light sensor", end = "", flush = True)
    if not wait_state(TamperChannel.LIGHT_SENSOR, True):
        return False
    print("Cover light sensor", end = "", flush = True)
    if not wait_state(TamperChannel.LIGHT_SENSOR, False):
        return False
    print("Uncover light sensor", end = "", flush = True)
    if not wait_state(TamperChannel.LIGHT_SENSOR, True):
        return False
    # Reset tamper device so that it is ticking and write system date/time to the device
    t.reset()
    os.system("/sbin/hwclock -w")
    return True


def wait_state(channel, state):
    stop = False
    count = 0
    t = Tamper()
    while not stop:
        print(".", end = "", flush = True)
        t.reset()
        t.arm()
        if t.is_tampered(channel) == state:
            stop = True
        count += 1
        if count >= WAIT_TIMEOUT:
            print("ERROR: TIMED OUT")
            return False
    print("OK")
    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
