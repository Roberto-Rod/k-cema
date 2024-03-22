import power_supply_qpx
import serial
import ssh
import time

password_dict = {}
CMD = "/usr/sbin/flashcp /run/media/mmcblk0p2/KT-956-0197-00_v1.3.0.bin /dev/mtd0 -v"
EMA_BL_UPDATE_COMMAND_TIMEOUT_S = 120  # 2 minutes


def run_test():
    times = []
    psu = power_supply_qpx.PowerSupplyQPX(reset_device=False)
    if not psu.find_and_initialise():
        return False
    psu.set_sense_remote()
    psu.set_current(10)
    #psu.set_enabled(False)
    time.sleep(3)
    psu.set_enabled(True)
    line_buffer = []
    attempts = 0
    success = 0
    max_elapsed = 0
    with serial.Serial("COM10", 115200, timeout=10) as ser:
        booted = True
        while not booted:
            line = str(ser.readline()).strip("\r\n")
            line_buffer.append(line)
            print("\r{}".format(line), end="", flush=True)
            if "udhcpc: no lease, forking to background" in line:
                booted = True
        # Open SSH connection
        s = ssh.SSH("169.254.7.116", password_dict)
        if not s.is_connected():
            print("ERROR: Failed to make SSH connection")
            return False
        while True:
            attempts += 1
            start = time.time()
            result = s.send_command(CMD, EMA_BL_UPDATE_COMMAND_TIMEOUT_S)
            elapsed = time.time() - start
            if elapsed > max_elapsed:
                max_elapsed = elapsed
            print("Elapsed {:.2f}".format(elapsed))
            if result.return_code == 0:
                success += 1
            else:
                print("Command failed")
                print(result)
            print("Attempts: {}, Success: {}, Max Elapsed: {:.2f}".format(attempts, success, max_elapsed))


if __name__ == "__main__":
    run_test()
