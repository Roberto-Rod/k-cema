/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file spi_synth_driver.h
**
** Include file for spi_synth_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SPI_SYNTH_DRIVER_H
#define __SPI_SYNTH_DRIVER_H

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
#define SSD_MIN_CENTRE_FREQ_MHZ		10800U
#define SSD_MAX_CENTRE_FREQ_MHZ		12900U


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
typedef void (*ssd_assert_synth_cs_t)(bool);

typedef struct ssd_SpiSynthDriver
{
	SPI_HandleTypeDef		*spi_device;
	ssd_assert_synth_cs_t	p_assert_synth_cs_func;
	bool 					initialised;
} ssd_SpiSynthDriver_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ssd_InitInstance(	ssd_SpiSynthDriver_t 	*p_inst,
						SPI_HandleTypeDef		*spi_device,
						ssd_assert_synth_cs_t	p_assert_synth_cs_func);
bool ssd_InitDevice(ssd_SpiSynthDriver_t *p_inst);
bool ssd_SetCentreFreqMhz(ssd_SpiSynthDriver_t *p_inst, uint32_t centre_freq_mhz);
bool ssd_SetSynthPowerDown(ssd_SpiSynthDriver_t *p_inst, bool power_down);
bool ssd_WriteSynthRegister(ssd_SpiSynthDriver_t *p_inst, uint32_t reg_val);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SPI_SYNTH_DRIVER_H */
