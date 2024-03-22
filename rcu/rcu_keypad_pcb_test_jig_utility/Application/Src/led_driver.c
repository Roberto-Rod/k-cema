/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file led_driver.c
*
* Driver for the KT-000-0147-00 LEDs, turns LEDs on/off using Microchip
* MCP23017 I2C GPIO expanders
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo Could be made more generic using an initialisation structure
*
******************************************************************************/
#define __LED_DRIVER_C

#include "led_driver.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define LD_MCP23017_DEV0_I2C_ADDR	0x20U << 1
#define LD_MCP23017_DEV1_I2C_ADDR	0x21U << 1

#define LD_MCP23017_IODIR_REG_ADDR	0x00U
#define LD_MCP23017_GPIO_REG_ADDR	0x12U

#define LD_MCP23017_WR_LEN			3U

#define LD_TYPICAL_MODE_NO_LEDS		5

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


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
ld_Led_t lg_ld_leds[LD_NO_LEDS] = {
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
ld_Led_t lg_ld_leds_typical_mode[LD_TYPICAL_MODE_NO_LEDS] = {
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 6U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Yellow, 9U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Red, 12U},
	{LD_MCP23017_DEV0_I2C_ADDR, ld_Green, 2U},
	{LD_MCP23017_DEV1_I2C_ADDR, ld_Green, 10U}
};

/*****************************************************************************/
/**
* Initialises the MCP23017 GPIO expanders on the -0147 board.  Sets all GPIO
* pins as outputs and all LEDs off.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param	p_reset_pin_port GPIO port that the I2C device reset pin is
* 			attached to
* @param	reset_pin GPIO pin that the I2C device reset signal is attached to
* @return   true if the MCP23017 initialisation is successful, else false
*
******************************************************************************/
bool ld_Init(	I2C_HandleTypeDef* i2c_device,
				GPIO_TypeDef* p_reset_pin_port,
				uint16_t reset_pin)
{
	bool ret_val;
	uint8_t buf[LD_MCP23017_WR_LEN];

	HAL_GPIO_WritePin(p_reset_pin_port, reset_pin, GPIO_PIN_SET);

	ret_val = ld_SetAllLeds(i2c_device, ld_Off);

	/* Set all the GPIO pins as outputs */
	buf[0] = LD_MCP23017_IODIR_REG_ADDR;
	buf[1] = 0U;
	buf[2] = 0U;

	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);

	return ret_val;
}

/*****************************************************************************/
/**
* Sets all the LEDs to the specified colour or off
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param 	colour one of ld_Colours_t enumerated values
* @return   true if LEDs set, else false
*
******************************************************************************/
bool ld_SetAllLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour)
{
	bool ret_val;
	uint8_t buf_dev0[LD_MCP23017_WR_LEN], buf_dev1[LD_MCP23017_WR_LEN];
	uint16_t dev0_gpo = 0xFF7FU, dev1_gpo = 0xFFFFU, i;

	buf_dev0[0] = LD_MCP23017_GPIO_REG_ADDR;
	buf_dev1[0] = LD_MCP23017_GPIO_REG_ADDR;

	if (colour == ld_Off)
	{
		buf_dev0[1] = 0x7FU;
		buf_dev0[2] = 0xFFU;

		buf_dev1[1] = 0xFFU;
		buf_dev1[2] = 0xFFU;
	}
	else
	{
		for (i = 0; i < LD_NO_LEDS; ++i)
		{
			if ((lg_ld_leds[i].colour == colour) &&
				(lg_ld_leds[i].i2c_addr == LD_MCP23017_DEV0_I2C_ADDR))
			{
				dev0_gpo &= (~(1 << lg_ld_leds[i].pin));
			}
			else if ((lg_ld_leds[i].colour == colour) &&
					(lg_ld_leds[i].i2c_addr == LD_MCP23017_DEV1_I2C_ADDR))
			{
				dev1_gpo &= (~(1 << lg_ld_leds[i].pin));
			}
			else
			{
			}
		}

		buf_dev0[1] = (uint8_t)(dev0_gpo & 0xFFU);
		buf_dev0[2] = (uint8_t)((dev0_gpo >> 8) & 0xFFU);

		buf_dev1[1] = (uint8_t)(dev1_gpo & 0xFFU);
		buf_dev1[2] = (uint8_t)((dev1_gpo >> 8) & 0xFFU);
	}

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)  == HAL_OK);

	return ret_val;
}

