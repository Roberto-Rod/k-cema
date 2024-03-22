from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['cts_prod_test_gui.py'],

    py_modules=['cts_micro_test_intf', 'cts_prod_test', 'cts_program_devices', 'cts_test_jig_intf',
                ],
    data_files=[('', [r'kirintec_logo.ico']),
                ],
    options={
             'py2exe': {
                    'packages': ['invoke', 'decorator', 'cffi'],
                    'dist_dir': 'dist_prod_test_gui',
                    'compressed': False,
                    'includes': ['pyvisa.resources.resource'],
             }
    }
)
