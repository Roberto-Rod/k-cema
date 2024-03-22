/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file serial_echo_task.c
*
* Provides serial echo task handling, incoming bytes on the rx queue are
* forwarded to the tx queue.
* <br><br>
* Echos received bytes
*
* Project   : K-CEMA
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
* @todo None
*
******************************************************************************/
#include "serial_echo_task.h"

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


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
set_Init_t lg_set_init_data = {0};
bool lg_set_initialised = false;

/*****************************************************************************/
/**
* Initialise the serial echo task.
*
* @param    init_data initialisation data for the task
* @return   None
* @note     None
*
******************************************************************************/
void set_InitTask(set_Init_t init_data)
{
	for (uint16_t i = 0U; i < SET_MAX_NO_UARTS; ++i)
	{
		lg_set_init_data.tx_data_queue[i] = init_data.tx_data_queue[i];
		lg_set_init_data.rx_data_queue[i] = init_data.rx_data_queue[i];
	}
	lg_set_initialised = true;
}

/*****************************************************************************/
/**
* Serial echo task function.
*
* @param    argument not used
* @return   None
* @note     None
*
******************************************************************************/
void set_SerialEchoTask(void const * argument)
{
	osEvent event;

	if (!lg_set_initialised)
	{
		for(;;)
		{
		}
	}

	for(;;)
	{
		for (uint16_t i = 0U; i < SET_MAX_NO_UARTS; ++i)
		{
			uint32_t rx_waiting = osMessageWaiting(lg_set_init_data.rx_data_queue[i]);

			for (uint32_t j = 0U; j < rx_waiting; ++j)
			{
				event = osMessageGet(lg_set_init_data.rx_data_queue[i], 0U);

				if (event.status == osEventMessage)
				{
					osMessagePut(lg_set_init_data.tx_data_queue[i], event.value.v, 0U);
				}
			}
		}
		osDelay(1U);
	}
}

