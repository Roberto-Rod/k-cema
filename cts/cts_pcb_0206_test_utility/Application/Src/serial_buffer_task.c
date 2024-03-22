/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
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
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SBT_DMA_LIFCR_TC_FLAG(dma_channel) (1UL << ((8 * dma_channel) + 5))
#define SBT_DMA_LIFCR_HT_FLAG(dma_channel) (1UL << ((8 * dma_channel) + 4))
#define SBT_DMA_LIFCR_TE_FLAG(dma_channel) (1UL << ((8 * dma_channel) + 3))
#define SBT_DMA_HIFCR_TC_FLAG(dma_channel) (1UL << ((8 * (dma_channel - 4)) + 5))
#define SBT_DMA_HIFCR_HT_FLAG(dma_channel) (1UL << ((8 * (dma_channel - 4)) + 4))
#define SBT_DMA_HIFCR_TE_FLAG(dma_channel) (1UL << ((8 * (dma_channel - 4)) + 3))

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
static void sbt_InitialiseDMAReceiver(sbt_Uart_t *p_uart);
static void sbt_CheckDMAReceiver(sbt_Uart_t *p_uart);
static void sbt_ProcessDMATransmit(sbt_Uart_t *p_uart);

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
*
******************************************************************************/
void sbt_InitTask(sbt_Init_t init_data)
{
	memcpy(&lg_sbt_init_data, &init_data, sizeof(sbt_Init_t));
	lg_sbt_init_data.no_uarts = (init_data.no_uarts > SBT_MAX_NO_UARTS ? SBT_MAX_NO_UARTS : init_data.no_uarts);
	lg_sbt_initialised = true;
}

/*****************************************************************************/
/**
* Serial buffer task function.
*
* @param    argument defined by FreeRTOS function prototype, not used
*
******************************************************************************/
void sbt_SerialBufferTask(void const *argument)
{
	int16_t i = 0;

	if (!lg_sbt_initialised)
	{
		for(;;)
		{
			osDelay(1U);
		}
	}

	for (i = 0; i< lg_sbt_init_data.no_uarts; ++i)
	{
		/* Setup DMA receiver for each UART */
		sbt_InitialiseDMAReceiver(&lg_sbt_init_data.uarts[i]);
		(void) osSemaphoreRelease(lg_sbt_init_data.uarts[i].tx_semaphore);
	}

	for(;;)
	{
		for (i = 0; i< lg_sbt_init_data.no_uarts; ++i)
		{
			sbt_CheckDMAReceiver(&lg_sbt_init_data.uarts[i]);

			if (osMessageQueueGetCount(lg_sbt_init_data.uarts[i].tx_data_queue))
			{
				sbt_ProcessDMATransmit(&lg_sbt_init_data.uarts[i]);
			}
		}

        osDelay(1U);
	}
}


static void sbt_InitialiseDMAReceiver(sbt_Uart_t *p_uart)
{
	uint32_t uart_dma_reg_addr = LL_USART_DMA_GetRegAddr(p_uart->huart);

    LL_DMA_SetPeriphAddress(p_uart->dma_device, p_uart->rx_dma_stream, uart_dma_reg_addr);
    LL_DMA_SetMemoryAddress(p_uart->dma_device, p_uart->rx_dma_stream, (uint32_t)p_uart->rx_buf);
    LL_DMA_SetDataLength(p_uart->dma_device, p_uart->rx_dma_stream, sizeof(p_uart->rx_buf));

    /* Clear all flags */
    if ( p_uart->rx_dma_stream < LL_DMA_STREAM_4)
    {
		WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TC_FLAG(p_uart->rx_dma_stream));
		WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_HT_FLAG(p_uart->rx_dma_stream));
		WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TE_FLAG(p_uart->rx_dma_stream));
    }
    else
    {
		WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TC_FLAG(p_uart->rx_dma_stream));
		WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_HT_FLAG(p_uart->rx_dma_stream));
		WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TE_FLAG(p_uart->rx_dma_stream));
    }

    LL_USART_ClearFlag_FE(p_uart->huart);
    LL_USART_ClearFlag_ORE(p_uart->huart);

    /* Enable HT & TC interrupts */
    LL_DMA_EnableIT_HT(p_uart->dma_device, p_uart->rx_dma_stream);
    LL_DMA_EnableIT_TC(p_uart->dma_device, p_uart->rx_dma_stream);
    LL_USART_EnableDMAReq_RX(p_uart->huart);
    LL_DMA_EnableStream(p_uart->dma_device, p_uart->rx_dma_stream);
}


