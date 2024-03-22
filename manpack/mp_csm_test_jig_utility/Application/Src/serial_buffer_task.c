/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file serial_buffer_task.c
*
* Provides serial buffer task handling.
*
* Processes received serial bytes and sends them to tasks for handling
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "serial_buffer_task.h"

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

/*****************************************************************************/
/**
* Initialise the serial buffer task.
*
* @param    init_data initialisation data for the task
* @return   None
*
******************************************************************************/
void sbt_InitTask(sbt_Init_t init_data)
{
	int16_t i = 0;

	lg_sbt_init_data.rx_event_queue	= init_data.rx_event_queue;
	lg_sbt_init_data.no_uarts = (init_data.no_uarts > SBT_MAX_NO_UARTS ? SBT_MAX_NO_UARTS : init_data.no_uarts);

	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		lg_sbt_init_data.uarts[i].huart 				= init_data.uarts[i].huart;
		lg_sbt_init_data.uarts[i].uart_rx_data_queue	= init_data.uarts[i].uart_rx_data_queue;
		lg_sbt_init_data.uarts[i].uart_tx_data_queue 	= init_data.uarts[i].uart_tx_data_queue;
	}

	lg_sbt_initialised = true;
}

/*****************************************************************************/
/**
* Serial buffer task function.
*
* @param    argument defined by FreeRTOS function prototype, not used
* @return   None
*
******************************************************************************/
void sbt_SerialBufferTask(void const *argument)
{
	sbt_Event_t* p_event_buf = NULL;
	uint32_t rx_count = 0U;
	int16_t i = 0, j = 0;;
	osEvent event;

	if (!lg_sbt_initialised)
	{
		for(;;);
	}

	/* Put all of the UARTs in to interrupt receive mode */
	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		(void) HAL_UART_Receive_IT(lg_sbt_init_data.uarts[i].huart, &lg_sbt_init_data.uarts[i].uart_rx_buf, 1U);
	}

	for(;;)
	{
		osDelay(1);

		rx_count = osMessageWaiting(lg_sbt_init_data.rx_event_queue);

		if (rx_count > 0U)
		{
			for (j = 0; j < rx_count; ++j)
			{
				event = osMessageGet(lg_sbt_init_data.rx_event_queue, 0U);

				if (event.status == osEventMessage)
				{
					p_event_buf = (sbt_Event_t *)&event.value.v;
					osMessagePut(lg_sbt_init_data.uarts[p_event_buf->uart_idx].uart_rx_data_queue, (uint32_t)p_event_buf->data, 0U);
				}
			}
		}

		for (i = 0; i< lg_sbt_init_data.no_uarts; ++i)
		{
			sbt_ProcessTxBuffer(lg_sbt_init_data.uarts[i].huart,
								lg_sbt_init_data.uarts[i].uart_tx_data_queue,
								lg_sbt_init_data.uarts[i].uart_tx_buf);

			(void) HAL_UART_Receive_IT(lg_sbt_init_data.uarts[i].huart, &lg_sbt_init_data.uarts[i].uart_rx_buf, 1U);
		}
	}
}

/*****************************************************************************/
/**
* Fill a tx buffer if there is data to send and start transmitting data.
*
* @param    huart HAL UART device definition handle
* @parma	uart_tx_data_queue handle for CMSIS queue to pull tx bytes from
* @param	uart_tx_buf pointer to buffer to fill with bytes for transmission
* @return   None
*
******************************************************************************/
void sbt_ProcessTxBuffer(	UART_HandleTypeDef* huart,
							osMessageQId		uart_tx_data_queue,
							uint8_t*			uart_tx_buf)
{
	uint32_t tx_count = 0U;
	int16_t i = 0;
	osEvent event;

	tx_count = osMessageWaiting(uart_tx_data_queue);

	if ((huart->gState == HAL_UART_STATE_READY) && (tx_count > 0U))
	{
		if (tx_count > SBT_TX_BUF_SIZE)
		{
			tx_count = SBT_TX_BUF_SIZE;
		}

		for (i = 0; i < tx_count; ++i)
		{
			event = osMessageGet(uart_tx_data_queue, 0U);

			if (event.status == osEventMessage)
			{
				 uart_tx_buf[i] = (int8_t)event.value.v;
			}
		}

		HAL_UART_Transmit_IT(huart, uart_tx_buf, tx_count);
	}
}

/*****************************************************************************/
/**
* Implements HAL UART Rx data user callback function
*
* @param    huart HAL UART device definition handle for UART that caused irq
*
******************************************************************************/
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	sbt_Event_t event_buf;
	uint32_t* p_event_buf = (uint32_t*)&event_buf;
	int16_t i = 0;

	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		if (huart == lg_sbt_init_data.uarts[i].huart)
		{
			event_buf.uart_idx = (uint8_t)i;
			event_buf.data = lg_sbt_init_data.uarts[i].uart_rx_buf;
			(void) HAL_UART_Receive_IT(huart, &lg_sbt_init_data.uarts[i].uart_rx_buf, 1U);
			osMessagePut(lg_sbt_init_data.rx_event_queue, *p_event_buf, 0U);
			break;
		}
	}
}
