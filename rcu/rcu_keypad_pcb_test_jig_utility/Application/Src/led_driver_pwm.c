/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file led_driver_pwm.c
*
* Driver for the KT-000-0147-00 RevE.x onwards LEDs, turns LEDs on/off using
* NXP PCA9685 I2C LED PWM driver ICs.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo Could be made more generic using an initialisation structure.
* @todo Add support for PWM LED dimming.
*
******************************************************************************/
#define __LED_DRIVER_PWM_C

#include "led_driver_pwm.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define LDP_PCA9685_DEV0_I2C_ADDR			0x40U << 1
#define LDP_PCA9685_DEV1_I2C_ADDR			0x41U << 1

#define LDP_TYPICAL_MODE_NO_LEDS			5

#define LDP_PCA9685_RD_WR_REG_LEN			2U
#define LDP_PCA9685_WR_ALL_LED_REG_LEN		65U

#define LDP_PCA9685_MODE1_REG_ADDR			0x00U
#define LDP_PCA9685_MODE2_REG_ADDR			0x01U
#define LDP_PCA9685_LEDN_BASE_REG_ADDR		0x06U

#define LDP_PCA9685_MODE1_REG_RESTART_BIT	0x80U
#define LDP_PCA9685_MODE1_REG_EXTCLK_BIT	0x40U
#define LDP_PCA9685_MODE1_REG_AI_BIT		0x20U
#define LDP_PCA9685_MODE1_REG_SLEEP_BIT		0x10U
#define LDP_PCA9685_MODE1_REG_SUB1_BIT		0x08U
#define LDP_PCA9685_MODE1_REG_SUB2_BIT		0x04U
#define LDP_PCA9685_MODE1_REG_SUB3_BIT		0x02U
#define LDP_PCA9685_MODE1_REG_ALLCALL_BIT	0x01U

#define LDP_PCA9685_MODE2_REG_INVRT_BIT		0x10U
#define LDP_PCA9685_MODE2_REG_OCH_BIT		0x08U
#define LDP_PCA9685_MODE2_REG_OUTDRV_BIT	0x04U
#define LDP_PCA9685_MODE2_REG_OUTNE_BITS	0x03U

#define LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT	0x10U

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
ld_Led_t lg_ldp_leds[LD_NO_LEDS] = {
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	6U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow,	5U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Red, 	4U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	10U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow, 	9U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Red, 	8U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	14U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Yellow, 	13U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	12U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	2U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Yellow, 	1U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	0U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	2U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow, 	1U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Red, 	3U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	14U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow, 	15U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Red, 	0U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	11U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow, 	12U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Red, 	13U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	10U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Yellow, 	9U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	11U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	7U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Yellow, 	6U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	8U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	4U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Yellow, 	3U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	5U}
};

/* List of LEDs indexes to turn on in typical mode */
ld_Led_t lg_ldp_leds_typical_mode[LDP_TYPICAL_MODE_NO_LEDS] = {
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	6U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Yellow, 	9U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Red, 	12U},
	{LDP_PCA9685_DEV0_I2C_ADDR, ld_Green, 	2U},
	{LDP_PCA9685_DEV1_I2C_ADDR, ld_Green, 	10U}
};

