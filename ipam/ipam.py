import serial
import crc


def reg_to_index_variant(reg):
    index = (reg >> 8) & 0xFFFF
    variant = reg & 0xFF
    if index > 9999:
        index = 9999
    if variant > 99:
        variant = 99
    return str(index).zfill(4) + "-" + str(variant).zfill(2)


def reg_to_revision(reg):
    rev = (reg >> 16) & 0xFF
    rev_alpha = "?"
    if rev <= 25:
        rev_alpha = chr(0x41 + rev)
    return rev_alpha


def reg_to_mod(reg):
    return str(((reg >> 24) & 0x7F) + 1)


def reg_to_serial(reg):
    return str(reg & 0xFFFF).zfill(6)


class Ipam:
    def __init__(self, port):
        # Serial port variable
        self.ser = serial.Serial(port, 1000000, timeout=1)

        # Factory settings variables
        self.bias_dac_channel_a = [0, 0, 0, 0, 0, 0, 0, 0]
        self.bias_dac_channel_b = [0, 0, 0, 0, 0, 0, 0, 0]
        self.aux_dac_channel_a = [0, 0, 0, 0]
        self.aux_dac_channel_b = [0, 0, 0, 0]
        self.rf_path_base_attenuation = 0
        #self.unit_part_number = 0

    def read(self, addr):
        val = -1
        # Create read command
        packet = bytearray(b'\x01')
        packet.append((addr >> 8) & 0xFF)
        packet.append(addr & 0xFF)
        # Calculate and append the CRC
        c = crc.crca(packet)
        packet.append((c >> 8) & 0xFF)
        packet.append(c & 0xFF)
        # Write the command to the serial port
        self.ser.write(packet)
        # Read the response from the serial port
        resp = bytearray(self.ser.read(7))
        # Check the response size
        if len(resp) == 0:
            print("ERROR: no response on serial port")
            quit()
        # Check the response CRC
        if crc.crca(resp) == 0:
            val = ((resp[1] << 24) & 0xFF000000) |\
                  ((resp[2] << 16) & 0x00FF0000) |\
                  ((resp[3] << 8) & 0x0000FF00) |\
                   (resp[4] & 0x000000FF)
        return val
        
    def write(self, addr, val):
        ret_val = False
        # Create write command
        packet = bytearray(b'\x00')
        packet.append((addr >> 8) & 0xFF)
        packet.append(addr & 0xFF)
        packet.append((val >> 24) & 0xFF)
        packet.append((val >> 16) & 0xFF)
        packet.append((val >> 8) & 0xFF)
        packet.append(val & 0xFF)
        # Calculate and append the CRC
        c = crc.crca(packet)
        packet.append((c >> 8) & 0xFF)
        packet.append(c & 0xFF)
        # Write the command to the serial port
        self.ser.write(packet)
        # Read the response from the serial port
        resp = bytearray(self.ser.read(7))
        # Check the response size
        if len(resp) == 0:
            print("ERROR: no response on serial port")
            quit()
        # Check the response CRC
        if crc.crca(resp) == 0:
            ret_val = True
        return ret_val

    def unlock_registers(self):
        ok = True
        # Reset the FPGA before attempting to unlock
        ok = ok and self.write(self.REG_RESTORE_DEFAULTS, 0)
        # Issue unlock command
        ok = ok and self.write(self.REG_READ_ONLY_WRITE_UNLOCK, 0x6709)
        # Read back to check that the unlock worked
        ok = ok and self.read(self.REG_READ_ONLY_WRITE_UNLOCK) == 0
        return ok

    def nvm_erase_block(self, addr):
        ok = True
        ok = ok and self.write(self.REG_NVM_ADDRESS, addr)
        ok = ok and self.write(self.REG_NVM_CONTROL_AND_STATUS, 0x80000000)
        wait_count = 0
        while ok:
            reg = self.read(self.REG_NVM_CONTROL_AND_STATUS)
            if reg == -1:
                ok = False
            elif reg & 0x1:
                wait_count += 1
            else:
                break
        return ok

    def nvm_write(self, addr, data):
        ok = True
        ok = ok and self.write(self.REG_NVM_ADDRESS, addr)
        ok = ok and self.write(self.REG_NVM_DATA, data)
        return ok

    def nvm_read(self, addr):
        ok = True
        ok = ok and self.write(self.REG_NVM_ADDRESS, addr)
        return self.read(self.REG_NVM_DATA)

    def get_factory_settings(self):
        ok = True

        # Read bias DACs
        ok = ok and self.write(self.FACTORY_SETTINGS_BIAS_DAC_0_CHANNEL_A, self.FACTORY_SETTINGS_BASE)
        for i in range(8):
            self.bias_dac_channel_a[i] = self.read(self.REG_NVM_DATA)
            self.bias_dac_channel_b[i] = self.read(self.REG_NVM_DATA)

        # Read aux DACs
        ok = ok and self.write(self.FACTORY_SETTINGS_AUX_DAC_0_CHANNEL_A, self.FACTORY_SETTINGS_BASE)
        for i in range(8):
            self.aux_dac_channel_a[i] = self.read(self.REG_NVM_DATA)
            self.aux_dac_channel_b[i] = self.read(self.REG_NVM_DATA)

        self.rf_path_base_attenuation = self.nvm_read(self.FACTORY_SETTINGS_RF_PATH_BASE_ATTENUATION)
        self.unit_part_number = self.nvm_read(self.FACTORY_SETTINGS_UNIT_PART_NUMBER)

    def set_factory_settings_crc(self):
        ok = True
        by = bytes()
        for addr in range(self.FACTORY_SETTINGS_BASE, self.FACTORY_SETTINGS_CRC, 4):
            data = self.nvm_read(addr)
            by += data.to_bytes(4, 'big')
        ba = bytearray(by)
        ba.append(0)
        ba.append(0)
        c = crc.crca(ba)
        print("Write factory settings CRC: " + hex(c))
        return self.nvm_write(self.FACTORY_SETTINGS_CRC, c)

    def check_factory_settings_crc(self):
        ok = False
        by = bytes()
        for addr in range(self.FACTORY_SETTINGS_BASE, self.FACTORY_SETTINGS_CRC + 4, 4):
            data = self.nvm_read(addr)
            by += data.to_bytes(4, 'big')

        return crc.crca(bytearray(by)) == 0

    def check_user_settings(self):
        return False

    def unit_type(self):
        unit_type = "Unknown"
        t = self.read(self.REG_UNIT_DETECTED_TYPE)
        # Check that this is a Kirintec IPAM
        if (t & 0x300) == 0x100:
            # Ignore bits 7:6, RF_ID which are "11" when RF board not attached, "00" when RF board attached
            t &= 0x3F
            if t == 0x00:
                unit_type = "IPAM-LB-100W"
            elif t == 0x01:
                unit_type = "IPAM-MB-100W"
            elif t == 0x02:
                unit_type = "IPAM-HB-50W"
            else:
                unit_type = "IPAM-<" + hex(t) + ">"
        else:
            unit_type = "<" + hex(t) + ">"
                
        return unit_type

    def unit_part_number(self):
        reg = self.read(self.REG_UNIT_PART_NUMBER)
        return "KT-950-" + reg_to_index_variant(reg)

    def control_part_number(self):
        reg = self.read(self.REG_CONTROL_PART_NUMBER)
        return "KT-950-" + reg_to_index_variant(reg)

    def rf_part_number(self):
        reg = self.read(self.REG_RF_PART_NUMBER)
        return "KT-950-" + reg_to_index_variant(reg)

    def unit_serial_number(self):
        reg = self.read(self.REG_UNIT_SERIAL_NUMBER_AND_REVISION)
        return reg_to_serial(reg)

    def control_serial_number(self):
        reg = self.read(self.REG_CONTROL_SERIAL_NUMBER_AND_REVISION)
        return reg_to_serial(reg)

    def rf_serial_number(self):
        reg = self.read(self.REG_RF_SERIAL_NUMBER_AND_REVISION)
        return reg_to_serial(reg)
        
    def unit_revision(self):
        reg = self.read(self.REG_UNIT_SERIAL_NUMBER_AND_REVISION)
        return reg_to_revision(reg)

    def control_revision(self):
        reg = self.read(self.REG_CONTROL_SERIAL_NUMBER_AND_REVISION)
        return reg_to_revision(reg)

    def rf_revision(self):
        reg = self.read(self.REG_RF_SERIAL_NUMBER_AND_REVISION)
        return reg_to_revision(reg)

    def unit_mod(self):
        reg = self.read(self.REG_UNIT_SERIAL_NUMBER_AND_REVISION)
        return reg_to_mod(reg)

    def control_mod(self):
        reg = self.read(self.REG_CONTROL_SERIAL_NUMBER_AND_REVISION)
        return reg_to_mod(reg)

    def rf_mod(self):
        reg = self.read(self.REG_RF_SERIAL_NUMBER_AND_REVISION)
        return reg_to_mod(reg)

    def firmware_version(self):
        reg = self.read(self.REG_FIRMWARE_VERSION)
        major = (reg >> 24) & 0xFF
        minor = (reg >> 8) & 0xFFFF
        patch = reg & 0xFF
        return str(major) + "." + str(minor) + "." + str(patch)
        
    def firmware_build_id(self):
        reg = self.read(self.REG_FIRMWARE_BUILD_ID)
        return format(reg, 'x').zfill(8)

    # Register Addresses
    REG_UNIT_DETECTED_TYPE = 0x0000
    REG_UNIT_PART_NUMBER = 0x0001
    REG_UNIT_SERIAL_NUMBER_AND_REVISION = 0x0002
    REG_CONTROL_PART_NUMBER = 0x0003
    REG_CONTROL_SERIAL_NUMBER_AND_REVISION = 0x0004
    REG_FIRMWARE_NUMBER = 0x0005
    REG_FIRMWARE_VERSION = 0x0006
    REG_FIRMWARE_BUILD_ID = 0x0007
    REG_RF_PART_NUMBER = 0x0008
    REG_RF_SERIAL_NUMBER_AND_REVISION = 0x0009
    REG_READ_ONLY_WRITE_UNLOCK = 0x0010
    REG_RESTORE_DEFAULTS = 0x0011
    REG_NVM_CONTROL_AND_STATUS = 0x0021
    REG_NVM_ADDRESS = 0x0022
    REG_NVM_DATA = 0x0023
    REG_PA_CONTROL_AND_STATUS = 0x005A
    REG_LED_CONTROL = 0xFFFD

    # Factory Settings NVM Addresses
    FACTORY_SETTINGS_BASE = 0x040000
    FACTORY_SETTINGS_BIAS_DAC_0_CHANNEL_A = 0x040000
    FACTORY_SETTINGS_BIAS_DAC_0_CHANNEL_B = 0x040004
    FACTORY_SETTINGS_BIAS_DAC_1_CHANNEL_A = 0x040008
    FACTORY_SETTINGS_BIAS_DAC_1_CHANNEL_B = 0x04000C
    FACTORY_SETTINGS_BIAS_DAC_2_CHANNEL_A = 0x040010
    FACTORY_SETTINGS_BIAS_DAC_2_CHANNEL_B = 0x040014
    FACTORY_SETTINGS_BIAS_DAC_3_CHANNEL_A = 0x040018
    FACTORY_SETTINGS_BIAS_DAC_3_CHANNEL_B = 0x04001C
    FACTORY_SETTINGS_BIAS_DAC_4_CHANNEL_A = 0x040020
    FACTORY_SETTINGS_BIAS_DAC_4_CHANNEL_B = 0x040024
    FACTORY_SETTINGS_BIAS_DAC_5_CHANNEL_A = 0x040028
    FACTORY_SETTINGS_BIAS_DAC_5_CHANNEL_B = 0x04002C
    FACTORY_SETTINGS_BIAS_DAC_6_CHANNEL_A = 0x040030
    FACTORY_SETTINGS_BIAS_DAC_6_CHANNEL_B = 0x040034
    FACTORY_SETTINGS_BIAS_DAC_7_CHANNEL_A = 0x040038
    FACTORY_SETTINGS_BIAS_DAC_7_CHANNEL_B = 0x04003C
    FACTORY_SETTINGS_AUX_DAC_0_CHANNEL_A = 0x040040
    FACTORY_SETTINGS_AUX_DAC_0_CHANNEL_B = 0x040044
    FACTORY_SETTINGS_AUX_DAC_1_CHANNEL_A = 0x040048
    FACTORY_SETTINGS_AUX_DAC_1_CHANNEL_B = 0x04004C
    FACTORY_SETTINGS_AUX_DAC_2_CHANNEL_A = 0x040050
    FACTORY_SETTINGS_AUX_DAC_2_CHANNEL_B = 0x040054
    FACTORY_SETTINGS_AUX_DAC_3_CHANNEL_A = 0x040058
    FACTORY_SETTINGS_AUX_DAC_3_CHANNEL_B = 0x04005C
    FACTORY_SETTINGS_RF_PATH_BASE_ATTENUATION = 0x040060
    FACTORY_SETTINGS_UNIT_PART_NUMBER = 0x040064
    FACTORY_SETTINGS_UNIT_REVISION_AND_SERIAL_NUMBER = 0x040068
    FACTORY_SETTINGS_CONTROL_BOARD_PART_NUMBER = 0x04006C
    FACTORY_SETTINGS_CONTROL_BOARD_SERIAL_NUMBER = 0x040070
    FACTORY_SETTINGS_RF_BOARD_PART_NUMBER = 0x040074
    FACTORY_SETTINGS_RF_BOARD_REVISION_AND_SERIAL_NUMBER = 0x040078
    FACTORY_SETTINGS_THERMAL_OVERLOAD_THRESHOLDS = 0x04007C
    FACTORY_SETTINGS_DUTY_CYCLE_THRESHOLD = 0x040080
    FACTORY_SETTINGS_PULSE_WIDTH_THRESHOLD = 0x040084
    FACTORY_SETTINGS_PRF_THRESHOLD = 0x040088
    FACTORY_SETTINGS_RETURN_LOSS_THRESHOLD = 0x04008C
    FACTORY_SETTINGS_CRC = 0x040090

    # User Settings NVM Addresses
    USER_SETTINGS_BASE = 0x050000
    USER_SETTINGS_RF_PATH_USER_ATTENUATION = 0x050000
    USER_SETTINGS_BIT_FLAG_MASK_LOWER_BLOCK = 0x050004
    USER_SETTINGS_BIT_FLAG_MASK_UPPER_BLOCK = 0x050008
    USER_SETTINGS_FORWARD_POWER_THRESHOLD = 0x05000C
    USER_SETTINGS_CRC = 0x050010

    # User Area NVM Address
    NVM_USER_AREA_BASE = 0x060000
