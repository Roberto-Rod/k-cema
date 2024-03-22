/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file hw_config_info.c
*
* Driver for accessing Hardware Configuration Information stored in an NXP
* PCA9500 GPIO expander/EEPROM device.
*
* Project : N/A
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo Could be made generic by using a data structure to define I2C
* addresses and HAL driver handle.
*
******************************************************************************/
#define __HW_CONFIG_INFO_C

#include "hw_config_info.h"
#include "main.h"
#include <string.h>

/*****************************************************************************/
/**
* Reads hardware configuration information from the PCA9500 I2C device.  The
* CRC for information read from the device is calculated and compared to the
* CRC stored on the device to verify data integrity.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	p_hw_config_info pointer to data structure to receive information
* 			read from the PCA9500
* @return   true if data read from device, else false
* @note     None
*
******************************************************************************/
bool hci_ReadHwConfigInfo(	I2C_HandleTypeDef* 	i2c_device,
							hci_HwConfigInfo* 	p_hw_config_info)
{
	bool ret_val = true;
	uint16_t crc_calc = 0U;
	uint8_t buf = 0xFFU;

	/* PCA9500 IO pins are quasi-directional and need to be set high before
	 * they are read. */
	if (HAL_I2C_Master_Transmit(i2c_device, PCA9500_GPIO_I2C_ADDR, &buf, 1U, I2C_TIMEOUT) == HAL_OK)
	{
		if (HAL_I2C_Master_Receive(i2c_device, PCA9500_GPIO_I2C_ADDR, &buf, 1U, I2C_TIMEOUT) == HAL_OK)
		{
			p_hw_config_info->hw_version = buf & 0x1FU;
			p_hw_config_info->hw_mod_version = (buf & 0xE0U) >> 5;
		}
		else
		{
			ret_val = false;
		}
	}
	else
	{
		ret_val = false;
	}

	if (ret_val)
	{
		/* Read the contents of the PC9500 device */
		if (HAL_I2C_Mem_Read(	i2c_device,
								PCA9500_EEPROM_I2C_ADDR,
								0U, 1U,
								(uint8_t *)&lg_device_data,
								PCA9500_MEM_SIZE_BYTES,
								I2C_TIMEOUT)
				== HAL_OK)
		{
			memcpy(	&p_hw_config_info->assy_part_no,
					lg_device_data.assy_part_no, HCI_STR_PARAM_LEN);
			memcpy(	&p_hw_config_info->assy_rev_no,
					lg_device_data.assy_rev_no, HCI_STR_PARAM_LEN);
			memcpy(	&p_hw_config_info->assy_serial_no,
					lg_device_data.assy_serial_no, HCI_STR_PARAM_LEN);
			memcpy(	&p_hw_config_info->assy_build_date_batch_no,
					lg_device_data.assy_build_date_batch_no, HCI_STR_PARAM_LEN);

			p_hw_config_info->hci_version_no = lg_device_data.hci_version_no;
			p_hw_config_info->hci_crc = lg_device_data.hci_crc;

			crc_calc = hci_ComputeCRCCCITT(	(uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

			if (crc_calc == p_hw_config_info->hci_crc)
			{
				p_hw_config_info->hci_crc_valid = true;
			}
			else
			{
				p_hw_config_info->hci_crc_valid = false;
			}
		}
		else
		{
			ret_val = false;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Clears all the hardware config information to blank, sets version
* parameter to 1 and creates CRC
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_ResetHwConfigInfo(I2C_HandleTypeDef* i2c_device)
{
	bool ret_val = true;

	/* Clear out the local EEPROM data structure ready to write to device */
	memset((void *)&lg_device_data, '\0', PCA9500_MEM_SIZE_BYTES);
	lg_device_data.hci_version_no = 1U;
	lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
										PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

	ret_val = hci_WriteDeviceData(i2c_device, &lg_device_data);

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly part number in PCA9500 EEPROM:
* - Reads PCA9500 EEPROM
* - Modifies value
* - Calculates CRC
* - Writes modified data to PCA9500 EEPROM
*
* Assumes that the EEPROM has been initialised using hci_ResetHwConfigInfo()
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	assy_part_no pointer to null terminated string defining the assembly
* 			part number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyPartNo(I2C_HandleTypeDef* i2c_device, uint8_t* assy_part_no)
{
	bool ret_val = true;

	if (HAL_I2C_Mem_Read( 	i2c_device, PCA9500_EEPROM_I2C_ADDR, 0U, 1U,
							(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
							I2C_TIMEOUT)
			== HAL_OK)
	{
		memcpy(lg_device_data.assy_part_no, assy_part_no, HCI_STR_PARAM_LEN);

		lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

		ret_val = hci_WriteDeviceData(i2c_device, &lg_device_data);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly revision number in PCA9500 EEPROM:
* - Reads PCA9500 EEPROM
* - Modifies value
* - Calculates CRC
* - Writes modified data to PCA9500 EEPROM
*
* Assumes that the EEPROM has been initialised using hci_ResetHwConfigInfo()
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	assy_rev_no pointer to null terminated string defining the assembly
* 			revision number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyRevNo(I2C_HandleTypeDef* i2c_device, uint8_t* assy_rev_no)
{
	bool ret_val = true;

	if (HAL_I2C_Mem_Read( 	i2c_device, PCA9500_EEPROM_I2C_ADDR, 0U, 1U,
							(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
							I2C_TIMEOUT)
			== HAL_OK)
	{
		memcpy(lg_device_data.assy_rev_no, assy_rev_no, HCI_STR_PARAM_LEN);

		lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

		ret_val = hci_WriteDeviceData(i2c_device, &lg_device_data);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly serial number in PCA9500 EEPROM:
* - Reads PCA9500 EEPROM
* - Modifies value
* - Calculates CRC
* - Writes modified data to PCA9500 EEPROM
*
* Assumes that the EEPROM has been initialised using hci_ResetHwConfigInfo()
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	assy_serial_no pointer to null terminated string defining the assembly
* 			serial number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssySerialNo(I2C_HandleTypeDef* i2c_device, uint8_t* assy_serial_no)
{
	bool ret_val = true;

	if (HAL_I2C_Mem_Read( 	i2c_device, PCA9500_EEPROM_I2C_ADDR, 0U, 1U,
							(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
							I2C_TIMEOUT)
			== HAL_OK)
	{
		memcpy(lg_device_data.assy_serial_no, assy_serial_no, HCI_STR_PARAM_LEN);

		lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

		ret_val = hci_WriteDeviceData(i2c_device, &lg_device_data);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly build date/batch number in PCA9500 EEPROM:
* - Reads PCA9500 EEPROM
* - Modifies value
* - Calculates CRC
* - Writes modified data to PCA9500 EEPROM
*
* Assumes that the EEPROM has been initialised using hci_ResetHwConfigInfo()
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	assy_build_date_batch_no pointer to null terminated string defining
* 			the assembly build date/batch number, max string length is
* 			HCI_STR_PARAM_LEN including null terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyBuildDataBatchNo(	I2C_HandleTypeDef* i2c_device,
									uint8_t* assy_build_date_batch_no)
{
	bool ret_val = true;

	if (HAL_I2C_Mem_Read( 	i2c_device, PCA9500_EEPROM_I2C_ADDR, 0U, 1U,
							(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
							I2C_TIMEOUT)
			== HAL_OK)
	{
		memcpy(	lg_device_data.assy_build_date_batch_no,
				assy_build_date_batch_no, HCI_STR_PARAM_LEN);

		lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

		ret_val = hci_WriteDeviceData(i2c_device, &lg_device_data);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Writes device data structure to PCA9500 EEPROM using page writes to
* minimise programming time
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9500 is connected to
* @param	device_data pointer to data structure to write to EEPROM
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_WriteDeviceData(	I2C_HandleTypeDef* i2c_device,
							hci_HwConfigEepromData* device_data)
{
	uint16_t i = 0U;
	bool ret_val = true;

	for (i = 0U; i < PCA9500_MEM_SIZE_BYTES; i += PCA9500_PAGE_SIZE_BYES)
	{
		if (HAL_I2C_Mem_Write(	i2c_device,	PCA9500_EEPROM_I2C_ADDR,
								i, 1U,	&((uint8_t *)(device_data))[i],
								PCA9500_PAGE_SIZE_BYES,	I2C_TIMEOUT) != HAL_OK)
		{
			ret_val = false;
		}

		HAL_Delay(PCAA9500_WRITE_TIME_MS);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Computes CRC using HCI algorithm, CRC-16 CCITT The CRC-16 CCITT, initial
* value of 0xFFFF and polynomial of 0x1021; the ASCII string "123456789"
* generates the checksum 0x29B1
*
* @param    message point to input data
* @paran 	msg_length length of input data
* @return   Calculated CRC-16 CCITT value
* @note     None
*
******************************************************************************/
uint16_t hci_ComputeCRCCCITT(uint8_t* message, uint16_t msg_length)
{
	uint16_t i, b;
	int16_t remainder = 0xFFFF;

	for (i = 0U; i < msg_length; ++i)
	{
		remainder ^= (message[i] & 0xFFU) << 8;   /* <<CRC_WIDTH - 8 */

		for (b = 0U; b < 8U; ++b)
		{
			if (remainder & 0x8000)
			{
				remainder = (remainder << 1) ^ 0x1021;
			}
        	else
        	{
        		remainder = (remainder << 1);
        	}
		}
   }

   return (uint16_t)((remainder ^ 0x0000) & 0xFFFF);
}
