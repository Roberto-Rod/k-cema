import logging
import sys
from drcu_fd_prod_test import *
from tkinter import messagebox
import tkinter as tk

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
fmt = "%(asctime)s: %(message)s"
logging.basicConfig(format=fmt, level=logging.INFO, datefmt="%H:%M:%S", stream=sys.stdout)

test_jig_com_port = "COM20"
csm_com_port = "COM18"
# unit_hostname = "rcu-000000.local"
unit_hostname = "169.254.7.156"
gbe_switch_serial_port = "/dev/ttymxc2"
test_fw = r"C:\workspace\k-cema\PcbTest\drcu_pcb_production_test_files\drcu_micro_test_utility\KT-956-0256-00.bin"
operational_fw = r"C:\workspace\k-cema\PcbTest\drcu_pcb_production_test_files\drcu_micro_operational_software\KT-956-0376-00.bin"
platform_test_scripts = r"C:\workspace\k-cema\PcbTest\drcu_pcb_production_test_files\drcu_fd_platform_test_scripts\KT-956-0258-00_v1-1-0.tgz"


def instruction_dialog(msg):
    tk.messagebox.showinfo("Instruction", msg)


def yesno_check_dialog(msg):
    return tk.messagebox.askyesno("Manual Check", msg)


with DrcuProdTest(test_jig_com_port, csm_com_port, unit_hostname, gbe_switch_serial_port) as dpt:
    # dpt.enable_som(False)
    # dpt.unit_buzzer_test(yesno_check_dialog)
    # dpt.unit_pps_test(instruction_dialog, yesno_check_dialog)
    # dpt.check_for_sd_card()
    # dpt.discrete_op_test(input)
    # dpt.program_micro(test_fw)
    # dpt.board_case_switch_test(instruction_dialog)
    # dpt.board_light_sensor_test(instruction_dialog)
    # dpt.offboard_supply_rail_test()
    # dpt.poe_pd_pse_type_test()
    # dpt.set_hw_config_info("B.1", "AZTB00046", "MAR23")
    # dpt.batt_temp_sensor_test()
    # dpt.xchange_reset_test()
    # dpt.program_micro(operational_fw)
    # dpt.som_bring_up(input)
    # dpt.enable_som(False)
    # dpt.enable_som(True)
    # dpt.copy_test_scripts_to_som(platform_test_scripts)
    dpt.unit_set_config_info("KT-950-0429-00", "A.1", "000000", "NA", platform_test_scripts, instruction_dialog)
    # dpt.unit_tamper_test()
    # dpt.som_supply_rail_test()
    # dpt.som_ad7415_temp_sensor_test()
    # dpt.som_nvme_test()
    # dpt.gbe_sw_connection_test()
    # dpt.gbe_sw_bandwidth_test()
    # dpt.poe_pse_test()
    # dpt.rtc_test()
    # dpt.board_buzzer_test()
    # dpt.function_button_test(input)
    # dpt.remove_test_scripts()
    # dpt.display_backlight_test(yesno_check_dialog)
    # dpt.keypad_button_test(instruction_dialog)
    # dpt.keypad_led_test(instruction_dialog, yesno_check_dialog)
