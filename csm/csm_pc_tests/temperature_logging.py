#!/usr/bin/env python3
"""
Utility script for logging CSM temperatures to a CSV file.

Requires the following to be installed on the CSM:
- KT-956-0230-00 K-CEMA CSM PCB Zeroise Micro Test Utility v3.0.3 onwards on Zeroise Microcontroller
- KT-956-0234-00 K-CEMA CSM Platform Test Scripts v1.9.5 onwards in folder /run/media/mmcblk1p2/test on the SoM
"""

import csv
from csm_zero_micro_test_intf import *
import logging
import time
from datetime import datetime
from csm_plat_test_intf import CsmPlatformTest

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

fmt = "%(asctime)s: %(message)s"
# Set logging level to DEBUG to see test pass/fail results and DEBUG
# to see detailed information
logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

COM_PORT = "COM13"
HOSTNAME = "csm-014486.local"
USERNAME = "root"
PASSWORD = "gbL^58TJc"
HEADERS = ["time", "battery", "amb_tmp442", "amb_ad7415", "amb_ltc2991",
           "som", "gbe_sw", "gbe_sw_phy", "stm32", "poe_pse"]

with open("{}_temperature_log.csv".format(datetime.now().strftime("%Y%m%d%H%M")), 'w', newline='') as f:
    f_csv = csv.writer(f)
    f_csv.writerow(HEADERS)
    print(HEADERS)

    with CsmZeroiseMircoTestInterface(COM_PORT) as c:
        with CsmPlatformTest(USERNAME, PASSWORD, HOSTNAME) as cssh:
            # for _ in range(0, 5):
            while True:
                gbe_sw, gbe_sw_phy = cssh.get_gbe_sw_temperatures()
                row = (datetime.utcnow().astimezone().replace(microsecond=0).isoformat(),
                       "{:.2f}".format(c.get_battery_temperature()),
                       "{:.2f}".format(cssh.get_tmp442_temperatures().get("Internal", -255.0)),
                       "{:.2f}".format(cssh.get_ad7415_temperature()),
                       "{:.2f}".format(cssh.get_ltc2991_temperature()),
                       "{:.2f}".format(cssh.get_som_temperature()),
                       "{:.2f}".format(gbe_sw),
                       "{:.2f}".format(gbe_sw_phy),
                       "{:.2f}".format(c.get_stm32_temperature()),
                       "{:.2f}".format(c.get_poe_pse_temperature()))
                print(row)
                f_csv.writerow(row)
                time.sleep(0.1)
