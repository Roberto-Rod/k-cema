set_device \
    -family  IGLOO2 \
    -die     PA4MGL2500_N \
    -package fg484 \
    -speed   STD \
    -tempr   {IND} \
    -voltr   {IND}
set_def {VOLTAGE} {1.2}
set_def {VCCI_1.2_VOLTR} {COM}
set_def {VCCI_1.5_VOLTR} {COM}
set_def {VCCI_1.8_VOLTR} {COM}
set_def {VCCI_2.5_VOLTR} {COM}
set_def {VCCI_3.3_VOLTR} {COM}
set_def USE_CONSTRAINTS_FLOW 1
set_name top_level
set_workdir {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level}
set_design_state post_layout
