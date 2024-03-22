from serial import Serial
import time

sp = Serial("COM13", 115200, timeout=10, xonxoff=False, rtscts=False, dsrdtr=False)

input("Loop P11 Pin to Pin 7 and load the SoM Configuration MicroSD card into J4 <Enter>")

print(sp.read_until(b"Hit any key to stop autoboot:").decode("utf-8"))
sp.write(b"\r")
time.sleep(1)

sp.write(b"fatload mmc 0 0x10000000 system.bin\r")
print(sp.read_until(b"K-CEMA-CSM>").decode("utf-8"))
time.sleep(1)

sp.write(b"fpga load 0 0x10000000 4045564\r")
print(sp.read_until(b"K-CEMA-CSM>").decode("utf-8"))
time.sleep(1)

sp.timeout = 60
sp.write(b"boot\r")
print(sp.read_until(b"login:").decode("utf-8"))
sp.timeout = 10
time.sleep(1)

sp.write(b"root\r")
print(sp.read_until(b"Password:").decode("utf-8"))
time.sleep(1)

sp.write(b"root\r")
print(sp.read_until(b"root@CSM-").decode("utf-8"))
time.sleep(1)

sp.write(b"cd /run/media/mmcblk0p1\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"flashcp -v boot.bin /dev/mtd8\r")
print(sp.read_until(b"Verifying data: 566k/566k (100%)").decode("utf-8"))
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"fdisk /dev/mmcblk1\r")
print(sp.read_until(b"Command (m for help):").decode("utf-8"))
time.sleep(1)

# Need to add a delete path for previously formatted device here...
sp.write(b"n\r")
print(sp.read_until(b"Select (default p):").decode("utf-8"))
time.sleep(1)

sp.write(b"p\r")
print(sp.read_until(b"Select (default p):").decode("utf-8"))
time.sleep(1)

sp.write(b"1\r")
print(sp.read_until(b"First sector (2048-7520255, default 2048):").decode("utf-8"))
time.sleep(1)

sp.write(b"\r")
print(sp.read_until(b"Last sector, +sectors or +size{K,M,G,T,P} (2048-7520255, default 7520255):").decode("utf-8"))
time.sleep(1)

sp.write(b"+128M\r")
print(sp.read_until(b"Created a new partition 1 of type 'Linux' and of size 128 MiB.").decode("utf-8"))
print(sp.read_until(b"Command (m for help):").decode("utf-8"))
time.sleep(1)

sp.write(b"n\r")
print(sp.read_until(b"Select (default p):").decode("utf-8"))
time.sleep(1)

sp.write(b"p\r")
print(sp.read_until(b"Select (default p):").decode("utf-8"))
time.sleep(1)

sp.write(b"2\r")
print(sp.read_until(b"First sector (264192-7520255, default 264192):").decode("utf-8"))
time.sleep(1)

sp.write(b"\r")
print(sp.read_until(b"Last sector, +sectors or +size{K,M,G,T,P} (264192-7520255, default 7520255):").decode("utf-8"))
time.sleep(1)

sp.write(b"\r")
print(sp.read_until(b"Created a new partition 2 of type 'Linux' and of size 3.5 GiB").decode("utf-8"))
print(sp.read_until(b"Command (m for help):").decode("utf-8"))
time.sleep(1)

sp.write(b"w\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"partprobe /dev/mmcblk1\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"mkfs.vfat /dev/mmcblk1p1\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"mount /dev/mmcblk1p1 /tmp\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"cp system.bin /tmp/system.bin\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"umount /tmp\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"mkfs.ext4 /dev/mmcblk1p2\r")
print(sp.read_until(b"Writing superblocks and filesystem accounting information: done").decode("utf-8"))
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"mkfs.ext4 /dev/mmcblk1p2\r")
print(sp.read_until(b"EXT4-fs (mmcblk1p2): mounted filesystem with ordered data mode. Opts: (null)").decode("utf-8"))
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"mount /dev/mmcblk1p2 /tmp\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"cp csm_p2.tgz /tmp/csm_p2.tgz\r")
print(sp.read_until(b":/run/media/mmcblk0p1#").decode("utf-8"))
time.sleep(1)

sp.write(b"cd /tmp\r")
print(sp.read_until(b":/tmp#"))
time.sleep(1)

sp.write(b"tar -xvzf -C /tmp sm_p2.tgz\r")
print(sp.read_until(b":/tmp#").decode("utf-8"))
time.sleep(1)

sp.write(b"cd /\r")
print(sp.read_until(b":/#").decode("utf-8"))
time.sleep(1)

sp.write(b"umount /tmp\r")
print(sp.read_until(b":/#").decode("utf-8"))
time.sleep(1)

input("Remove the P11 loopback and the MicroSD card<Enter>")

sp.timeout = 60
sp.write(b"reboot -f\r")
print(sp.read_until(b"K-CEMA-CSM>").decode("utf-8"))
sp.timeout = 10
time.sleep(1)

# Set the environment variables






sp.timeout = 60
sp.write(b"reset\r")
print(sp.read_until(b"login:"))
sp.timeout = 10
time.sleep(1)


