/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file led_driver_common.h
**
** Common include file for LED drivers.
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __LED_DRIVER_COMMON_H
#define __LED_DRIVER_COMMON_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define LD_I2C_TIMEOUT				100U
#define LD_NO_LEDS					30U

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
typedef enum
{
	ld_Off = 0,
	ld_Green,
	ld_Red,
	ld_Yellow
}ld_Colours_t;

typedef struct ld_Led
{
	uint8_t			i2c_addr;
	ld_Colours_t	colour;
	uint16_t		pin;
} ld_Led_t;

typedef bool (*ld_SetAllLeds_t)(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour);

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/


/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __LED_DRIVER_COMMON_H */
