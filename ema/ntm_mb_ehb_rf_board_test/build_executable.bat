pyinstaller ^
--noconfirm ^
--onedir ^
--specpath="./build/" ^
--icon="../images/kirintec_logo.ico" ^
--name="NTM MB-eHB RF Board Test Utility" ^
--add-data="../calibration/;./calibration/" ^
--add-data="../images/;./images/" ^
--add-data="../plots/;./plots/" ^
--add-data="../test_equipment/;./test_equipment/" ^
--add-data="../test_reports/;./test_reports/" ^
--add-data="../ocpi_iq_capture.ipynb;." ^
--add-data="../ocpi_iq_transmit.ipynb;." ^
ntm_mb_ehb_rf_board_test.py
pause