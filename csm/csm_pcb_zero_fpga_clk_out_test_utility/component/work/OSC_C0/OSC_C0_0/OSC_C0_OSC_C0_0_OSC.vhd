-- Version: v12.4 12.900.0.16

library ieee;
use ieee.std_logic_1164.all;
library smartfusion2;
use smartfusion2.all;

entity OSC_C0_OSC_C0_0_OSC is

    port( XTL                : in    std_logic;
          RCOSC_25_50MHZ_CCC : out   std_logic;
          RCOSC_25_50MHZ_O2F : out   std_logic;
          RCOSC_1MHZ_CCC     : out   std_logic;
          RCOSC_1MHZ_O2F     : out   std_logic;
          XTLOSC_CCC         : out   std_logic;
          XTLOSC_O2F         : out   std_logic
        );

end OSC_C0_OSC_C0_0_OSC;

architecture DEF_ARCH of OSC_C0_OSC_C0_0_OSC is 

  component RCOSC_25_50MHZ_FAB
    port( A      : in    std_logic := 'U';
          CLKOUT : out   std_logic
        );
  end component;

  component RCOSC_25_50MHZ
    generic (FREQUENCY:real := 50.0);

    port( CLKOUT : out   std_logic
        );
  end component;

  component CLKINT
    port( A : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component RCOSC_1MHZ_FAB
    port( A      : in    std_logic := 'U';
          CLKOUT : out   std_logic
        );
  end component;

  component RCOSC_1MHZ
    port( CLKOUT : out   std_logic
        );
  end component;

    signal N_RCOSC_25_50MHZ_CLKOUT, N_RCOSC_25_50MHZ_CLKINT, 
        N_RCOSC_1MHZ_CLKOUT, N_RCOSC_1MHZ_CLKINT : std_logic;

begin 


    I_RCOSC_25_50MHZ_FAB : RCOSC_25_50MHZ_FAB
      port map(A => N_RCOSC_25_50MHZ_CLKOUT, CLKOUT => 
        N_RCOSC_25_50MHZ_CLKINT);
    
    I_RCOSC_25_50MHZ : RCOSC_25_50MHZ
      generic map(FREQUENCY => 50.0)

      port map(CLKOUT => N_RCOSC_25_50MHZ_CLKOUT);
    
    I_RCOSC_1MHZ_FAB_CLKINT : CLKINT
      port map(A => N_RCOSC_1MHZ_CLKINT, Y => RCOSC_1MHZ_O2F);
    
    I_RCOSC_1MHZ_FAB : RCOSC_1MHZ_FAB
      port map(A => N_RCOSC_1MHZ_CLKOUT, CLKOUT => 
        N_RCOSC_1MHZ_CLKINT);
    
    I_RCOSC_25_50MHZ_FAB_CLKINT : CLKINT
      port map(A => N_RCOSC_25_50MHZ_CLKINT, Y => 
        RCOSC_25_50MHZ_O2F);
    
    I_RCOSC_1MHZ : RCOSC_1MHZ
      port map(CLKOUT => N_RCOSC_1MHZ_CLKOUT);
    

end DEF_ARCH; 
