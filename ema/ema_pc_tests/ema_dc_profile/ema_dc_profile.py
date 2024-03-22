from test_equipment.power_supply_qpx import *
from system.vehicle_system_test.ssh import *

EMA_CMD_PREFIX = "cd /run/media/mmcblk0p2/test/;python3 "
EMA_CMD_INIT = EMA_CMD_PREFIX + "sys_test_initialise.py"
EMA_CMD_TERM = EMA_CMD_PREFIX + "sys_test_jam.py -t"
EMA_CMD_MUTE = EMA_CMD_PREFIX + "sys_test_ipam_set_mute.py True"
EMA_CMD_UNMUTE = EMA_CMD_PREFIX + "sys_test_ipam_set_mute.py False"
EMA_CMD_FANS = EMA_CMD_PREFIX + "sys_test_jam.py -F"
EMA_CMD_JAM = EMA_CMD_PREFIX + "sys_test_jam.py -j"
EMA_CMD_TONE = EMA_CMD_PREFIX + "sys_test_full_power_tone.py {}" + ";" + EMA_CMD_UNMUTE
EMA_CMD_STOP = EMA_CMD_PREFIX + "sys_test_jam.py -sf" + ";" + EMA_CMD_MUTE
EMA_CMD_ADD = EMA_CMD_PREFIX + "sys_test_jam.py -a {} {} 10000 0 0"
TEST_LOG_REL_DIR = "./test_logs/"


def run_test(addr):
    psu = PowerSupplyQPX(reset_device=False)
    if not psu.find_and_initialise():
        return False
    psu.set_sense_remote()
    psu.set_current(35)

    # Open SSH connection
    s = SSH(addr, "root", "root")
    if s.is_connected():
        print("Connected to {}".format(addr))
    else:
        print("ERROR: Failed to make SSH connection")
        return False

    filename = addr.replace(".local", ".csv")
    print("Open {} for writing: ".format(filename), end="")
    try:
        # Open file for writing
        file = open(filename, "w")

        # Write header
        file.write("Input Voltage (V),Freq (MHz),Input Current (A),Input Power (W)\n")
        print("OK")
    except:
        print("FAIL")
        return False

    s.send_command(EMA_CMD_INIT)

    time_ns = 1000000
    first = True
    # Input voltage loop: 18 V to 32 V in 2 V steps
    for input_voltage in [18, 20, 24, 28, 32]:
        psu.set_voltage(input_voltage)
        s.send_command(EMA_CMD_FANS)
        # Frequency loop
        start = 1800
        end = 6000
        step = 25
        for freq_MHz in range(start, end + step, step):
            s.send_command(EMA_CMD_TONE.format(int(freq_MHz * 1e6)))
            if first:
                print("Warm up (seconds remaining)....", end="", flush=True)
                for i in range(18, 0, -1):
                    print(" {}".format(i * 10), end="", flush=True)
                    sleep(10)
                print()
                first = False
            else:
                sleep(2)
            current = psu.get_average_current_out(nr_readings=5000)
            power = round(input_voltage * current, 4)
            print("{} V, {} MHz: {} A, {} W".format(input_voltage, freq_MHz, current, power))
            file.write("{},{},{},{}\n".format(input_voltage, freq_MHz, current, power))
            s.send_command(EMA_CMD_STOP)
    s.send_command(EMA_CMD_TERM)


if __name__ == "__main__":
    run_test("EMA-010482.local")
