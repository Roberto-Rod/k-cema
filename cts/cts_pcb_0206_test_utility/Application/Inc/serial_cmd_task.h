/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file serial_cmd_task.h
**
** Include file for serial_cmd_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SERIAL_CMD_TASK_H
#define __SERIAL_CMD_TASK_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include <stdbool.h>
#include "cmsis_os2.h"
#include "stm32f4xx_ll_dma.h"
#include "stm32f4xx_ll_adc.h"
#include "stm32f4xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define SCT_LB_TEST_PAIR_NUM		15
#define SCT_GPO_PIN_NUM				9
#define SCT_GPIO_PIN_NAME_MAX_LEN	32

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
typedef struct sct_LbTestIoPair
{
	GPIO_TypeDef *pin_a_port;
	uint16_t pin_a_pin;
	GPIO_TypeDef *pin_b_port;
	uint16_t pin_b_pin;
} sct_LbTestIoPair_t;

typedef struct
{
	GPIO_TypeDef	*port;
	uint16_t		pin;
	char			name[SCT_GPIO_PIN_NAME_MAX_LEN];
} sct_GpioSignal;

typedef struct sct_Init
{
	osMessageQueueId_t 	tx_data_queue;
	osMessageQueueId_t 	rx_data_queue;
	I2C_HandleTypeDef  	*i2c_device;
	ADC_TypeDef			*bit_adc_device;
	DMA_TypeDef			*bit_adc_dma_device;
	uint32_t			bit_adc_dma_stream;
	osSemaphoreId_t		bit_adc_semaphore;
	uint16_t			pps_gpio_pin;
	int16_t				pps_gpio_irq;
	GPIO_TypeDef 		*rx_path_sw_3_a_port;
	uint16_t 			rx_path_sw_3_a_pin;
	GPIO_TypeDef 		*rx_path_sw_3_b_port;
	uint16_t 			rx_path_sw_3_b_pin;
	GPIO_TypeDef 		*rx_path_sw_4_a_port;
	uint16_t 			rx_path_sw_4_a_pin;
	GPIO_TypeDef 		*rx_path_sw_4_b_port;
	uint16_t	 		rx_path_sw_4_b_pin;
	GPIO_TypeDef 		*rx_path_sw_5_vc_port;
	uint16_t	 		rx_path_sw_5_vc_pin;
	GPIO_TypeDef 		*rx_path_sw_6_vc_port;
	uint16_t	 		rx_path_sw_6_vc_pin;
	ADC_TypeDef			*rf_det_adc_device;
	uint32_t			rf_det_adc_channel;
	TIM_HandleTypeDef	*rf_det_timer;
	GPIO_TypeDef 		*rx_path_det_en_port;
	uint16_t	 		rx_path_det_en_pin;
	GPIO_TypeDef 		*rx_path_pk_det_dischrg_port;
	uint16_t	 		rx_path_pk_det_dischrg_pin;
	sct_LbTestIoPair_t	lb_test_io_pairs[SCT_LB_TEST_PAIR_NUM];
	sct_GpioSignal		gpo_pins[SCT_GPO_PIN_NUM];
	GPIO_TypeDef 		*lb_i2c_scl_pin_port;
	uint16_t 			lb_i2c_scl_pin;
	GPIO_TypeDef 		*lb_i2c_sda_pin_port;
	uint16_t 			lb_i2c_sda_pin;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
//void sct_SerialCmdTask(void const *argument);
void sct_AdcDMAIrqHandler(ADC_TypeDef *adc_device);
void sct_RfDetTmrCallback(TIM_HandleTypeDef *htim);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SERIAL_CMD_TASK_H */
