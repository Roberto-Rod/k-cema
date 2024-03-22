/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
*
* @file i2c_temp_sensor.c
*
* Driver for AD7415 I2C temperature sensor.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/

#include "i2c_bit_bash.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/


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
__STATIC_INLINE void ibb_BusInit(idd_I2cBitBash_t *p_inst)
{
	HAL_GPIO_WritePin(p_inst->sda_pin_port, p_inst->sda_pin, GPIO_PIN_SET);
	HAL_GPIO_WritePin(p_inst->scl_pin_port, p_inst->scl_pin, GPIO_PIN_SET);
};

__STATIC_INLINE void ibb_SetSda(idd_I2cBitBash_t *p_inst)
{
	HAL_GPIO_WritePin(p_inst->sda_pin_port, p_inst->sda_pin, GPIO_PIN_SET);
};

__STATIC_INLINE void ibb_ClearSda(idd_I2cBitBash_t *p_inst)
{
	HAL_GPIO_WritePin(p_inst->sda_pin_port, p_inst->sda_pin, GPIO_PIN_RESET);
};

__STATIC_INLINE uint16_t ibb_GetSda(idd_I2cBitBash_t *p_inst)
{
	return (uint16_t)HAL_GPIO_ReadPin(p_inst->sda_pin_port, p_inst->sda_pin);
};

__STATIC_INLINE void ibb_SetScl(idd_I2cBitBash_t *p_inst)
{
	HAL_GPIO_WritePin(p_inst->scl_pin_port, p_inst->scl_pin, GPIO_PIN_SET);
};

__STATIC_INLINE void ibb_ClearScl(idd_I2cBitBash_t *p_inst)
{
	HAL_GPIO_WritePin(p_inst->scl_pin_port, p_inst->scl_pin, GPIO_PIN_RESET);
};

__STATIC_INLINE void ibb_WrControl(idd_I2cBitBash_t *p_inst, uint8_t b, uint8_t mask)
{
	(b & mask) ? ibb_SetSda(p_inst) : ibb_ClearSda(p_inst);
};

__STATIC_INLINE void ibb_RdControl(idd_I2cBitBash_t *p_inst, uint8_t *b, uint8_t mask)
{
	if (ibb_GetSda(p_inst))
	{
		*b |= mask;
	}
};

/*****************************************************************************/
/**
* 10 us delay required for 1-bit on 3100 kHz I2C bus.  The actual delay will depend on
* compiler optimisation, the factor of '3' attempts to compensate for loop
* overhead.
*
******************************************************************************/
__STATIC_INLINE void ibb_SetupDelay(void)
{
	volatile uint32_t wait_loop_index = (3U * (SystemCoreClock / (100000U * 3U))) / 10U;
	while(wait_loop_index-- != 0);
};

__STATIC_INLINE void ibb_HalfBitDelay(void)
{
	volatile uint32_t wait_loop_index = (5U * (SystemCoreClock / (100000U * 3U))) / 10U;
	while(wait_loop_index-- != 0);
};

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


/*****************************************************************************/
/**
* Initialise the I2C Bit Bash driver, this function copies the hw information
* into the driver data and sets the initial state of the GPIO signals
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	scl_pin_port GPIO port for SCL pin
* @param	scl_pin SCL GPIO pin
* @param	sda_pin_port GPIO port for SDA pin
* @param	sda_pin SCL GPIO pin
*
******************************************************************************/

void ibb_Init(idd_I2cBitBash_t *p_inst,
		      GPIO_TypeDef *scl_pin_port, uint16_t scl_pin,
			  GPIO_TypeDef *sda_pin_port, uint16_t sda_pin)
{
	p_inst->scl_pin_port = scl_pin_port;
	p_inst->scl_pin = scl_pin;
	p_inst->sda_pin_port = sda_pin_port;
	p_inst->sda_pin = sda_pin;

	ibb_BusInit(p_inst);
}

/**
 * @brief I2C master write 8-bit data bit-bang
 * @param unsigned char b - data to transmit
 * @return uint8_t ack – acknowledgement received
 */
uint8_t ibb_MasterWriteByte(idd_I2cBitBash_t *p_inst, uint8_t b)
{
	uint8_t mask = 0x80U;
	uint8_t ack;

	do
	{
		ibb_WrControl(p_inst, b, mask);
		ibb_SetupDelay();
		ibb_SetScl(p_inst);
		ibb_HalfBitDelay();
		ibb_ClearScl(p_inst);
		ibb_SetupDelay();
	} while ((mask >>= 1) != 0U);

	ibb_SetSda(p_inst);/* ACK slot checking */
	ibb_SetScl(p_inst);
	ibb_HalfBitDelay();
	ack = ibb_GetSda(p_inst);
	ibb_ClearScl(p_inst);

	return ack;
}

/**
 * @brief I2C master read 8-bit bit-bang
 * @param unsigned char ack – acknowledgement control
 * @retval unsigned char b – data received
 */
uint8_t ibb_MasterReadByte(idd_I2cBitBash_t *p_inst, uint8_t ack)
{
	uint8_t mask = 0x80U;
	uint8_t b = 0U;

	do
	{
		ibb_SetScl(p_inst);
		ibb_HalfBitDelay();
		ibb_RdControl(p_inst, &b, mask);
		ibb_ClearScl(p_inst);
		ibb_HalfBitDelay();
	} while ((mask >>=1 ) != 0U);

	if (ack != 0U)
	{
		ibb_ClearSda(p_inst);/* ACK slot control */
	}
	ibb_SetupDelay();
	ibb_SetScl(p_inst);
	ibb_HalfBitDelay();
	ibb_ClearScl(p_inst);
	ibb_HalfBitDelay();

	return b;
}

/**
 * @brief I2C start
 * @param none
 * @retval none
 */
void ibb_StartCondition(idd_I2cBitBash_t *p_inst)
{
	ibb_BusInit(p_inst);
	ibb_HalfBitDelay();
	ibb_ClearSda(p_inst);
	ibb_HalfBitDelay();
	ibb_ClearScl(p_inst);
	ibb_HalfBitDelay();
}
/**
 * @brief I2C stop
 * @param none
 * @retval none
 */
void ibb_StopCondition(idd_I2cBitBash_t *p_inst)
{
	ibb_ClearSda(p_inst);
	ibb_ClearScl(p_inst);
	ibb_HalfBitDelay();
	ibb_SetScl(p_inst);
	ibb_HalfBitDelay();
	ibb_SetSda(p_inst);
	ibb_HalfBitDelay();
}
