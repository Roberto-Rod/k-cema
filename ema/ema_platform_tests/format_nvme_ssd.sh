#!/bin/bash

# Unmount the SSD if it is currently mounted
/bin/umount /dev/nvme0n1

# Wipe existing file systems and signatures
/usr/sbin/wipefs -a /dev/nvme0n1

# Use fdisk to create a single Linux partition spanning the entire disk
# pipe the series of command characters into fdisk, the comments below are
# stripped and not piped to fdisk
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | /sbin/fdisk /dev/nvme0n1
  o # clear the in-memory partition table
  n # new partition
  p # primary partition
  1 # partition number 1
    # default - start at beginning of disk
    # default - extend to end of disk
  w # write the partition table
  q # exit fdisk
EOF

# Use mkfs to make an ext4 filesystem on the partition
echo 'y' | /sbin/mkfs.ext4 /dev/nvme0n1
