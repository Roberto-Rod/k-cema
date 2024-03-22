/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file serial_cmd_task.h
**
** Include file for serial_cmd_task.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
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
#define SCT_GPO_PIN_NUM				12
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

typedef struct
{
	osMessageQId 		tx_data_queue;
	osMessageQId 		rx_data_queue;
	I2C_HandleTypeDef  	*i2c_device0;
	I2C_HandleTypeDef  	*i2c_device1;
	GPIO_TypeDef		*buzzer_gpio_port;
	uint16_t			buzzer_gpio_pin;
	GPIO_TypeDef 		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	uint16_t			pps_gpio_pin;
	int16_t				pps_gpio_irq;
	sct_GpioSignal		gpi_pins[SCT_GPI_PIN_NUM];
	sct_GpioSignal		gpo_pins[SCT_GPO_PIN_NUM];
	TIM_HandleTypeDef 	*pwr_btn_timer;
	ADC_HandleTypeDef	*adc_device;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
void sct_SerialCmdTask(void const *argument);
void sct_KeypadPwrBtnCallback(void);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/

#endif /* __SERIAL_CMD_TASK_H */
