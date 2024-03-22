/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file led_driver.c
*
* Driver for the KT-000-0147-00 LEDs, turns LEDs on/off using Microchip
* MCP23017 I2C GPIO expanders
*
* ld_Init0165() and ld_SetLed0165() functions can be used when using the
* driver with the KT-000-0165-00 Keypad and RCU Board test jig.  They allow
* the single tri-colour LED on the test jig to be driven one-LED at a
* time.  The MCP23017 has the same I2C address as Device 0 on the
* KT-000-0147-00 board.
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
#include "main.h"

/*****************************************************************************/
/**
* Initialises the MCP23017 GPIO expanders on the -0147 board.  Sets all GPIO
* as outputs and all LEDs off
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @return   None
* @note     None
*
******************************************************************************/
void ld_Init(I2C_HandleTypeDef* i2c_device)
{
	uint8_t buf[LD_MCP23017_WR_LEN];

	HAL_GPIO_WritePin(I2C_RESET_N_GPIO_Port, I2C_RESET_N_Pin, GPIO_PIN_SET);

	ld_SetAllLeds(i2c_device, ld_Off);

	/* Set all the GPIO pins as outputs */
	buf[0] = LD_MCP23017_IODIR_REG_ADDR;
	buf[1] = 0U;
	buf[2] = 0U;

	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
									buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
}


/*****************************************************************************/
/**
* Initialises the MCP23017 GPIO expanders on the -0165 board.  Sets all GPIO
* as outputs and the tri-colour LED green LED on
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices is connected to
* @return   None
* @note     None
*
******************************************************************************/
void ld_Init0165(I2C_HandleTypeDef* i2c_device)
{
	uint8_t buf[LD_MCP23017_WR_LEN];

	HAL_GPIO_WritePin(I2C_RESET_N_GPIO_Port, I2C_RESET_N_Pin, GPIO_PIN_SET);

	/* Set all the GPIO pins as outputs */
	buf[0] = LD_MCP23017_GPIO_REG_ADDR;
	buf[1] = 6U;
	buf[2] = 0U;

	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);

	/* Set all the GPIO pins as outputs */
	buf[0] = LD_MCP23017_IODIR_REG_ADDR;
	buf[1] = 0U;
	buf[2] = 0U;

	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
}


/*****************************************************************************/
/**
* Sets all the LEDs to the specified colour or off
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param 	colour one of ld_Colours_t enumerated values
* @return   None
* @note     None
*
******************************************************************************/
void ld_SetAllLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour)
{
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

	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
									buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
}

/*****************************************************************************/
/**
* Turn an  individual LED on, all other LEDs are turned off
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param	index of LED to turn on
* @return   None
* @note     None
*
******************************************************************************/
void ld_SetLed(I2C_HandleTypeDef* i2c_device, int16_t index)
{
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
		(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
		(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	}
	else
	{
		(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
										clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
		(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
										set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	}
}


/*****************************************************************************/
/**
* Turn an individual LED in the -0165 tri-colour LED on, all other LEDs are
* turned off.  The following indexes from the -0147 board map to the -0165 board:
* 	12 - Green
* 	13 - Yellow
* 	17 - Red
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 device is connected to
* @param	index of LED to turn on
* @return   None
* @note     None
*
******************************************************************************/
void ld_SetLed0165(I2C_HandleTypeDef* i2c_device, int16_t index)
{
	uint8_t buf[LD_MCP23017_WR_LEN];
	uint8_t mask;

	(void) HAL_I2C_Mem_Read(i2c_device,	LD_MCP23017_DEV0_I2C_ADDR, LD_MCP23017_GPIO_REG_ADDR,
							1U, buf, LD_MCP23017_RD_LEN, LD_I2C_TIMEOUT);

	buf[2] = buf[1];
	mask = (~(1 << lg_ld_leds[index].pin));
	buf[1] = 0x7 & mask;
	buf[0] = LD_MCP23017_GPIO_REG_ADDR;

	(void) HAL_I2C_Master_Transmit(	i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
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
* @return   None
* @note     None
*
******************************************************************************/
void ld_SetMixLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t mix_start_colour)
{
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

	(void) HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV0_I2C_ADDR, buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	(void) HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR, buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
}


/*****************************************************************************/
/**
* Sets the LEDs to a typical operational scenario.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @return   None
* @note     None
*
******************************************************************************/
void ld_SetTypicalLeds(I2C_HandleTypeDef* i2c_device)
{
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

	(void) HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV0_I2C_ADDR,
									set_buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
	(void) HAL_I2C_Master_Transmit(i2c_device, LD_MCP23017_DEV1_I2C_ADDR,
									set_buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT);
}

