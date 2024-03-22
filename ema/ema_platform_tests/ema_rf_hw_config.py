#!/usr/bin/env python3
import argparse
import test_hardware_config
from hardware_unit_config import *
import power_supplies
import time
from ipam import *
from serial_number import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check/configure EMA RF hardware IDs")
    parser.add_argument("rev", metavar="rev", type=str, nargs=1, help="EMA assembly revision (e.g. A.1)")
    parser.add_argument("ser", metavar="ser", type=str, nargs=1, help="EMA assembly serial number (e.g. 010461)")
    parser.add_argument("date", metavar="date", type=str, nargs=1, help="EMA build date")
    args = parser.parse_args()
    rev = str(args.rev[0])
    ser = str(args.ser[0])
    date = str(args.date[0])

    print("Enable IPAM power...")
    IPAM.enable_power(True)

    print("Enable RF board digital power...")
    power_supplies.PowerSupplies.rail_3v6_en(True)
    power_supplies.PowerSupplies.rail_5v5_en(True)
    power_supplies.PowerSupplies.rx_en(True)
    time.sleep(1)

    if not IPAM.wait_comms_good(IPAM.POWER_ENABLE_TIMEOUT_S):
        print("ERROR - IPAM timed out")
        exit()
    ipam_part = IPAM.get_part_number()

    # Find RF board part number
    status, rf_config = get_config_info(AssemblyType.NTM_RF_LB)
    ntm_rf_part = ""
    if "Assembly Part Number" in rf_config.keys():
        ntm_rf_part = rf_config["Assembly Part Number"]

    config = None

    if ipam_part == "KT-950-0340-00" or ipam_part == "KT-950-0500-00":
        # Low-Band IPAM
        if ntm_rf_part == "KT-000-0136-00":
            config = AssemblyType.EMA_LB_R
    elif ipam_part == "KT-950-0341-00" or ipam_part == "KT-950-0501-00":
        # Mid-Band IPAM
        if ntm_rf_part == "KT-000-0137-00":
            config = AssemblyType.EMA_MB_R
        elif ntm_rf_part == "KT-000-0202-00" or "KT-000-0202-01":
            config = AssemblyType.EMA_EHB_6GHZ_R
    elif ipam_part == "KT-950-0342-00" or ipam_part == "KT-950-0502-01":
        # High-Band, Responsive IPAM, 6 GHz
        if ntm_rf_part == "KT-000-0137-00":
            config = AssemblyType.EMA_HB_R
        elif ntm_rf_part == "KT-000-0202-00" or "KT-000-0202-01":
            config = AssemblyType.EMA_EHB_6GHZ_R
    elif ipam_part == "KT-950-0502-00":
        # High-Band, Responsive IPAM, 8 GHz
        if ntm_rf_part == "KT-000-0137-00":
            config = AssemblyType.EMA_HB_R
        elif ntm_rf_part == "KT-000-0202-00":
            config = AssemblyType.EMA_EHB_8GHZ_R
    elif ipam_part == "KT-950-0405-00":
        # High-Band, Active IPAM, 6 GHz
        if ntm_rf_part == "KT-000-0137-00" or ntm_rf_part == "KT-000-0137-01":
            config = AssemblyType.EMA_HB_A

    if config is None:
        print("ERROR: Unrecognised IPAM/NTM-RF configuration: {}, {}".format(ipam_part, ntm_rf_part))
    else:
        test_hardware_config.run_test(config, revision=rev, serial_number=ser, date=date)

    print("Disable RF board digital power...")
    power_supplies.PowerSupplies.rx_en(False)
    power_supplies.PowerSupplies.rail_5v5_en(False)
    power_supplies.PowerSupplies.rail_3v6_en(False)

    print("Disable IPAM power...")
    IPAM.enable_power(False)
