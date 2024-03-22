/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
**
** @file i2c_adc_driver_bit_bash.h
**
** Include file for i2c_adc_driver_bit_bash.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_ADC_DRIVER_BIT_BASH_H
#define __I2C_ADC_DRIVER_BIT_BASH_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32f4xx_hal.h"
#include "i2c_bit_bash.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define IAD_LTC2991_READ_CH_NUM				10U
#define IAD_LTC2991_SE_CH_NUM				8U
#define IAD_LTC2991_INT_TEMP_RD_IDX			8
#define IAD_LTC2991_VCC_RD_IDX				9

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
	idd_I2cBitBash_t 	i2c_bit_bash;
	uint16_t			i2c_address;
	bool 				initialised;
} iad_I2cAdcDriver_t;

typedef struct
{
	uint16_t	adc_ch_mv[IAD_LTC2991_SE_CH_NUM];
	uint16_t	adc_ch_int_temp_k;
	uint16_t	adc_ch_vcc_mv;
} iad_I2cAdcData_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool iad_InitInstance(iad_I2cAdcDriver_t  *p_inst,
					  GPIO_TypeDef *scl_pin_port, uint16_t scl_pin,
					  GPIO_TypeDef *sda_pin_port, uint16_t sda_pin,
					  uint16_t i2c_address);
bool iad_InitDevice(iad_I2cAdcDriver_t  *p_inst);
bool iad_ReadAdcData(iad_I2cAdcDriver_t *p_inst, iad_I2cAdcData_t *p_data);
const char **iad_GetChannelNames(void);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __I2C_ADC_DRIVER_BIT_BASH_H */
