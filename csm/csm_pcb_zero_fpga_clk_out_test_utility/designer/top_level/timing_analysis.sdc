# Microsemi Corp.
# Date: 2020-Sep-01 12:36:02
# This file was generated based on the following SDC source files:
#   C:/workspace/k-cema/hw-test/csm/csm_pcb_zero_fpga_clk_out_test_utility/constraint/top_level_derived_constraints.sdc
#

create_clock -name {OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT} -period 20 [ get_pins { OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT } ]
create_clock -name {OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT} -period 1000 [ get_pins { OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT } ]
