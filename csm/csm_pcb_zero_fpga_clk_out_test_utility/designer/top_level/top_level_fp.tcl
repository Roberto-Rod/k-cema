new_project \
         -name {top_level} \
         -location {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level_fp} \
         -mode {chain} \
         -connect_programmers {FALSE}
add_actel_device \
         -device {M2GL025} \
         -name {M2GL025}
enable_device \
         -name {M2GL025} \
         -enable {TRUE}
save_project
close_project
