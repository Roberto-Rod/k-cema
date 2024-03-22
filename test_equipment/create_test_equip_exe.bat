@echo off
REM Changing to the test_equipment directory
cd C:\workspace\k-cema\hw-test\test_equipment\

REM Create executable
echo "Creating Test Equipment Executable. Please wait..."
python test_equipment_service_gui_setup.py py2exe


