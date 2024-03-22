from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['cts_scan_task_gui.py'],

    py_modules=['cts_serial_msg_intf', 'serial_message_handler'
                ],
    data_files=[('', [r'kirintec_logo.ico']),
                ],
    options={
             'py2exe': {
                    'packages': ['invoke', 'decorator', 'cffi'],
                    'dist_dir': 'dist_scan_task_gui',
                    'compressed': False,
                    'includes': [],
             }
    }
)
