#!/usr/bin/env python3
import time
import datetime
import ssh
import time

hostname = 'EMA-010482.local'
#hostname = '169.254.11.44'
#hostname = 'fe80::821f:12ff:fef0:bbe2'
username = 'root'
password = 'root'

# CSM channel 0 (case switch) tamper normally-closed configuration:
# TEB=1, TIE=1, TCM=0, TPM=1, TDS=1, TCHI=0, CLR1_EXT=0, CLR1=1

# CSM channel 1 (light sensor) & EMA (both channels) normally-open configuration:
# TEB=1, TIE=1, TCM=1, TPM=0, TDS=0, TCHI=0, CLR1_EXT=0, CLR1=1

CSM_DISARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x14 0;/usr/sbin/i2cset -f -y 1 0x68 0x15 0"
CSM_ARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x14 0xD9;/usr/sbin/i2cset -f -y 1 0x68 0x15 0xE1"
CSM_SET_TAMPER_ABE_CMD = "/usr/sbin/i2cset -f -y 1 0x68 0x0A 0x20"
CSM_GET_TAMPER_FLAGS = "/usr/sbin/i2cget -f -y 1 0x68 0xF"
EMA_DISARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x14 0;/usr/sbin/i2cset -f -y 0 0x68 0x15 0"
EMA_ARM_TAMPER_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x14 0xE1;/usr/sbin/i2cset -f -y 0 0x68 0x15 0xE1"
EMA_SET_TAMPER_ABE_CMD = "/usr/sbin/i2cset -f -y 0 0x68 0x0A 0x20"
EMA_GET_TAMPER_FLAGS = "/usr/sbin/i2cget -f -y 0 0x68 0xF"
EMA_TEST_FULL_POWER_TONE_CMD = "python3 /run/media/mmcblk0p2/test/sys_test_full_power_tone.py -v "
EMA_TEST_INITIALISE_CMD = "python3 /run/media/mmcblk0p2/test/sys_test_initialise.py -v"
EMA_TEST_TERMINATE_CMD = "python3 /run/media/mmcblk0p2/test/sys_test_terminate.py -v"
EMA_TEST_IPAM_GET_TEMPERATURE_CMD = "python3 /run/media/mmcblk0p2/test/sys_test_ipam_get_temperature.py -v"
EMA_TEST_IPAM_SET_MUTE_CMD = "python3 /run/media/mmcblk0p2/test/sys_test_ipam_set_mute.py -v "


if __name__ == "__main__":
    print("Connecting to {}".format(hostname))
    connection = ssh.SSH(hostname, username, password)
    connection.send_command(EMA_TEST_INITIALISE_CMD)
    START_FREQ = 1300000000
    STOP_FREQ = 2000000000
    STEP_FREQ = 100000000

    NOTCH_START = 1300000000
    NOTCH_END = 1700000000

    freq = START_FREQ
    loop_count = 0
    cmd_count = 0
    start_time = time.time()
    while False:
        if freq <= NOTCH_START or freq >= NOTCH_END:
            connection.send_command(EMA_TEST_IPAM_GET_TEMPERATURE_CMD)
            connection.send_command(EMA_TEST_IPAM_SET_MUTE_CMD + "true")
            connection.send_command(EMA_TEST_FULL_POWER_TONE_CMD + str(freq))
            connection.send_command(EMA_TEST_IPAM_SET_MUTE_CMD + "false")
            cmd_count += 4
            print()
            print("*** Sent {} commands ***".format(cmd_count))
            print("*** Running for {} ***".format(str(datetime.timedelta(seconds=round(time.time() - start_time)))))
            print()
        freq += STEP_FREQ
        if freq > STOP_FREQ:
            loop_count += 1
            print("\nCOMPLETED LOOP {} TIMES\n".format(loop_count))
            freq = START_FREQ

    print("Arming tamper detection device")
    if str(connection.send_command(EMA_DISARM_TAMPER_CMD).stdout).strip() == "" and\
       str(connection.send_command(EMA_ARM_TAMPER_CMD).stdout).strip() == "" and\
       str(connection.send_command(EMA_SET_TAMPER_ABE_CMD).stdout).strip() == "":
        print("OK")
    else:
        print("ERROR")
    print("Checking tamper flags...")
    time.sleep(1)
    tamper_flags = str(connection.send_command(EMA_GET_TAMPER_FLAGS).stdout).strip()
    if tamper_flags == "0x00":
        print("OK")
    else:
        print("ERROR: tamper flags not clear")
        if int(tamper_flags, 16) & 0x1:
            print("  > Light sensor triggered")
        if int(tamper_flags, 16) & 0x2:
            print("  > Case switch triggered")
        exit()

    print("Setting time & date")
    now = datetime.datetime.now()
    connection.send_command("/bin/date +%Y%m%d%T -s '{:04d}{:02d}{:02d} {:02d}:{:02d}:{:02d}'".format(now.year, now.month, now.day, now.hour, now.minute, now.second))
    connection.send_command("/sbin/hwclock -w")
    # Wait before reading hardware clock to ensure it has not stopped
    # (it stops if tamper is detected)
    # Wait a bit more than 1 second so we can be sure it should have advanced over the time sent above
    time.sleep(1.2)
    print("Reading hardware clock")
    connection.send_command("/sbin/hwclock")
