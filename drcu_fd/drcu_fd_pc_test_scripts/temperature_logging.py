import csv
from drcu_micro_test_intf import *
import logging
import time
from datetime import datetime
from drcu_plat_test_intf import DrcuPlatformTest

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

fmt = "%(asctime)s: %(message)s"
# Set logging level to DEBUG to see test pass/fail results and DEBUG
# to see detailed information
logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S")

COM_PORT = "COM46"
HOSTNAME = "rcu-000000.local"
USERNAME = "root"
HEADERS = ["time", "battery", "ambient", "soc_main", "soc_arm", "gbe_sw", "stm32", "poe_pse", "nvme"]

with open("{}_temperature_log.csv".format(datetime.now().strftime("%Y%m%d%H%M")), 'w', newline='') as f:
    f_csv = csv.writer(f)
    f_csv.writerow(HEADERS)
    print(HEADERS)

    with DrcuMircoTestInterface(COM_PORT) as d:
        with DrcuPlatformTest(USERNAME, HOSTNAME) as dssh:
            while True:
                soc_main_temp, soc_arm_core_temp = dssh.get_soc_temperatures()
                row = (datetime.utcnow().astimezone().replace(microsecond=0).isoformat(),
                       "{:.2f}".format(d.get_battery_temperature()),
                       "{:.2f}".format(dssh.get_ad7415_temperature()),
                       "{:.2f}".format(soc_main_temp),
                       "{:.2f}".format(soc_arm_core_temp),
                       "{:.2f}".format(dssh.get_gbe_sw_temperature(serial_port="/dev/ttymxc2")),
                       "{:.2f}".format(d.get_stm32_temperature()),
                       "{:.2f}".format(dssh.get_poe_pse_temperature()),
                       "{:.2f}".format(dssh.get_nvme_temperature()))
                print(row)
                f_csv.writerow(row)
                time.sleep(1.0)
