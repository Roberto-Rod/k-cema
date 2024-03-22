/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file serial_buffer_task.h
**
** Include file for serial_buffer_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SERIAL_BUFFER_TASK_H
#define __SERIAL_BUFFER_TASK_H

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
#define SBT_TX_BUF_SIZE		16
#define SBT_MAX_NO_UARTS	2

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
	UART_HandleTypeDef* huart;
	osMessageQId		uart_tx_data_queue;
	osMessageQId 		uart_rx_data_queue;
	uint8_t 			uart_rx_buf;
	uint8_t 			uart_tx_buf[SBT_TX_BUF_SIZE];
} sbt_Uart_t;

typedef struct
{
	osMessageQId		rx_event_queue;
	uint16_t			no_uarts;
	sbt_Uart_t			uarts[SBT_MAX_NO_UARTS];
} sbt_Init_t;

typedef struct
{
	uint8_t 	uart_idx;
	uint8_t 	data;
	uint16_t	spare;
} sbt_Event_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sbt_InitTask(sbt_Init_t init_data);
void sbt_SerialBufferTask(void const *argument);

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
#ifdef __SERIAL_BUFFER_TASK_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/


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
void sbt_ProcessTxBuffer(	UART_HandleTypeDef* huart,
							osMessageQId		uart_tx_data_queue,
							uint8_t* 			uart_tx_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sbt_Init_t lg_sbt_init_data = {0};
bool lg_sbt_initialised = false;

#endif /* __SERIAL_BUFFER_TASK_C */

#endif /* __SERIAL_BUFFER_TASK_H */
