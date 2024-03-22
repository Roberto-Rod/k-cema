open_project -project {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level_fp\top_level.pro}\
         -connect_programmers {FALSE}
load_programming_data \
    -name {M2GL025} \
    -fpga {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.map} \
    -header {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.hdr} \
    -spm {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.spm} \
    -dca {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\top_level.dca}
export_single_ppd \
    -name {M2GL025} \
    -file {C:\workspace\k-cema\hw-test\csm\csm_pcb_zero_fpga_clk_out_test_utility\designer\top_level\export/tempExport\top_level.ppd}

save_project
close_project
