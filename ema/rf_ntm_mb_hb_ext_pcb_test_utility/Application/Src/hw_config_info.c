/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
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
******************************************************************************/
#include "hw_config_info.h"
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define HCI_CRC_LEN		2U

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
static bool hci_WriteDeviceData(	hci_HwConfigInfo_t *p_inst,
							hci_HwConfigEepromData_t *device_data);
static uint16_t hci_ComputeCRCCCITT(uint8_t *message, uint16_t msg_length);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static hci_HwConfigEepromData_t lg_device_data;

/*****************************************************************************/
/**
* Initialise the hardware configuration information driver instance
*
* @param    p_inst pointer to HCI driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			GPIO expanders are connected to
* @param	i2c_reset_gpio_port HAL driver GPIO port for GPIO expander reset
* @param	i2c_reset_gpio_pin HAL driver GPIO pin for GPIO expander reset
* @return   None
* @note     None
*
******************************************************************************/
void hci_Init(	hci_HwConfigInfo_t 	*p_inst,
				I2C_HandleTypeDef	*i2c_device,
				uint16_t			i2c_gpio_address,
				uint16_t			i2c_mem_address)
{
	/* Just need to copy data back to the driver instance and flag driver
	 * as initialised */
	p_inst->i2c_device			= i2c_device;
	p_inst->i2c_gpio_address	= i2c_gpio_address;
	p_inst->i2c_mem_address		= i2c_mem_address;

	p_inst->initialised = true;
}


/*****************************************************************************/
/**
* Reads hardware configuration information from the PCA9500 I2C device.  The
* CRC for information read from the device is calculated and compared to the
* CRC stored on the device to verify data integrity.
*
* @param    p_inst pointer to HCI driver instance data
* @param	p_hw_config_info pointer to data structure to receive information
* 			read from the PCA9500
* @return   true if data read from device, else false
* @note     None
*
******************************************************************************/
bool hci_ReadHwConfigInfo(	hci_HwConfigInfo_t		*p_inst,
							hci_HwConfigInfoData_t	*p_hw_config_info)
{
	bool ret_val = true;
	uint16_t crc_calc = 0U;
	uint8_t buf = 0xFFU;

	if (p_inst->initialised)
	{
		if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_gpio_address,
									&buf, 1U, I2C_TIMEOUT) == HAL_OK)
		{
			if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_gpio_address,
										&buf, 1U, I2C_TIMEOUT) == HAL_OK)
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
			if (HAL_I2C_Mem_Read(	p_inst->i2c_device,
									p_inst->i2c_mem_address,
									0U, 1U,
									(uint8_t *)&lg_device_data,
									PCA9500_MEM_SIZE_BYTES,
									I2C_TIMEOUT) == HAL_OK)
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
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Clears all the hardware config information to blank, sets version
* parameter to 1 and creates CRC
*
* @param    p_inst pointer to HCI driver instance data
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_ResetHwConfigInfo(hci_HwConfigInfo_t *p_inst)
{
	bool ret_val = true;

	if (p_inst->initialised)
	{
		/* Clear out the local EEPROM data structure ready to write to device */
		memset((void *)&lg_device_data, '\0', PCA9500_MEM_SIZE_BYTES);
		lg_device_data.hci_version_no = 1U;
		lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
											PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

		ret_val = hci_WriteDeviceData(p_inst, &lg_device_data);
	}
	else
	{
		ret_val = false;
	}

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
* @param    p_inst pointer to HCI driver instance data
* @param	assy_part_no pointer to null terminated string defining the assembly
* 			part number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyPartNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_part_no)
{
	bool ret_val = true;

	if (p_inst->initialised)
	{
		if (HAL_I2C_Mem_Read( 	p_inst->i2c_device, p_inst->i2c_mem_address, 0U, 1U,
								(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
								I2C_TIMEOUT) == HAL_OK)
		{
			memcpy(lg_device_data.assy_part_no, assy_part_no, HCI_STR_PARAM_LEN);

			lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
												PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

			ret_val = hci_WriteDeviceData(p_inst, &lg_device_data);
		}
	}
	else
	{
		ret_val = false;
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
* @param    p_inst pointer to HCI driver instance data
* @param	assy_rev_no pointer to null terminated string defining the assembly
* 			revision number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyRevNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_rev_no)
{
	bool ret_val = true;

	if (p_inst->initialised)
	{
		if (HAL_I2C_Mem_Read( 	p_inst->i2c_device, p_inst->i2c_mem_address, 0U, 1U,
								(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
								I2C_TIMEOUT) == HAL_OK)
		{
			memcpy(lg_device_data.assy_rev_no, assy_rev_no, HCI_STR_PARAM_LEN);

			lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
												PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

			ret_val = hci_WriteDeviceData(p_inst, &lg_device_data);
		}
	}
	else
	{
		ret_val = false;
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
* @param    p_inst pointer to HCI driver instance data
* @param	assy_serial_no pointer to null terminated string defining the assembly
* 			serial number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssySerialNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_serial_no)
{
	bool ret_val = true;

	if (p_inst->initialised)
	{
		if (HAL_I2C_Mem_Read( 	p_inst->i2c_device, p_inst->i2c_mem_address, 0U, 1U,
								(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
								I2C_TIMEOUT) == HAL_OK)
		{
			memcpy(lg_device_data.assy_serial_no, assy_serial_no, HCI_STR_PARAM_LEN);

			lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
												PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

			ret_val = hci_WriteDeviceData(p_inst, &lg_device_data);
		}
	}
	else
	{
		ret_val = false;
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
* @param    p_inst pointer to HCI driver instance data
* @param	assy_build_date_batch_no pointer to null terminated string defining
* 			the assembly build date/batch number, max string length is
* 			HCI_STR_PARAM_LEN including null terminator
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
bool hci_SetAssyBuildDataBatchNo(	hci_HwConfigInfo_t *p_inst,
									uint8_t *assy_build_date_batch_no)
{
	bool ret_val = true;

	if (p_inst->initialised)
	{
		if (HAL_I2C_Mem_Read( 	p_inst->i2c_device, p_inst->i2c_mem_address, 0U, 1U,
								(uint8_t *)&lg_device_data, PCA9500_MEM_SIZE_BYTES,
								I2C_TIMEOUT) == HAL_OK)
		{
			memcpy(	lg_device_data.assy_build_date_batch_no,
					assy_build_date_batch_no, HCI_STR_PARAM_LEN);

			lg_device_data.hci_crc = hci_ComputeCRCCCITT((uint8_t *)&lg_device_data,
												PCA9500_MEM_SIZE_BYTES - HCI_CRC_LEN);

			ret_val = hci_WriteDeviceData(p_inst, &lg_device_data);
		}
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Writes device data structure to PCA9500 EEPROM using page writes to
* minimise programming time
*
* @param    p_inst pointer to HCI driver instance data
* @param	device_data pointer to data structure to write to EEPROM
* @return   true if data written to device, else false
* @note     None
*
******************************************************************************/
static bool hci_WriteDeviceData(	hci_HwConfigInfo_t *p_inst,
							hci_HwConfigEepromData_t *device_data)
{
	uint16_t i = 0U;
	bool ret_val = true;

	for (i = 0U; i < PCA9500_MEM_SIZE_BYTES; i += PCA9500_PAGE_SIZE_BYES)
	{
		if (HAL_I2C_Mem_Write(	p_inst->i2c_device, p_inst->i2c_mem_address,
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
static uint16_t hci_ComputeCRCCCITT(uint8_t *message, uint16_t msg_length)
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
