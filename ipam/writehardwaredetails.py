import sys
import glob
import serial
import ipam


def write_details(port):
    # Create IPAM object using the serial port name passed as a command line argument
    pa = ipam.Ipam(port)

    if pa.unlock_registers():
        print("Registers unlocked")
    else:
        print("ERROR: could not unlock registers")
        return

    pa.set_factory_settings_crc()

    if pa.check_factory_settings_crc():
        print("Factory settings CRC OK")
    else:
        print("Factory settings CRC error")



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

    write_details(sys.argv[1])
