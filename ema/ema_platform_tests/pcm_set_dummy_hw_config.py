#!/usr/bin/env python3

from hardware_unit_config import *

if __name__ == "__main__":
    ok = set_config_info("000000", "N/A", "N/A", AssemblyType.PCM)
    print("{}".format("OK: hardware configuration written to PCM hardware ID IC" if ok
                      else "ERROR: failed to write hardware configuration to PCM hardware ID IC"))
