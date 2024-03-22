/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
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
#include "stm32l4xx_ll_dma.h"
#include "stm32l4xx_ll_usart.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define SBT_RX_TX_BUF_SIZE	128
#define SBT_MAX_NO_UARTS	1

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
typedef struct sbt_Uart
{
	USART_TypeDef* 		huart;
	DMA_TypeDef*		dma_device;
	uint32_t			rx_dma_channel;
	osMessageQId 		rx_data_queue;
	int16_t				rx_buf_tail;
	uint8_t 			rx_buf[SBT_RX_TX_BUF_SIZE];	/* At 115200 baud 128 bytes will hold 10ms of data */
	uint32_t			tx_dma_channel;
	osSemaphoreId		tx_semaphore;
	osMessageQId		tx_data_queue;
	uint8_t 			tx_buf[SBT_RX_TX_BUF_SIZE];
} sbt_Uart_t;

typedef struct sbt_Init
{
	osMessageQId		rx_event_queue;
	uint16_t			no_uarts;
	sbt_Uart_t			uarts[SBT_MAX_NO_UARTS];
} sbt_Init_t;

typedef struct sbt_Event
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
void sbt_UARTRxCpltCallback(USART_TypeDef *huart);
void sbt_TxDMAIrqHandler(USART_TypeDef *huart);
void sbt_RxDMAIrqHandler(USART_TypeDef *huart);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SERIAL_BUFFER_TASK_H */
