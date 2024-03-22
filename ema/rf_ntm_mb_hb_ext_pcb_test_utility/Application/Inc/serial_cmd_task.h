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
	SPI_HandleTypeDef   *spi_device;
	GPIO_TypeDef    	*i2c_reset_gpio_port;
	uint16_t			i2c_reset_gpio_pin;
	GPIO_TypeDef		*xcvr_ncs_gpio_port;
	uint16_t			xcvr_ncs_gpio_pin;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
void sct_SerialCmdTask(void const *argument);
void sct_AssertSynthChipSelect(bool assert);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SERIAL_CMD_TASK_H */
