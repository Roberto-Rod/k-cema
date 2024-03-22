/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
#define SSD_MIN_CENTRE_FREQ_MHZ		45U
#define SSD_MAX_CENTRE_FREQ_MHZ		495U


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
	GPIO_TypeDef		*synth_ncs_gpio_port;
	uint16_t			synth_ncs_gpio_pin;
	bool 				initialised;
} ssd_SpiSynthDriver_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ssd_InitInstance(	ssd_SpiSynthDriver_t 	*p_inst,
						SPI_HandleTypeDef		*spi_device,
						GPIO_TypeDef			*synth_ncs_gpio_port,
						uint16_t				synth_ncs_gpio_pin);
bool ssd_InitDevice(ssd_SpiSynthDriver_t *p_inst);
bool ssd_SetCentreFreqMhz(ssd_SpiSynthDriver_t *p_inst, uint32_t centre_freq_mhz);

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
#ifdef __SPI_SYNTH_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SSD_SYNTH_REG_LEN_BYTES			4
#define SSD_SYNTH_NUM_REGS				6

#define SSD_SPI_TIMEOUT_MS				100U

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
void ssd_AssertChipSelect(ssd_SpiSynthDriver_t *p_inst, bool assert);


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
uint8_t lg_ssd_synth_init_data[SSD_SYNTH_NUM_REGS][SSD_SYNTH_REG_LEN_BYTES] = {
		{0x00U, 0x00U, 0x0EU, 0x78U}, \
		{0x08U, 0x00U, 0xA0U, 0x01U}, \
		{0x7AU, 0x00U, 0x7EU, 0x42U}, \
		{0x00U, 0x80U, 0x00U, 0x03U}, \
		{0x00U, 0xA2U, 0x86U, 0x3CU}, \
		{0x00U, 0x58U, 0x00U, 0x05U}
};


#endif /* __SPI_SYNTH_DRIVER_C */

#endif /* __SPI_SYNTH_DRIVER_H */
