from distutils.core import setup
import py2exe
import sys
import os

sys.path.append(r'{}\venv\Lib\site-packages'.format(os.path.dirname(__file__)))

setup(
    windows=['bootblocker_config_gui.py'],
    py_modules=['bootblocker_config'],
    data_files=[('', [r'kirintec_logo.ico'])],
    options={
             'py2exe': {
                    'packages': [],
                    'dist_dir': 'dist_bootblocker_config_gui',
                    'compressed': False,
                    'includes': [],
             }
    }
)
