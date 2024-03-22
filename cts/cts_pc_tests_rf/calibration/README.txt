This folder must contain three "Touchstone" (.s2p) files in it for the calibrated path(s) between UUT and RF Signal Generator and
the calibrated path(s) between UUT and RF Spectrum Analyser. The calibration files must cover a minimum frequency range of
20-12600 MHz.

The three files must be named:

signal_generator_to_uut_rf_board_ant.s2p
spectrum_analyser_to_uut_rf_board_ant.s2p
spectrum_analyser_to_uut_rf_board_if.S2P

These files must be in "DB" or "MA" format.

Use the "CALIBRATE SET-UP" button in the test GUI in conjunction with a VNA to produce the calibration files. 