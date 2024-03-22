#!/usr/bin/env python3


class TestLimits:    
    TEST_LIMITS = [
        # Section 1: Built-In Test
        [
            # Description                   Units       LL          UL
            ["Initial PSU Current",         "mA",       175,        215     ],  # Sub-section 1
            ["Synth Lock Detect",           "n/a",      1,          1       ],  # Sub-section 2
            ["+12V Voltage",                "mV",       11400,      12600   ],  # Sub-section 3
            ["+5V0 Voltage",                "mV",       4750,       5250    ],  # Sub-section 4
            ["+3V3 Current",                "mA",       185,        225     ],  # Sub-section 5
            ["+3V3 Voltage",                "mV",       3130,       3470    ],  # Sub-section 6
            ["+5V0 Current",                "mA",       220,        270     ],  # Sub-section 7
            ["VREF Internal Voltage",       "mV",       3130,       3470    ]   # Sub-section 8
        ],

        # Section 2: Rx Paths
        [
            # Description                   Units       LL          UL
            ["RX0, 20 MHz, Fund",           "dBm",      -14.0,      -8.0    ],  # Sub-section 1 - Rev A limit
            ["RX0, 1854 MHz, Image",        "dBc",      -99.0,      -45.0   ],  # Sub-section 2 - Rev A limit
            ["RX0, 260 MHz, Fund",          "dBm",      -14.0,      -8.0    ],  # Sub-section 3 - Rev A limit
            ["RX0, 500 MHz, Fund",          "dBm",      -14.0,      -8.0    ],  # Sub-section 4 - Rev A limit
            ["RX1, 500 MHz, Fund",          "dBm",      -16.0,      -10.0   ],  # Sub-section 5
            ["RX1, 5120 MHz, Image",        "dBc",      -99.0,      -60.0   ],  # Sub-section 6 - Rev A limit
            ["RX1, 650 MHz, Fund",          "dBm",      -16.0,      -10.0   ],  # Sub-section 7
            ["RX1, 800 MHz, Fund",          "dBm",      -16.0,      -10.0   ],  # Sub-section 8
            ["RX2, 800 MHz, Fund",          "dBm",      -16.0,      -10.0   ],  # Sub-section 9
            ["RX2, 5510 MHz, Image",        "dBc",      -99.0,      -45.0   ],  # Sub-section 10 - Rev A limit
            ["RX2, 1400 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 11
            ["RX2, 2000 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 12
            ["RX3, 2000 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 13 - Rev A limit
            ["RX3, 170 MHz, Image",         "dBc",      -99.0,      -65.0   ],  # Sub-section 14
            ["RX3, 2300 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 15
            ["RX3, 2600 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 16
            ["RX4, 2600 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 17 - Rev A limit
            ["RX4, 770 MHz, Image",         "dBc",      -99.0,      -55.0   ],  # Sub-section 18 - Rev A limit
            ["RX4, 2800 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 19
            ["RX4, 3000 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 20
            ["RX4, 3001 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 21 - Rev A limit
            ["RX4, 3700 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 22 - Rev A limit
            ["RX4, 4400 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 23 - Rev A limit          
            ["RX5, 4400 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 24
            ["RX5, 310 MHz, Image",         "dBc",      -99.0,      -65.0   ],  # Sub-section 25
            ["RX5, 4535 MHz, Fund",         "dBm",      -16.0,      -10.0   ],  # Sub-section 26
            ["RX5, 4670 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 27 - Rev A limit
            ["RX5, 4671 MHz, Fund",         "dBm",      -18.0,      -10.0   ],  # Sub-section 28 - Rev A limit
            ["RX5, 5335 MHz, Fund",         "dBm",      -20.0,      -10.0   ],  # Sub-section 29 - Rev A limit
            ["RX5, 6000 MHz, Fund",         "dBm",      -22.0,      -10.0   ]   # Sub-section 30 - Rev A limit         
        ],

        # Section 3: Rx Attenuation
        [
            # Description                   Units       LL          UL
            ["Reference Level",             "dBm",      -16.0,      -10.0   ],  # Sub-section 1
            ["0.50 dB State",               "dB",       0.20,       0.80    ],  # Sub-section 2
            ["1.00 dB State",               "dB",       0.55,       1.45    ],  # Sub-section 3
            ["2.00 dB State",               "dB",       1.40,       2.60    ],  # Sub-section 4
            ["4.00 dB State",               "dB",       3.25,       4.75    ],  # Sub-section 5
            ["8.00 dB State",               "dB",       7.00,       9.00    ],  # Sub-section 6
            ["16.00 dB State",              "dB",       14.85,      17.15   ],  # Sub-section 7
            ["31.50 dB State",              "dB",       29.30,      33.70   ]   # Sub-section 8
        ],

        # Section 4: Tx Paths
        [
            # Description                   Units       LL          UL
            ["TX0, 20 MHz, Fund",           "dBm",      10.0,       16.0    ],  # Sub-section 1
            ["TX0, 40 MHz, 2nd Harm",       "dBc",      -99.0,      -13.0   ],  # Sub-section 2
            ["TX0, 60 MHz, 3rd Harm",       "dBc",      -99.0,      -10.0   ],  # Sub-section 3 - Rev A limit
            ["TX0, 410 MHz, Fund",          "dBm",      10.0,       16.0    ],  # Sub-section 4
            ["TX0, 820 MHz, 2nd Harm",      "dBc",      -99.0,      -13.0   ],  # Sub-section 5
            ["TX0, 1230 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 6
            ["TX0, 800 MHz, Fund",          "dBm",      10.0,       16.0    ],  # Sub-section 7
            ["TX0, 1600 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 8
            ["TX0, 2400 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 9
            ["TX1, 700 MHz, Fund",          "dBm",      10.0,       16.0    ],  # Sub-section 10
            ["TX1, 1400 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 11
            ["TX1, 2100 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 12
            ["TX1, 1100 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 13
            ["TX1, 2200 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 14
            ["TX1, 3300 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 15
            ["TX1, 1500 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 16
            ["TX1, 3000 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 17
            ["TX1, 4500 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 18
            ["TX2, 1200 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 19
            ["TX2, 2400 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 20
            ["TX2, 3600 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 21
            ["TX2, 1950 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 22
            ["TX2, 3900 MHz, 2nd Harm",     "dBc",      -99.0,      -10.0   ],  # Sub-section 23 - Rev A limit
            ["TX2, 5850 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 24
            ["TX2, 2700 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 25
            ["TX2, 5400 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 26
            ["TX2, 8100 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 27
            ["TX3, 2400 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 28
            ["TX3, 4800 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 29
            ["TX3, 7200 MHz, 3rd Harm",     "dBc",      -99.0,      -20.0   ],  # Sub-section 30
            ["TX3, 4200 MHz, Fund",         "dBm",      10.0,       16.0    ],  # Sub-section 31
            ["TX3, 8400 MHz, 2nd Harm",     "dBc",      -99.0,      -13.0   ],  # Sub-section 32
            ["TX3, 12600 MHz, 3rd Harm",    "dBc",      -99.0,      -20.0   ],  # Sub-section 33
            ["TX3, 6000 MHz, Fund",         "dBm",      7.5,        16.0    ],  # Sub-section 34 - Rev A limit
            ["TX3, 12000 MHz, 2nd Harm",    "dBc",      -99.0,      -13.0   ]   # Sub-section 35
        ],

        # Section 5: Tx Attenuation
        [
            # Description                   Units       LL          UL
            ["Reference Level",             "dBm",      7.5,        16.0    ],  # Sub-section 1 - Rev A limit
            ["0.50 dB State",               "dB",       0.20,       0.80    ],  # Sub-section 2
            ["1.00 dB State",               "dB",       0.55,       1.45    ],  # Sub-section 3
            ["2.00 dB State",               "dB",       1.40,       2.60    ],  # Sub-section 4
            ["4.00 dB State",               "dB",       3.00,       4.75    ],  # Sub-section 5 - Rev A limit
            ["8.00 dB State",               "dB",       7.00,       9.00    ],  # Sub-section 6
            ["16.00 dB State",              "dB",       14.35,      17.15   ],  # Sub-section 7 - Rev A limit
            ["31.50 dB State",              "dB",       29.30,      33.70   ]   # Sub-section 8
        ],
    ]

    def get(self, section, sub_section):
        description = self.TEST_LIMITS[section][sub_section][0]
        units       = self.TEST_LIMITS[section][sub_section][1]
        lower_limit = self.TEST_LIMITS[section][sub_section][2]
        upper_limit = self.TEST_LIMITS[section][sub_section][3]
        
        return description, units, lower_limit, upper_limit
    
    def section_size(self, section):
        # Return the number of tests within a given section
        return len(self.TEST_LIMITS[section])
    
if __name__ == "__main__":
    print("This module is not intended to be executed stand-alone")