from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['icts_rf_board_test.py'
             ],
    py_modules=['cts_test_jig_intf', 's2p_file_reader', 'test_limits', 'test_equipment.power_supply_72_xxxx',
                'test_equipment.power_supply_cpx400dp', 'test_equipment.signal_generator_hp83752a',
                'test_equipment.signal_generator_n51x3b', 'test_equipment.spectrum_analyser_fsw',
                'test_equipment.spectrum_analyser_hp8563e', 'test_equipment.spectrum_analyser_n90xxb'
                ],
    data_files=[('images', [r'.\images\kirintec_logo.ico', r'.\images\setup_uut_rf_rx_paths.png',
                            r'.\images\setup_uut_rf_tx_paths.png', r'.\images\setup_uut_rf_no_rf_paths.png',
                            r'.\images\setup_sig_gen_to_uut_rf_ant.png', r'.\images\setup_spec_an_to_uut_rf_if.png',
                            r'.\images\setup_spec_an_to_uut_rf_ant.png']),
                ('calibration', [r'.\calibration\README.txt']),
                ],
    options={
             'py2exe': {
                    'packages': [],
                    'dist_dir': 'dist_icts_rf_board_test',
                    'compressed': False,
                    'includes': ['pyvisa.resources.resource'],
             }
    }
)
