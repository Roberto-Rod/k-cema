/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file ltc2991.h
**
** Include file for ltc2991.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __LTC2991_DRIVER_H
#define __LTC2991_DRIVER_H

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
#define LTC2991_READ_CH_NUM			10U
#define LTC2991_SE_CH_NUM			8U
#define LTC2991_INT_TEMP_RD_IDX		8
#define LTC2991_VCC_RD_IDX			9

#define LTC2991_SE_V_SCALE_FACTOR	305.18E-3F
#define LTC2991_VCC_OFFSET_MV		2500U
#define LTC2991_TEMP_SCALE_FACTOR	6.25E-2F

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
typedef struct ltc2991_Driver
{
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	bool 				initialised;
	float				scaling_factors[LTC2991_SE_CH_NUM];
} ltc2991_Driver_t;

typedef struct ltc2991_Data
{
	uint16_t	adc_ch_mv[LTC2991_SE_CH_NUM];
	uint16_t	adc_ch_int_temp_k;
	uint16_t	adc_ch_vcc_mv;
} ltc2991_Data_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ltc2991_InitInstance(	ltc2991_Driver_t  *p_inst,
							I2C_HandleTypeDef	*p_i2c_device,
							uint16_t			i2c_address);
bool ltc2991_InitDevice(ltc2991_Driver_t  *p_inst);
bool ltc2991_ReadAdcData(ltc2991_Driver_t *p_inst, ltc2991_Data_t *p_data);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __LTC2991_DRIVER_H */
