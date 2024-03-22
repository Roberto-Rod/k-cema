import ssh
import time
import serial

password_dict = {}
#IP_ADDRESS = "169.254.4.67"  # EMA-013121
#IP_ADDRESS = "169.254.10.222"  # EMA-010471
TEST_DIR = "/run/media/mmcblk0p2/test"
TRIM_CLK_CMD = "{}/adctrim 0x7ff"
CYCLE_PDWN_CMD = "cd {};./devmem 0x40004000 0x81A;/bin/sleep 0.5;./devmem 0x40004000 0x1A"
RESET_ADC_CMD = "{}/adctool -R"
LINK_ADC_CMD = "cd {};./adctool -L 1;/bin/sleep 0.1;./adctool -S"
ADC_INIT_CMD = "{}/adctool -t"
GET_STATUS_CMD = "{}/adctool -l"
ADC_POWER_OFF_CMD = "cd {};/sbin/devmem 0x40014000 32 0x24"
ADC_POWER_ON_CMD = "cd {};/sbin/devmem 0x40014000 32 0xdf;/bin/sleep 0.5"
REBOOT_CMD = "cd {};/sbin/reboot"


def send_command(s, cmd, desc, verbose=True):
    ret_val = False
    if verbose:
        print("{}: ".format(desc), end="", flush=True)
    result = s.send_command(cmd.format(TEST_DIR))
    if result.return_code != 0:
        print("error sending: {}".format(cmd))
        print(result)
    else:
        if verbose:
            print("OK")
        if result.stdout:
            ret_val = result.stdout
        else:
            ret_val = True
    return ret_val


def run_test():
    attempts = 0
    success = 0
    while True:
        attempts += 1
        # Open SSH connection
        for i in range(100):
            print("Connection attempt {}...".format(i + 1))
            s = ssh.SSH(IP_ADDRESS, password_dict)
            if s.is_connected():
                break
        if not s.is_connected():
            print("ERROR: Failed to make SSH connection")
            return False
        time.sleep(10)
        #if not send_command(s, CYCLE_PDWN_CMD, "Cycle PDWN"):
        #    return False
        #if not send_command(s, ADC_POWER_ON_CMD, "ADC Power On"):
        #    return False
        #if not send_command(s, TRIM_CLK_CMD, "Trim ADC Clock"):
        #    return False
        if not send_command(s, ADC_INIT_CMD, "ADC Init"):
            return False
        #if not send_command(s, RESET_ADC_CMD, "Reset ADC"):
        #    return False
        #if not send_command(s, LINK_ADC_CMD, "Link ADC"):
        #    return False
        status = send_command(s, GET_STATUS_CMD, "Get Status")
        if "JESD204B link is synchronised" in status:
            print("Link Synced")
            success += 1
        else:
            print("Link Not Synced")
        if not send_command(s, ADC_POWER_OFF_CMD, "ADC Power Off"):
            return False
        print("Attempts: {}, Success: {}".format(attempts, success))
        if attempts >= 10:
            pass
        if not send_command(s, REBOOT_CMD, "Reboot"):
            return False
        for i in range(60):
            time.sleep(1)
            if (i + 1) % 5 == 0:
                print("{}".format(i+1), end="", flush=True)
            else:
                print(".", end="", flush=True)
        print("")


if __name__ == "__main__":
    run_test()
