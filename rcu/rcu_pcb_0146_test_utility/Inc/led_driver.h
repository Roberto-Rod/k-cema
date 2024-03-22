/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
#include "stm32l0xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define LD_MCP23017_DEV0_I2C_ADDR	0x20U << 1
#define LD_MCP23017_DEV1_I2C_ADDR	0x21U << 1
#define LD_I2C_TIMEOUT				100U
#define LD_NO_LEDS					30U

/* Definitions specific to the KT-000-0165-00 board */
#define LD_NO_0165_LEDS				3U
#define LD_0165_GREEN_LED_IDX		12
#define LD_0165_YELLOW_LED_IDX		13
#define LD_0165_RED_LED_IDX			17

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

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void ld_Init(I2C_HandleTypeDef* i2c_device);
void ld_Init0165(I2C_HandleTypeDef* i2c_device);
void ld_SetAllLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour);
void ld_SetLed(I2C_HandleTypeDef* i2c_device, int16_t index);
void ld_SetLed0165(I2C_HandleTypeDef* i2c_device, int16_t index);
void ld_SetMixLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t mix_start_colour);
void ld_SetTypicalLeds(I2C_HandleTypeDef* i2c_device);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


/*****************************************************************************
*
*  Local to the C file
*
*****************************************************************************/
#ifdef __LED_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define LD_MCP23017_IODIR_REG_ADDR	0x00U
#define LD_MCP23017_GPIO_REG_ADDR	0x12U

#define LD_MCP23017_WR_LEN			3U
#define LD_MCP23017_RD_LEN			2U

#define LD_TYPICAL_MODE_NO_LEDS		5

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef struct
{
	uint8_t			i2c_addr;
	ld_Colours_t	colour;
	uint16_t		pin;
}ld_Led;


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
ld_Led lg_ld_leds[LD_NO_LEDS] = {
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 6U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 5U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Red, 4U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 10U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 9U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Red, 8U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 14U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Yellow, 13U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 12U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 2U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Yellow, 1U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 0U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 2U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 1U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Red, 3U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 14U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 15U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Red, 0U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 11U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 12U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Red, 13U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 10U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Yellow, 9U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 11U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 7U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Yellow, 6U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 8U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 4U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Yellow, 3U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 5U}
};

/* List of LEDs indexes to turn on in typical mode */
ld_Led lg_ld_leds_typical_mode[LD_TYPICAL_MODE_NO_LEDS] = {
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 6U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 9U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 12U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 2U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 10U}
};

#endif /* __HW_CONFIG_INFO_C */

#endif /* __HW_CONFIG_INFO_H */
