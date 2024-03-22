/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
#include "stm32l4xx_hal.h"
#include "hw_config_info.h"
#include "eui48.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/


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
/* Provides compatibility with CMSIS V1 */
typedef struct
{
	osMessageQId 		tx_data_queue;
	osMessageQId 		rx_data_queue;
	I2C_HandleTypeDef  	*i2c_device;
	uint16_t			pps_gpio_pin;
	GPIO_TypeDef    	*system_reset_n_gpio_port;
	uint16_t			system_reset_n_gpio_pin;
	GPIO_TypeDef		*dcdc_off_n_gpio_port;
	uint16_t			dcdc_off_n_gpio_pin;
	GPIO_TypeDef		*rack_addr_gpio_port;
	uint16_t			rack_addr_gpio_pin;
	TIM_HandleTypeDef 	*ab_1pps_out_htim;
	uint32_t 			ab_1pps_out_channel;
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
