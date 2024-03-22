#!/usr/bin/env python3
from enum import Enum
from os import walk
from os import path
from ssh import *
from tkinter import *


class Action(Enum):
    RECOVER_SOFTWARE = 0,
    UPLOAD_MISSION = 1,
    ZEROISE_SYSTEMS = 2,
    REBOOT_SYSTEMS = 3


class SoftwareType(Enum):
    CSM_APP = 0,
    EMA_LB_APP = 2,
    EMA_MB_HB_APP = 3,
    EMA_LB_TPU = 4,
    EMA_MB_HB_TPU = 5


class TargetType(Enum):
    CSM = 0,
    EMA = 1,
    EMA_LB = 2,
    EMA_MB_HB = 3


class RecoverSoftware:
    SUBDIR_NAME = {}
    SUBDIR_NAME[SoftwareType.CSM_APP] = "CSM/Application"
    SUBDIR_NAME[SoftwareType.EMA_LB_APP] = "EMA/Application/LB"
    SUBDIR_NAME[SoftwareType.EMA_MB_HB_APP] = "EMA/Application/MB-HB"
    SUBDIR_NAME[SoftwareType.EMA_LB_TPU] = "EMA/TPU/LB"
    SUBDIR_NAME[SoftwareType.EMA_MB_HB_TPU] = "EMA/TPU/MB-HB"

    TARGET_NAME = {}
    TARGET_NAME[SoftwareType.CSM_APP] = "/run/media/mmcblk1p1/csm_app.bin"
    TARGET_NAME[SoftwareType.EMA_LB_APP] = "/run/media/mmcblk0p1/ema_app.bin"
    TARGET_NAME[SoftwareType.EMA_MB_HB_APP] = "/run/media/mmcblk0p1/ema_app.bin"
    TARGET_NAME[SoftwareType.EMA_LB_TPU] = "/run/media/mmcblk0p1/tpu.elf"
    TARGET_NAME[SoftwareType.EMA_MB_HB_TPU] = "/run/media/mmcblk0p1/tpu.elf"

    TARGET_TYPE = {}
    TARGET_TYPE[SoftwareType.CSM_APP] = TargetType.CSM
    TARGET_TYPE[SoftwareType.EMA_LB_APP] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_MB_HB_APP] = TargetType.EMA_MB_HB
    TARGET_TYPE[SoftwareType.EMA_LB_TPU] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_MB_HB_TPU] = TargetType.EMA_MB_HB

    ZEROISE_CSM_SW_LIST = [SoftwareType.CSM_APP]
    ZEROISE_EMA_SW_LIST = [SoftwareType.EMA_LB_APP, SoftwareType.EMA_LB_TPU]

    #CSM_MISSION_PATH = "/mnt/sf0/missions/{}/mission.iff"
    CSM_MISSION_PATH = "/run/media/mmcblk1p2/missions/{}/mission.iff"
    CSM_MISSION_FIRST = 1
    CSM_MISSION_LAST = 5

    SYMLINK_CSM_APP = "/run/media/mmcblk1p2/KCemaCSMApp"
    SYMLINK_EMA_APP = "/run/media/mmcblk0p2/KCemaEMAApp"

    REBOOT_CMD = "/sbin/reboot"
    KILL_CMD_CSM = "/usr/bin/killall KCemaCSMApp;/usr/bin/killall csm_app.bin;/usr/bin/killall sb_app.bin"
    KILL_CMD_EMA = "/usr/bin/killall KCemaEMAApp;/usr/bin/killall ema_app.bin"
    EMA_GET_ASSY_NR_CMD = "dd if=/sys/bus/i2c/devices/0-0050/eeprom bs=1 skip=0 count=14 2>/dev/null"
    ZEROISE_FILE_CMD = "shred -n 3 -z -u {}"

    SYMLINK_APP_CMD_CSM = "unlink {};ln -s {} {}".format(SYMLINK_CSM_APP, TARGET_NAME[SoftwareType.CSM_APP],
                                                         SYMLINK_CSM_APP)
    SYMLINK_APP_CMD_EMA = "unlink {};ln -s {} {}".format(SYMLINK_EMA_APP, TARGET_NAME[SoftwareType.EMA_LB_APP],
                                                         SYMLINK_EMA_APP)

    ASSY_NR_TARGET_TYPE = [["KT-950-0331-00", TargetType.EMA_LB],     # LB-R
                           ["KT-950-0332-00", TargetType.EMA_MB_HB],  # MB-R
                           ["KT-950-0409-00", TargetType.EMA_MB_HB],  # HB-A
                           ["KT-950-0333-00", TargetType.EMA_MB_HB]]  # HB-R

    def __init__(self, root_app, text, dir=""):
        self.root_app = root_app
        self.text = text
        self.dir = dir
        self.load_schedule = []
        if dir is not None:
            self.find_binaries()

    def find_binaries(self):
        for (dirpath, dirnames, filenames) in walk(self.dir):
            try:
                filenames.remove(".gitignore")
            except ValueError:
                pass
            dir = dirpath.replace("\\", "/").replace(self.dir + "/", "")
            for sw_type, name in self.SUBDIR_NAME.items():
                if name == dir:
                    if len(filenames) > 1:
                        self.text.insert("ERROR: more than one file in {}".format(dir))
                    elif len(filenames) == 1:
                        self.load_schedule.append([sw_type, self.dir + "/" + dir + "/" + filenames[0]])

    def print_load_schedule(self):
        for item in self.load_schedule:
            self.text.insert("{}: {}".format(item[0], item[1]))

    def upload_mission(self, csms, emas, mission_file):
        for csm in csms:
            if csm.hostname:
                name = csm.hostname
            else:
                name = "CSM @ {}".format(csm.ip_address)
            self.text.insert("Uploading mission to: {}".format(name))
            s = SSH(csm.ip_address)
            s.send_file(mission_file, self.CSM_MISSION_PATH.format("1"))
            self.text.insert("Rebooting {}".format(name))
            s.send_command(self.REBOOT_CMD)
        for ema in emas:
            if ema.hostname:
                name = ema.hostname
            else:
                name = "EMA @ {}".format(ema.ip_address)
            s = SSH(ema.ip_address)
            s.send_command(self.REBOOT_CMD)
            self.text.insert("Rebooting {}".format(name))

    def update_csm(self, csms, do_reboot=True):
        ok = True
        sent_something = False
        for csm in csms:
            if csm.hostname:
                name = csm.hostname
            else:
                name = "CSM @ {}".format(csm.ip_address)
            self.text.insert("Sending files to: {}".format(name))
            s = SSH(csm.ip_address)
            s.send_command(self.KILL_CMD_CSM)
            print(self.KILL_CMD_CSM)
            final_cmd = ""
            for sw_type, file in self.load_schedule:
                if self.TARGET_TYPE[sw_type] == TargetType.CSM:
                    sent_something = True
                    self.text.insert("  {} -> {}".format(file, self.TARGET_NAME[sw_type]))
                    # Make the target directory if it does not exist
                    target_dir = path.dirname(self.TARGET_NAME[sw_type])
                    s.send_command("mkdir -p {}".format(target_dir))
                    if sw_type == SoftwareType.CSM_APP:
                        # Unlink in case there is a symlink using the filename we want to use
                        s.send_command("unlink {}".format(self.TARGET_NAME[sw_type]))
                    # Send the file
                    s.send_file(file, self.TARGET_NAME[sw_type])
                    # Change file mode to 755 (rwxr-xr-x). This only works on an ext4 partition but send it anyway,
                    # does no harm on a FAT partition.
                    s.send_command("chmod 755 {}".format(self.TARGET_NAME[sw_type]))
            # Create the application links
            s.send_command(self.SYMLINK_APP_CMD_CSM)
            # Finished updating this module, now reboot it
            if do_reboot and sent_something:
                final_cmd += self.REBOOT_CMD
                self.text.insert("Rebooting {}...".format(name))
                self.root_app.mutex.acquire()
                csm.state = "Rebooting"
                self.root_app.mutex.release()
            if final_cmd is not None:
                s.send_command(final_cmd)
        return ok

    def update_ema(self, emas, do_reboot=True):
        ok = True
        sent_something = False
        for ema in emas:
            if ema.hostname:
                name = ema.hostname
            else:
                name = "EMA @ {}".format(ema.ip_address)
            self.text.insert("Sending files to: {}".format(name))
            s = SSH(ema.ip_address)
            s.send_command(self.KILL_CMD_EMA)
            target_type = self.get_ema_band(s)
            final_cmd = ""
            for sw_type, file in self.load_schedule:
                if self.TARGET_TYPE[sw_type] == TargetType.EMA or self.TARGET_TYPE[sw_type] == target_type:
                    sent_something = True
                    self.text.insert("  {} -> {}".format(file, self.TARGET_NAME[sw_type]))
                    # Make the target directory if it does not exist
                    target_dir = path.dirname(self.TARGET_NAME[sw_type])
                    s.send_command("mkdir -p {}".format(target_dir))
                    if sw_type == SoftwareType.EMA_LB_APP or sw_type == SoftwareType.EMA_MB_HB_APP:
                        # Unlink in case there is a symlink using the filename we want to use
                        s.send_command("unlink {}".format(self.TARGET_NAME[sw_type]))
                    # Send the file
                    s.send_file(file, self.TARGET_NAME[sw_type])
                    # Change file mode to 755 (rwxr-xr-x). This only works on an ext4 partition but send it anyway,
                    # does no harm on a FAT partition.
                    s.send_command("chmod 755 {}".format(self.TARGET_NAME[sw_type]))
            # Create the application links
            s.send_command(self.SYMLINK_APP_CMD_EMA)
            # Finished updating this module, now reboot it
            if do_reboot and sent_something:
                final_cmd += self.REBOOT_CMD
                self.text.insert("Rebooting {}...".format(name))
                self.root_app.mutex.acquire()
                ema.state = "Rebooting"
                self.root_app.mutex.release()
            if final_cmd is not None:
                s.send_command(final_cmd)
        return ok

    def zeroise_csms(self, csms):
        for csm in csms:
            if csm.hostname:
                name = csm.hostname
            else:
                name = "CSM @ {}".format(csm.ip_address)
            self.text.insert("Zeroising {}...".format(name))
            self.root_app.mutex.acquire()
            csm.state = "Zeroising"
            self.root_app.mutex.release()
            ssh = SSH(csm.ip_address)
            # Stop CSM app
            resp = ssh.send_command(RecoverSoftware.KILL_CMD_CSM)
            # Zeroise CSM software
            for sw in RecoverSoftware.ZEROISE_CSM_SW_LIST:
                file = RecoverSoftware.TARGET_NAME[sw]
                ssh.send_command(RecoverSoftware.ZEROISE_FILE_CMD.format(file))
            # Zeroise fill
            for slot in range(RecoverSoftware.CSM_MISSION_FIRST, RecoverSoftware.CSM_MISSION_LAST + 1):
                file = RecoverSoftware.CSM_MISSION_PATH.format(slot)
                ssh.send_command(RecoverSoftware.ZEROISE_FILE_CMD.format(file))
            # Remove command/status files
            ssh.send_command("/bin/rm {}".format(self.root_app.JAM_REQUEST_FILE))
            ssh.send_command("/bin/rm {}".format(self.root_app.JAM_ACTIVE_FILE))
            ssh.send_command("/bin/rm {}".format(self.root_app.FAULT_FLAG_FILE))
            # Reboot CSM
            self.text.insert("Rebooting {}...".format(name))
            self.root_app.mutex.acquire()
            csm.state = "Rebooting"
            self.root_app.mutex.release()
            ssh.send_command(RecoverSoftware.REBOOT_CMD)

    def zeroise_emas(self, emas):
        for ema in emas:
            if ema.hostname:
                name = ema.hostname
            else:
                name = "EMA @ {}".format(ema.ip_address)
            self.text.insert("Zeroising {}...".format(name))
            self.root_app.mutex.acquire()
            ema.state = "Zeroising"
            self.root_app.mutex.release()
            ssh = SSH(ema.ip_address)
            # Stop EMA app
            resp = ssh.send_command(RecoverSoftware.KILL_CMD_EMA)
            # Zeroise EMA software
            for sw in RecoverSoftware.ZEROISE_EMA_SW_LIST:
                file = RecoverSoftware.TARGET_NAME[sw]
                ssh.send_command(RecoverSoftware.ZEROISE_FILE_CMD.format(file))
            # Reboot EMA
            self.text.insert("Rebooting {}...".format(name))
            self.root_app.mutex.acquire()
            ema.state = "Rebooting"
            self.root_app.mutex.release()
            ssh.send_command(RecoverSoftware.REBOOT_CMD)

    def reboot_csms(self, csms):
        for csm in csms:
            if csm.hostname:
                name = csm.hostname
            else:
                name = "CSM @ {}".format(csm.ip_address)
            self.text.insert("Rebooting {}...".format(name))
            self.root_app.mutex.acquire()
            csm.state = "Rebooting"
            self.root_app.mutex.release()
            ssh = SSH(csm.ip_address)
            # Send reboot commands
            ssh.send_command(RecoverSoftware.REBOOT_CMD)

    def reboot_emas(self, emas):
        for ema in emas:
            if ema.hostname:
                name = ema.hostname
            else:
                name = "EMA @ {}".format(ema.ip_address)
            self.text.insert("Rebooting {}...".format(name))
            self.root_app.mutex.acquire()
            ema.state = "Rebooting"
            self.root_app.mutex.release()
            ssh = SSH(ema.ip_address)
            # Send reboot commands
            ssh.send_command(RecoverSoftware.REBOOT_CMD)

    def get_ema_band(self, ssh):
        self.text.insert("Get EMA band...")
        target_type = None
        resp = ssh.send_command(self.EMA_GET_ASSY_NR_CMD).stdout
        for entry in self.ASSY_NR_TARGET_TYPE:
            if entry[0] == resp:
                target_type = entry[1]
        if target_type is None:
            self.text.insert("ERROR: could not get EMA band")
        else:
            self.text.insert("{}".format(target_type))
        return target_type


if __name__ == "__main__":
    print("This script is not intended to be run stand-alone.")
