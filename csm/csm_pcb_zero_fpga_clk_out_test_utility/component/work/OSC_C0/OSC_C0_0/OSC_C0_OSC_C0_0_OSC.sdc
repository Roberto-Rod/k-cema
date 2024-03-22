set_component OSC_C0_OSC_C0_0_OSC
# Microsemi Corp.
# Date: 2020-Sep-01 12:10:20
#

create_clock -ignore_errors -period 20 [ get_pins { I_RCOSC_25_50MHZ/CLKOUT } ]
create_clock -ignore_errors -period 1000 [ get_pins { I_RCOSC_1MHZ/CLKOUT } ]
