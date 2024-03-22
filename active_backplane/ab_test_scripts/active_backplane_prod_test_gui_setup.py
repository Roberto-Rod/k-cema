from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['active_backplane_prod_test_gui.py'],
    py_modules=['ab_program_devices', 'ab_serial_msg_intf', 'ab_test_jig_intf', 'active_backplane_prod_test',
                'gbe_switch', 'mac_address', 'rpi4_iperf3', 'serial_message_handler', 'ssh', 'tl_sg3428', 'win_iperf3'],
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