static void sbt_CheckDMAReceiver(sbt_Uart_t *p_uart)
{
    /* The DMA buffer (pointed to by (p_uart->rx_buf) is being written to in a circular manner by the hardware.
     * The buffer is of SBT_RX_TX_BUF_SIZE and the p_uart->rx_buf_tail is the index of the last byte processed by this task.
     * dma_buffer_available_space is read from the hardware (DMA_CNDTR NDT) and returns the number of bytes available
     * before the end of the buffer (since the rx buffer is in circular mode, the number of bytes before wrap around occurs) */
	uint32_t dma_buffer_available_space = LL_DMA_GetDataLength(p_uart->dma_device, p_uart->rx_dma_stream);
	uint32_t head = sizeof(p_uart->rx_buf) - dma_buffer_available_space;
	uint32_t count, next_tail, i;
	uint8_t data;

    if (head != p_uart->rx_buf_tail)
    {
    	count = (head > p_uart->rx_buf_tail) ? (head - p_uart->rx_buf_tail) : ((sizeof(p_uart->rx_buf) - p_uart->rx_buf_tail) + head);
        next_tail = p_uart->rx_buf_tail;

        for (i = 0U; i < count; ++i)
        {
        	data = (uint8_t)p_uart->rx_buf[next_tail++];
        	next_tail %= sizeof(p_uart->rx_buf);	/* Wrap tail if necessary */

        	if (osMessageQueuePut(p_uart->rx_data_queue, &data, 0U, 0U) == osOK)
        	{
        		p_uart->rx_buf_tail = next_tail;
        	}
        	else
        	{
        		/* p_uart->rx_buf_tail remains the same so we should attempt to process the data again next time */
        		break;
        	}
        }
    }
}


/*****************************************************************************/
/**
* Fill a tx buffer if there is data to send and start transmitting data.
*
* @param    p_uart UART device
*
******************************************************************************/
static void sbt_ProcessDMATransmit(sbt_Uart_t *p_uart)
{
	uint32_t tx_count;
	int16_t i = 0;
	uint8_t data = 0U;

	/* A bit dodgy as we could get stuck in here forever! */
    (void) osSemaphoreAcquire(p_uart->tx_semaphore, osWaitForever);

	tx_count = osMessageQueueGetCount(p_uart->tx_data_queue);
	tx_count = tx_count > sizeof(p_uart->tx_buf) ? sizeof(p_uart->tx_buf) : tx_count;

	for (i = 0; i < tx_count; ++i)
	{
		if (osMessageQueueGet(p_uart->tx_data_queue, &data, 0U, 0U) == osOK)
		{
			p_uart->tx_buf[i] = data;
		}
	}

    /* Configure DMA */
    LL_DMA_DisableStream(p_uart->dma_device, p_uart->tx_dma_stream);
    LL_DMA_SetPeriphAddress(p_uart->dma_device, p_uart->tx_dma_stream, LL_USART_DMA_GetRegAddr(p_uart->huart));
    LL_DMA_SetMemoryAddress(p_uart->dma_device, p_uart->tx_dma_stream, (uint32_t)p_uart->tx_buf);
    LL_DMA_SetDataLength(p_uart->dma_device, p_uart->tx_dma_stream, tx_count);

    /* Clear all flags */
    if ( p_uart->tx_dma_stream < LL_DMA_STREAM_4)
    {
    	WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TC_FLAG(p_uart->tx_dma_stream));
    	WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_HT_FLAG(p_uart->tx_dma_stream));
    	WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TE_FLAG(p_uart->tx_dma_stream));
    }
    else
    {
    	WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TC_FLAG(p_uart->tx_dma_stream));
    	WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_HT_FLAG(p_uart->tx_dma_stream));
    	WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TE_FLAG(p_uart->tx_dma_stream));
    }

    /* Start transfer */
    LL_DMA_EnableIT_TC(p_uart->dma_device, p_uart->tx_dma_stream);
    LL_USART_EnableDMAReq_TX(p_uart->huart);
    LL_DMA_EnableStream(p_uart->dma_device, p_uart->tx_dma_stream);
}


/*****************************************************************************/
/**
* Implements LL UART Rx data user callback function, just handle errors as
* rx/tx data is handled by DMA.
*
* @param    huart LL UART device definition handle for UART that caused irq
*
******************************************************************************/
void sbt_UARTRxCpltCallback(USART_TypeDef *huart)
{
	int16_t i = 0;

	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		if (huart == lg_sbt_init_data.uarts[i].huart)
		{
			/* Framing Error */
			if (LL_USART_IsActiveFlag_FE(huart))
			{
				LL_USART_ClearFlag_FE(huart);
			}
			/* Overrun Error */
			else if (LL_USART_IsActiveFlag_ORE(huart))
			{
				LL_USART_ClearFlag_ORE(huart);
			}
			else if (LL_USART_IsEnabledIT_IDLE(huart) && LL_USART_IsActiveFlag_IDLE(huart))
			{
				/* Clear IDLE line flag */
				LL_USART_ClearFlag_IDLE(huart);
			}

			/* Interrupt handled so break out of loop */
			break;
		}
	}
}


