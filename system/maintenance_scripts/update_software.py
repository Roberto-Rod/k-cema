#!/usr/bin/env python3
from enum import Enum
from os import walk
from os import path
from find_service import *
from ssh import *
from tkinter import *


class SoftwareType(Enum):
    CSM_BOOT = 0,
    CSM_OS = 1,
    CSM_FPGA = 2,
    CSM_APP = 3,
    CSM_TEST_SCRIPT = 4,
    CSM_PASSWORD = 5,
    CSM_SETTINGS = 6,
    CSM_RTPS = 7,
    EMA_BOOT = 8,
    EMA_OS = 9,
    EMA_TEST_SCRIPT = 10,
    EMA_LB_FPGA = 11,
    EMA_MB_HB_FPGA = 12,
    EMA_LB_APP = 13,
    EMA_MB_HB_APP = 14,
    EMA_LB_TPU = 15,
    EMA_MB_HB_TPU = 16,
    EMA_DRM_DAEMON = 17,
    EMA_RUN_FILE = 18,
    EMA_RTPS = 19,
    EMA_SETTINGS = 20,
    EMA_BOOT_ENV = 21,
    EMA_PLATFORM_SCRIPT = 22,
    EMA_SMP_FILE = 23,
    EMA_OCPI_LB = 24,
    EMA_OCPI_MBHB = 25,
    SB_APP = 26,
    SB_SETTINGS = 27,
    SB_INTERFACES = 28,
    SB_LAUNCHER = 29,
    MORA_BRIDGE = 30,
    MORA_SETTINGS = 31,
    CSM_PLATFORM_SCRIPT = 32,
    CSM_RUN_FILE = 33,
    CSM_DUMMY_MISSION = 34,
    CSM_KTK_SIGN_KEY = 35


class TargetType(Enum):
    CSM = 0,
    EMA = 1,
    EMA_LB = 2,
    EMA_MB_HB = 3


