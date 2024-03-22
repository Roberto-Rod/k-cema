#!/usr/bin/env python3
"""
This file contains utility functions to program/erase the CSM Zeroise
microcontroller using a Segger J-Link and the GbE Switch SPI Flash device
using an ASIX PRESTO programmer.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2022, Kirintec
#
# -----------------------------------------------------------------------------
"""
OPTIONS ------------------------------------------------------------------
None

ARGUMENTS -------------------------------------------------------------
None
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# stdlib imports -------------------------------------------------------
import logging
import os
import platform
import time

# Third-party imports -----------------------------------------------
from serial import Serial

# Our own imports ---------------------------------------------------
from csm_test_jig_intf import CsmTestJigInterface, CsmTestJigGpoSignals

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

JLINK_SCRIPT_PROGRAM_DEVICE = "device STM32L071CZ\nsi SWD\nspeed auto\nr\nh\nloadfile \"{}\",0\nr\ng\nexit\n"
JLINK_SCRIPT_ERASE_DEVICE = "device STM32L071CZ\nsi SWD\nspeed auto\nr\nh\nerase\nexit\n"
JLINK_SCRIPT_FILENAME = "command.jlink"
JLINK_PATH_WIN32 = "C:\\Program Files (x86)\\SEGGER\\JLink\\JLink.exe"
JLINK_PATH_WIN64 = "C:\\Program Files\\SEGGER\\JLink\\JLink.exe"
JLINK_PROGRAM_CMD = "\"{}\" -CommandFile \"{}\" -ExitOnError 1 -NoGui 1 -Log j-link_log.txt"

ASIX_UP_PATH_WIN32 = "C:\\Program Files (x86)\\ASIX\\UP\\up.exe"
ASIX_UP_PATH_WIN64 = "C:\\Program Files\\ASIX\\UP\\up.exe"
ASIX_UP_PROGRAM_CMD = "\"{}\" /part MX25L2006E /q1 /p \"{}\""
ASIX_UP_ERASE_CMD = "\"{}\" /part MX25L2006E /q1 /erase"

FLASHPRO_SCRIPT_PROGRAM_DEVICE = \
    "create_job_project \\\n-job_project_location {{{}}} \\\n\t-job_file {{{}}} \\\n\t-overwrite 1\n" \
    "set_programming_action -name {{M2GL025}} -action {{PROGRAM}}\n" \
    "run_selected_actions -prog_spi_flash 0 -disable_prog_design 0\n" \
    "set_programming_action -name {{M2GL025}} -action {{VERIFY}}\n" \
    "run_selected_actions -prog_spi_flash 0 -disable_prog_design 0\n"
FLASHPRO_SCRIPT_ERASE_DEVICE = \
    "create_job_project \\\n-job_project_location {{{}}} \\\n\t-job_file {{{}}} \\\n\t-overwrite 1\n" \
    "set_programming_action -name {{M2GL025}} -action {{ERASE}}\n" \
    "run_selected_actions -prog_spi_flash 0 -disable_prog_design 0\n"
FLASHPRO_SCRIPT_FILENAME = "command.tcl"
FLASHPRO_PATH_WIN32 = "C:\\Microsemi\\Libero_SoC_v12.4\\Designer\\bin\\FPExpress.exe"
FLASHPRO_CMD = "\"{}\" script:{} logfile:flashpro_log.txt"

