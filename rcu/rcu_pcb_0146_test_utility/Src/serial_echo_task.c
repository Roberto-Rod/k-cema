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
#define __SERIAL_ECHO_TASK_C

#include "serial_echo_task.h"

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
	lg_set_init_data.tx_data_queue 	= init_data.tx_data_queue;
	lg_set_init_data.rx_data_queue 	= init_data.rx_data_queue;
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
		event = osMessageGet(lg_set_init_data.rx_data_queue, portMAX_DELAY);

		if (event.status == osEventMessage)
		{
			osMessagePut(lg_set_init_data.tx_data_queue, event.value.v, 0U);
		}
	}
}

