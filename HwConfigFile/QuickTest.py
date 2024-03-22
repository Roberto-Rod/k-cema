from intelhex import IntelHex
from PyCRC.CRCCCITT import CRCCCITT

ih = IntelHex()
ih.putsz(0x0, "My string\0")
ih.write_hex_file("HwConfigInfo1.hex")


ih = IntelHex()
ih.putsz(0x20, "Another string\0")
ih.write_hex_file("HwConfigInfo2.hex")

input = '123456789'
print("0x%x" % CRCCCITT(version="FFFF").calculate(input))

