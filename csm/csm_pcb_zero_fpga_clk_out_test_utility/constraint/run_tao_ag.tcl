set_device -family {IGLOO2} -die {M2GL025}
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
read_sdc -component {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\component\work\OSC_C0\OSC_C0_0\OSC_C0_OSC_C0_0_OSC.sdc}
derive_constraints
write_sdc {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\top_level_derived_constraints.sdc}
write_pdc {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\fp\top_level_derived_constraints.pdc}
