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
#include "cmsis_os.h"
#include "stm32l0xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define SCT_GPI_PIN_NUM				8
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
typedef struct
{
	GPIO_TypeDef	*port;
	uint16_t		pin;
	char			name[SCT_GPIO_PIN_NAME_MAX_LEN];
} sct_GpioSignal;

typedef struct sct_Init
{
	osMessageQId 		tx_data_queue;
	osMessageQId 		rx_data_queue;
	I2C_HandleTypeDef  	*i2c_device0;
	sct_GpioSignal		gpi_pins[SCT_GPI_PIN_NUM];
	sct_GpioSignal		gpo_pins[SCT_GPO_PIN_NUM];
	ADC_HandleTypeDef	*adc_device;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
void sct_SerialCmdTask(void const *argument);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SERIAL_CMD_TASK_H */
