#!/usr/bin/python3

import argparse
import datetime
import os
import paramiko
import pysftp
import re
import shutil
import signal
import socket
import sys
import time
from zeroconf import (ServiceBrowser, Zeroconf)

################################################################################
# This script is intended to recover log files from all the cards in the system.
# and then produce a unified log in date/time order.
# 
# Additional Python3 modules that will require installation are:
# - paramiko
# - pysftp
# - zeroconf
################################################################################


hosts = []

kDiscoveryDelay = 3   # delay in seconds

kEMARemotePath = "/run/media/mmcblk0p2/log/"
kCSMRemotePath = "/run/media/mmcblk1p2/log/"

kLocalPath = "/tmp/LogCache/"

parser = argparse.ArgumentParser(description="Generate a unified log file")
parser.add_argument('-u', '--username', default="root", help="Username. Default is root")
parser.add_argument('-p', '--password', default="root", help="Password. Default is root")
parser.add_argument('-a', '--all', action='store_true', help="Select all files. Default is critical files only")

class Listener(object):

  def add_service(self, zeroconf, type, name):
    info = zeroconf.get_service_info(type, name)

    print("%s at IP address: %s" % (name.split('.')[0], socket.inet_ntoa(info.addresses[0])))
      
    # Add the IP address to the host list  
    hosts.append(socket.inet_ntoa(info.addresses[0]))

  def remove_service(self, zeroconf, type, name):
    # Functionally don't require this method but zerconf will issue a warning if not implemented
    pass

  def update_service(self, zeroconf, type, name):
    # Functionally don't require this method but zerconf will issue a warning if not implemented
    pass

# ------------------------------------------------------------
def discover_hosts():
  print("Peforming hardware discovery...")

  zeroconf = Zeroconf()
  listener = Listener()
  browser = ServiceBrowser(zeroconf, "_ssh._tcp.local.", listener)

  # The discovery runs in it's own thread so need to wait here
  # to give all the cards a chance to report their IP addresses
  delay = kDiscoveryDelay
  while(delay):
    time.sleep(1)
    delay = delay - 1

  print("Hardware discovery complete")

# ------------------------------------------------------------
def ssh_connect(hostname, username, password, all_files, localFilePath):
  print("Attempting to connect to " + hostname)
  cnopts=pysftp.CnOpts()
  cnopts.hostkeys = None
  with pysftp.Connection(host=hostname, username=username, password=password, cnopts=cnopts) as sftp:
    print("Connection succesfully established")

    # Execute 'hostname' command on the remote system, returns a list
    result = sftp.execute("hostname")

    # The 'hostname' call will only ever return a list containing one entry
    host = result[0].decode("ascii").rstrip()

    if host.startswith('EMA'):
      remoteFilePath = kEMARemotePath
    else:
      remoteFilePath = kCSMRemotePath

    print(host + ": retrieving files...")

    # Return a list of files for the remote location
    files = sftp.listdir(remoteFilePath)

    logFileCount = 0

    # Copy all files, who's name matches the correct format, from remote to local host
    for filename in files:
      if all_files:
        if filename.startswith('k-cema-ema') or filename.startswith('k-cema-csm'):
          if filename.endswith('.log'):
            print(filename)
            sftp.get(remoteFilePath + '/' + filename, localFilePath + '/' + host + '_' + filename)
            logFileCount = logFileCount + 1
      else:
        if filename.startswith('k-cema-ema-critical') or filename.startswith('k-cema-csm-critical'):
          if filename.endswith('.log'):
            print(filename)
            sftp.get(remoteFilePath + '/' + filename, localFilePath + '/' + host + '_' + filename)
            logFileCount = logFileCount + 1

    print(str(logFileCount) + ' files found')

    sftp.close()
    print("Connection closed")
    print("\n")

    return host

