pyinstaller ^
--noconfirm ^
--noconsole ^
--onedir ^
--specpath="./build/" ^
--icon="../images/kirintec_logo.ico" ^
--name="iCTS RF Board Test Utility" ^
--add-data="../calibration/;./calibration/" ^
--add-data="../images/;./images/" ^
--add-data="../test_equipment/;./test_equipment/" ^
--add-data="../test_reports/;./test_reports/" ^
icts_rf_board_test.py
pause