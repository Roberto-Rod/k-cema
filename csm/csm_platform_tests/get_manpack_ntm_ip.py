import argparse
import serial
import time


class GetManpackNTMIP:
    BAUD_RATE = 115200
    USER = "root"
    PASS = "gbL^58TJc"

    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.serial_device = None

    def connect(self):
        try:
            self.serial_device = serial.Serial(self.serial_port, self.BAUD_RATE, timeout=1.0)
            return True
        except Exception as e:
            print(e)
            return False

    def login(self):
        if self.serial_device:
            # Send ctrl-c, see what we get back, last line will be:
            #    "root@EMA-<nnnnnn>: <curr_dir># " if already logged in
            #    "EMA-<nnnnnn> login: " if not logged in
            self.serial_device.write(b"\x03")
            for line in self.serial_device.readlines():
                line = line.decode("utf-8")
                if line.endswith(" login: "):
                    # Not logged in, write username and password
                    self.serial_device.write("{}\n".format(self.USER).encode("utf-8"))
                    time.sleep(1)
                    self.serial_device.write("{}\n".format(self.PASS).encode("utf-8"))
                    time.sleep(1)
                    # Read lines back to confirm that we have logged in
                    for line in self.serial_device.readlines():
                        line = line.decode("utf-8")
                        if line.startswith("Last login: "):
                            time.sleep(1)
                            self.serial_device.flush()
                            return True
                elif line.startswith("root@EMA-"):
                    # Already logged in
                    return True
        return False

    def get_ip(self):
        if self.serial_device:
            self.serial_device.write("ifconfig\n".encode("utf-8"))
            for line in self.serial_device.readlines():
                line = line.decode("utf-8").strip()
                index = line.find("inet addr:")
                if index != -1:
                    line = line[index + 10:]
                    return line.split(" ")[0]
        return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Manpack NTM IP Address")
    parser.add_argument("-p", "--serial_port", help="EMA serial port e.g. /dev/ttyNTM1")
    args = parser.parse_args()

    if args.serial_port:
        ntm = GetManpackNTMIP(args.serial_port)
        if ntm.connect():
            if ntm.login():
                print(ntm.get_ip())
            else:
                print("Failed to login")
        else:
            print("Failed to connect to {}".format(args.serial_port))
    else:
        print("Serial port must be specified, see help")