/*****************************************************************************/
/**
* Turn an  individual LED on, all other LEDs are turned off
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param	index LED to turn on
* @return   true if LED set, else false
*
******************************************************************************/
bool ld_SetLed(I2C_HandleTypeDef* i2c_device, int16_t index)
{
	bool ret_val;
	uint8_t set_buf[LD_MCP23017_WR_LEN], clear_buf[LD_MCP23017_WR_LEN];
	uint16_t gpo;

	set_buf[0] = LD_MCP23017_GPIO_REG_ADDR;
	clear_buf[0] = LD_MCP23017_GPIO_REG_ADDR;

	if (lg_ld_leds[index].i2c_addr == LD_MCP23017_DEV0_I2C_ADDR)
	{
		gpo = 0xFF7FU;
		clear_buf[1] = 0xFFU;
		clear_buf[2] = 0xFFU;
	}
	else
	{
		gpo = 0xFFFFU;
		clear_buf[1] = 0x7FU;
		clear_buf[2] = 0xFFU;
	}

	gpo &= (~(1 << lg_ld_leds[index].pin));
	set_buf[1] = (uint8_t)(gpo & 0xFFU);
	set_buf[2] = (uint8_t)((gpo >> 8) & 0xFFU);

	if (lg_ld_leds[index].i2c_addr == LD_MCP23017_DEV0_I2C_ADDR)
	{
		ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
											clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
		ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
											set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	}
	else
	{
		ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
											clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
		ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
											set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets the LEDs such that one LED from each device is on in the repeating
* pattern Red/Green/Yellow.  The first colour in the pattern is specified in the
* function call.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param	mix_start_colour colour of the first LED device, one of
* 			ld_Colours_t enumerated values: ld_Green, ld_Red, ld_Yellow
* @return   true if LEDs set, else false
*
******************************************************************************/
bool ld_SetMixLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t mix_start_colour)
{
	bool ret_val;
	uint8_t buf_dev0[LD_MCP23017_WR_LEN], buf_dev1[LD_MCP23017_WR_LEN];

	buf_dev0[0] = LD_MCP23017_GPIO_REG_ADDR;
	buf_dev1[0] = LD_MCP23017_GPIO_REG_ADDR;

	switch (mix_start_colour)
	{
		case ld_Green:
			buf_dev0[1] = (uint8_t)(~0xC3);
			buf_dev0[2] = (uint8_t)(~0x0A);

			buf_dev1[1] = (uint8_t)(~0x14);
			buf_dev1[2] = (uint8_t)(~0x13);

			break;

		case ld_Yellow:
			buf_dev0[1] = (uint8_t)(~0xA8);
			buf_dev0[2] = (uint8_t)(~0x51);

			buf_dev1[1] = (uint8_t)(~0x8A);
			buf_dev1[2] = (uint8_t)(~0x48);

			break;

		case ld_Red:
			buf_dev0[1] = (uint8_t)(~0x94);
			buf_dev0[2] = (uint8_t)(~0xA4);

			buf_dev1[1] = (uint8_t)(~0x61);
			buf_dev1[2] = (uint8_t)(~0x24);

			break;

		case ld_Off:
		default:
			break;
	}

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	return ret_val;
}


/*****************************************************************************/
/**
* Sets the LEDs to a typical operational scenario.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @return   true if LEDs set, else false
*
******************************************************************************/
bool ld_SetTypicalLeds(I2C_HandleTypeDef* i2c_device)
{
	bool ret_val;
	uint8_t set_buf_dev0[LD_MCP23017_WR_LEN];
	uint8_t set_buf_dev1[LD_MCP23017_WR_LEN];
	uint16_t gpo_dev0 = 0xFF7FU;
	uint16_t gpo_dev1 = 0xFFFFU;
	int16_t i;

	set_buf_dev0[0] = LD_MCP23017_GPIO_REG_ADDR;
	set_buf_dev1[0] = LD_MCP23017_GPIO_REG_ADDR;

	for (i = 0; i < LD_TYPICAL_MODE_NO_LEDS; ++i)
	{
		if (lg_ld_leds_typical_mode[i].i2c_addr == LD_MCP23017_DEV0_I2C_ADDR)
		{
			gpo_dev0 &= (~(1 << lg_ld_leds_typical_mode[i].pin));
		}
		else
		{
			gpo_dev1 &= (~(1 << lg_ld_leds_typical_mode[i].pin));
		}
	}

	set_buf_dev0[1] = (uint8_t)(gpo_dev0 & 0xFFU);
	set_buf_dev0[2] = (uint8_t)((gpo_dev0 >> 8) & 0xFFU);

	set_buf_dev1[1] = (uint8_t)(gpo_dev1 & 0xFFU);
	set_buf_dev1[2] = (uint8_t)((gpo_dev1 >> 8) & 0xFFU);

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										set_buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										set_buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	return ret_val;
}

