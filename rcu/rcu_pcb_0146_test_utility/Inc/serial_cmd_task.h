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
#include "stm32l0xx_hal.h"

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
	I2C_HandleTypeDef* 	i2c_device;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
void sct_SerialCmdTask(void const * argument);

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

/* Command definitions */
#define SCT_HW_CONFIG_INFO_CMD			"$HCI"
#define SCT_HW_CONFIG_INFO_CMD_LEN		4
#define SCT_HW_CONFIG_INFO_RESP			"!HCI"
#define SCT_HW_CONFIG_INFO_RESP_LEN		4

#define SCT_HW_RST_CONFIG_INFO_CMD		"#RHCI"
#define SCT_HW_RST_CONFIG_INFO_CMD_LEN 	5
#define SCT_HW_RST_CONFIG_INFO_RESP		">RHCI"
#define SCT_HW_RST_CONFIG_INFO_RESP_LEN	4

#define SCT_HW_SET_PARAM_CMD			"#SHCI"
#define SCT_HW_SET_PARAM_CMD_LEN		5
#define SCT_HW_SET_PARAM_CMD_FORMAT		"#SHCI %d %16s"
#define SCT_HW_SET_PARAM_CMD_FORMAT_NO	2
#define SCT_HW_SET_PARAM_RESP			">SHCI"
#define SCT_HW_SET_PARAM_RESP_LEN		5

#define SCT_READ_BTN_CMD				"$BTN"
#define SCT_READ_BTN_CMD_LEN			4
#define SCT_READ_BTN_RESP				"!BTN"
#define SCT_READ_BTN_RESP_LEN			4

#define SCT_SET_BZR_CMD					"#BZR"
#define SCT_SET_BZR_CMD_LEN				4
#define SCT_SET_BZR_CMD_FORMAT			"#BZR %hu"
#define SCT_SET_BZR_CMD_FORMAT_NO		1
#define SCT_SET_BZR_RESP				">BZR"
#define SCT_SET_BZR_ESP_LEN				4

#define SCT_SET_XRST_CMD				"#XRST"
#define SCT_SET_XRST_CMD_LEN			5
#define SCT_SET_XRST_RESP				">XRST"
#define SCT_SET_XRST_RESP_LEN			5
#define SCT_SET_XRST_CMD_FORMAT			"#XRST %hu"
#define SCT_SET_XRST_CMD_FORMAT_NO		1

#define SCT_SET_LDC_CMD					"#LDC"
#define SCT_SET_LDC_CMD_LEN				4
#define SCT_SET_LDC_RESP				">LDC"
#define SCT_SET_LDC_RESP_LEN			4
#define SCT_SET_LDC_CMD_FORMAT			"#LDC %hd"
#define SCT_SET_LDC_CMD_FORMAT_NO		1

#define SCT_SET_LDM_CMD					"#LDM"
#define SCT_SET_LDM_CMD_LEN				4
#define SCT_SET_LDM_RESP				">LDM"
#define SCT_SET_LDM_RESP_LEN			4
#define SCT_SET_LDM_CMD_FORMAT			"#LDM %hd"
#define SCT_SET_LDM_CMD_FORMAT_NO		1

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef enum
{
	sct_PartNo = 0,
	sct_RevNo,
	sct_SerialNo,
	sct_BuildBatchNo
} sct_SetHciParams;

const char* sct_SetHciParamStrings[] = {
	"Part No",
	"Revision No",
	"Serial No",
	"Build Batch No"
};

/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
void sct_ProcessReceivedByte(uint8_t data);
void sct_FlushRespBuf(void);
void sct_ProcessCommand(void);
void sct_ProcessHwConfigInfoCommand(void);
void sct_ProcessResetHwConfigInfoCommand(void);
void sct_ProcessSetHwConfigInfoCommand(void);
void sct_ProcessReadButtonStateCommand(void);
void sct_ProcessSetBuzzerStateCommand(void);
void sct_ProcessSetXchangeResetStateCommand(void);
void sct_ProcessSetLedChangeEventCommand(void);
void sct_ProcessSetLedModeCommand(void);
void sct_ProcessUnkownCommand(void);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sct_Init_t lg_sct_init_data = {NULL, NULL, NULL};
bool lg_sct_initialised = false;

uint8_t 	lg_sct_cmd_buf[SCT_MAX_BUF_SIZE] = {0U};
uint16_t	lg_sct_cmd_buf_idx = 0U;
uint8_t 	lg_sct_resp_buf[SCT_MAX_BUF_SIZE];

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