/*****************************************************************************/
/**
* Initialises the PCA9685 PWM drivers on the -0147 board.  Sets all LEDs off.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			PCA9685 devices are connected to
* @param	p_reset_pin_port GPIO port that the I2C device output enable
* 			signal is attached to
* @param	noe_pin GPIO pin that the I2C device output enable signal is
* 			attached to
* @return   true if  PCA9685 initialisation is successful, else false
*
******************************************************************************/
bool ldp_Init(	I2C_HandleTypeDef* i2c_device,
				GPIO_TypeDef* p_noe_pin_port,
				uint16_t noe_pin)
{
	bool ret_val;
	uint8_t buf[LDP_PCA9685_RD_WR_REG_LEN];

	/* Set Mode 1 control register:
	 * 	- ALLCALL = '0', devices don't respond to all call address
	 * 	- SUB1-3 = '0', devices don't respond to sub-addresses
	 * 	- SLEEP = '0', normal mode
	 * 	- AI = '1', register auto-increment enabled
	 * 	- EXTCLK = '0', use internal clock
	 * 	- RESTART = '0', restart disabled
	 */
	buf[0] = LDP_PCA9685_MODE1_REG_ADDR;
	buf[1] = LDP_PCA9685_MODE1_REG_AI_BIT;

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LDP_PCA9685_DEV0_I2C_ADDR,
										buf, LDP_PCA9685_RD_WR_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LDP_PCA9685_DEV1_I2C_ADDR,
										buf, LDP_PCA9685_RD_WR_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);

	/* Set Mode 2 control register:
	 * 	- OUTNE = '00', active low enable
	 * 	- OUTDRV = '0', LEDs configured with an open-drain structure
	 * 	- OCH = '0', outputs change on STOP command
	 * 	- INVRT = '1', output logic state inverted
	 */
	buf[0] = LDP_PCA9685_MODE2_REG_ADDR;
	buf[1] = LDP_PCA9685_MODE2_REG_INVRT_BIT;

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LDP_PCA9685_DEV0_I2C_ADDR,
										buf, LDP_PCA9685_RD_WR_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LDP_PCA9685_DEV1_I2C_ADDR,
										buf, LDP_PCA9685_RD_WR_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);

	ret_val &= ldp_SetAllLeds(i2c_device, ld_Off);

	/* Assert LED output enable signal */
	if (ret_val)
	{
		HAL_GPIO_WritePin(p_noe_pin_port, noe_pin, GPIO_PIN_RESET);
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Sets all the LEDs to the specified colour or off, uses
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @param 	colour one of ld_Colours_t enumerated values
* @return 	true if LEDs set, else false
*
******************************************************************************/
bool ldp_SetAllLeds(I2C_HandleTypeDef* i2c_device, ld_Colours_t colour)
{
	bool ret_val;
	uint8_t buf_dev0[LDP_PCA9685_WR_ALL_LED_REG_LEN] = {0U},
			buf_dev1[LDP_PCA9685_WR_ALL_LED_REG_LEN] = {0U};
	uint16_t offset, i;

	buf_dev0[0] = LDP_PCA9685_LEDN_BASE_REG_ADDR;
	buf_dev1[0] = LDP_PCA9685_LEDN_BASE_REG_ADDR;

	for (i = 0; i < LD_NO_LEDS; ++i)
	{
		/* Turn LEDs on/off by setting LEDx full ON/OFF bits, I2C write starts at
		 * LED0_ON_L register (0x06), first-byte in I2C write buffer is address byte */
		offset = ((lg_ldp_leds[i].colour == colour) && (colour != ld_Off)) ?
					(lg_ldp_leds[i].pin * 4) + 2 : (lg_ldp_leds[i].pin * 4) + 4;

		if (lg_ldp_leds[i].i2c_addr == LDP_PCA9685_DEV0_I2C_ADDR)
		{
			buf_dev0[offset] = LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT;
		}
		else
		{
			buf_dev1[offset] = LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT;
		}
	}

	/* Set Device 0 LED7 to ON to take control of the power LED, I2C write starts at
	 * LED0_ON_L register (0x06), first-byte in I2C write buffer is address byte */
	buf_dev0[30] = LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT;

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LDP_PCA9685_DEV0_I2C_ADDR,
										buf_dev0, LDP_PCA9685_WR_ALL_LED_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LDP_PCA9685_DEV1_I2C_ADDR,
										buf_dev1, LDP_PCA9685_WR_ALL_LED_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);

	return ret_val;
}

/*****************************************************************************/
/**
* Sets the LEDs to a typical operational scenario.
*
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 devices are connected to
* @return 	true if LEDs set, else false
*
******************************************************************************/
bool ldp_SetTypicalLeds(I2C_HandleTypeDef* i2c_device)
{
	bool ret_val;
	uint8_t buf_dev0[LDP_PCA9685_WR_ALL_LED_REG_LEN] = {0U},
			buf_dev1[LDP_PCA9685_WR_ALL_LED_REG_LEN] = {0U};
	uint16_t offset, i;

	buf_dev0[0] = LDP_PCA9685_LEDN_BASE_REG_ADDR;
	buf_dev1[0] = LDP_PCA9685_LEDN_BASE_REG_ADDR;

	for (i = 0U; i < LDP_TYPICAL_MODE_NO_LEDS; ++i)
	{
		/* Turn LED on by setting LEDx full ON bits, I2C write starts at
		 * LED0_ON_L register (0x06), first-byte in I2C write buffer is address byte */
		offset = (lg_ldp_leds_typical_mode[i].pin * 4) + 2;

		if (lg_ldp_leds[i].i2c_addr == LDP_PCA9685_DEV0_I2C_ADDR)
		{
			buf_dev0[offset] = LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT;
		}
		else
		{
			buf_dev1[offset] = LDP_PCA9685_LEDN_H_REG_ON_OFF_BIT;
		}
	}

	ret_val = (HAL_I2C_Master_Transmit(	i2c_device, LDP_PCA9685_DEV0_I2C_ADDR,
										buf_dev0, LDP_PCA9685_WR_ALL_LED_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);
	ret_val &= (HAL_I2C_Master_Transmit(i2c_device, LDP_PCA9685_DEV1_I2C_ADDR,
										buf_dev1, LDP_PCA9685_WR_ALL_LED_REG_LEN, LD_I2C_TIMEOUT) == HAL_OK);

	return ret_val;
}
