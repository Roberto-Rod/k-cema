/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
**
** @file i2c_bit_bash.h
**
** Include file for i2c_bit_bash.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_BIT_BASH_H
#define __I2C_BIT_BASH_H

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
typedef struct idd_I2cBitBash
{
	GPIO_TypeDef *scl_pin_port;
	uint16_t scl_pin;
	GPIO_TypeDef *sda_pin_port;
	uint16_t sda_pin;
} idd_I2cBitBash_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void ibb_Init(idd_I2cBitBash_t  *p_inst,
		      GPIO_TypeDef *scl_pin_port, uint16_t scl_pin,
			  GPIO_TypeDef *sda_pin_port, uint16_t sda_pin);
uint8_t ibb_MasterWriteByte(idd_I2cBitBash_t *p_inst, uint8_t b);
uint8_t ibb_MasterReadByte(idd_I2cBitBash_t *p_inst, uint8_t ack);
void ibb_StartCondition(idd_I2cBitBash_t *p_inst);
void ibb_StopCondition(idd_I2cBitBash_t *p_inst);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __I2C_BIT_BASH_H */
