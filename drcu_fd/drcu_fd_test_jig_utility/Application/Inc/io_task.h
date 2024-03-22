/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file io_task.h
**
** Include file for io_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __IO_TASK_H
#define __IO_TASK_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include <stdbool.h>
#include "cmsis_os.h"
#include "stm32l4xx_hal.h"
#include "stm32l4xx_ll_dma.h"
#include "stm32l4xx_ll_adc.h"

/*****************************************************************************
*
*  Global Definitions
******************************************************************************/

#define IOT_MAX_STR_LEN						32
#define IOT_ANALOGUE_READING_NAME_MAX_LEN	IOT_MAX_STR_LEN

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
typedef enum iot_GpoPinId
{
	iot_gpo_csm_1pps_dir = 0,
	iot_gpo_som_sys_rst,
	iot_gpo_som_sd_boot_en,
	iot_gpo_qty
} iot_GpoPinId_t;

typedef enum ot_GpiPinId
{
	iot_gpi_pwr_btn_n = 0,
	iot_gpi_pwr_en_zer_n,
	iot_gpi_xchange_reset,
	iot_gpi_qty
} iot_GpiPinId_t;

typedef enum iot_GpioPinState
{
	iot_gpio_reset = 0,
	iot_gpio_set
} iot_GpioPinState_t;

typedef struct
{
	GPIO_TypeDef	*port;
	uint16_t		pin;
	char			name[IOT_MAX_STR_LEN];
} iot_GpioSignal;


typedef struct iot_Init
{
	TIM_HandleTypeDef 	*pps_out_htim;
	uint32_t 			pps_out_channel;
	GPIO_TypeDef		*pps_dir_gpio_port;
	uint16_t 			pps_dir_gpio_pin;
	uint16_t			xchange_1pps_gpio_pin;
	int16_t				xchange_1pps_gpio_irq;
	ADC_TypeDef			*adc_device;
	DMA_TypeDef			*adc_dma_device;
	uint32_t			adc_dma_channel;
	osSemaphoreId		adc_semaphore;
	iot_GpioSignal		gpi_signals[iot_gpi_qty];
	iot_GpioSignal		gpo_signals[iot_gpo_qty];
} iot_Init_t;

typedef enum iot_AdcChannelId
{
	iot_adc_buzzer_12v = 0,
	iot_adc_aux_supply_12v,
	iot_adc_xchange_12v,
	iot_adc_fd_eth_gnd,
	iot_adc_csm_eth_gnd,
	iot_adc_vref_int,		/* This should always be the last entry in lg_iot_adc_channels */
	iot_adc_ch_qty
} iot_AdcChannelId_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void iot_InitTask(iot_Init_t init_data);
void iot_IoTask(void const *argument);
iot_GpioPinState_t iot_GetGpiPinState(iot_GpiPinId_t pin_id, const char **p_chanel_name);
void iot_SetGpoPinState(iot_GpoPinId_t pin_id, iot_GpioPinState_t pin_state, const char **p_gpo_name);
bool iot_GetAdcScaledValue(iot_AdcChannelId_t adc_channel, int16_t *p_scaled_value, const char **p_channel_name);
void iot_AdcDMAIrqHandler(ADC_TypeDef *adc_device);
void iot_Enable1PpsOp(bool enable);
bool iot_1ppsDetected(uint32_t *p_1pps_delta);


/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/

extern const char *IOT_UART_EXPECTED_STRING;

#endif /* __IO_TASK_H */
