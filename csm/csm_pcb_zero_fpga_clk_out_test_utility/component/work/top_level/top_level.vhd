----------------------------------------------------------------------
-- Created by SmartDesign Mon Nov 23 11:26:48 2020
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
-- top_level entity declaration
----------------------------------------------------------------------
entity top_level is
    -- Port list
    port(
        -- Inputs
        devrst_n       : in    std_logic;
        i2c_scl        : in    std_logic;
        zer_fpga_rst_n : in    std_logic;
        -- Outputs
        clk_out_1mhz   : out   std_logic;
        gpo            : out   std_logic;
        zer_qspi_sel   : out   std_logic;
        -- Inouts
        i2c_sda        : inout std_logic
        );
end top_level;
----------------------------------------------------------------------
-- top_level architecture body
----------------------------------------------------------------------
architecture RTL of top_level is
----------------------------------------------------------------------
-- Component declarations
----------------------------------------------------------------------
-- AND2
component AND2
    -- Port list
    port(
        -- Inputs
        A : in  std_logic;
        B : in  std_logic;
        -- Outputs
        Y : out std_logic
        );
end component;
-- i2cSlave
component i2cSlave
    -- Port list
    port(
        -- Inputs
        clk    : in    std_logic;
        rst    : in    std_logic;
        scl    : in    std_logic;
        -- Outputs
        myReg0 : out   std_logic_vector(7 downto 0);
        -- Inouts
        sda    : inout std_logic
        );
end component;
-- NAND2
component NAND2
    -- Port list
    port(
        -- Inputs
        A : in  std_logic;
        B : in  std_logic;
        -- Outputs
        Y : out std_logic
        );
end component;
-- OSC_C0
component OSC_C0
    -- Port list
    port(
        -- Outputs
        RCOSC_1MHZ_O2F     : out std_logic;
        RCOSC_25_50MHZ_O2F : out std_logic
        );
end component;
-- SYSRESET
component SYSRESET
    -- Port list
    port(
        -- Inputs
        DEVRST_N         : in  std_logic;
        -- Outputs
        POWER_ON_RESET_N : out std_logic
        );
end component;
----------------------------------------------------------------------
-- Signal declarations
----------------------------------------------------------------------
signal clk_out_1mhz_net_0          : std_logic;
signal gpo_net_0                   : std_logic_vector(7 downto 0);
signal gpo_0                       : std_logic_vector(0 to 0);
signal i2cSlave_0_myReg01to1       : std_logic_vector(1 to 1);
signal NAND2_0_Y                   : std_logic;
signal OSC_C0_0_RCOSC_1MHZ_O2F     : std_logic;
signal OSC_C0_0_RCOSC_25_50MHZ_O2F : std_logic;
signal SYSRESET_0_POWER_ON_RESET_N : std_logic;
signal clk_out_1mhz_net_1          : std_logic;
signal gpo_0_net_0                 : std_logic;
signal myReg0_slice_0              : std_logic_vector(2 to 2);
signal myReg0_slice_1              : std_logic_vector(3 to 3);
signal myReg0_slice_2              : std_logic_vector(4 to 4);
signal myReg0_slice_3              : std_logic_vector(5 to 5);
signal myReg0_slice_4              : std_logic_vector(6 to 6);
signal myReg0_slice_5              : std_logic_vector(7 to 7);
----------------------------------------------------------------------
-- TiedOff Signals
----------------------------------------------------------------------
signal GND_net                     : std_logic;

begin
----------------------------------------------------------------------
-- Constant assignments
----------------------------------------------------------------------
 GND_net <= '0';
----------------------------------------------------------------------
-- TieOff assignments
----------------------------------------------------------------------
 zer_qspi_sel       <= '0';
----------------------------------------------------------------------
-- Top level output port assignments
----------------------------------------------------------------------
 clk_out_1mhz_net_1 <= clk_out_1mhz_net_0;
 clk_out_1mhz       <= clk_out_1mhz_net_1;
 gpo_0_net_0        <= gpo_0(0);
 gpo                <= gpo_0_net_0;
----------------------------------------------------------------------
-- Slices assignments
----------------------------------------------------------------------
 gpo_0(0)                 <= gpo_net_0(0);
 i2cSlave_0_myReg01to1(1) <= gpo_net_0(1);
 myReg0_slice_0(2)        <= gpo_net_0(2);
 myReg0_slice_1(3)        <= gpo_net_0(3);
 myReg0_slice_2(4)        <= gpo_net_0(4);
 myReg0_slice_3(5)        <= gpo_net_0(5);
 myReg0_slice_4(6)        <= gpo_net_0(6);
 myReg0_slice_5(7)        <= gpo_net_0(7);
----------------------------------------------------------------------
-- Component instances
----------------------------------------------------------------------
-- AND2_0
AND2_0 : AND2
    port map( 
        -- Inputs
        A => OSC_C0_0_RCOSC_1MHZ_O2F,
        B => i2cSlave_0_myReg01to1(1),
        -- Outputs
        Y => clk_out_1mhz_net_0 
        );
-- i2cSlave_0
i2cSlave_0 : i2cSlave
    port map( 
        -- Inputs
        clk    => OSC_C0_0_RCOSC_25_50MHZ_O2F,
        rst    => NAND2_0_Y,
        scl    => i2c_scl,
        -- Outputs
        myReg0 => gpo_net_0,
        -- Inouts
        sda    => i2c_sda 
        );
-- NAND2_0
NAND2_0 : NAND2
    port map( 
        -- Inputs
        A => SYSRESET_0_POWER_ON_RESET_N,
        B => zer_fpga_rst_n,
        -- Outputs
        Y => NAND2_0_Y 
        );
-- OSC_C0_0
OSC_C0_0 : OSC_C0
    port map( 
        -- Outputs
        RCOSC_1MHZ_O2F     => OSC_C0_0_RCOSC_1MHZ_O2F,
        RCOSC_25_50MHZ_O2F => OSC_C0_0_RCOSC_25_50MHZ_O2F 
        );
-- SYSRESET_0
SYSRESET_0 : SYSRESET
    port map( 
        -- Inputs
        DEVRST_N         => devrst_n,
        -- Outputs
        POWER_ON_RESET_N => SYSRESET_0_POWER_ON_RESET_N 
        );

end RTL;
