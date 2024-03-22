# Written by Synplify Pro version mapact, Build 2737R. Synopsys Run ID: sid1606130883 
# Top Level Design Parameters 

# Clocks 
create_clock -period 1000.000 -waveform {0.000 500.000} -name {OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT} [get_pins {OSC_C0_0/OSC_C0_0/I_RCOSC_1MHZ/CLKOUT}] 
create_clock -period 20.000 -waveform {0.000 10.000} -name {OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT} [get_pins {OSC_C0_0/OSC_C0_0/I_RCOSC_25_50MHZ/CLKOUT}] 

# Virtual Clocks 

# Generated Clocks 

# Paths Between Clocks 

# Multicycle Constraints 

# Point-to-point Delay Constraints 

# False Path Constraints 
set_false_path -through [get_pins {SYSRESET_0/POWER_ON_RESET_N}] 

# Output Load Constraints 

# Driving Cell Constraints 

# Input Delay Constraints 

# Output Delay Constraints 

# Wire Loads 

# Other Constraints 

# syn_hier Attributes 

# set_case Attributes 

# Clock Delay Constraints 

# syn_mode Attributes 

# Cells 

# Port DRC Rules 

# Input Transition Constraints 

# Unused constraints (intentionally commented out) 


# Non-forward-annotatable constraints (intentionally commented out) 

# Block Path constraints 

