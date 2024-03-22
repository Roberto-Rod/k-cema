from distutils.core import setup
import py2exe

setup(
    windows=['bb_test_gui.py'],
    py_modules=['bb_serial_msg_intf', 'serial_message_handler'],
    data_files=[('', [r'kirintec_logo.ico'])],
    options={
             'py2exe': {
                    'packages': [],
                    'dist_dir': 'dist_test_gui',
                    'compressed': False,
                    'includes': [],
             }
    }
)
