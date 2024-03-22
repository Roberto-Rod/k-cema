/****************************************************************************/
/**
** Copyright 2020 Davies Systems Ltd & Kirintec Ltd. All rights reserved.
**
** @file serial_cmd_task.h
**
** Include file for serial_cmd_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
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
typedef struct
{
	osMessageQId 		pc_tx_data_queue;
	osMessageQId 		pc_rx_data_queue;
	osMessageQId 		ema_tx_data_queue;
	osMessageQId 		ema_rx_data_queue;
	GPIO_TypeDef*		dop_power_off_pin_port;
	uint16_t			dop_power_off_pin;
	GPIO_TypeDef*		dop_rf_mute_pin_port;
	uint16_t			dop_rf_mute_pin;
	TIM_HandleTypeDef 	*htim_1pps;
	uint32_t 			tim_channel_1pps;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
void sct_SerialCmdEmaTask(void const *argument);
void sct_SerialCmdTask(void const *argument);

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
#ifdef __SERIAL_CMD_TASK_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SCT_MAX_BUF_SIZE		256

/* Some basic ASCII and ANSI terminal control codes */
#define SCT_CRLF                "\r\n"          /* Carriage return & line feed */
#define SCT_CR                  "\r"            /* Carriage return only */
#define SCT_LF                  "\n"            /* New line only */
#define SCT_TAB                 "\t"            /* Horizontal tab */
#define SCT_CLS                 "[2J"          /* Clear screen */
#define SCT_CL                  "[K"           /* Clear from cursor to end of line */
#define SCT_ERASE_LINE          "[2K"
#define SCT_HOME                "[H"           /* Move cursor to top corner */
#define SCT_LINE_HOME           "[1000D"       /* Assumes the current line isn't longer than 1000 characters! */
#define SCT_RESETSCREEN         "[0;37;40m" CLS HOME
#define SCT_REDTEXT             "[0;1;31m"
#define SCT_YELLOWTEXT          "[0;1;33m"
#define SCT_GREENTEXT           "[0;1;32m"
#define SCT_WHITETEXT           "[0;1;37m"
#define SCT_DEFAULTTEXT         WHITETEXT
#define SCT_FLASHTEXT           "[5m"
#define SCT_UNDERLINETEXT       "[4m"
#define SCT_RESETTEXTATTRIBUTES "[0m"
#define SCT_ENTER               13
#define SCT_ESC                 27
#define SCT_BACKSPACE           8
#define SCT_UP_ARROW            24

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
void sct_FlushRespBuf(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sct_Init_t lg_sct_init_data = {NULL, NULL, NULL};
bool lg_sct_initialised = false;
bool lg_sct_uart_echo_enabled = false;
bool lg_sct_1pps_enabled = false;

uint8_t 	lg_sct_cmd_buf[SCT_MAX_BUF_SIZE] = {0U};
uint16_t	lg_sct_cmd_buf_idx = 0U;

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
