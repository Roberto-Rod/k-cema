from sys_test_jam import *

if __name__ == "__main__":
    jam = SysTestJam()

    # Initialise IPAM, DDS etc.
    print("Initialise")
    jam.initialise()

    # Loop for frequencies 400 MHz to 2700 MHz in steps of 20 MHz
    for freq in range(400, 2700, 20):
        # Add a jamming line
        print("Add jamming line: {} MHz to {} MHz".format(freq, freq+5))
        jam.add_jam_line(time_ns=200000, start_MHz=freq, stop_MHz=freq+5)

        # Add a blank line
        print("Add blanking line")
        jam.add_blank_line(time_ns=20000)

        # Add a jamming line
        print("Add jamming line: {} MHz to {} MHz".format(freq+15, freq + 20))
        jam.add_jam_line(time_ns=200000, start_MHz=freq+15, stop_MHz=freq+20)

        # Start the jamming table
        print("Start jamming")
        jam.start_jamming()

        # Sleep for 3 seconds
        sleep(3)

        # Stop the jamming table (clears lines by default)
        print("Stop jamming")
        jam.stop_jamming()

    # Power-down IPAM, DDS etc.
    print("Terminate")
    jam.terminate()
