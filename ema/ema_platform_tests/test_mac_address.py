#!/usr/bin/env python3
import os


def run_test():
    ok = True
    print("")
    print("test_mac_address")
    print("----------------")
    mac = str(os.popen("/usr/bin/getmac").read())
    mac_bytes = mac.split(":")
    if len(mac_bytes) == 6:
        for by in mac_bytes:
            try:
                i = int(by, 16)
                if i > 255:
                    ok = False
            except:
                ok = False
    else:
        ok = False

    if ok:
        print("PASS ({})".format(mac))
    else:
        print("FAIL - MAC address error ({})".format(mac))

    return ok


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
