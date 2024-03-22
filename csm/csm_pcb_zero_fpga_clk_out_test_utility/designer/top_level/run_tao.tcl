set_family {IGLOO2}
read_vhdl -mode vhdl_2008 {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\component\work\OSC_C0\OSC_C0_0\OSC_C0_OSC_C0_0_OSC.vhd}
read_vhdl -mode vhdl_2008 {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\component\work\OSC_C0\OSC_C0.vhd}
 add_include_path  {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl}
read_verilog -mode system_verilog {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl\registerInterface.v}
 add_include_path  {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl}
 add_include_path  {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl}
read_verilog -mode system_verilog {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl\serialInterface.v}
 add_include_path  {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl}
read_verilog -mode system_verilog {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\hdl\i2cSlave.v}
read_vhdl -mode vhdl_2008 {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\component\work\top_level\top_level.vhd}
set_top_level {top_level}
map_netlist
read_sdc {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\top_level_derived_constraints.sdc}
check_constraints {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\synthesis_sdc_errors.log}
write_fdc {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\synthesis.fdc}
