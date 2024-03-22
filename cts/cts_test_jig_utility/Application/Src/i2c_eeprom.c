/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
*
* @file hw_config_info.c
*
* Generic driver for reading and writing an I2C EEPROM device.
*
* Project : N/A
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "i2c_eeprom.h"
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define IEE_I2C_TIMEOUT				100U

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Functions
*
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


/*****************************************************************************/
/**
* Initialise the driver instance.
*
* @param    p_inst pointer to I2C EEPROM driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			GPIO expanders are connected to
* @param	i2c_address 7-bit I2C bus address
* @param	address_len number of byte used to represent memeory address
* @param	mem_size_bytes size of the EEPROM device in bytes
* @param	page_size_bytes page size of the EEPROM device in bytes
* @param	write_time_ms EEPROM device write cycle time in ms
*
******************************************************************************/
void iee_Init(iee_DeviceInfo_t *p_inst,
		      I2C_HandleTypeDef* i2c_device,
		      uint16_t i2c_address,
			  uint16_t address_len,
		      uint16_t mem_size_bytes,
		      uint16_t page_size_bytes,
		      uint32_t write_time_ms)
{
	/* Just need to copy data back to the driver instance and flag it as initialised */
	p_inst->i2c_device = i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->address_len = address_len;
	p_inst->mem_size_bytes = mem_size_bytes;
	p_inst->page_size_bytes = page_size_bytes;
	p_inst->write_time_ms = write_time_ms;
	p_inst->initialised = true;
}


/*****************************************************************************/
/**
* Write a byte to the EEPROM device, this function is blocking and will return
* once the I2C bus transaction is complete.
*
* @param    p_inst pointer to I2C EEPROM driver instance data
* @param	address memory address to write to
* @param 	data value to write to the I2C EEPROM
*
******************************************************************************/
bool iee_WriteByte(iee_DeviceInfo_t *p_inst, uint16_t address, uint8_t data)
{
	bool ret_val = false;

	if (p_inst->initialised && (address >= 0U) && (address <= p_inst->mem_size_bytes))
	{
		ret_val = (HAL_I2C_Mem_Write(p_inst->i2c_device, p_inst->i2c_address, address, p_inst->address_len, &data, 1U, IEE_I2C_TIMEOUT) == HAL_OK);

		if (ret_val)
		{
			HAL_Delay(p_inst->write_time_ms);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read a byte from the EEPROM device, this function is blocking and will return
* once the I2C bus transaction is complete.
*
* @param    p_inst pointer to I2C EEPROM driver instance data
* @param	address memory address to read from
* @param 	p_data variable to receive value read from the I2C EEPROM
*
******************************************************************************/
bool iee_ReadByte(iee_DeviceInfo_t *p_inst, uint16_t address, uint8_t *p_data)
{
	bool ret_val = false;

	if (p_inst->initialised && (address >= 0U) && (address <= p_inst->mem_size_bytes))
	{
		ret_val = (HAL_I2C_Mem_Read(p_inst->i2c_device, p_inst->i2c_address, address, p_inst->address_len, p_data, 1U, IEE_I2C_TIMEOUT) == HAL_OK);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read a page of data from the EEPROM device, this function is blocking and
* will return once the I2C bus transaction is complete.
*
* @param    p_inst pointer to I2C EEPROM driver instance data
* @param	page_address start memory address of page to read
* @param 	p_data buffer to receive page data read from the I2C EEPROM, must be
* 			the greater than or equal to the size of a page.
*
******************************************************************************/
bool iee_ReadPage(iee_DeviceInfo_t *p_inst, uint16_t page_address, uint8_t *p_data)
{
	bool ret_val = false;

	if (p_inst->initialised && (page_address >= 0U) && (page_address <= p_inst->mem_size_bytes))
	{
		/* Align page address to page size boundary */
		uint8_t aligned_page_address = page_address & ~(p_inst->page_size_bytes - 1);
		ret_val = (HAL_I2C_Mem_Read(p_inst->i2c_device, p_inst->i2c_address, aligned_page_address, p_inst->address_len, p_data, p_inst->page_size_bytes, IEE_I2C_TIMEOUT) == HAL_OK);
	}

	return ret_val;
}

