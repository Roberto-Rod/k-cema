#!/usr/bin/env python3


class TestLimitsProduction:    
    TEST_LIMITS = [
        # Section 1: Built-In Test
        [
            # Description                   Units       LL          UL
            ["Initial PSU Current",         "mA",       850,        1100    ],  # Sub-section 1
            ["Daughter ID",                 "n/a",      2,          2       ],  # Sub-section 2
            ["+1V3 Rail",                   "V",        1.23,       1.37    ],  # Sub-section 3
            ["+1V8 Rail",                   "V",        1.71,       1.89    ],  # Sub-section 4
            ["+3V3 Rail",                   "V",        3.13,       3.47    ],  # Sub-section 5
            ["+5V0 Rail",                   "V",        4.75,       5.25    ],  # Sub-section 6
            ["-2V5 Rail",                   "V",        -2.62,      -2.38   ],  # Sub-section 7
            ["-3V3 Rail",                   "V",        -3.47,      -3.13   ],  # Sub-section 8
            ["LNA 1 VDD (off)",             "V",        0.00,       0.01    ],  # Sub-section 9
            ["LNA 2 VDD (off)",             "V",        0.00,       0.01    ],  # Sub-section 10
            ["GB 2 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 11
            ["GB 3 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 12
            ["GB 4 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 13
            ["GB 5 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 14
            ["GB 6 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 15
            ["GB 7 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 16
            ["GB 8 VDD (off)",              "V",        0.00,       0.01    ],  # Sub-section 17
            ["LNA 1 VDD (on)",              "V",        4.75,       5.25    ],  # Sub-section 18
            ["LNA 2 VDD (on)",              "V",        4.75,       5.25    ],  # Sub-section 19
            ["GB 2 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 20
            ["GB 3 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 21
            ["GB 7 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 22
            ["GB 8 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 23
            ["GB 4 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 24
            ["GB 5 VDD (on)",               "V",        4.75,       5.25    ],  # Sub-section 25
            ["GB 6 VDD (on)",               "V",        4.75,       5.25    ]   # Sub-section 26                
        ],
        
        # Section 2: Hardware Configuration Data
        [
            # Description                   Units       LL          UL
            ["Set HW Configuration Data",   "n/a",      "Pass",     "Pass"  ],  # Sub-section 1
            ["Verify Serial Number",        "n/a",      "",         ""      ],  # Sub-section 2
            ["Verify Revision Number",      "n/a",      "",         ""      ],  # Sub-section 3
            ["Verify Batch Number",         "n/a",      "",         ""      ],  # Sub-section 4
            ["Verify Part Number",          "n/a",      "",         ""      ],  # Sub-section 5
            ["Verify Checksum Valid",       "n/a",      "Pass",     "Pass"  ]   # Sub-section 6
        ],

        # Section 3: DDS Tx Paths
        # Only the known w.c. spur mechanisms are measured, up to 8 GHz maximum frequency
        [
            # Description                   Units       LL          UL          Tx Attenuation
            ["DDS0, 400 MHz, F1 Fund",      "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 1
            ["DDS0, 800 MHz, F2 Spur",      "dBc",      -99.0,      -23.0           ],  # Sub-section 2
            ["DDS0, 1200 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 3
            ["DDS0, 1600 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 4
            ["DDS0, 950 MHz, F1 Fund",      "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 5
            ["DDS0, 1900 MHz, F2 Spur",     "dBc",      -99.0,      -25.0           ],  # Sub-section 6
            ["DDS0, 2850 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 7
            ["DDS0, 3800 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 8
            ["DDS0, 1500 MHz, F1 Fund",     "dBm",      8.0,        15.0,       0.5 ],  # Sub-section 9
            ["DDS0, 3000 MHz, F2 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 10
            ["DDS0, 4500 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 11
            ["DDS0, 6000 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 12
            ["DDS1, 1480 MHz, F2 Fund",     "dBm",      8.0,        15.0,       1.5 ],  # Sub-section 13
            ["DDS1, 740 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 14
            ["DDS1, 2220 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 15
            ["DDS1, 2960 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 16
            ["DDS1, 1680 MHz, F2 Fund",     "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 17
            ["DDS1, 840 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 18
            ["DDS1, 2520 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 19
            ["DDS1, 3360 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 20
            ["DDS1, 1880 MHz, F2 Fund",     "dBm",      8.0,        15.0,       2.0 ],  # Sub-section 21
            ["DDS1, 940 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 22
            ["DDS1, 2820 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 23
            ["DDS1, 3760 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 24
            ["DDS2, 1850 MHz, F2 Fund",     "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 25
            ["DDS2, 925 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 26
            ["DDS2, 2775 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 27
            ["DDS2, 3700 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 28
            ["DDS2, 2050 MHz, F2 Fund",     "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 29
            ["DDS2, 1025 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 30
            ["DDS2, 3075 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 31
            ["DDS2, 4100 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 32
            ["DDS2, 2250 MHz, F2 Fund",     "dBm",      8.0,        15.0,       0.5 ],  # Sub-section 33
            ["DDS2, 1125 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 34
            ["DDS2, 3375 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 35
            ["DDS2, 4500 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 36
            ["DDS3, 2250 MHz, F2 Fund",     "dBm",      8.0,        15.0,       1.5 ],  # Sub-section 37
            ["DDS3, 1125 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 38
            ["DDS3, 3375 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 39
            ["DDS3, 4500 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 40
            ["DDS3, 2625 MHz, F2 Fund",     "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 41
            ["DDS3, 1312.5 MHz, F1 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 42
            ["DDS3, 3937.5 MHz, F3 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 43
            ["DDS3, 5250 MHz, F4 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 44
            ["DDS3, 3000 MHz, F2 Fund",     "dBm",      4.0,        15.0,       0.0 ],  # Sub-section 45
            ["DDS3, 1500 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 46
            ["DDS3, 4500 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 47
            ["DDS3, 6000 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 48
            ["DDS4, 2400 MHz, F4 Fund",     "dBm",      8.0,        15.0,       1.0 ],  # Sub-section 49
            ["DDS4, 600 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 50
            ["DDS4, 1200 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 51
            ["DDS4, 1800 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 52
            ["DDS4, 3000 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 53
            ["DDS4, 3600 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 54
            ["DDS4, 4200 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 55
            ["DDS4, 4800 MHz, F8 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 56
            ["DDS4, 2900 MHz, F4 Fund",     "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 57
            ["DDS4, 725 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 58
            ["DDS4, 1450 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 59
            ["DDS4, 2175 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 60
            ["DDS4, 3625 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 61
            ["DDS4, 4350 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 62
            ["DDS4, 5075 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 63
            ["DDS4, 5800 MHz, F8 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 64
            ["DDS4, 3400 MHz, F4 Fund",     "dBm",      6.0,        15.0,       0.0 ],  # Sub-section 65
            ["DDS4, 850 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 66
            ["DDS4, 1700 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 67
            ["DDS4, 2550 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 68
            ["DDS4, 4250 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 69
            ["DDS4, 5100 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 70
            ["DDS4, 5950 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 71
            ["DDS4, 6800 MHz, F8 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 72
            ["DDS5, 3400 MHz, F4 Fund",     "dBm",      8.0,        15.0,       1.5 ],  # Sub-section 73
            ["DDS5, 850 MHz, F1 Spur",      "dBc",      -99.0,      -30.0           ],  # Sub-section 74
            ["DDS5, 1700 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 75
            ["DDS5, 2550 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 76
            ["DDS5, 4250 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 77
            ["DDS5, 5100 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 78
            ["DDS5, 5950 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 79
            ["DDS5, 6800 MHz, F8 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 80
            ["DDS5, 4000 MHz, F4 Fund",     "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 81
            ["DDS5, 1000 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 82
            ["DDS5, 2000 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 83
            ["DDS5, 3000 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 84
            ["DDS5, 5000 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 85
            ["DDS5, 6000 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 86
            ["DDS5, 7000 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 87
            ["DDS5, 8000 MHz, F8 Spur",     "dBc",      -99.0,      -27.0           ],  # Sub-section 88
            ["DDS5, 4600 MHz, F4 Fund",     "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 89
            ["DDS5, 1150 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 90
            ["DDS5, 2300 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 91
            ["DDS5, 3450 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 92
            ["DDS5, 5750 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 93
            ["DDS5, 6900 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 94
            ["DDS6, 4600 MHz, F4 Fund",     "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 95
            ["DDS6, 1150 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 96
            ["DDS6, 2300 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 97
            ["DDS6, 3450 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 98
            ["DDS6, 5750 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 99
            ["DDS6, 6900 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 100
            ["DDS6, 5300 MHz, F4 Fund",     "dBm",      8.0,        15.0,       1.5 ],  # Sub-section 101
            ["DDS6, 1325 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 102
            ["DDS6, 2650 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 103
            ["DDS6, 3975 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 104
            ["DDS6, 6625 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 105
            ["DDS6, 7950 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 106
            ["DDS6, 6000 MHz, F4 Fund",     "dBm",      5.0,        15.0,       0.0 ],  # Sub-section 107
            ["DDS6, 1500 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 108
            ["DDS6, 3000 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 109
            ["DDS6, 4500 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 110
            ["DDS6, 7500 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 111
            ["DDS7, 5700 MHz, F8 Fund",     "dBm",      8.0,        15.0,       2.0 ],  # Sub-section 112
            ["DDS7, 712.5 MHz, F1 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 113
            ["DDS7, 1425 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 114
            ["DDS7, 2137.5 MHz, F3 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 115
            ["DDS7, 2850 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 116
            ["DDS7, 3562.5 MHz, F5 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 117
            ["DDS7, 4275 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 118
            ["DDS7, 4987.5 MHz, F7 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 119
            ["DDS7, 6412.5 MHz, F9 Spur",   "dBc",      -99.0,      -27.0           ],  # Sub-section 120
            ["DDS7, 7125 MHz, F10 Spur",    "dBc",      -99.0,      -25.0           ],  # Sub-section 121
            ["DDS7, 7837.5 MHz, F11 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 122
            ["DDS7, 6850 MHz, F8 Fund",     "dBm",      8.0,        15.0,       1.5 ],  # Sub-section 123
            ["DDS7, 856.25 MHz, F1 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 124
            ["DDS7, 1712.5 MHz, F2 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 125
            ["DDS7, 2568.75 MHz, F3 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 126
            ["DDS7, 3425 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 127
            ["DDS7, 4281.25 MHz, F5 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 128
            ["DDS7, 5137.5 MHz, F6 Spur",   "dBc",      -99.0,      -30.0           ],  # Sub-section 129
            ["DDS7, 5993.75 MHz, F7 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 130
            ["DDS7, 7706.25 MHz, F9 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 131
            ["DDS7, 8000 MHz, F8 Fund",     "dBm",      2.0,        15.0,       0.0 ],  # Sub-section 132
            ["DDS7, 1000 MHz, F1 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 133
            ["DDS7, 2000 MHz, F2 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 134
            ["DDS7, 3000 MHz, F3 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 135
            ["DDS7, 4000 MHz, F4 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 136
            ["DDS7, 5000 MHz, F5 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 137
            ["DDS7, 6000 MHz, F6 Spur",     "dBc",      -99.0,      -30.0           ],  # Sub-section 138
            ["DDS7, 7000 MHz, F7 Spur",     "dBc",      -99.0,      -30.0           ]   # Sub-section 139
        ],

        # Section 4: DDS Tx Attenuation
        [
            # Description                   Units       LL          UL
            ["Reference Level",             "dBm",      8.0,        15.0    ],  # Sub-section 1
            ["0.25 dB State",               "dB",       0.10,       0.40    ],  # Sub-section 2
            ["0.50 dB State",               "dB",       0.20,       0.80    ],  # Sub-section 3
            ["1.00 dB State",               "dB",       0.55,       1.45    ],  # Sub-section 4
            ["2.00 dB State",               "dB",       1.40,       2.60    ],  # Sub-section 5
            ["4.00 dB State",               "dB",       3.25,       4.75    ],  # Sub-section 6
            ["8.00 dB State",               "dB",       7.00,       9.00    ],  # Sub-section 7
            ["16.00 dB State",              "dB",       14.85,      17.15   ],  # Sub-section 8
            ["51.75 dB State",              "dB",       48.05,      55.45   ]   # Sub-section 9
        ],

        # Section 5: Transceiver Tx Paths
        # Only the known w.c. spur mechanisms are measured, up to 8 GHz maximum frequency
        [
            # Description                   Units       LL          UL          Tx Attenuation (dB)
            ["XCVR0, 400 MHz, F1 Fund",     "dBm",      8.0,        15.0,       4.5 ],  # Sub-section 1
            ["XCVR0, 800 MHz, F2 Spur",     "dBc",      -99.0,      -20.0           ],  # Sub-section 2
            ["XCVR0, 1200 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 3
            ["XCVR0, 613 MHz, F1 Fund",     "dBm",      8.0,        15.0,       6.0 ],  # Sub-section 4
            ["XCVR0, 1226 MHz, F2 Spur",    "dBc",      -99.0,      -23.0           ],  # Sub-section 5
            ["XCVR0, 1839 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 6
            ["XCVR0, 825 MHz, F1 Fund",     "dBm",      8.0,        15.0,       5.0 ],  # Sub-section 7
            ["XCVR0, 1650 MHz, F2 Spur",    "dBc",      -99.0,      -25.0           ],  # Sub-section 8
            ["XCVR0, 2475 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 9            
            ["XCVR1, 825 MHz, F1 Fund",     "dBm",      8.0,        15.0,       6.5 ],  # Sub-section 10
            ["XCVR1, 1650 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 11
            ["XCVR1, 2475 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 12
            ["XCVR1, 1156 MHz, F1 Fund",    "dBm",      8.0,        15.0,       6.0 ],  # Sub-section 13
            ["XCVR1, 2312 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 14
            ["XCVR1, 3468 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 15
            ["XCVR1, 1485 MHz, F1 Fund",    "dBm",      8.0,        15.0,       3.0 ],  # Sub-section 16
            ["XCVR1, 2970 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 17
            ["XCVR1, 4455 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 18
            ["XCVR2, 1485 MHz, F1 Fund",    "dBm",      8.0,        15.0,       6.0 ],  # Sub-section 19
            ["XCVR2, 2970 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 20
            ["XCVR2, 4455 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 21
            ["XCVR2, 2043 MHz, F1 Fund",    "dBm",      8.0,        15.0,       5.5 ],  # Sub-section 22
            ["XCVR2, 4086 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 23
            ["XCVR2, 6129 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 24
            ["XCVR2, 2600 MHz, F1 Fund",    "dBm",      8.0,        15.0 ,      4.5 ],  # Sub-section 25
            ["XCVR2, 5200 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 26
            ["XCVR2, 7800 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 27
            ["XCVR3, 2600 MHz, F1 Fund",    "dBm",      8.0,        15.0,       5.5 ],  # Sub-section 28
            ["XCVR3, 5200 MHz, F2 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 29
            ["XCVR3, 7800 MHz, F3 Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 30
            ["XCVR3, 4300 MHz, F1 Fund",    "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 31
            ["XCVR3, 6000 MHz, F1 Fund",    "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 32
            ["XCVR4, 6000 MHz, F1 Fund",    "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 33
            ["XCVR4, 5000 MHz, IF Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 34
            ["XCVR4, 5500 MHz, LO/2 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 35
            ["XCVR4, 7000 MHz, F1 Fund",    "dBm",      8.0,        15.0,       0.0 ],  # Sub-section 36
            ["XCVR4, 5000 MHz, IF Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 37
            ["XCVR4, 6000 MHz, LO/2 Spur",  "dBc",      -99.0,      -30.0           ],  # Sub-section 38
            ["XCVR4, 8000 MHz, F1 Fund",    "dBm",      2.0,        15.0,       0.0 ],  # Sub-section 39
            ["XCVR4, 5000 MHz, IF Spur",    "dBc",      -99.0,      -30.0           ],  # Sub-section 40
            ["XCVR4, 6500 MHz, LO/2 Spur",  "dBc",      -99.0,      -30.0           ]   # Sub-section 41
        ],

        # Section 6: Rx Paths
        # B = Bypass path, L = LNA path, currently only testing at centre of each band due to long capture time (30s per)
        # LNA path tested in first and last bands only since it is common to all paths
        [
            # Description                   Units       LL          UL          FFT Offset (dB)
            ["RX0, 525 MHz, -10 dBm, B",    "dBm",      -13.0,      -7.0,       155.0 ],    # Sub-section 1
            ["RX0, 525 MHz, -30 dBm, L",    "dBm",      -33.0,      -27.0,      176.0 ],    # Sub-section 2
            ["RX1, 800 MHz, -10 dBm, B",    "dBm",      -13.0,      -7.0,       155.5 ],    # Sub-section 3
            ["RX2, 1200 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       155.5 ],    # Sub-section 4
            ["RX3, 1800 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       155.0 ],    # Sub-section 5
            ["RX4, 2600 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       154.0 ],    # Sub-section 6
            ["RX5, 3800 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       149.5 ],    # Sub-section 7
            ["RX6, 5275 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       149.0 ],    # Sub-section 8
            ["RX7, 6850 MHz, -10 dBm, B",   "dBm",      -13.0,      -7.0,       153.5 ],    # Sub-section 9
            ["RX7, 6850 MHz, -30 dBm, L",   "dBm",      -33.0,      -27.0,      170.5 ]     # Sub-section 10
        ],

        # Section 7: Observation Rx Paths
        [
            # Description                   Units       LL          # UL        # FFT Offset (dB)
            ["Currently untested",          "n/a",      0.0,        0.0,        0.0 ]       # Sub-section 1
        ],
    ]

    def get(self, section, sub_section):
        description = self.TEST_LIMITS[section][sub_section][0]
        units       = self.TEST_LIMITS[section][sub_section][1]
        lower_limit = self.TEST_LIMITS[section][sub_section][2]
        upper_limit = self.TEST_LIMITS[section][sub_section][3]
        
        return description, units, lower_limit, upper_limit
    
    def fft_offset(self, section, sub_section):
        try:
            # Return the FFT offset value from section 6 or 7 limits
            if section == 5 or section == 6:
                return self.TEST_LIMITS[section][sub_section][4]
            else:
                return 0
        except IndexError:
            return 0
        
    def tx_att_dB(self, section, sub_section):
        try:
            # Return the Tx attenuation value from section 3 or 5 limits
            if section == 2 or section == 4:
                return self.TEST_LIMITS[section][sub_section][4]
            else:
                return 0
        except IndexError:
            return 0
    
    def section_size(self, section):
        # Return the number of tests within a given section
        return len(self.TEST_LIMITS[section])
    
if __name__ == "__main__":
    print("This module is not intended to be executed stand-alone")