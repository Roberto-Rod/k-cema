/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
#include "main.h"

/*****************************************************************************/
/**
* Initialises the MCP23017 GPIO expanders on the -0147 board.  Sets all GPIO
* as outputs and all LEDs off
*
* @param    p_inst pointer to test board LED driver instance data
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param	dev0_i2c_address MCP23017 device 0 I2C bus address
* @param	dev1_i2c_address MCP23017 device 1 I2C bus address
* @param	i2c_reset_gpio_port HAL driver GPIO port for GPIO expander reset
* @param	i2c_reset_gpio_pin HAL driver GPIO pin for GPIO expander reset
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool ld_InitInstance(	td_LedDriver_t *p_inst,
						I2C_HandleTypeDef *i2c_device,
						uint16_t dev0_i2c_address,
						uint16_t dev1_i2c_address,
						GPIO_TypeDef *i2c_reset_gpio_port,
						uint16_t i2c_reset_gpio_pin)
{
	p_inst->i2c_device			= i2c_device;
	p_inst->dev0_i2c_address	= dev0_i2c_address;
	p_inst->dev1_i2c_address	= dev1_i2c_address;
	p_inst->i2c_reset_gpio_port	= i2c_reset_gpio_port;
	p_inst->i2c_reset_gpio_pin	= i2c_reset_gpio_pin;
	p_inst->initialised			= true;

	return ld_InitDevice(p_inst);
}


/*****************************************************************************/
/**
* Initialise the LED driver device, brings GPIO expanders out of reset and
* sets all the LEDs to the OFF state
*
* @param    p_inst pointer to test board LED driver instance data
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool ld_InitDevice(td_LedDriver_t *p_inst)
{
	uint8_t buf[LD_MCP23017_WR_LEN];
	bool 	ret_val;

	HAL_GPIO_WritePin(	p_inst->i2c_reset_gpio_port, p_inst->i2c_reset_gpio_pin,
						GPIO_PIN_SET);

	ret_val = ld_SetAllLeds(p_inst, ld_Off);

	/* Set all the GPIO pins as outputs */
	buf[0] = LD_MCP23017_IODIR_REG_ADDR;
	buf[1] = 0U;
	buf[2] = 0U;

	ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev0_i2c_address,
										buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
				== HAL_OK) && ret_val;

	ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev1_i2c_address,
										buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
				== HAL_OK) && ret_val;

	return ret_val;
}


/*****************************************************************************/
/**
* Sets all the LEDs to the specified colour or off
*
* @param    p_inst pointer to test board LED driver instance data
* @param 	colour one of ld_Colours_t enumerated values
* @return   true if LEDs set, else false
* @note     None
*
******************************************************************************/
bool ld_SetAllLeds(td_LedDriver_t *p_inst, ld_Colours_t colour)
{
	uint8_t 	buf_dev0[LD_MCP23017_WR_LEN];
	uint8_t		buf_dev1[LD_MCP23017_WR_LEN];
	uint16_t 	dev0_gpo = 0xFF7FU;
	uint16_t 	dev1_gpo = 0xFFFFU;
	int16_t 	i;
	bool 		ret_val = true;

	if (p_inst->initialised &&
		((colour >= ld_Off) && (colour <= ld_Yellow)))
	{
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
					(lg_ld_leds[i].gpio_device == LD_MCP23017_DEV0))
				{
					dev0_gpo &= (~(1 << lg_ld_leds[i].pin));
				}
				else if ((lg_ld_leds[i].colour == colour) &&
						(lg_ld_leds[i].gpio_device == LD_MCP23017_DEV1))
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

		ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev0_i2c_address,
											buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
					== HAL_OK) && ret_val;

		ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev1_i2c_address,
											buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
					== HAL_OK) && ret_val;
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Turn an  individual LED on, all other LEDs are turned off
*
* @param    p_inst pointer to test board LED driver instance data
* @param	index LED to turn on
* @return   true if LEDs set, else false
* @note     None
*
******************************************************************************/
bool ld_SetLed(td_LedDriver_t *p_inst, int16_t index)
{
	uint8_t set_buf[LD_MCP23017_WR_LEN];
	uint8_t clear_buf[LD_MCP23017_WR_LEN];
	uint16_t gpo = 0U;
	bool ret_val = true;

	if (p_inst->initialised && (index < LD_NO_LEDS))
	{
		set_buf[0] = LD_MCP23017_GPIO_REG_ADDR;
		clear_buf[0] = LD_MCP23017_GPIO_REG_ADDR;

		if (lg_ld_leds[index].gpio_device == LD_MCP23017_DEV0)
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

		if (lg_ld_leds[index].gpio_device == LD_MCP23017_DEV0)
		{
			ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev1_i2c_address,
												clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
						== HAL_OK) && ret_val;

			ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev0_i2c_address,
												set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
						== HAL_OK) && ret_val;
		}
		else
		{
			ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev0_i2c_address,
												clear_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
						== HAL_OK) && ret_val;

			ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev1_i2c_address,
												set_buf, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
						== HAL_OK) && ret_val;
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
* Sets the LEDs such that one LED from each device is on in the repeating
* pattern Red/Green/Yellow.  The first colour in the pattern is specified in the
* function call.
*
* @param    p_inst pointer to test board LED driver instance data
* @param	mix_start_colour colour of the first LED device, one of
* 			ld_Colours_t enumerated values: ld_Green, ld_Red, ld_Yellow
* @return   true if LEDs set, else false
* @note     None
*
******************************************************************************/
bool ld_SetMixLeds(td_LedDriver_t *p_inst, ld_Colours_t mix_start_colour)
{
	uint8_t buf_dev0[LD_MCP23017_WR_LEN];
	uint8_t	buf_dev1[LD_MCP23017_WR_LEN];
	bool 	ret_val = true;

	if (p_inst->initialised)
	{
		buf_dev0[0] = LD_MCP23017_GPIO_REG_ADDR;
		buf_dev1[0] = LD_MCP23017_GPIO_REG_ADDR;

		switch (mix_start_colour)
		{
			case ld_Green:
				buf_dev0[1] = (uint8_t)(~0x43);
				buf_dev0[2] = (uint8_t)(~0x0A);

				buf_dev1[1] = (uint8_t)(~0x14);
				buf_dev1[2] = (uint8_t)(~0x13);

				break;

			case ld_Yellow:
				buf_dev0[1] = (uint8_t)(~0x28);
				buf_dev0[2] = (uint8_t)(~0x51);

				buf_dev1[1] = (uint8_t)(~0x8A);
				buf_dev1[2] = (uint8_t)(~0x48);

				break;

			case ld_Red:
				buf_dev0[1] = (uint8_t)(~0x14);
				buf_dev0[2] = (uint8_t)(~0xA4);

				buf_dev1[1] = (uint8_t)(~0x61);
				buf_dev1[2] = (uint8_t)(~0x24);

				break;

			case ld_Off:
			default:
				break;
		}

		ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev0_i2c_address,
											buf_dev0, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
					== HAL_OK) && ret_val;

		ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->dev1_i2c_address,
											buf_dev1, LD_MCP23017_WR_LEN, LD_I2C_TIMEOUT)
					== HAL_OK) && ret_val;
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Accessor to array of strings describing the LED colours, array length is
* LD_NO_LED_COLOURS
*
* @return   Pointer to first element of array of strings describing the LED
* 			colours
* @note     None
*
******************************************************************************/
const char **ld_GetLedColourNames(void)
{
	return lg_ld_led_colour_names;
}

