#!/usr/bin/env python3
from ssh import *
import time


class TestTamper:
    PYTHON_PATH = "python3"
    CSM_TEST_SCRIPT_PATH = "/tmp/test/"
    EMA_TEST_SCRIPT_PATH = "/tmp/test/"
    SET_INACTIVE_TAMPER_CMD = "tamper.py -i"
    DISARM_TAMPER_CMD = "tamper.py -d"
    ARM_TAMPER_CMD = "tamper.py -a"
    GET_TAMPER_GET_STATUS = "tamper.py -s"
    CMD_FAILED = {"Error: Write failed", "Error: Read failed"}
    STATUS_RESP_NO_TAMPER = {"Channel TamperChannel.LIGHT_SENSOR is tampered: False",
                             "Channel TamperChannel.MICROSWITCH is tampered: False"}

    def __init__(self, text, csms, emas):
        self.text = text
        self.csms = csms
        self.emas = emas

    def run_test(self):
        all_ok = True

        for csm in self.csms:
            self.text.insert("Checking tamper detection ({})...".format(csm[0].rstrip(".local")))
            s = SSH(csm[1])
            all_ok = self.arm_tamper(s, self.CSM_TEST_SCRIPT_PATH)

        for ema in self.emas:
            self.text.insert("Checking tamper detection ({})...".format(ema[0].rstrip(".local")))
            s = SSH(ema[1])
            all_ok = self.arm_tamper(s, self.EMA_TEST_SCRIPT_PATH)

        if all_ok and len(self.csms) > 0 and len(self.emas) > 0:
            self.text.insert("OK")
        return all_ok

    def arm_tamper(self, ssh_conn, test_script_path):
        """
        Arm an LRUs tamper sensors and test their status is armed/not tampered
        :param ssh_conn: SSH connection to use for configuring the LRU :type: SSH
        :param: location of test scripts on the LRU :type: string
        :return: True if arming tamper sensors is successful, else False :type: boolean
        """
        all_ok = True

        cmd_str = "{} {}{}".format(self.PYTHON_PATH, test_script_path, self.SET_INACTIVE_TAMPER_CMD)
        return_str = str(ssh_conn.send_command(cmd_str).stderr).strip()
        all_ok = not self.check_str_for_error(return_str, self.CMD_FAILED) and all_ok
        if not all_ok:
            self.text.insert("ERROR: Failed to set tamper sensors to inactive state")

        cmd_str = "{} {}{}".format(self.PYTHON_PATH, test_script_path, self.ARM_TAMPER_CMD)
        return_str = str(ssh_conn.send_command(cmd_str).stderr).strip()
        all_ok = not self.check_str_for_error(return_str, self.CMD_FAILED) and all_ok
        if not all_ok:
            self.text.insert("ERROR: Failed to arm the tamper sensors")

        cmd_str = "{} {}{}".format(self.PYTHON_PATH, test_script_path, self.GET_TAMPER_GET_STATUS)
        return_str = str(ssh_conn.send_command(cmd_str).stderr).strip()
        all_ok = not self.check_str_for_error(return_str, self.CMD_FAILED) and \
                 self.check_str_for_pass(return_str, self.STATUS_RESP_NO_TAMPER) and all_ok
        if not all_ok:
            self.text.insert("ERROR: tamper flags not clear\n{}".format(return_str))

        cmd_str = "{} {}{}".format(self.PYTHON_PATH, test_script_path, self.SET_INACTIVE_TAMPER_CMD)
        return_str = str(ssh_conn.send_command(cmd_str).stderr).strip()
        all_ok = not self.check_str_for_error(return_str, self.CMD_FAILED) and all_ok
        if not all_ok:
            self.text.insert("ERROR: Failed to set tamper sensors to inactive state")

        return all_ok

    @staticmethod
    def check_str_for_error(str_to_check, strs_to_check_against):
        """
        :return: True if str_to_check matches one of the error strs_to_check_against, else False
        """
        for test_str in strs_to_check_against:
            if test_str in str_to_check:
                return True
        return False

    @staticmethod
    def check_str_for_pass(str_to_check, strs_to_check_against):
        """
        :return: True if all of strs_to_check_against are in str_to_check, else False
        """
        for test_str in strs_to_check_against:
            if test_str not in str_to_check:
                return False
        return True