void sbt_TxDMAIrqHandler(USART_TypeDef *huart)
{
	int16_t i = 0;
	sbt_Uart_t *p_uart;

	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		if (huart == lg_sbt_init_data.uarts[i].huart)
		{
			p_uart = &lg_sbt_init_data.uarts[i];

		    if (LL_DMA_IsEnabledIT_TC(p_uart->dma_device, p_uart->tx_dma_stream))
		    {
		    	if ( p_uart->tx_dma_stream < LL_DMA_STREAM_4)
		    	{
					if (READ_BIT(p_uart->dma_device->LISR, SBT_DMA_LIFCR_TE_FLAG(p_uart->tx_dma_stream)) == SBT_DMA_LIFCR_TE_FLAG(p_uart->tx_dma_stream))
					{
						/* Clear transfer error flag */
						WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TE_FLAG(p_uart->tx_dma_stream));
						(void) osSemaphoreRelease(p_uart->tx_semaphore);
					}
					else if (READ_BIT(p_uart->dma_device->LISR, SBT_DMA_LIFCR_TC_FLAG(p_uart->tx_dma_stream)) == SBT_DMA_LIFCR_TC_FLAG(p_uart->tx_dma_stream))
					{
					   /* Clear transfer complete flag */
					   WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TC_FLAG(p_uart->tx_dma_stream));
					   (void) osSemaphoreRelease(p_uart->tx_semaphore);
					}
		    	}
		    	else
		    	{
					if (READ_BIT(p_uart->dma_device->HISR, SBT_DMA_HIFCR_TE_FLAG(p_uart->tx_dma_stream)) == SBT_DMA_HIFCR_TE_FLAG(p_uart->tx_dma_stream))
					{
						/* Clear transfer error flag */
						WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TE_FLAG(p_uart->tx_dma_stream));
						(void) osSemaphoreRelease(p_uart->tx_semaphore);
					}
					else if (READ_BIT(p_uart->dma_device->HISR, SBT_DMA_HIFCR_TC_FLAG(p_uart->tx_dma_stream)) == SBT_DMA_HIFCR_TC_FLAG(p_uart->tx_dma_stream))
					{
					   /* Clear transfer complete flag */
					   WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TC_FLAG(p_uart->tx_dma_stream));
					   (void) osSemaphoreRelease(p_uart->tx_semaphore);
					}
		    	}
		    }

			/* Interrupt handled so break out of loop */
			break;
		}
	}
}


void sbt_RxDMAIrqHandler(USART_TypeDef *huart)
{
	int16_t i = 0;
	sbt_Uart_t *p_uart;

	for (i = 0; i < lg_sbt_init_data.no_uarts; ++i)
	{
		if (huart == lg_sbt_init_data.uarts[i].huart)
		{
			p_uart = & lg_sbt_init_data.uarts[i];

	    	if ( p_uart->rx_dma_stream < LL_DMA_STREAM_4)
	    	{
				if (READ_BIT(p_uart->dma_device->LISR, SBT_DMA_LIFCR_TE_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_LIFCR_TE_FLAG(p_uart->rx_dma_stream))
				{
					/* Clear transfer error flag */
					WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TE_FLAG(p_uart->rx_dma_stream));
				}
				else if (LL_DMA_IsEnabledIT_HT(p_uart->dma_device, p_uart->rx_dma_stream) &&
							READ_BIT(p_uart->dma_device->LISR, SBT_DMA_LIFCR_HT_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_LIFCR_HT_FLAG(p_uart->rx_dma_stream))
				{
				   /* Clear half transfer complete flag */
				   WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_HT_FLAG(p_uart->rx_dma_stream));
				}
				else if (LL_DMA_IsEnabledIT_TC(p_uart->dma_device, p_uart->rx_dma_stream) &&
							READ_BIT(p_uart->dma_device->LISR, SBT_DMA_LIFCR_TC_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_LIFCR_TC_FLAG(p_uart->rx_dma_stream))
				{
				   /* Clear transfer complete flag */
				   WRITE_REG(p_uart->dma_device->LIFCR, SBT_DMA_LIFCR_TC_FLAG(p_uart->rx_dma_stream));
				}
	    	}
	    	else
	    	{
				if (READ_BIT(p_uart->dma_device->HISR, SBT_DMA_HIFCR_TE_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_HIFCR_TE_FLAG(p_uart->rx_dma_stream))
				{
					/* Clear transfer error flag */
					WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TE_FLAG(p_uart->rx_dma_stream));
				}
				else if (LL_DMA_IsEnabledIT_HT(p_uart->dma_device, p_uart->rx_dma_stream) &&
							READ_BIT(p_uart->dma_device->HISR, SBT_DMA_HIFCR_HT_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_HIFCR_HT_FLAG(p_uart->rx_dma_stream))
				{
				   /* Clear half transfer complete flag */
				   WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_HT_FLAG(p_uart->rx_dma_stream));
				}
				else if (LL_DMA_IsEnabledIT_TC(p_uart->dma_device, p_uart->rx_dma_stream) &&
							READ_BIT(p_uart->dma_device->HISR, SBT_DMA_HIFCR_TC_FLAG(p_uart->rx_dma_stream)) == SBT_DMA_HIFCR_TC_FLAG(p_uart->rx_dma_stream))
				{
				   /* Clear transfer complete flag */
				   WRITE_REG(p_uart->dma_device->HIFCR, SBT_DMA_HIFCR_TC_FLAG(p_uart->rx_dma_stream));
				}
	    	}

			/* Interrupt handled so break out of loop */
			break;
		}
	}
}
