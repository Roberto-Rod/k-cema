----------------------------------------------------------------------
-- Created by SmartDesign Tue Sep  1 12:10:20 2020
-- Version: v12.4 12.900.0.16
----------------------------------------------------------------------

----------------------------------------------------------------------
-- Libraries
----------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

library smartfusion2;
use smartfusion2.all;
----------------------------------------------------------------------
-- OSC_C0 entity declaration
----------------------------------------------------------------------
entity OSC_C0 is
    -- Port list
    port(
        -- Outputs
        RCOSC_1MHZ_O2F     : out std_logic;
        RCOSC_25_50MHZ_O2F : out std_logic
        );
end OSC_C0;
----------------------------------------------------------------------
-- OSC_C0 architecture body
----------------------------------------------------------------------
architecture RTL of OSC_C0 is
----------------------------------------------------------------------
-- Component declarations
----------------------------------------------------------------------
-- OSC_C0_OSC_C0_0_OSC   -   Actel:SgCore:OSC:2.0.101
component OSC_C0_OSC_C0_0_OSC
    -- Port list
    port(
        -- Inputs
        XTL                : in  std_logic;
        -- Outputs
        RCOSC_1MHZ_CCC     : out std_logic;
        RCOSC_1MHZ_O2F     : out std_logic;
        RCOSC_25_50MHZ_CCC : out std_logic;
        RCOSC_25_50MHZ_O2F : out std_logic;
        XTLOSC_CCC         : out std_logic;
        XTLOSC_O2F         : out std_logic
        );
end component;
----------------------------------------------------------------------
-- Signal declarations
----------------------------------------------------------------------
signal RCOSC_1MHZ_O2F_net_0       : std_logic;
signal RCOSC_25_50MHZ_O2F_0       : std_logic;
signal RCOSC_1MHZ_O2F_net_1       : std_logic;
signal RCOSC_25_50MHZ_O2F_0_net_0 : std_logic;
----------------------------------------------------------------------
-- TiedOff Signals
----------------------------------------------------------------------
signal GND_net                    : std_logic;

begin
----------------------------------------------------------------------
-- Constant assignments
----------------------------------------------------------------------
 GND_net <= '0';
----------------------------------------------------------------------
-- Top level output port assignments
----------------------------------------------------------------------
 RCOSC_1MHZ_O2F_net_1       <= RCOSC_1MHZ_O2F_net_0;
 RCOSC_1MHZ_O2F             <= RCOSC_1MHZ_O2F_net_1;
 RCOSC_25_50MHZ_O2F_0_net_0 <= RCOSC_25_50MHZ_O2F_0;
 RCOSC_25_50MHZ_O2F         <= RCOSC_25_50MHZ_O2F_0_net_0;
----------------------------------------------------------------------
-- Component instances
----------------------------------------------------------------------
-- OSC_C0_0   -   Actel:SgCore:OSC:2.0.101
OSC_C0_0 : OSC_C0_OSC_C0_0_OSC
    port map( 
        -- Inputs
        XTL                => GND_net, -- tied to '0' from definition
        -- Outputs
        RCOSC_25_50MHZ_CCC => OPEN,
        RCOSC_25_50MHZ_O2F => RCOSC_25_50MHZ_O2F_0,
        RCOSC_1MHZ_CCC     => OPEN,
        RCOSC_1MHZ_O2F     => RCOSC_1MHZ_O2F_net_0,
        XTLOSC_CCC         => OPEN,
        XTLOSC_O2F         => OPEN 
        );

end RTL;
