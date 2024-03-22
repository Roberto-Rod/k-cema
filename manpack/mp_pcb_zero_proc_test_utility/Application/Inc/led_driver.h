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
#define LD_I2C_TIMEOUT				100U
#define LD_NO_LEDS					30
#define LD_NO_LED_COLOURS			4	/* Including OFF */

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
	uint16_t			dev0_i2c_address;
	uint16_t			dev1_i2c_address;
	GPIO_TypeDef 		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	bool 				initialised;
} td_LedDriver_t;

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
bool ld_InitInstance(	td_LedDriver_t *p_inst,
						I2C_HandleTypeDef *i2c_device,
						uint16_t dev0_i2c_address,
						uint16_t dev1_i2c_address,
						GPIO_TypeDef *i2c_reset_gpio_port,
						uint16_t i2c_reset_gpio_pin);
bool ld_InitDevice(td_LedDriver_t *p_inst);
bool ld_SetAllLeds(td_LedDriver_t *p_inst, ld_Colours_t colour);
bool ld_SetLed(td_LedDriver_t *p_inst, int16_t index);
bool ld_SetMixLeds(td_LedDriver_t *p_inst, ld_Colours_t mix_start_colour);
const char **ld_GetLedColourNames(void);

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

#define LD_MCP23017_DEV0			0
#define LD_MCP23017_DEV1			1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef struct
{
	int16_t			gpio_device;
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
	{LD_MCP23017_DEV0, ld_Green, 6U},
	{LD_MCP23017_DEV0, ld_Yellow, 5U},
	{LD_MCP23017_DEV0, ld_Red, 4U},
	{LD_MCP23017_DEV0, ld_Green, 10U},
	{LD_MCP23017_DEV0, ld_Yellow, 9U},
	{LD_MCP23017_DEV0, ld_Red, 8U},
	{LD_MCP23017_DEV1, ld_Green, 14U},
	{LD_MCP23017_DEV1, ld_Yellow, 13U},
	{LD_MCP23017_DEV1, ld_Red, 12U},
	{LD_MCP23017_DEV1, ld_Green, 2U},
	{LD_MCP23017_DEV1, ld_Yellow, 1U},
	{LD_MCP23017_DEV1, ld_Red, 0U},
	{LD_MCP23017_DEV0, ld_Green, 2U},
	{LD_MCP23017_DEV0, ld_Yellow, 1U},
	{LD_MCP23017_DEV0, ld_Red, 3U},
	{LD_MCP23017_DEV0, ld_Green, 14U},
	{LD_MCP23017_DEV0, ld_Yellow, 15U},
	{LD_MCP23017_DEV0, ld_Red, 0U},
	{LD_MCP23017_DEV0, ld_Green, 11U},
	{LD_MCP23017_DEV0, ld_Yellow, 12U},
	{LD_MCP23017_DEV0, ld_Red, 13U},
	{LD_MCP23017_DEV1, ld_Green, 10U},
	{LD_MCP23017_DEV1, ld_Yellow, 9U},
	{LD_MCP23017_DEV1, ld_Red, 11U},
	{LD_MCP23017_DEV1, ld_Green, 7U},
	{LD_MCP23017_DEV1, ld_Yellow, 6U},
	{LD_MCP23017_DEV1, ld_Red, 8U},
	{LD_MCP23017_DEV1, ld_Green, 4U},
	{LD_MCP23017_DEV1, ld_Yellow, 3U},
	{LD_MCP23017_DEV1, ld_Red, 5U}
};

const char *lg_ld_led_colour_names[LD_NO_LED_COLOURS] = \
{
	"OFF",
	"GREEN",
	"RED",
	"YELLOW"
};

#endif /* __HW_CONFIG_INFO_C */

#endif /* __HW_CONFIG_INFO_H */
