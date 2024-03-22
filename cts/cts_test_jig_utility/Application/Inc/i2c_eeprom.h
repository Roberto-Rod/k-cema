/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
**
** @file i2c_eeprom.h
**
** Include file for i2c_eeprom.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __HW_I2C_EEPROM_H
#define __HW_I2C_EEPROM_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/


/*****************************************************************************
*
*  Global Macros
*
*****************************************************************************/


/*****************************************************************************
*
*  Global Datatypes
*
*****************************************************************************/
typedef struct
{
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	uint16_t 			address_len;
	uint16_t			mem_size_bytes;
	uint16_t			page_size_bytes;
	uint32_t			write_time_ms;
	bool 				initialised;
} iee_DeviceInfo_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void iee_Init(iee_DeviceInfo_t *p_inst,
		      I2C_HandleTypeDef* i2c_device,
		      uint16_t i2c_address,
			  uint16_t address_len,
		      uint16_t mem_size_bytes,
		      uint16_t page_size_bytes,
		      uint32_t write_time_ms);
bool iee_WriteByte(iee_DeviceInfo_t *p_inst, uint16_t address, uint8_t data);
bool iee_ReadByte(iee_DeviceInfo_t *p_inst, uint16_t address, uint8_t *p_data);
bool iee_ReadPage(iee_DeviceInfo_t *p_inst, uint16_t page_address, uint8_t *p_data);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __HW_I2C_EEPROM_H */
