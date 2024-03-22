import sys
import glob
import serial
import ipam


def read_details(port):
    # Create IPAM object using the serial port name passed as a command line argument
    pa = ipam.Ipam(port)

    print("Unit Type:                   " + pa.unit_type())
    print("Unit Part Number:            " + pa.unit_part_number())
    print("Unit Revision:               " + pa.unit_revision())
    print("Unit Mod Level:              " + pa.unit_mod())
    print("Unit Serial Number:          " + pa.unit_serial_number())
    print("Unit Build/Batch:            ")
    print()
    print("RF Board Part Number:        " + pa.rf_part_number())
    print("RF Board Revision:           " + pa.rf_revision())
    print("RF Board Mod Level:          " + pa.rf_mod())
    print("RF Board Serial Number:      " + pa.rf_serial_number())
    print("RF Board Build/Batch:        ")
    print()
    print("Control Board Part Number:   " + pa.control_part_number())
    print("Control Board Revision:      " + pa.control_revision())
    print("Control Board Mod Level:     " + pa.control_mod())
    print("Control Board Serial Number: " + pa.control_serial_number())
    print("Control Board Build/Batch:    ")
    print()
    print("Firmware Version:            " + pa.firmware_version())
    print("Firmware Build ID:           " + pa.firmware_build_id())


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


if __name__ == "__main__":
    # Check number of arguments
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <serial port name>")
        print("Available Ports:")
        print(serial_ports())
        quit()

    read_details(sys.argv[1])
