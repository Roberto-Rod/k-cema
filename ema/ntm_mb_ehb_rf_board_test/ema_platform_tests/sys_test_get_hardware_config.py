#!/usr/bin/env python3
from hardware_unit_config import *

import argparse


# Class provided to get the hardware configuration information using command line arguments
class SysTestGetHwConfigInfo:
    def get_hw_config_info(self, assembly_type):
        print("Getting hardware config info for {}...".format(assembly_type))
        return get_config_info(assembly_type, config_version=1)


if __name__ == "__main__":
    o = SysTestGetHwConfigInfo()
    parser = argparse.ArgumentParser(description="Get the hardware configuration information")
    parser.add_argument("assembly_type", type=AssemblyType.from_string, choices=list(AssemblyType), help="Enumerated AssemblyType found in hardware_unit_config.py")
    args = parser.parse_args()
    ok, return_dict = o.get_hw_config_info(args.assembly_type)
    if ok:
        print("OK")
        print(return_dict)
    else:
        print("Error")