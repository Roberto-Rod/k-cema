from distutils.core import setup
import py2exe

setup(
    windows=["k-cema_fleet_tool.py"],
    py_modules=["kcema_system", "ssh", "text_update"]
)

