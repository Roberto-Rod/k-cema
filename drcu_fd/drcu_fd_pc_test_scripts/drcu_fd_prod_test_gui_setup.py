from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['drcu_fd_prod_test_gui.py'],

    py_modules=['drcu_fd_prod_test', 'drcu_fd_program_devices', 'drcu_fd_test_jig_intf', 'drcu_micro_test_intf',
                'drcu_plat_test_intf', 'drcu_serial_msg_intf', 'rpi4_iperf3', 'serial_message_handler', 'ssh',
                'win_iperf3'],
    data_files=[('', [r'kirintec_logo.ico']),
                ('iperf-3.1.3-win64', [r'.\iperf-3.1.3-win64\iperf3.exe', r'.\iperf-3.1.3-win64\cygwin1.dll'])],
    options={
             'py2exe': {
                    'packages': ['invoke', 'decorator', 'cffi'],
                    'dist_dir': 'dist_prod_test_gui',
                    'compressed': False,
                    'includes': [],
             }
    }
)
