set_family {IGLOO2}
read_adl {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.adl}
read_afl {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.afl}
map_netlist
read_sdc {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\top_level_derived_constraints.sdc}
check_constraints {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\constraint\timing_sdc_errors.log}
write_sdc -strict -afl {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\timing_analysis.sdc}
