import power_supply_qpx
import serial
import time

MAX_TRIES = 100


def run_test():
    psu = power_supply_qpx.PowerSupplyQPX(reset_device=False)
    if not psu.find_and_initialise():
        return False
    psu.set_sense_remote()
    psu.set_current(10)
    psu.set_enabled(False)
    max_timeouts = 0
    not_attached_count = 0
    not_mounted_count = 0
    first_attempt_count = 0
    attempts = 0
    line_buffer = []
    with serial.Serial("COM10", 115200, timeout=10) as ser:
        while True:
            time.sleep(3)
            psu.set_enabled(True)
            nvme_attached = False
            nvme_mounted = False
            nvme_timeouts = 0
            booted = False
            while not booted:
                line = str(ser.readline())
                line_buffer.append(line)
                if "pci 0000:00:00.0: BAR 8: assigned" in line:
                    nvme_attached = True
                if "EXT4-fs (nvme0n1): mounted filesystem" in line:
                    nvme_mounted = True
                    if nvme_timeouts == 0:
                        first_attempt_count += 1
                if "ECAM access timeout" in line:
                    nvme_timeouts += 1
                    print("T", end="", flush=True)
                if nvme_mounted or nvme_timeouts == MAX_TRIES:
                    booted = True
                if booted:
                    attempts += 1
                    if nvme_timeouts > max_timeouts:
                        max_timeouts = nvme_timeouts
                    if not nvme_attached:
                        not_attached_count += 1
                    if not nvme_mounted:
                        not_mounted_count += 1
                    print("\rAttempts: {}, Timeouts: {}, First Attempt: {}, Not Attached: {},"
                          "Not Mounted: {}, Max Timeouts: {}".format(attempts,
                                                                     nvme_timeouts,
                                                                     first_attempt_count,
                                                                     not_attached_count,
                                                                     not_mounted_count,
                                                                     max_timeouts))
                    if nvme_timeouts == MAX_TRIES:
                        print("Stop test")
                        exit(1)
                    psu.set_enabled(False)
                    line_buffer.clear()


if __name__ == "__main__":
    run_test()
