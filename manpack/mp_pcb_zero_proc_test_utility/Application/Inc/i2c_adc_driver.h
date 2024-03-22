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
#include "stm32l0xx_hal.h"
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
	I2C_HandleTypeDef* 	i2c_device;
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
bool iad_InitInstance(	iad_I2cAdcDriver_t  *p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address);
bool iad_InitDevice(iad_I2cAdcDriver_t  *p_inst);
bool iad_ReadAdcData(iad_I2cAdcDriver_t *p_inst, iad_I2cAdcData_t *p_data);
const char **iad_GetChannelNames(void);

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
#ifdef __I2C_ADC_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define IAD_LTC2991_CHANNEL_EN_REG_ADDR		0x01U
#define IAD_LTC2991_V1V2V3V4_CTRL_REG_ADDR	0x06U
#define IAD_LTC2991_V5V6V7V8_CTRL_REG_ADDR	0x07U
#define IAD_LTC2991_CONTROL_REG_ADDR		0x08U
#define IAD_LTC2991_V1_REG_ADDR				0x0AU
#define IAD_LTC2991_V2_REG_ADDR				0x0CU
#define IAD_LTC2991_V3_REG_ADDR				0x0EU
#define IAD_LTC2991_V4_REG_ADDR				0x10U
#define IAD_LTC2991_V5_REG_ADDR				0x12U
#define IAD_LTC2991_V6_REG_ADDR				0x14U
#define IAD_LTC2991_V7_REG_ADDR				0x16U
#define IAD_LTC2991_V8_REG_ADDR				0x18U
#define IAD_LTC2991_INT_TEMP_REG_ADDR		0x1AU
#define IAD_LTC2991_VCC_REG_ADDR			0x1CU

#define IAD_LTC2991_CHANNEL_EN_REG_VAL		0xF8U	/* V1-V8 enabled; internal temperature/VCC enabled */
#define IAD_LTC2991_V1V2V3V4_CTRL_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define IAD_LTC2991_V5V6V7V8_CTR_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define IAD_LTC2991_CONTROL_REG_VAL			0x14U	/* PWM disabled; repeated acquisition; internal voltage filter disabled, Kelvin temp. */

#define IAD_LTC2991_DATA_VALID_BIT			0x8000U
#define IAD_LTC2991_DATA_VALID_MASK			0x7FFFU

#define IAD_LTC2991_SE_V_SCALE_FACTOR		305.18E-3F
#define IAD_LTC2991_VCC_OFFSET_MV			2500U
#define IAD_LTC2991_TEMP_SCALE_FACTOR		0.0625F

#define IAD_RD_REG_LEN			1U
#define IAD_RD_ADC_CH_LEN		2U
#define IAD_WR_REG_ADDR_LEN		1U
#define IAD_WR_REG_LEN			2U

#define IAD_I2C_TIMEOUT_MS		100U

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
bool iad_ReadRegister(	iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t *p_val);
bool iad_ReadAdcChannel(iad_I2cAdcDriver_t *p_inst,
						uint8_t ch_addr, uint16_t *p_val);
bool iad_WriteRegister (iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
float lg_iad_adc_ch_scaling_factors[IAD_LTC2991_READ_CH_NUM] = \
{
	IAD_LTC2991_SE_V_SCALE_FACTOR * 3.7F,
	IAD_LTC2991_SE_V_SCALE_FACTOR * 3.7F,
	IAD_LTC2991_SE_V_SCALE_FACTOR,
	IAD_LTC2991_SE_V_SCALE_FACTOR,
	IAD_LTC2991_SE_V_SCALE_FACTOR,
	IAD_LTC2991_SE_V_SCALE_FACTOR,
	IAD_LTC2991_SE_V_SCALE_FACTOR,
	IAD_LTC2991_TEMP_SCALE_FACTOR,
	IAD_LTC2991_TEMP_SCALE_FACTOR,
	IAD_LTC2991_SE_V_SCALE_FACTOR
};

const char *lg_iad_ch_names[IAD_LTC2991_READ_CH_NUM] = \
{
	"+VBAT_ZER (mV)\t\t",
	"+3V3_ZER_BUF (mV)\t",
	"+3V0_ZER_PROC (mV)\t",
	"+3V0_ZER_FPGA (mV)\t",
	"+2V5_ZER (mV)\t\t",
	"+2V5_SOM (mV)\t\t",
	"+1V2_ZER_FPGA (mV)\t",
	"Spare (mV)\t\t",
	"Temp (K)\t\t",
	"VCC (mV)\t\t"
};

#endif /* __I2C_ADC_DRIVER_C */

#endif /* __I2C_ADC_DRIVER_H */
