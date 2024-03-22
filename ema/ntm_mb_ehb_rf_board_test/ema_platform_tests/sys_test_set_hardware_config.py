#!/usr/bin/env python3
from hardware_unit_config import *

import argparse


# Class provided to set the hardware configuration information using command line arguments
class SysTestSetHwConfigInfo:
    def set_hw_config_info(self, serial_no, rev_no, batch_no, assembly_type):
        print("Setting hardware config info for {}...".format(assembly_type))
        return set_config_info(serial_no, rev_no, batch_no, assembly_type, config_version=1)


if __name__ == "__main__":
    o = SysTestSetHwConfigInfo()
    parser = argparse.ArgumentParser(description="Set the hardware configuration information")
    parser.add_argument("serial_no", type=str, help="Serial number e.g. 123456")
    parser.add_argument("rev_no", type=str, help="Revision number e.g. A.1")
    parser.add_argument("batch_no", type=str, help="Batch number/build date e.g. 31/05/2023")    
    parser.add_argument("assembly_type", type=AssemblyType.from_string, choices=list(AssemblyType), help="Enumerated AssemblyType found in hardware_unit_config.py")
    args = parser.parse_args()
    ok = o.set_hw_config_info(args.serial_no, args.rev_no, args.batch_no, args.assembly_type)
    if ok:
        print("OK")
    else:
        print("Error")