class UpdateSoftware:
    SUBDIR_NAME = {}
    SUBDIR_NAME[SoftwareType.CSM_BOOT] = "CSM/Bootloader"
    SUBDIR_NAME[SoftwareType.CSM_OS] = "CSM/OS"
    SUBDIR_NAME[SoftwareType.CSM_FPGA] = "CSM/FPGA"
    SUBDIR_NAME[SoftwareType.CSM_APP] = "CSM/Application"
    SUBDIR_NAME[SoftwareType.CSM_TEST_SCRIPT] = "CSM/Scripts/Test Scripts Archive"
    SUBDIR_NAME[SoftwareType.CSM_PLATFORM_SCRIPT] = "CSM/Scripts/Platform Scripts Archive"
    SUBDIR_NAME[SoftwareType.CSM_PASSWORD] = "CSM/Settings/Password"
    SUBDIR_NAME[SoftwareType.CSM_SETTINGS] = "CSM/Settings/Platform Settings"
    SUBDIR_NAME[SoftwareType.MORA_SETTINGS] = "CSM/Settings/MORA Settings"
    SUBDIR_NAME[SoftwareType.CSM_RUN_FILE] = "CSM/Scripts/Run File"
    SUBDIR_NAME[SoftwareType.CSM_RTPS] = "CSM/Settings/RTPS Configuration"
    SUBDIR_NAME[SoftwareType.CSM_DUMMY_MISSION] = "CSM/Dummy Mission"
    SUBDIR_NAME[SoftwareType.CSM_KTK_SIGN_KEY] = "CSM/Settings/KTK Sign Key"
    SUBDIR_NAME[SoftwareType.EMA_BOOT] = "EMA/Bootloader"
    SUBDIR_NAME[SoftwareType.EMA_OS] = "EMA/OS"
    SUBDIR_NAME[SoftwareType.EMA_TEST_SCRIPT] = "EMA/Scripts/Test Scripts Archive"
    SUBDIR_NAME[SoftwareType.EMA_PLATFORM_SCRIPT] = "EMA/Scripts/Platform Scripts Archive"
    SUBDIR_NAME[SoftwareType.EMA_LB_FPGA] = "EMA/FPGA/LB"
    SUBDIR_NAME[SoftwareType.EMA_MB_HB_FPGA] = "EMA/FPGA/MB-HB"
    SUBDIR_NAME[SoftwareType.EMA_LB_APP] = "EMA/Application/LB"
    SUBDIR_NAME[SoftwareType.EMA_MB_HB_APP] = "EMA/Application/MB-HB"
    SUBDIR_NAME[SoftwareType.EMA_LB_TPU] = "EMA/TPU/LB"
    SUBDIR_NAME[SoftwareType.EMA_MB_HB_TPU] = "EMA/TPU/MB-HB"
    SUBDIR_NAME[SoftwareType.EMA_DRM_DAEMON] = "EMA/DRM Daemon"
    SUBDIR_NAME[SoftwareType.EMA_RUN_FILE] = "EMA/Scripts/Run File"
    SUBDIR_NAME[SoftwareType.EMA_RTPS] = "EMA/Settings/RTPS Configuration"
    SUBDIR_NAME[SoftwareType.EMA_SETTINGS] = "EMA/Settings/Platform Settings"
    SUBDIR_NAME[SoftwareType.EMA_SMP_FILE] = "EMA/Settings/SMP"
    SUBDIR_NAME[SoftwareType.EMA_BOOT_ENV] = "EMA/Boot Env"
    SUBDIR_NAME[SoftwareType.EMA_OCPI_LB] = "EMA/OCPI/LB"
    SUBDIR_NAME[SoftwareType.EMA_OCPI_MBHB] = "EMA/OCPI/MBHB"
    SUBDIR_NAME[SoftwareType.SB_APP] = "SB/Application"
    SUBDIR_NAME[SoftwareType.SB_SETTINGS] = "SB/Settings/Sapient Settings"
    SUBDIR_NAME[SoftwareType.SB_INTERFACES] = "SB/Settings/Network Interfaces"
    SUBDIR_NAME[SoftwareType.SB_LAUNCHER] = "SB/Launcher"
    SUBDIR_NAME[SoftwareType.MORA_BRIDGE] = "CSM/MORA Bridge"

    TARGET_NAME = {}
    TARGET_NAME[SoftwareType.CSM_BOOT] = "/home/root/boot.bin"
    TARGET_NAME[SoftwareType.CSM_OS] = "/run/media/mmcblk1p1/image.ub"
    TARGET_NAME[SoftwareType.CSM_FPGA] = "/run/media/mmcblk1p1/system.bin"
    TARGET_NAME[SoftwareType.CSM_APP] = "/run/media/mmcblk1p1/csm_app.bin"
    TARGET_NAME[SoftwareType.CSM_TEST_SCRIPT] = "/tmp/test_scripts.tgz"
    TARGET_NAME[SoftwareType.CSM_PLATFORM_SCRIPT] = "/run/media/mmcblk1p2/script.tgz"
    TARGET_NAME[SoftwareType.CSM_PASSWORD] = "/run/media/mmcblk1p2/settings/pass.json"
    TARGET_NAME[SoftwareType.CSM_SETTINGS] = "/run/media/mmcblk1p2/settings/platform_settings.json"
    TARGET_NAME[SoftwareType.MORA_SETTINGS] = "/run/media/mmcblk1p2/settings/mora_settings.json"
    TARGET_NAME[SoftwareType.CSM_RUN_FILE] = "/run/media/mmcblk1p2/run.sh"
    TARGET_NAME[SoftwareType.CSM_RTPS] = "/run/media/mmcblk1p2/rtps.ini"
    TARGET_NAME[SoftwareType.CSM_DUMMY_MISSION] = "/run/media/mmcblk1p2/mission.iff"
    TARGET_NAME[SoftwareType.CSM_KTK_SIGN_KEY] = "/run/media/mmcblk1p2/.key/pub.key"
    TARGET_NAME[SoftwareType.EMA_BOOT] = "/home/root/boot.bin"
    TARGET_NAME[SoftwareType.EMA_OS] = "/run/media/mmcblk0p1/image.ub"
    TARGET_NAME[SoftwareType.EMA_TEST_SCRIPT] = "/tmp/test_scripts.tgz"
    TARGET_NAME[SoftwareType.EMA_PLATFORM_SCRIPT] = "/run/media/mmcblk0p2/script.tgz"
    TARGET_NAME[SoftwareType.EMA_LB_FPGA] = "/run/media/mmcblk0p1/system.bin"
    TARGET_NAME[SoftwareType.EMA_MB_HB_FPGA] = "/run/media/mmcblk0p1/system.bin"
    TARGET_NAME[SoftwareType.EMA_LB_APP] = "/run/media/mmcblk0p1/ema_app.bin"
    TARGET_NAME[SoftwareType.EMA_MB_HB_APP] = "/run/media/mmcblk0p1/ema_app.bin"
    TARGET_NAME[SoftwareType.EMA_LB_TPU] = "/run/media/mmcblk0p1/tpu.elf"
    TARGET_NAME[SoftwareType.EMA_MB_HB_TPU] = "/run/media/mmcblk0p1/tpu.elf"
    TARGET_NAME[SoftwareType.EMA_RUN_FILE] = "/run/media/mmcblk0p2/run.sh"
    TARGET_NAME[SoftwareType.EMA_RTPS] = "/run/media/mmcblk0p2/rtps.ini"
    TARGET_NAME[SoftwareType.EMA_SETTINGS] = "/run/media/mmcblk0p2/settings/platform_settings.json"
    TARGET_NAME[SoftwareType.EMA_SMP_FILE] = "/run/media/mmcblk0p2/SMP"
    TARGET_NAME[SoftwareType.EMA_BOOT_ENV] = "/tmp/ema_bootenv.bin"
    TARGET_NAME[SoftwareType.EMA_OCPI_LB] = "/run/media/mmcblk0p2/ocpi.tgz"
    TARGET_NAME[SoftwareType.EMA_OCPI_MBHB] = "/run/media/mmcblk0p2/ocpi.tgz"
    TARGET_NAME[SoftwareType.SB_APP] = "/run/media/mmcblk1p1/sb_app.bin"
    TARGET_NAME[SoftwareType.SB_SETTINGS] = "/run/media/mmcblk1p2/settings/sapient_settings.json"
    TARGET_NAME[SoftwareType.SB_INTERFACES] = "/run/media/mmcblk1p2/network/interfaces"
    TARGET_NAME[SoftwareType.SB_LAUNCHER] = "/run/media/mmcblk1p2/csm_sb_launcher.sh"
    TARGET_NAME[SoftwareType.MORA_BRIDGE] = "/run/media/mmcblk1p1/mora_brdg.bin"

    TARGET_TYPE = {}
    TARGET_TYPE[SoftwareType.CSM_BOOT] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_OS] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_TEST_SCRIPT] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_FPGA] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_APP] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_TEST_SCRIPT] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_PLATFORM_SCRIPT] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_PASSWORD] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_SETTINGS] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_RUN_FILE] = TargetType.CSM
    TARGET_TYPE[SoftwareType.MORA_SETTINGS] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_RTPS] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_DUMMY_MISSION] = TargetType.CSM
    TARGET_TYPE[SoftwareType.CSM_KTK_SIGN_KEY] = TargetType.CSM
    TARGET_TYPE[SoftwareType.EMA_BOOT] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_OS] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_TEST_SCRIPT] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_PLATFORM_SCRIPT] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_LB_FPGA] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_MB_HB_FPGA] = TargetType.EMA_MB_HB
    TARGET_TYPE[SoftwareType.EMA_LB_APP] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_MB_HB_APP] = TargetType.EMA_MB_HB
    TARGET_TYPE[SoftwareType.EMA_LB_TPU] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_MB_HB_TPU] = TargetType.EMA_MB_HB
    TARGET_TYPE[SoftwareType.EMA_DRM_DAEMON] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_RUN_FILE] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_RTPS] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_SETTINGS] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_SMP_FILE] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_BOOT_ENV] = TargetType.EMA
    TARGET_TYPE[SoftwareType.EMA_OCPI_LB] = TargetType.EMA_LB
    TARGET_TYPE[SoftwareType.EMA_OCPI_MBHB] = TargetType.EMA_MB_HB
    TARGET_TYPE[SoftwareType.SB_APP] = TargetType.CSM
    TARGET_TYPE[SoftwareType.SB_SETTINGS] = TargetType.CSM
    TARGET_TYPE[SoftwareType.SB_INTERFACES] = TargetType.CSM
    TARGET_TYPE[SoftwareType.SB_LAUNCHER] = TargetType.CSM
    TARGET_TYPE[SoftwareType.MORA_BRIDGE] = TargetType.CSM

    ZEROISE_CSM_SW_LIST = [SoftwareType.CSM_APP, SoftwareType.MORA_BRIDGE, SoftwareType.CSM_PASSWORD]
    ZEROISE_EMA_SW_LIST = [SoftwareType.EMA_LB_APP, SoftwareType.EMA_LB_TPU]

    CSM_MISSION_PATH = "/mnt/sf0/missions/{}/mission.iff"
    CSM_MISSION_FIRST = 1
    CSM_MISSION_LAST = 5

    BOOT_NODE = {TargetType.CSM: "/dev/mtd8",
                 TargetType.EMA: "/dev/mtd0",
                 TargetType.EMA_LB: "/dev/mtd0",
                 TargetType.EMA_MB_HB: "/dev/mtd0"
                 }

    ENV_NODE = {TargetType.CSM: "/dev/mtd9",
                TargetType.EMA: "/dev/mtd1",
                TargetType.EMA_LB: "/dev/mtd1",
                TargetType.EMA_MB_HB: "/dev/mtd1"
                }

    SYMLINK_CSM_APP = "/run/media/mmcblk1p2/KCemaCSMApp"
    SYMLINK_EMA_APP = "/run/media/mmcblk0p2/KCemaEMAApp"

    CLEAR_ENV_CMD = "/bin/cat /dev/zero >"
    FLASH_CMD = "/usr/sbin/flashcp -v"
    REBOOT_CMD = "/sbin/reboot"
    KILL_CMD_CSM = "/usr/bin/killall KCemaCSMApp;/usr/bin/killall csm_app.bin;/usr/bin/killall sb_app.bin;/usr/bin/killall mora_brdg.bin"
    KILL_CMD_EMA = "/usr/bin/killall KCemaEMAApp;/usr/bin/killall ema_app.bin"
    EMA_GET_ASSY_NR_CMD = "dd if=/sys/bus/i2c/devices/0-0050/eeprom bs=1 skip=0 count=14 2>/dev/null"
    ZEROISE_FILE_CMD = "shred -n 3 -z -u {}"
    EXTRACT_TEST_CMD_CSM = "cd /tmp;rm -rf test;/bin/tar -xzf {}".format(TARGET_NAME[SoftwareType.CSM_TEST_SCRIPT])
    EXTRACT_TEST_CMD_EMA = "cd /tmp;rm -rf test;/bin/tar -xzf {}".format(TARGET_NAME[SoftwareType.EMA_TEST_SCRIPT])
    EXTRACT_PLATFORM_CMD_CSM = "cd /run/media/mmcblk1p2;rm -rf script;/bin/tar -xzf {};rm {}".format(
                                TARGET_NAME[SoftwareType.CSM_PLATFORM_SCRIPT],
                                TARGET_NAME[SoftwareType.CSM_PLATFORM_SCRIPT])
    EXTRACT_PLATFORM_CMD_EMA = "cd /run/media/mmcblk0p2;rm -rf script;/bin/tar -xzf {}; rm {}".format(
                                TARGET_NAME[SoftwareType.EMA_PLATFORM_SCRIPT],
                                TARGET_NAME[SoftwareType.CSM_PLATFORM_SCRIPT])
    EXTRACT_OCPI_CMD_EMA = "cd /run/media/mmcblk0p2;rm -rf opencpi;/bin/tar -xzf {};rm {}".format(
                                TARGET_NAME[SoftwareType.EMA_OCPI_LB],
                                TARGET_NAME[SoftwareType.EMA_OCPI_LB])
    RM_SCRIPTS_CMD_CSM = "rm -rf /run/media/mmcblk1p2/test;rm -f /run/media/mmcblk1p2/*.tgz"
    RM_SCRIPTS_CMD_EMA = "rm -rf /run/media/mmcblk0p2/test;rm -f /run/media/mmcblk0p2/*.tgz"

    EMA_BL_UPDATE_COMMAND_TIMEOUT_S = 120     # 2 minutes
    CSM_BL_UPDATE_COMMAND_TIMEOUT_S = 30      # 0.5 minutes
    EMA_OCPI_EXTRACT_COMMAND_TIMEOUT_S = 120  # 2 minutes

    SYMLINK_APP_CMD_CSM = "unlink {};ln -s {} {}".format(SYMLINK_CSM_APP, TARGET_NAME[SoftwareType.CSM_APP],
                                                         SYMLINK_CSM_APP)
    SYMLINK_APP_CMD_EMA = "unlink {};ln -s {} {}".format(SYMLINK_EMA_APP, TARGET_NAME[SoftwareType.EMA_LB_APP],
                                                         SYMLINK_EMA_APP)

    ASSY_NR_TARGET_TYPE = [["KT-950-0331-00", TargetType.EMA_LB],     # LB-R
                           ["KT-950-0332-00", TargetType.EMA_MB_HB],  # MB-R
                           ["KT-950-0409-00", TargetType.EMA_MB_HB],  # HB-A
                           ["KT-950-0333-00", TargetType.EMA_MB_HB],  # HB-R
                           ["KT-950-0505-00", TargetType.EMA_MB_HB],  # EHB-R-8GHZ
                           ["KT-950-0505-01", TargetType.EMA_MB_HB]]  # EHB-R-6GHZ

    def __init__(self, dir, text):
        self.text = text
        self.dir = dir
        self.software = {SoftwareType.CSM_BOOT: None, SoftwareType.CSM_OS: None, SoftwareType.CSM_FPGA: None,
                         SoftwareType.CSM_APP: None, SoftwareType.EMA_BOOT: None, SoftwareType.EMA_OS: None,
                         SoftwareType.EMA_LB_FPGA: None, SoftwareType.EMA_MB_HB_FPGA: None,
                         SoftwareType.EMA_LB_APP: None, SoftwareType.EMA_MB_HB_APP: None}
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

    def send_type(self, sw_type, scripts_only, do_boot_flash, bootloader_only):
        is_boot = (sw_type == SoftwareType.CSM_BOOT or sw_type == SoftwareType.EMA_BOOT)
        is_scripts = (sw_type == SoftwareType.CSM_TEST_SCRIPT or sw_type == SoftwareType.EMA_TEST_SCRIPT)
        if bootloader_only:
            return is_boot
        elif scripts_only:
            return is_scripts
        elif do_boot_flash:
            return True
        else:
            return not is_boot

    def update_ema(self, emas, do_boot_flash=False, bootloader_only=False, scripts_only=False, do_reboot=True):
        ok = True
        sent_something = False
        for ema in emas:
            self.text.insert("\nSending files to: {}".format(ema[0].rstrip(".local")))
            s = SSH(ema[1])
            target_type = self.get_ema_band(s)
            final_cmd = ""
            killed_ema = False
            for sw_type, file in self.load_schedule:
                if (self.TARGET_TYPE[sw_type] == TargetType.EMA or self.TARGET_TYPE[sw_type] == target_type) and\
                        self.send_type(sw_type, scripts_only, do_boot_flash, bootloader_only):
                    # Kill EMA app if we are loading anything except for Test Scripts
                    if (sw_type != SoftwareType.EMA_TEST_SCRIPT) and not killed_ema:
                        s.send_command(self.KILL_CMD_EMA)
                        killed_ema = True
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
                    # If this is test script archive then removed old scripts and extract archive
                    if sw_type == SoftwareType.EMA_TEST_SCRIPT:
                        s.send_command(self.RM_SCRIPTS_CMD_EMA)
                        s.send_command(self.EXTRACT_TEST_CMD_EMA)
                    # If this is platform script archive then extract archive
                    if sw_type == SoftwareType.EMA_PLATFORM_SCRIPT:
                        s.send_command(self.EXTRACT_PLATFORM_CMD_EMA)
                    # If this is OCPI archive then extract it
                    if sw_type == SoftwareType.EMA_OCPI_LB or sw_type == SoftwareType.EMA_OCPI_MBHB:
                        s.send_command(self.EXTRACT_OCPI_CMD_EMA, timeout=self.EMA_OCPI_EXTRACT_COMMAND_TIMEOUT_S)
                    # If this is bootloader then prepare to reflash
                    if do_boot_flash and sw_type == SoftwareType.EMA_BOOT:
                        final_cmd = "{} {};{} {} {};".format(self.CLEAR_ENV_CMD, self.ENV_NODE[target_type],
                                                             self.FLASH_CMD, self.TARGET_NAME[sw_type],
                                                             self.BOOT_NODE[target_type])
                    if sw_type == SoftwareType.EMA_BOOT_ENV:
                        final_cmd += "{} {} {};".format(self.FLASH_CMD, self.TARGET_NAME[sw_type], self.ENV_NODE[target_type])
            # Create the application links
            s.send_command(self.SYMLINK_APP_CMD_EMA)
            # Finished updating this module, now reflash & reboot it
            # Standard command timeout if not re-flashing bootloader
            final_cmd_timeout = s.COMMAND_TIMEOUT_S
            if do_reboot and sent_something:
                final_cmd += self.REBOOT_CMD
                if do_boot_flash:
                    self.text.insert("Flashing and rebooting {}...".format(ema[0].rstrip(".local")))
                    # Extended command timeout if re-flashing bootloader
                    final_cmd_timeout = self.EMA_BL_UPDATE_COMMAND_TIMEOUT_S
                else:
                    self.text.insert("Rebooting {}...".format(ema[0].rstrip(".local")))
            if final_cmd is not None:
                print("Command: {}".format(final_cmd))
                s.send_command(final_cmd, final_cmd_timeout)
        return ok

    def update_csm(self, csms, do_boot_flash=False, bootloader_only=False, scripts_only=False, do_reboot=True):
        ok = True
        sent_something_other_than_password = False
        for csm in csms:
            self.text.insert("\nSending files to: {}".format(csm[0].rstrip(".local")))
            s = SSH(csm[1])
            final_cmd = ""
            killed_csm = False
            for sw_type, file in self.load_schedule:
                if self.TARGET_TYPE[sw_type] == TargetType.CSM and\
                        self.send_type(sw_type, scripts_only, do_boot_flash, bootloader_only):
                    # Kill CSM app if we are loading anything except for Test Scripts
                    if (sw_type != SoftwareType.CSM_TEST_SCRIPT) and not killed_csm:
                        s.send_command(self.KILL_CMD_CSM)
                        killed_csm = True
                    if sw_type != SoftwareType.CSM_PASSWORD:
                        sent_something_other_than_password = True
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
                    # If this is test script archive then removed old scripts and extract archive
                    if sw_type == SoftwareType.CSM_TEST_SCRIPT:
                        s.send_command(self.RM_SCRIPTS_CMD_CSM)
                        s.send_command(self.EXTRACT_TEST_CMD_CSM)
                    # If this is platform script archive then extract archive
                    if sw_type == SoftwareType.CSM_PLATFORM_SCRIPT:
                        s.send_command(self.EXTRACT_PLATFORM_CMD_CSM)
                    # If this is bootloader then prepare to reflash
                    if do_boot_flash and sw_type == SoftwareType.CSM_BOOT:
                        final_cmd = "{} {};{} {} {};".format(self.CLEAR_ENV_CMD, self.ENV_NODE[TargetType.CSM],
                                                             self.FLASH_CMD, self.TARGET_NAME[sw_type],
                                                             self.BOOT_NODE[TargetType.CSM])
            # Create the application links
            s.send_command(self.SYMLINK_APP_CMD_CSM)
            # Finished updating this module, now reflash & reboot it
            # Standard command timeout if not re-flashing bootloader
            final_cmd_timeout = s.COMMAND_TIMEOUT_S
            if do_reboot and sent_something_other_than_password:
                final_cmd += self.REBOOT_CMD
                if do_boot_flash:
                    self.text.insert("Flashing and rebooting {}...".format(csm[0].rstrip(".local")))
                    # Extended command timeout if re-flashing bootloader
                    final_cmd_timeout = self.CSM_BL_UPDATE_COMMAND_TIMEOUT_S
                else:
                    self.text.insert("Rebooting {}...".format(csm[0].rstrip(".local")))
            if final_cmd is not None:
                s.send_command(final_cmd, final_cmd_timeout)
        return ok

    def zeroise_csms(self, csms):
        for csm in csms:
            self.text.insert("\nZeroise {}".format(csm[0].rstrip(".local")))
            ssh = SSH(csm[1])
            ssh.send_command(self.KILL_CMD_CSM)
            self.text.insert("  Zeroise software...")
            for sw in self.ZEROISE_CSM_SW_LIST:
                file = self.TARGET_NAME[sw]
                ssh.send_command(self.ZEROISE_FILE_CMD.format(file))
            self.text.insert("  Zeroise fill...")
            for slot in range(self.CSM_MISSION_FIRST, self.CSM_MISSION_LAST+1):
                file = self.CSM_MISSION_PATH.format(slot)
                ssh.send_command(self.ZEROISE_FILE_CMD.format(file))
            self.text.insert("Rebooting {}...".format(csm[0].rstrip(".local")))
            ssh.send_command(self.REBOOT_CMD)

    def zeroise_emas(self, emas):
        for ema in emas:
            self.text.insert("\nZeroise {}".format(ema[0].rstrip(".local")))
            ssh = SSH(ema[1])
            ssh.send_command(self.KILL_CMD_EMA)
            self.text.insert("  Zeroise software...")
            for sw in self.ZEROISE_EMA_SW_LIST:
                file = self.TARGET_NAME[sw]
                ssh.send_command(self.ZEROISE_FILE_CMD.format(file))
            self.text.insert("Rebooting {}...".format(ema[0].rstrip(".local")))
            ssh.send_command(self.REBOOT_CMD)

    def get_ema_band(self, ssh):
        self.text.insert("Get EMA band...")
        target_type = None
        for i in range(10):
            try:
                resp = ssh.send_command(self.EMA_GET_ASSY_NR_CMD)
                for entry in self.ASSY_NR_TARGET_TYPE:
                    if entry[0] == resp.stdout:
                        target_type = entry[1]
                        break
            except Exception as e:
                self.text.insert(e)
            if target_type:
                break
        if target_type is None:
            self.text.insert("WARNING: could not get EMA band, defaulting to Low-Band")
            target_type = TargetType.EMA_LB
        self.text.insert("{}".format(target_type))
        return target_type


if __name__ == "__main__":
    print("This script is not intended to be run stand-alone.")
