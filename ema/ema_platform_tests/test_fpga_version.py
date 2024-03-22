#!/usr/bin/env python3
from devmem import *


def run_test():
    print("")
    print("test_fpga_version")
    print("-----------------")
    test_fpga_version_mask = 0xFF00FF00
    version_address = 0x40000000
    build_id_address = 0x40000004
    reg = DevMem.read(version_address)
    if reg & test_fpga_version_mask != test_fpga_version_mask:
        print("FAIL (the loaded FPGA is not a test image)")
        return False
    version = reg & 0xFF
    build_id = DevMem.read(build_id_address)
    print("PASS (test FPGA image version {}, build ID 0x{:08x})".format(version, build_id))
    return True


if __name__ == "__main__":
    if run_test():
        print("\n*** OK - test passed ***\n")
    else:
        print("\n*** TEST FAILED ***\n")
