from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\.venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['csm_prod_test_gui.py'],
    py_modules=['csm_plat_test_intf', 'csm_prod_test', 'csm_program_devices', 'csm_test_jig_intf',
                'csm_zero_micro_test_intf', 'keypad_buzzer_test', 'ptp_phy_test', 'rpi4_iperf3', 'som_bring_up',
                'som_eia422_intf_test', 'ssh', 'tl_sg3428', 'win_iperf3', 'zeroise_fpga_test'],
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

