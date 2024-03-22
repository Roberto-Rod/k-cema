/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file i2c_adc_driver.h
**
** Include file for i2c_adc_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_ADC_DRIVER_H
#define __I2C_ADC_DRIVER_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define IAD_LTC2991_READ_CH_NUM				10
#define IAD_LTC2991_SE_CH_NUM				8U
#define IAD_LTC2991_INT_TEMP_RD_IDX			8
#define IAD_LTC2991_VCC_RD_IDX				9

#define IAD_LTC2991_SE_V_SCALE_FACTOR		305.18E-3F
#define IAD_LTC2991_VCC_OFFSET_MV			2500U
#define IAD_LTC2991_TEMP_SCALE_FACTOR		0.0625F

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
	uint16_t			i2c_address;
	float 				ch_scaling_factors[IAD_LTC2991_READ_CH_NUM];	/* Host application initialises these */
	int16_t				ch_offsets_mv[IAD_LTC2991_READ_CH_NUM];			/* Host application initialises these */
	const char 			**ch_names;										/* Host application initialises this pointer */
	bool 				initialised;
} iad_I2cAdcDriver_t;

typedef struct
{
	int16_t	adc_ch_mv[IAD_LTC2991_SE_CH_NUM];
	int16_t	adc_ch_int_temp_k;
	int16_t	adc_ch_vcc_mv;
} iad_I2cAdcData_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool iad_InitInstance(	iad_I2cAdcDriver_t  *p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address);
bool iad_InitDevice(iad_I2cAdcDriver_t  *p_inst);
bool iad_ReadAdcData(iad_I2cAdcDriver_t *p_inst, iad_I2cAdcData_t *p_data);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __I2C_ADC_DRIVER_H */