# -----------------------------------------------------------------------------
# LOCAL UTILITIES
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def program_micro_device(bin_file_path):
    """
    Uses Segger J-Link to program the STM32L071CZ Zeroise microcontroller using the specified file.
    A temporary J-Link script file is created for performing the programming operation, this file
    is removed once the programming operation is complete.
    :param bin_file_path: path of binary file that will be programmed into the microcontroller :type: string
    :return: True if the device is successfully programmed, else False
    """
    if not os.path.isfile(bin_file_path):
        raise RuntimeError("Invalid binary file path!")

    # Create a J-Link script file for device programming
    with open(JLINK_SCRIPT_FILENAME, 'w') as f:
        f.write(JLINK_SCRIPT_PROGRAM_DEVICE.format(bin_file_path))

    # Execute command to program device
    cmd_prompt = os.popen(JLINK_PROGRAM_CMD.format(get_jlink_exe_path_win(), JLINK_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the J-Link script file
    if os.path.isfile(JLINK_SCRIPT_FILENAME):
        os.remove(JLINK_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


def erase_micro_device():
    """
    Uses Segger J-Link to erase the TM4C1294NCPDT microcontroller.  A temporary J-Link script file is
    created for performing the erase operation, this file is removed once the erase operation is complete.
    :return: True if the device is successfully erased, else False
    """
    # Create a J-Link script file for device programming
    with open(JLINK_SCRIPT_FILENAME, 'w') as f:
        f.write(JLINK_SCRIPT_ERASE_DEVICE)

    # Execute command to program device
    cmd_prompt = os.popen(JLINK_PROGRAM_CMD.format(get_jlink_exe_path_win(), JLINK_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the J-Link script file
    if os.path.isfile(JLINK_SCRIPT_FILENAME):
        os.remove(JLINK_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


def get_jlink_exe_path_win():
    """
    Checks for Segger J-Link executable in standard 32/64-bit installation folders on Windows OS
    :return: jlink.exe path as string, None if not found
    """
    if platform.system().lower() == "windows":
        if os.path.isfile(JLINK_PATH_WIN64):
            return JLINK_PATH_WIN64
        elif os.path.isfile(JLINK_PATH_WIN32):
            return JLINK_PATH_WIN32
        else:
            raise RuntimeError("Segger J-Link executable not found!")
    else:
        raise RuntimeError("Unsupported platform!")


def program_gbe_sw_spi_flash(bin_file_path):
    """
    Uses the ASIX PRESTO programmer via UP software to program the GbE Switch Macronix MX25V2033FM1I
    SPI Flash device with the specified file.
    :param bin_file_path: path of binary file that will be programmed into the SPI Flash device :type: string
    :return: True if the device is successfully programmed, else False
    """
    if not os.path.isfile(bin_file_path):
        raise RuntimeError("Invalid binary file path!")

    # Execute command to program device
    cmd_prompt = os.popen(ASIX_UP_PROGRAM_CMD.format(get_asix_up_exe_path_win(), bin_file_path))
    log.debug(cmd_prompt.read())

    return True if cmd_prompt.close() is None else False


def program_som(csm_username, csm_password, test_jig_com_port, csm_master_com_port,
                test_jig_intf=None, som_sd_boot_en_signal=None):
    """
    Program the SoM.
    Prerequisites:
    - boot.bin, system.bin and image.ub files on SoM SD Card installed on board under test
    - Bench PSU turned on and board powered off
    Uses:
    - Test jig STM32 serial interface
    - CSM Master serial port connected to Linux terminal
    :return: True if device programmed, else False
    """
    with CsmTestJigInterface(test_jig_com_port) if test_jig_intf is None else test_jig_intf as ctji:
        # Set the SoM to SD Card boot mode
        som_sd_boot_en_signal = CsmTestJigGpoSignals.SOM_SD_BOOT_ENABLE if som_sd_boot_en_signal is None else \
            som_sd_boot_en_signal
        ret_val = ctji.assert_gpo_signal(som_sd_boot_en_signal, True)

        # Turn on the board/unit under test
        ret_val = ctji.toggle_rcu_power_button(hard_power_off=False) and ret_val

        with Serial(csm_master_com_port, 115200, timeout=3.0, xonxoff=False, rtscts=False, dsrdtr=False) as cmsp:
            while True:
                # Interrupt auto-boot to set SD Card boot environment
                # Allow 10 x 3-second timeout, 30-seconds to hit prompt
                at_stop_autoboot_prompt = False
                console_str = b""
                for _ in range(0, 10):
                    console_str += cmsp.read_until(b"Hit any key to stop autoboot:")
                    if b"Hit any key to stop autoboot:" in console_str:
                        cmsp.write(b'q\r')
                        cmsp.read_until(b"K-CEMA-CSM> ")
                        at_stop_autoboot_prompt = True
                        break
                log.debug("{}".format(console_str))

                if not at_stop_autoboot_prompt:
                    ret_val = False
                    log.info("INFO - Failed to stop Linux auto-boot!")
                    break
                else:
                    log.info("INFO - Interrupted Linux auto-boot")

                # Set for SD Card boot
                sd_boot_env_cmds = [
                    b"env default -a\r",
                    b"saveenv\r",
                    b"fatload mmc 0 0x10000000 system.bin\r",
                    b"fpga load 0 0x10000000 4045564\r",
                    b"boot\r"
                ]

                for cmd in sd_boot_env_cmds:
                    cmsp.write(cmd)
                    console_str = cmsp.read_until(b"K-CEMA-CSM> ")
                    log.debug(console_str)
                    time.sleep(1.0)

                log.info("INFO - Booting from SD Card")

                # Allow 30 x 3-second timeout, 90-seconds for boot
                at_login_prompt = False
                console_str = b""
                log.info("INFO - Waiting for Linux login prompt (60-seconds approx)")
                for _ in range(0, 30):
                    console_str += cmsp.read_until(b" login: ")
                    if b" login: " in console_str:
                        at_login_prompt = True
                        break
                log.debug("{}".format(console_str))

                if not at_login_prompt:
                    ret_val = False
                    log.info("INFO - Failed to find Linux login prompt!")
                    break

                # Login
                time.sleep(1.0)
                cmsp.write("{}\r".format(csm_username).encode("UTF-8"))
                cmsp.read_until(b"Password:")
                cmsp.write("{}\r".format(csm_password).encode("UTF-8"))

                at_cmd_prompt = False
                console_str = b""
                for _ in range(0, 3):
                    console_str += cmsp.read_until(b":~#")
                    if b":~#" not in console_str:
                        cmsp.write(b"\r")
                    else:
                        at_cmd_prompt = True
                        break
                log.debug(console_str)

                if not at_cmd_prompt:
                    ret_val = False
                    log.info("INFO - Linux login failed!")
                    break

                log.info("INFO - Logged into Linux")

                # Flash boot.bin without BootBlocker
                cmsp.write(b"\rflashcp -v /run/media/mmcblk0p1/boot.bin /dev/mtd8\r")
                console_str = b""
                for _ in range(0, 10):
                    console_str += cmsp.read_until(b":~#")
                log.debug("{}".format(console_str))

                program_success = False
                for a_line in console_str.splitlines():
                    if b"Verifying data: " in a_line and b"(100%)" in a_line:
                        program_success = True
                        break

                if not program_success:
                    ret_val = False
                    log.info("INFO - Failed to perform boot.bin flashcp command!")
                    break
                else:
                    log.info("INFO - Successful boot.bin flashcp command")

                # fdisk partition tables, format eMMC and copy system images
                fdisk_format_emmc_copy_sys_images_cmds = [
                    # fdisk eMMC partition tables
                    (b"\rumount /dev/mmcblk1p1\r", b":~#"),
                    (b"\rumount /dev/mmcblk1p2\r", b":~#"),
                    (b"\rfdisk /dev/mmcblk1\r", b"Command (m for help): "),
                    (b"d\r", b": "), (b"\r", b": "),
                    (b"d\r", b": "), (b"\r", b": "),
                    # Partition 1
                    (b"n\r", b": "), (b"p\r", b": "), (b"1\r", b": "), (b"\r", b": "), (b"+128M\r", b": "),
                    (b"y\r", b": "),
                    # Partition 2
                    (b"n\r", b": "), (b"p\r", b": "), (b"2\r", b": "), (b"\r", b": "), (b"\r", b": "), (b"y\r", b": "),
                    # Write partitions
                    (b"w\r", b":~#"),
                    (b"partprobe /dev/mmcblk1\r", b":~#"),
                    # Format partitions
                    (b"mkfs.vfat /dev/mmcblk1p1\r", b":~#"),
                    (b"mkfs.ext4 /dev/mmcblk1p2\r", b":~#"),
                    # Copy System images
                    (b"mount /dev/mmcblk1p1 /tmp\r", b":~#"),
                    (b"cp /run/media/mmcblk0p1/system.bin /tmp/system.bin\r", b":~#"),
                    (b"cp /run/media/mmcblk0p1/image.ub /tmp/image.ub\r", b":~#"),
                    (b"umount /tmp\r", b":~#")
                ]

                for cmd, resp in fdisk_format_emmc_copy_sys_images_cmds:
                    cmsp.write(cmd)
                    console_str = cmsp.read_until(resp)
                    log.debug(console_str)
                    time.sleep(1.0)

                log.info("INFO - Formatted eMMC device and copied System images")

                copy_plat_test_scripts_cmds = [
                    # (command, response)
                    (b"mount /dev/mmcblk1p2 /tmp\r", b":~#"),
                    (b"cd /tmp\r", b":/tmp#"),
                    (b"cp /run/media/mmcblk0p1/csm_p2.tgz csm_p2.tgz\r", b":/tmp#"),
                    (b"tar -xvzf csm_p2.tgz\r", b":/tmp#"),
                    (b"rm -f csm_p2.tgz\r", b":/tmp#"),
                    (b"cd ~\r", b":~#"),
                    (b"umount /tmp\r", b":~#")
                ]

                for cmd, resp in copy_plat_test_scripts_cmds:
                    cmsp.write(cmd)
                    console_str = cmsp.read_until(resp)
                    log.debug(console_str)
                    time.sleep(1.0)

                log.info("INFO - Copied Platform Test Scripts to eMMC")

                # Clear SoM SD Card boot mode
                ret_val = ctji.assert_gpo_signal(som_sd_boot_en_signal, False) and ret_val

                # Reboot from eMMC
                cmsp.write(b"reboot -f\r")

                # Interrupt auto-boot to set eMMC boot environment
                # Allow 10 x 3-second timeout, 30-seconds to hit prompt
                at_stop_autoboot_prompt = False
                console_str = b""
                for _ in range(0, 10):
                    console_str += cmsp.read_until(b"Hit any key to stop autoboot:")
                    log.debug("{}: {}".format(_, console_str))
                    if b"Hit any key to stop autoboot:" in console_str:
                        cmsp.write(b'q\r')
                        cmsp.read_until(b"K-CEMA-CSM> ")
                        at_stop_autoboot_prompt = True
                        break
                log.debug(console_str)

                if not at_stop_autoboot_prompt:
                    ret_val = False
                    log.info("INFO - Failed to stop Linux auto-boot!")
                    break
                else:
                    log.info("INFO - Interrupted Linux auto-boot")

                # Set environment variables for normal operation
                normal_operation_env_cmds = [
                    b"env default -a\r",
                    b"setenv autoload 'no'\r",
                    b"setenv sdbootdev 1\r",
                    b"setenv fpga_img 'system.bin'\r",
                    b"setenv fpga_size '0x3dbafc'\r",
                    b"setenv fpga_load 'fpga load 0 ${loadaddr} ${fpga_size}'\r",
                    b"setenv fpga_tftp 'tftpboot ${loadaddr} system.bin'\r",
                    b"setenv fpga_mmc_boot 'run cp_fpga2ram; run fpga_load'\r",
                    b"setenv cp_fpga2ram 'mmcinfo && fatload mmc ${sdbootdev} ${loadaddr} ${fpga_img}'\r",
                    b"setenv default_bootcmd 'run uenvboot; mmc dev 1; run fpga_mmc_boot; "
                    b"run cp_kernel2ram && bootm ${netstart}'\r",
                    b"saveenv\r"
                ]
                for cmd in normal_operation_env_cmds:
                    cmsp.write(cmd)
                    console_str = cmsp.read_until(b"K-CEMA-CSM> ")
                    log.debug(console_str)
                    time.sleep(1.0)

                # Reset and boot into Linux
                cmsp.write(b"reset\r")
                log.info("INFO - Set environment variables for normal operation")

                # Allow 30 x 3-second timeout, 90-seconds for boot
                at_login_prompt = False
                console_str = b""
                log.info("INFO - Waiting for Linux login prompt (60-seconds approx)")
                for _ in range(0, 30):
                    console_str += cmsp.read_until(b" login: ")
                    if b" login: " in console_str:
                        at_login_prompt = True
                        break
                log.debug("{}".format(console_str))

                if not at_login_prompt:
                    ret_val = False
                    log.info("INFO - Failed to find Linux login prompt!")
                else:
                    log.info("INFO - Found Linux login prompt after reboot")

                # Login
                time.sleep(1.0)
                cmsp.write("{}\r".format(csm_username).encode("UTF-8"))
                cmsp.read_until(b"Password:")
                cmsp.write("{}\r".format(csm_password).encode("UTF-8"))

                at_cmd_prompt = False
                console_str = b""
                for _ in range(0, 3):
                    console_str += cmsp.read_until(b":~#")
                    if b":~#" not in console_str:
                        cmsp.write(b"\r")
                    else:
                        at_cmd_prompt = True
                        break
                log.debug(console_str)

                if not at_cmd_prompt:
                    ret_val = False
                    log.info("INFO - Linux login failed!")
                    break

                log.info("INFO - Logged into Linux")

                # Set default unit serial no. to "0000000" to allow SSH connections using
                # "csm-000000.local" hostname for board level testing, also sets default BootBlocker
                # configuration with tamper detection disabled.
                cmsp.write(b"\rpython3 /run/media/mmcblk1p2/test/hardware_unit_config.py "
                           b"-st 'CSM_ASSEMBLY' -sn '000000' -sr 'TBD' -sb 'TBD' -td\r")

                console_str = b""
                for _ in range(0, 5):
                    console_str += cmsp.read_until(b":~#")
                log.debug("{}".format(console_str))

                program_success = b"Programmed config info CSM_ASSEMBLY" in console_str
                log.info("INFO - Unit serial number{}set to '000000'".format(" " if program_success else " NOT "))
                ret_val = program_success and ret_val

                # Set tamper sensors to the inactive state
                cmsp.write(b"\rpython3 /run/media/mmcblk1p2/test/tamper.py -i\r")

                console_str = b""
                for _ in range(0, 5):
                    console_str += cmsp.read_until(b":~#")
                log.debug("{}".format(console_str))

                tamper_inactive_success = b"Setting both tamper channels to inactive" in console_str
                log.info("INFO - Tamper sensors{}set to inactive".format(" " if tamper_inactive_success else " NOT "))
                ret_val = tamper_inactive_success and ret_val

                # Only want to do this if setting the default BootBlocker configuration with
                # tamper detection and setting tamper channels inactive was successful
                if program_success and tamper_inactive_success:
                    # Flash boot_bb.bin with BootBlocker
                    cmsp.write(b"flashcp -v /run/media/mmcblk0p1/boot_bb.bin /dev/mtd8\r")
                    console_str = b""
                    for _ in range(0, 10):
                        console_str += cmsp.read_until(b":~#")
                    log.debug("{}".format(console_str))

                    program_success = False
                    for a_line in console_str.splitlines():
                        if b"Verifying data: " in a_line and b"(100%)" in a_line:
                            program_success = True
                            break

                    if not program_success:
                        ret_val = False
                        log.info("INFO - Failed to perform boot_bb.bin flashcp command!")
                        break
                    else:
                        log.info("INFO - Successful boot_bb.bin flashcp command")

                break

    return ret_val


def program_gbe_sw_spi_flash_from_som(csm_username, test_jig_com_port, csm_master_com_port,
                                      fw_file="KT-956-0195-00.bin", fw_file_path="/run/media/mmcblk0p1/",
                                      test_jig_intf=None):
    """
    Program the GbE Switch SPI Flash device with the operating firmware.
    Prerequisites:
    - GbE Switch Firmware binary file on SoM SD Card or eMMC
    - Bench PSU turned on and board powered off
    Uses:
    - Test jig STM32 serial interface
    - CSM Master serial port connected to Linux terminal
    :return: True if the device is successfully programmed, else False
    """
    fw_file = str(fw_file)
    fw_file_path = str(fw_file_path)

    with CsmTestJigInterface(test_jig_com_port) if test_jig_intf is None else test_jig_intf as ctji:
        # Turn on the board/unit under test
        ret_val = ctji.toggle_rcu_power_button(hard_power_off=False)

    with Serial(csm_master_com_port, 115200, timeout=3.0, xonxoff=False, rtscts=False, dsrdtr=False) as cmsp:
        while True:
            # Interrupt auto-boot so the FPGA GPIO can be configured to allow
            # the SoC to write the GbE Switch SPI Flash.
            # Allow 10 x 3-second timeout, 30-seconds to hit prompt
            at_stop_autoboot_prompt = False
            console_str = b""
            for _ in range(0, 10):
                console_str += cmsp.read_until(b"Hit any key to stop autoboot:")
                if b"Hit any key to stop autoboot:" in console_str:
                    cmsp.write(b'q\r')
                    cmsp.read_until(b"K-CEMA-CSM> ")
                    at_stop_autoboot_prompt = True
                    break
            log.debug("{}".format(console_str))

            if not at_stop_autoboot_prompt:
                ret_val = False
                log.info("INFO - Failed to stop Linux auto-boot!")
                break
            else:
                log.info("INFO - Interrupted Linux auto-boot")

            # Set up GPIO so that the SoM has control of the SPI Flash device then continue boot
            gbe_sw_boot_prog_cmds = [
                b"setenv sdbootdev 0\r",
                b"setenv fpga_img system_gbe_sw.bin\r",
                b"setenv kernel_img image_gbe_sw.ub\r",
                b"run fpga_mmc_boot\r",
                b"run cp_kernel2ram\r",
                b"mw.l 0x4000A000 0xD\r",
                b"bootm\r"
            ]

            for cmd in gbe_sw_boot_prog_cmds:
                cmsp.write(cmd)
                cmsp.read_until(b"K-CEMA-CSM> ")

            # Allow 30 x 3-second timeout, 90-seconds for boot
            at_login_prompt = False
            console_str = b""
            log.info("INFO - Waiting for Linux login prompt (60-seconds approx)")
            for _ in range(0, 30):
                console_str += cmsp.read_until(b" login: ")
                if b" login: " in console_str:
                    at_login_prompt = True
                    break
            log.debug("{}".format(console_str))

            if not at_login_prompt:
                ret_val = False
                log.info("INFO - Failed to find Linux login prompt!")
                break

            # Login
            time.sleep(1.0)
            cmsp.write("{}\r".format(csm_username).encode("UTF-8"))
            # GbE Switch programming Linux image password is "root"
            cmsp.read_until(b"Password:")
            cmsp.write(b"root\r")

            at_cmd_prompt = False
            console_str = b""
            for _ in range(0, 3):
                console_str += cmsp.read_until(b":~#")
                if b":~#" not in console_str:
                    cmsp.write(b"\r")
                else:
                    at_cmd_prompt = True
                    break
            log.debug(console_str)

            if not at_cmd_prompt:
                ret_val = False
                log.info("INFO - Linux login failed!")
                break

            log.info("INFO - Logged into Linux")

            # Program the SPI Flash device
            cmsp.write(b"\rflashcp -v " + fw_file_path.encode("UTF-8") + fw_file.encode("UTF-8") + b" /dev/mtd0\r")
            console_str = b""
            for _ in range(0, 5):
                console_str += cmsp.read_until(b":~#")
                log.debug("{}: {}".format(_, console_str))

            program_success = False
            for a_line in console_str.splitlines():
                if b"Verifying data: " in a_line and b"(100%)" in a_line:
                    program_success = True
                    break

            if not program_success:
                ret_val = False
                log.info("INFO - Failed to perform flashcp command!")
                break
            else:
                log.info("INFO - Successful flashcp command")

            break

    return ret_val


def erase_gbe_sw_spi_flash():
    """
    Uses the ASIX PRESTO programmer via UP software to erase the Macronix MX25V2033FM1I GbE Switch SPI Flash device.
    :return: True if the device is successfully erased, else False
    """
    # Execute command to program device
    cmd_prompt = os.popen(ASIX_UP_ERASE_CMD.format(get_asix_up_exe_path_win()))
    log.debug(cmd_prompt.read())

    return True if cmd_prompt.close() is None else False


def get_asix_up_exe_path_win():
    """
    Checks for the ASIX UP executable in standard 32/64-bit installation folders on Windows OS
    :return: up.exe path as string, None if not found
    """
    if platform.system().lower() == "windows":
        if os.path.isfile(ASIX_UP_PATH_WIN64):
            return ASIX_UP_PATH_WIN64
        elif os.path.isfile(ASIX_UP_PATH_WIN32):
            return ASIX_UP_PATH_WIN32
        else:
            raise RuntimeError("ASIX UP executable not found!")
    else:
        raise RuntimeError("Unsupported platform!")


def program_zeroise_fpga(job_file_path):
    """
    Uses the Microchip FlashPro programming software to program the Zeroise FPGA
    :param job_file_path: path of FlashPro job file for programming the Zeroise FPGA :type: string
    :return: True if the device is successfully programmed, else False
    """
    if not os.path.isfile(job_file_path) or not os.path.isfile(FLASHPRO_PATH_WIN32):
        raise RuntimeError("Invalid binary file or FlashPro executable path! - "
                           "{}; {}".format(job_file_path, FLASHPRO_PATH_WIN32))

    # Create a TCL script file for device programming
    with open(FLASHPRO_SCRIPT_FILENAME, 'w') as f:
        f.write(FLASHPRO_SCRIPT_PROGRAM_DEVICE.format(os.path.dirname(job_file_path), job_file_path))

    # Execute command to program device
    cmd_prompt = os.popen(FLASHPRO_CMD.format(FLASHPRO_PATH_WIN32, FLASHPRO_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the TCL script file
    if os.path.isfile(FLASHPRO_SCRIPT_FILENAME):
        os.remove(FLASHPRO_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


def erase_zeroise_fpga(job_file_path):
    """
    Uses the ASIX PRESTO programmer via UP software to erase the Macronix MX25V2033FM1I GbE Switch SPI Flash device.
     :param job_file_path: path of FlashPro job file for programming the Zeroise FPGA :type: string
    :return: True if the device is successfully erased, else False
    """
    if not os.path.isfile(job_file_path) or not os.path.isfile(FLASHPRO_PATH_WIN32):
        raise RuntimeError("Invalid binary file or FlashPro executable path! - "
                           "{}; {}".format(job_file_path, FLASHPRO_PATH_WIN32))

    # Create a TCL script file for device erasing
    with open(FLASHPRO_SCRIPT_FILENAME, 'w') as f:
        f.write(FLASHPRO_SCRIPT_ERASE_DEVICE.format(os.path.dirname(job_file_path), job_file_path))

    # Execute command to program device
    cmd_prompt = os.popen(FLASHPRO_CMD.format(FLASHPRO_PATH_WIN32, FLASHPRO_SCRIPT_FILENAME))
    log.debug(cmd_prompt.read())

    # Clean up the TCL script file
    if os.path.isfile(FLASHPRO_SCRIPT_FILENAME):
        os.remove(FLASHPRO_SCRIPT_FILENAME)

    return True if cmd_prompt.close() is None else False


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is NOT intended to be executed stand-alone
    """
    print("Module is NOT intended to be executed stand-alone")
