#!/usr/bin/python3

##############################################################################
# This script is intended to generate a run.sh file
##############################################################################

import argparse
import operator
import os
import re
import socket

port_to_slot_map = [['7', '1'],
                    ['8', '2'],
                    ['1', '3'],
                    ['2', '4'],
                    ['3', '5']]

mac_address_to_port_map = []
mac_address_to_slot_map = []

parser = argparse.ArgumentParser(description="Generate a run.sh file")
parser.add_argument('-o', '--output_file', default='/run/media/mmcblk1p2/run.sh', help="Output file. Default is /run/media/mmcblk1p2/run.sh")
parser.add_argument('-t', '--telnet_host', default='169.254.57.242', help="Telnet IP address. Default is 169.254.57.242")
parser.add_argument('-p', '--telnet_port', default=31, help="Telnet port number. Default is 31")

# ------------------------------------------------------------
def telnet(telnet_host, telnet_port):
  try:
    print("Connecting to " + telnet_host + " " + str(telnet_port))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.connect((telnet_host, telnet_port))
      print("Connection established")

      # Sometimes, using a script, telnet doesn't return all 
      # the MAC addresses so allow up to 5 retries 
      retries = 5

      while(retries):
        # Send the 'm' command (and the '\r\n' is essential)
        s.sendall(b'm\r\n')

        # Need to intercept a preceeding 3 byte byte sequence ('\xff\xfd\x03')
        data = s.recv(3)

        # Now intercept the response from the 'm' command
        data = s.recv(256)

        # Regex to pick out the individual MAC address lines 
        p = re.compile(r'(?:[0-9a-fA-F]-?){12}  D        [0-9]')
        lines = re.findall(p, repr(data))
        for line in lines:
          # Create a tuple of MAC address and port
          mac_address_to_port = line.split("  D        ")

          # Insert it into a map - if the MAC address starts with '80'
          if mac_address_to_port[0].startswith("80"):

            # Reformat the MAC address to replace '-' with ':'
            mac_address_to_port[0] = mac_address_to_port[0].replace('-', ':')

            # Ensure that the MAC address is in upper case
            mac_address_to_port[0] = mac_address_to_port[0].upper()

            # Before inserting it into the map
            mac_address_to_port_map.append(mac_address_to_port)

        # Expecting to get 7 MAC addresses (5 slots + CSM and backplane)
        if len(mac_address_to_port_map) >= 7:
          break;
        else:
          retries = retries - 1

          # Clear out the map read to try again
          mac_address_to_port_map.clear()

      # Can close the socket now
      s.close()

      if len(mac_address_to_port_map) == 0:
        print("No MAC addresses returned")
      else:
        print("Received MAC addresses:")
        for x in mac_address_to_port_map:
          print(x[0] + "   Port " + x[1])

  except:
     print("Telnet session failed")

# ------------------------------------------------------------
def generate_slot_map():
  # Now need to convert the port numbers to slot numbers
  for m2p_entry in mac_address_to_port_map:
    for p2s_entry in port_to_slot_map:
      # If the port in the mac_address_to_port_map has a corresponding
      # entry in the port_to_slot_map it'll be added to the mac_address_to_slot_map
      if m2p_entry[1] == p2s_entry[0]:

        # Copy the entry
        m2s_entry = m2p_entry

        # Then over-write the slot address 
        m2s_entry[1] = p2s_entry[1]

        # Before appending it to the new map
        mac_address_to_slot_map.append(m2s_entry)

        break

  # Finally sort the list by slot number
  mac_address_to_slot_map.sort(key=operator.itemgetter(1))

# ------------------------------------------------------------
def write_file(output_file):
  try:
    f = open(output_file, "w")

    f.write("LIB_ROOT=/usr/local/lib\n")
    f.write("export FILE_ROOT=/run/media/mmcblk1p2\n")
    f.write("export LD_LIBRARY_PATH=${LIB_ROOT}/Boost:${LIB_ROOT}/CryptoPP:${LIB_ROOT}/OpenSSL:${LIB_ROOT}/OpenDDS\n")

    for entry in mac_address_to_slot_map:
      string = "export SLOT_" + entry[1] + "_MAC=" + entry[0] + "\n"
      f.write(string)

    f.write("${FILE_ROOT}/KCemaCSMApp -DCPSConfigFile ${FILE_ROOT}/rtps.ini\n")

    f.close()

    # Finally change the file permissions to 755
    os.chmod(output_file, 0o755)

  except OSError:
    print("Unable to open file: " + output_file)


# ------------------------------------------------------------

if __name__ == '__main__':

    args = parser.parse_args()
    output_file = args.output_file
    telnet_host = args.telnet_host
    telnet_port = args.telnet_port

    telnet(telnet_host, telnet_port)
    generate_slot_map()
    write_file(output_file)