# ------------------------------------------------------------
def create_unified_log(localFilePath, output_file):

  output_file_contents = []

  # Regex to separate the timestamps from the rest of the log file entry
  p = re.compile(r'^\[([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})\](.*)')

  output_index = 0
  output_utc = 0

  # The way the unification is going to work is that'll construct the output file in memory by 
  # merging the log files, one at a time and a line at a time. This has proven to achieve the
  # best performance so far.
  # 
  # Algorithmn explanation:
  # The current position within the output file is tracked using the 'output_index'. A log
  # file is read a line at a time and it's timestamp compared to that of the current position
  # within the output file. If the log file timestamp is newer than the output file position
  # then 'output_index' is walked forward to the next line in the output file. This repeats
  # until either the log file timestamp is older than the current index or the end of the
  # output file is reached. In both cases the log file line is inserted at the current index,
  # the only difference is that when the log file entry is inserted anywhere other than at
  # the end of the output file, the output file index needs to be incremented to compensate.
  # With each new log file the output file index returns to the start of the file.

  filenames = os.listdir(localFilePath)

  if not filenames:
    print('No log files found')
    return
  else:
    print('Unifying ' + str(len(filenames)) + ' log files (this may take a while)')

  for name in filenames:
    print("Merging file: %s" % name)

    full_path = localFilePath + '/' + name

    # Don't process an empty file
    if os.stat(full_path).st_size == 0:
      continue

    fd = open(full_path, 'r')
 
    for line in fd:
      # The first log file and line requires special handling
      if len(output_file_contents) == 0:
        output_file_contents.insert(0, line)
        output_ts = (re.match(p, line)).group(1)
        output_utc = datetime.datetime.timestamp(datetime.datetime.strptime(output_ts, "%Y-%m-%d %H:%M:%S.%f"))
        continue

      # Only add a line to the output file content if starts with a timestamp 
      # otherwise it wont be possible to sort later and will cause problems
      m = re.match(p, line)
      if m == None:
        continue

      # Get just the timestamp (from group 1) and convert it to POSIX
      line_utc = datetime.datetime.timestamp(datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f"))

      # Compare timestamps 
      while(line_utc > output_utc):
          output_index = output_index + 1
          if output_index == len(output_file_contents):
            # Reached the end of file
            break
          else:
            # Walk the index forward
            output_line = output_file_contents[output_index]
            output_ts = (re.match(p, output_line)).group(1)
            output_utc = datetime.datetime.timestamp(datetime.datetime.strptime(output_ts, "%Y-%m-%d %H:%M:%S.%f"))

      # Perform the insertion into the output file at the current index position
      output_file_contents.insert(output_index, line)

      # If an insertion was made behind the index position 
      # the index needs to be moved forward to compensate
      if line_utc < output_utc:
        output_index = output_index + 1

    fd.close()

    # Reset back to the start of the output_file_content ready for merging the next log file
    output_index = 0
    output_line = output_file_contents[output_index]
    output_ts = (re.match(p, output_line)).group(1)
    output_utc = datetime.datetime.timestamp(datetime.datetime.strptime(output_ts, "%Y-%m-%d %H:%M:%S.%f"))


  outfile = open(output_file, "w")

  # With the content sorted write it to the output file
  outfile.writelines(output_file_contents)

  outfile.close()

  # Finally change the file permissions to 644
  os.chmod(output_file, 0o644)

  print("Generated: %s" % output_file)

# ------------------------------------------------------------
def stop(self, signal):
  shutil.rmtree(kLocalPath)
  sys.exit()

# ------------------------------------------------------------
if __name__ == '__main__':

  signal.signal(signal.SIGINT, stop)

  args = parser.parse_args()
  username = args.username
  password = args.password
  all_files = args.all

  csm_serial_number = ''

  # Delete any existing temporary directory  
  if os.path.exists(kLocalPath):
    shutil.rmtree(kLocalPath)

  try:
    # Create a temporary directory to store the logs
    os.mkdir(kLocalPath, 0o755)
  except FileExistsError:
    sys.exit('Unable to create temporary directory: ' + kLocalPath)

  try:
    # Discover IP addresses for connected host hardware
    discover_hosts()

    # Connect to each host by SSH and pull the log files
    for ipAddress in hosts:
      host = ssh_connect(ipAddress, username, password, all_files, kLocalPath)

      # Retain the CSM serial number when it becomes available (used for output file name)
      if host.startswith('CSM'):
        csm_serial_number = host.split('-')[1]

    if csm_serial_number != '':
      # Get current date/time (format is yyyy-mm-dd hh:mm:ss.xxxxxx)
      timestamp = str(datetime.datetime.now())

      # Remove the milliseconds from the timestamp
      timestamp = timestamp.split('.')[0]

      # Fiddle around with the timestamp format
      timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%d%m%Y-%H:%M:%S")

      # Unified log file name format should now be k-cema-nnnnnn_ddmmyyyy-hh:mm:ss.log
      output_file = "k-cema-" + csm_serial_number + '_' + timestamp + '.log'

      # Unify the log files into a single output file
      create_unified_log(kLocalPath, output_file)
    else:
      print('No CSM serial number - Unable to create log file')

    # Delete the temporary directory
    shutil.rmtree(kLocalPath)

  except (paramiko.ssh_exception.SSHException,
          paramiko.ssh_exception.AuthenticationException,
          paramiko.ssh_exception.PasswordRequiredException,
          paramiko.sftp.SFTPError,
          pysftp.exceptions.ConnectionException,
          pysftp.exceptions.CredentialException,
          pysftp.exceptions.HostKeysException,
          OSError,
          FileNotFoundError,
          AttributeError) as e:
    print(e)

