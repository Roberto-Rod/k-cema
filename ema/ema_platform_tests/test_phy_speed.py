#!/usr/bin/env python3
import os


def run_test():
    print("")
    print("test_phy_speed")
    print("----------------")
    cmd = "/bin/dmesg | /bin/grep 'macb e000b000.ethernet eth0: link'"
    resp = os.popen(cmd).read().splitlines()
    # Check the most recent message (the last line of the response)
    if resp:
        status = resp[-1]
        if "1000/Full" in status:
            print("PASS ({})".format(status))
            return True
        else:
            print("FAIL ({})".format(status))
            return False
    else:
        print("FAIL (no link)")
        return False


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
