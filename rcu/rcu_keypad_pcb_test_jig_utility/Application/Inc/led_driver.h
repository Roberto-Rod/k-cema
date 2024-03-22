/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file led_driver.h
**
** Include file for led_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __LED_DRIVER_H
#define __LED_DRIVER_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>
#include "led_driver_common.h"

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


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ld_Init(	I2C_HandleTypeDef* i2c_device,
				GPIO_TypeDef* p_reset_pin_port,
				uint16_t reset_pin);
bool ld_SetAllLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour);
bool ld_SetLed(I2C_HandleTypeDef* i2c_device, int16_t index);
bool ld_SetMixLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t mix_start_colour);
bool ld_SetTypicalLeds(I2C_HandleTypeDef* i2c_device);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __LED_DRIVER_H */
