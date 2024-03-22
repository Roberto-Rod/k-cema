/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file serial_echo_task.h
**
** Include file for serial_echo_task.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SERIAL_ECHO_TASK_H
#define __SERIAL_ECHO_TASK_H

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
#define SET_MAX_NO_UARTS	2

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
#ifndef osMessageQId_t
typedef osMessageQId osMessageQueueId_t;
#endif

typedef struct
{
	uint16_t			no_uarts;
	osMessageQueueId_t 	tx_data_queue[SET_MAX_NO_UARTS];
	osMessageQueueId_t 	rx_data_queue[SET_MAX_NO_UARTS];
} set_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void set_InitTask(set_Init_t init_data);
void set_SerialEchoTask(void const * argument);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __SERIAL_ECHO_TASK_H */
