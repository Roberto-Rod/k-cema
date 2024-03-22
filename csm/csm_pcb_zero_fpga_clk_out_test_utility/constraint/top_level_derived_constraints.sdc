# Microsemi Corp.
# Date: 2020-Sep-01 15:39:45
# This file was generated based on the following SDC source files:
#   C:/workspace/k-cema/hw-test/csm/csm_pcb_zero_fpga_clk_out_test_utility/component/work/OSC_C0/OSC_C0_0/OSC_C0_OSC_C0_0_OSC.sdc
#   C:/Microsemi/Libero_SoC_v12.4/Designer/data/aPA4M/cores/constraints/sysreset.sdc
#

create_clock -ignore_errors -name {OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT} -period 20 [ get_pins { OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT } ]
create_clock -ignore_errors -name {OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT} -period 1000 [ get_pins { OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT } ]
set_false_path -ignore_errors -through [ get_pins { SYSRESET_0/POWER_ON_RESET_N } ]
