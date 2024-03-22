import os
import sys
import time


class NVME:
    RESET_NODE = "/sys/kernel/kcema-driver/reset"
    READ_PATH_NODE = "/sys/kernel/kcema-driver/read_path"
    WRITE_PATH_NODE = "/sys/kernel/kcema-driver/write_path"
    READ_STATE_NODE = "/sys/kernel/kcema-driver/read_state"
    WRITE_STATE_NODE = "/sys/kernel/kcema-driver/write_state"
    BYTES_READ_NODE = "/sys/kernel/kcema-driver/bytes_read"
    BYTES_WRITTEN_NODE = "/sys/kernel/kcema-driver/bytes_written"
    NVME_ROOT = "/run/media/nvme0n1"

    def reset(self):
        with open(self.RESET_NODE, "w") as file:
            file.write("1")
            file.close()
        with open(self.RESET_NODE, "w") as file:
            file.write("0")
            file.close()

    def transmit(self, filename):
        print("Validate file: ", end="", flush=True)
        filepath = os.path.join(self.NVME_ROOT, filename)
        if not os.path.isfile(filepath):
            print("ERROR: file does not exist \"{}\"".format(filepath))
            return False
        file_size = os.stat(filepath).st_size
        if file_size == 0:
            print("ERROR: empty file")
            return False
        print("OK ({} bytes)".format(file_size))
        print("Reset NVMe driver...")
        self.reset()
        print("Set transmit file path...")
        with open(self.READ_PATH_NODE, "w") as file:

            file.write(filepath)
        print("Transmit file...")
        with open(self.READ_STATE_NODE, "w") as file:
            file.write("1")
        done = False
        prev_bytes_read = 0
        while not done:
            time.sleep(0.25)
            with open(self.BYTES_READ_NODE, "r") as file:
                line = file.readline()
                bytes_read = int(line)
                if bytes_read != 0 and bytes_read != prev_bytes_read:
                    print("Transmitted {} bytes".format(bytes_read))
                prev_bytes_read = bytes_read
                if bytes_read >= file_size:
                    done = True
        print("Done")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            loops = int(sys.argv[2])
        else:
            loops = 1
        nvme = NVME()
        for i in range(loops):
            nvme.reset()
            time.sleep(1)
            nvme.transmit(filename)
    else:
        print("Usage:")
        print("  nvme.py tx_file_name [loops]")
