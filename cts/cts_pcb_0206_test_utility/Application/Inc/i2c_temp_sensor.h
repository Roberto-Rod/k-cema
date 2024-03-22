/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file i2c_temp_sensor.h
**
** Include file for i2c_temp_sensor.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_TEMP_SENSOR_H
#define __I2C_TEMP_SENSOR_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32f4xx_hal.h"
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
typedef struct its_I2cTempSensor
{
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	bool 				initialised;
} its_I2cTempSensor_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool its_Init(its_I2cTempSensor_t  *p_inst, I2C_HandleTypeDef *p_i2c_device, uint16_t i2c_address);
bool its_ReadTemperature(its_I2cTempSensor_t *p_inst, int16_t *p_temp);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __I2C_TEMP_SENSOR_H */
