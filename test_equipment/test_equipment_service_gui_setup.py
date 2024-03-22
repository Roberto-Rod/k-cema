from distutils.core import setup
import py2exe

import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['test_equipment_service_gui.py'],
    py_modules=[ 'power_meter', 'power_meter_nrp', 'power_meter_service', 'power_supply', 'power_supply_72_xxxx', 'power_supply_cpx400dp', 'power_supply_qpx', 'power_supply_service',
                'signal_generator', 'signal_generator_hp83752a', 'signal_generator_mxg', 'signal_generator_n5173b_83b', 'signal_generator_service',
                'spectrum_analyser', 'spectrum_analyser_fsw', 'spectrum_analyser_hp8563e', 'spectrum_analyser_n9342c', 'spectrum_analyser_service', 'tenmaDcLib', 'visa_test_equipment'],
    data_files=[('', [r'kirintec_logo.ico']),
                ],
    options={
             'py2exe': {
                    'packages': ['invoke', 'decorator', 'cffi'],
                    'dist_dir': 'dist',
                    'compressed': False,
                    'includes': ['pyvisa.resources.resource'],
             }
    }
)

