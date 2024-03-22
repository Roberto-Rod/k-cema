/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file spi_adc_driver.h
**
** Include file for spi_adc_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SPI_ADC_DRIVER_H
#define __SPI_ADC_DRIVER_H

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
#define SAD_ADC122S101_READ_CH_NUM		1U

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
	SPI_HandleTypeDef	*spi_device;
	GPIO_TypeDef		*adc_ncs_gpio_port;
	uint16_t			adc_ncs_gpio_pin;
	bool 				initialised;
} sad_SpiAdcDriver_t;

typedef struct
{
	int16_t	adc_ch_cdbm;
} iad_SpiAdcData_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool sad_InitInstance(	sad_SpiAdcDriver_t  *p_inst,
						SPI_HandleTypeDef	*spi_device,
						GPIO_TypeDef		*adc_ncs_gpio_port,
						uint16_t			adc_ncs_gpio_pin);
bool sad_InitDevice(sad_SpiAdcDriver_t *p_inst);
bool sad_ReadAdcData(sad_SpiAdcDriver_t *p_inst, iad_SpiAdcData_t *p_data);
const char *sad_GetChannelNames(void);

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
#ifdef __SPI_ADC_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SAD_ADC122S101_RDWR_LEN		2
#define SAD_SPI_TIMEOUT_MS			100U

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
void sad_AssertChipSelect(sad_SpiAdcDriver_t *p_inst, bool assert);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
const char lg_sad_ch_name[] = "Mixer Level:";

#endif /* __SPI_ADC_DRIVER_C */

#endif /* __SPI_ADC_DRIVER_H */
