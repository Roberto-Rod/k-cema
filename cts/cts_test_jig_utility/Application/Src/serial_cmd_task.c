/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file serial_cmd_task.c
*
* Provides serial command task handling.
*
* Processes received serial bytes and converts them to commands, performs
* command error handling.
*
* Project   : K-CEMA
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "serial_cmd_task.h"
#include "io_task.h"
#include "version.h"
#include "hw_config_info.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SCT_MAX_BUF_SIZE		512
#define SCT_MAC_CMD_LEN			16
#define SCT_CMD_HISTORY_LEN		10
#define SCT_NUM_CMDS			22

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
#define SCT_CURSOR_UP			"[A"
#define SCT_CURSOR_DOWN			"[B"
#define SCT_CURSOR_FORWARD		"[C"
#define SCT_CURSOR_BACK			"[D"
#define SCT_CURSOR_NEXT_LINE	"[E"
#define SCT_CURSOR_PREV_LINE	"[F"
#define SCT_SCROLL_UP			"[S"
#define SCT_SCROLL_DOWN			"[T"
#define SCT_ENTER               13
#define SCT_ESC                 27
#define SCT_BACKSPACE           8
#define SCT_UP_ARROW            24

/* Serial command definitions */
#define SCT_SET_RX_ATT_CMD					"#RXATT"
#define SCT_SET_RX_ATT_CMD_LEN				6
#define SCT_SET_RX_ATT_CMD_FORMAT			"#RXATT %hu"
#define SCT_SET_RX_ATT_CMD_FORMAT_NO 		1
#define SCT_SET_RX_ATT_RESP					">RXATT"
#define SCT_SET_RX_ATT_RESP_LEN				6

#define SCT_SET_RX_PATH_CMD					"#RXP"
#define SCT_SET_RX_PATH_CMD_LEN				4
#define SCT_SET_RX_PATH_CMD_FORMAT			"#RXP %hu"
#define SCT_SET_RX_PATH_CMD_FORMAT_NO		1
#define SCT_SET_RX_PATH_RESP				">RXP"
#define SCT_SET_RX_PATH_RESP_LEN			4

#define SCT_SET_TX_ATT_CMD					"#TXATT"
#define SCT_SET_TX_ATT_CMD_LEN				6
#define SCT_SET_TX_ATT_CMD_FORMAT			"#TXATT %hu"
#define SCT_SET_TX_ATT_CMD_FORMAT_NO 		1
#define SCT_SET_TX_ATT_RESP					">TXATT"
#define SCT_SET_TX_ATT_RESP_LEN				6

#define SCT_SET_TX_PATH_CMD					"#TXP"
#define SCT_SET_TX_PATH_CMD_LEN				4
#define SCT_SET_TX_PATH_CMD_FORMAT			"#TXP %hu"
#define SCT_SET_TX_PATH_CMD_FORMAT_NO		1
#define SCT_SET_TX_PATH_RESP				">TXP"
#define SCT_SET_TX_PATH_RESP_LEN			4

#define SCT_SET_TX_DIV_CMD					"#TXD"
#define SCT_SET_TX_DIV_CMD_LEN				4
#define SCT_SET_TX_DIV_CMD_FORMAT			"#TXD %hu"
#define SCT_SET_TX_DIV_CMD_FORMAT_NO		1
#define SCT_SET_TX_DIV_RESP					">TXD"
#define SCT_SET_TX_DIV_RESP_LEN				4

#define SCT_SET_GPO_CMD						"#GPO"
#define SCT_SET_GPO_CMD_LEN					4
#define SCT_SET_GPO_CMD_FORMAT				"#GPO %hd %hd"
#define SCT_SET_GPO_CMD_FORMAT_NO			2
#define SCT_SET_GPO_RESP					">GPO"
#define SCT_SET_GPO_RESP_LEN				4

#define SCT_SET_TB_RF_PATH_CMD				"#TRFP"
#define SCT_SET_TB_RF_PATH_CMD_LEN			5
#define SCT_SET_TB_RF_PATH_CMD_FORMAT		"#TRFP %hu"
#define SCT_SET_TB_RF_PATH_CMD_FORMAT_NO	1
#define SCT_SET_TB_RF_PATH_RESP				">TRFP"
#define SCT_SET_TB_RF_PATH_RESP_LEN			5

#define SCT_SET_PPS_EN_CMD					"#PPSE"
#define SCT_SET_PPS_EN_CMD_LEN				5
#define SCT_SET_PPS_EN_CMD_FORMAT			"#PPSE %hd"
#define SCT_SET_PPS_EN_CMD_FORMAT_NO		1
#define SCT_SET_PPS_EN_RESP					">PPSE"
#define SCT_SET_PPS_EN_RESP_LEN				5

#define SCT_SET_PPS_SRC_CMD					"#PPSS"
#define SCT_SET_PPS_SRC_CMD_LEN				5
#define SCT_SET_PPS_SRC_CMD_FORMAT			"#PPSS %hd"
#define SCT_SET_PPS_SRC_CMD_FORMAT_NO		1
#define SCT_SET_PPS_SRC_RESP				">PPSS"
#define SCT_SET_PPS_SRC_RESP_LEN			5

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

#define SCT_GET_SYNTH_LOCK_DET_CMD			"$SYNLD"
#define SCT_GET_SYNTH_LOCK_DET_CMD_LEN		6
#define SCT_GET_SYNTH_LOCK_DET_RESP			"!SYNLD"
#define SCT_GET_SYNTH_LOCK_DET_RESP_LEN		6

#define SCT_SET_SYNTH_OP_FREQ_CMD			"#SYNFQ"
#define SCT_SET_SYNTH_OP_FREQ_CMD_LEN		6
#define SCT_SET_SYNTH_OP_FREQ_CMD_FORMAT	"#SYNFQ %lu"
#define SCT_SET_SYNTH_OP_FREQ_CMD_FORMAT_NO 1
#define SCT_SET_SYNTH_OP_FREQ_RESP			">SYNFQ"
#define SCT_SET_SYNTH_OP_FREQ_RESP_LEN		6

#define SCT_SET_SYNTH_PWR_DOWN_CMD			"#SYNPD"
#define SCT_SET_SYNTH_PWR_DOWN_CMD_LEN		6
#define SCT_SET_SYNTH_PWR_DOWN_CMD_FORMAT	"#SYNPD %hu"
#define SCT_SET_SYNTH_PWR_DOWN_CMD_FORMAT_NO 1
#define SCT_SET_SYNTH_PWR_DOWN_RESP			">SYNPD"
#define SCT_SET_SYNTH_PWR_DOWN_RESP_LEN		6

#define SCT_WRITE_SYNTH_REG_CMD				"#SYNRG"
#define SCT_WRITE_SYNTH_REG_CMD_LEN			6
#define SCT_WRITE_SYNTH_REG_CMD_FORMAT	"	#SYNRG %lx"
#define SCT_WRITE_SYNTH_REG_CMD_FORMAT_NO	1
#define SCT_WRITE_SYNTH_REG_RESP			">SYNRG"
#define SCT_WRITE_SYNTH_REG_RESP_LEN		6

#define SCT_INIT_SYNTH_CMD					"#SYNI"
#define SCT_INIT_SYNTH_CMD_LEN				5
#define SCT_INIT_SYNTH_RESP					">SYNI"
#define SCT_INIT_SYNTH_RESP_LEN				5

#define SCT_HW_CONFIG_INFO_CMD				"$HCI"
#define SCT_HW_CONFIG_INFO_CMD_LEN			4
#define SCT_HW_CONFIG_INFO_RESP				"!HCI"
#define SCT_HW_CONFIG_INFO_RESP_LEN			4

#define SCT_HW_RST_CONFIG_INFO_CMD			"#RHCI"
#define SCT_HW_RST_CONFIG_INFO_CMD_LEN 		5
#define SCT_HW_RST_CONFIG_INFO_RESP			">RHCI"
#define SCT_HW_RST_CONFIG_INFO_RESP_LEN		5

#define SCT_HW_SET_PARAM_CMD				"#SHCI"
#define SCT_HW_SET_PARAM_CMD_LEN			5
#define SCT_HW_SET_PARAM_CMD_FORMAT			"#SHCI %d %16s"
#define SCT_HW_SET_PARAM_CMD_FORMAT_NO		2
#define SCT_HW_SET_PARAM_RESP				">SHCI"
#define SCT_HW_SET_PARAM_RESP_LEN			5

#define SCT_SET_I2C_LOOPBACK_CMD			"#ILB"
#define SCT_SET_I2C_LOOPBACK_CMD_LEN		4
#define SCT_SET_I2C_LOOPBACK_CMD_FORMAT		"#ILB %hu"
#define SCT_SET_I2C_LOOPBACK_CMD_FORMAT_NO	1
#define SCT_SET_I2C_LOOPBACK_RESP			">ILB"
#define SCT_SET_I2C_LOOPBACK_RESP_LEN		4

#define SCT_EEPROM_WRITE_BYTE_CMD			"#EWRB"
#define SCT_EEPROM_WRITE_BYTE_CMD_LEN		5
#define SCT_EEPROM_WRITE_BYTE_CMD_FORMAT	"#EWRB %hx %hx"
#define SCT_EEPROM_WRITE_BYTE_CMD_FORMAT_NO	2
#define SCT_EEPROM_WRITE_BYTE_RESP			">EWRB"
#define SCT_EEPROM_WRITE_BYTE_RESP_LEN		5

#define SCT_EEPROM_READ_BYTE_CMD			"$ERDB"
#define SCT_EEPROM_READ_BYTE_CMD_LEN		5
#define SCT_EEPROM_READ_BYTE_CMD_FORMAT		"$ERDB %hx"
#define SCT_EEPROM_READ_BYTE_CMD_FORMAT_NO	1
#define SCT_EEPROM_READ_BYTE_RESP			"!ERDB"
#define SCT_EEPROM_READ_BYTE_RESP_LEN		5

#define SCT_EEPROM_READ_PAGE_CMD			"$ERDP"
#define SCT_EEPROM_READ_PAGE_CMD_LEN		5
#define SCT_EEPROM_READ_PAGE_CMD_FORMAT		"$ERDP %hx"
#define SCT_EEPROM_READ_PAGE_CMD_FORMAT_NO	1
#define SCT_EEPROM_READ_PAGE_RESP			"!ERDP"
#define SCT_EEPROM_READ_PAGE_RESP_LEN		5

#define SCT_UNKONWN_CMD_RESP				"?"
#define SCT_UNKONWN_CMD_RESP_LEN			1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef void (*sct_ProcessCommandFuncPtr_t)(uint8_t *cmd_buf, uint8_t *resp_buf);

typedef enum sct_SetHciParams
{
	sct_PartNo = 0,
	sct_RevNo,
	sct_SerialNo,
	sct_BuildBatchNo
} sct_SetHciParams_t;

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
static void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
static void sct_FlushRespBuf(uint8_t *resp_buf);
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessUnkownCommand(uint8_t *resp_buf);
static void sct_ProcessSetRxAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetRxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetTxAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetTxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetTxDividerCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetTestBoardRfPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetPpsSourceCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcesssGetAdcDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetSynthLockDetectCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetSynthOpFreqCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetSynthPowerDownCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessWriteSynthRegCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessInitSynthCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessResetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetI2cLoopbackCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEepromWriteByteCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEepromReadByteCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEepromReadPageCommand(uint8_t *cmd_buf, uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static sct_Init_t lg_sct_init_data = {0U};
static bool lg_sct_initialised = false;

static uint8_t 	lg_sct_cmd_buf_curr[SCT_MAX_BUF_SIZE] = {0U};
static uint8_t 	lg_sct_cmd_buf_hist[SCT_CMD_HISTORY_LEN][SCT_MAX_BUF_SIZE] = {0U};
static int16_t	lg_sct_cmd_buf_hist_idx = 0;
static int16_t	lg_sct_cmd_buf_hist_scroll_idx = 0;
static int16_t	lg_sct_cmd_buf_curr_idx = 0;

/*****************************************************************************/
/**
* Initialise the serial command task.
*
* @param    init_data    Initialisation data for the task
* @return   None
*
******************************************************************************/
void sct_InitTask(sct_Init_t init_data)
{
	memcpy((void *)&lg_sct_init_data, (void *)&init_data, sizeof(sct_Init_t));
	lg_sct_initialised = true;
}


/*****************************************************************************/
/**
* Process bytes received from the PC UART interface
*
* @param    argument required by FreeRTOS function prototype, not used
* @return   None
*
******************************************************************************/
void sct_SerialCmdTask(void const *argument)
{
	static uint8_t resp_buf[SCT_MAX_BUF_SIZE] = {0U};
	osEvent event;

	if (!lg_sct_initialised)
	{
		for(;;)
		{
			osDelay(1U);
		}
	}

  	HAL_Delay(100U);
  	/* Clear and reset the terminal */
  	sprintf((char *)resp_buf, "%s%s", SCT_CLS, SCT_HOME);
	sct_FlushRespBuf(resp_buf);
	/* Print software title and version banner */
	sprintf((char *)resp_buf, "%s %s - V%d.%d.%d%s",
			SW_PART_NO, SW_NAME, SW_VERSION_MAJOR, SW_VERSION_MINOR, SW_VERSION_BUILD, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	for(;;)
	{
		event = osMessageGet(lg_sct_init_data.rx_data_queue, portMAX_DELAY);

		if (event.status == osEventMessage)
		{
			sct_ProcessReceivedByte((uint8_t)event.value.v, resp_buf);
		}
	}
}


/*****************************************************************************/
/**
* Process a received byte and take appropriate action
*
* @param    data received byte to process
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
static void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf)
{
	/* To help with human-entered command strings, backspace key erases last character */
	if (data == SCT_BACKSPACE)
	{
		if (lg_sct_cmd_buf_curr_idx > 0U)
		{
			--lg_sct_cmd_buf_curr_idx;
		}

		sprintf((char *)resp_buf, "\b \b");
		sct_FlushRespBuf(resp_buf);
	}
	else if (data == SCT_ENTER)
	{
		/* Add null termination to command buffer and process command */
		lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx] = '\0';
		sct_ProcessCommand(lg_sct_cmd_buf_curr, resp_buf);

		/* Add command to the history buffer */
		memcpy(&lg_sct_cmd_buf_hist[lg_sct_cmd_buf_hist_idx], lg_sct_cmd_buf_curr, SCT_MAX_BUF_SIZE);

		if (++lg_sct_cmd_buf_hist_idx >= SCT_CMD_HISTORY_LEN)
		{
			lg_sct_cmd_buf_hist_idx = 0;
		}

		lg_sct_cmd_buf_hist_scroll_idx = lg_sct_cmd_buf_hist_idx;

		/* Reset index and clear buffer ready for next command */
		memset(lg_sct_cmd_buf_curr, 0U, SCT_MAX_BUF_SIZE);
		lg_sct_cmd_buf_curr_idx = 0U;
	}
	else
	{
		/* Add received byte to command buffer */
		lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx] = toupper(data);

		if (++lg_sct_cmd_buf_curr_idx >= SCT_MAX_BUF_SIZE)
		{
			lg_sct_cmd_buf_curr_idx = 0U;
		}

		/* Echo received data */
		sprintf((char *)resp_buf, "%c", data);
		sct_FlushRespBuf(resp_buf);

		/* Check for up/down cursor command sequences */
		if (lg_sct_cmd_buf_curr_idx >= 3)
		{
			if ((lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 3] == 0x1B) &&
					(lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 2] == 0x5B) &&
					(lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 1] == 0x41))
			{
				/* Clear the control sequence from the buffer */
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 3] = 0U;
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 2] = 0U;
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 1] = 0U;

				/* Tell terminal to clear line and move cursor home */
				sprintf((char *)resp_buf, "%s%s", SCT_CURSOR_NEXT_LINE, SCT_ERASE_LINE);
				sct_FlushRespBuf(resp_buf);

				/* Modify history index */
				if (--lg_sct_cmd_buf_hist_scroll_idx < 0)
				{
					lg_sct_cmd_buf_hist_scroll_idx = SCT_CMD_HISTORY_LEN - 1;
				}

				/* Copy into current buffer, echo back to user and move buffer index to end of the line */
				memcpy(lg_sct_cmd_buf_curr, &lg_sct_cmd_buf_hist[lg_sct_cmd_buf_hist_scroll_idx], SCT_MAX_BUF_SIZE);
				sct_FlushRespBuf(lg_sct_cmd_buf_curr);
				lg_sct_cmd_buf_curr_idx = strlen((char* )lg_sct_cmd_buf_curr);
			}
			else if ((lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 3] == 0x1B) &&
					(lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 2] == 0x5B) &&
					(lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 1] == 0x42))
			{
				/* Clear the control sequence from the buffer */
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 3] = 0U;
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 2] = 0U;
				lg_sct_cmd_buf_curr[lg_sct_cmd_buf_curr_idx - 1] = 0U;

				/* Tell terminal to clear line and move cursor home */
				sprintf((char *)resp_buf, "%s%s", SCT_CURSOR_NEXT_LINE, SCT_ERASE_LINE);
				sct_FlushRespBuf(resp_buf);

				/* Modify history index */
				if (++lg_sct_cmd_buf_hist_scroll_idx >= SCT_CMD_HISTORY_LEN)
				{
					lg_sct_cmd_buf_hist_scroll_idx = 0;
				}

				/* Copy into current buffer, echo back to user and move buffer index to end of the line */
				memcpy(lg_sct_cmd_buf_curr, &lg_sct_cmd_buf_hist[lg_sct_cmd_buf_hist_scroll_idx], SCT_MAX_BUF_SIZE);
				sct_FlushRespBuf(lg_sct_cmd_buf_curr);
				lg_sct_cmd_buf_curr_idx = strlen((char* )lg_sct_cmd_buf_curr);
			}
			else
			{
			}
		}
	}
}

/*****************************************************************************/
/**
* Flush contents of response buffer to UART tx queue
*
* @param    resp_buf data buffer to flush to UART tx queue
* @return   None
*
******************************************************************************/
static void sct_FlushRespBuf(uint8_t *resp_buf)
{
	int16_t i = 0;

	while ((resp_buf[i] != '\0')  && (i < SCT_MAX_BUF_SIZE))
	{
		osMessagePut(lg_sct_init_data.tx_data_queue, (uint32_t)resp_buf[i], 0U);
		++i;
	}
}


/*****************************************************************************/
/**
* Process received commands
*
* @param	cmd_buf buffer to extract commands from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	typedef struct process_cmd
	{
		char cmd_str[SCT_MAC_CMD_LEN];
		int16_t cmd_len;
		sct_ProcessCommandFuncPtr_t cmd_func;
	} process_cmd_t;

	/* Remember to modify SCT_NUM_CMDS when adding/removing commands from this array! */
	static const process_cmd_t process_cmd_func_map[SCT_NUM_CMDS] = {
			{SCT_SET_RX_ATT_CMD, SCT_SET_RX_ATT_CMD_LEN, sct_ProcessSetRxAttenCommand},
			{SCT_SET_RX_PATH_CMD, SCT_SET_RX_PATH_CMD_LEN, sct_ProcessSetRxPathCommand},
			{SCT_SET_TX_ATT_CMD, SCT_SET_TX_ATT_CMD_LEN, sct_ProcessSetTxAttenCommand},
			{SCT_SET_TX_PATH_CMD, SCT_SET_TX_PATH_CMD_LEN, sct_ProcessSetTxPathCommand},
			{SCT_SET_TX_DIV_CMD, SCT_SET_TX_DIV_CMD_LEN, sct_ProcessSetTxDividerCommand},
			{SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN, sct_ProcessSetGpoCommand},
			{SCT_SET_TB_RF_PATH_CMD, SCT_SET_TB_RF_PATH_CMD_LEN, sct_ProcessSetTestBoardRfPathCommand},
			{SCT_SET_PPS_EN_CMD, SCT_SET_PPS_EN_CMD_LEN, sct_ProcessEnablePpsCommand},
			{SCT_SET_PPS_SRC_CMD, SCT_SET_PPS_SRC_CMD_LEN, sct_ProcessSetPpsSourceCommand},
			{SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN, sct_ProcesssGetAdcDataCommand},
			{SCT_GET_SYNTH_LOCK_DET_CMD, SCT_GET_SYNTH_LOCK_DET_CMD_LEN, sct_ProcessGetSynthLockDetectCommand},
			{SCT_SET_SYNTH_OP_FREQ_CMD, SCT_SET_SYNTH_OP_FREQ_CMD_LEN, sct_ProcessSetSynthOpFreqCommand},
			{SCT_SET_SYNTH_PWR_DOWN_CMD, SCT_SET_SYNTH_PWR_DOWN_CMD_LEN, sct_ProcessSetSynthPowerDownCommand},
			{SCT_WRITE_SYNTH_REG_CMD, SCT_WRITE_SYNTH_REG_CMD_LEN, sct_ProcessWriteSynthRegCommand},
			{SCT_INIT_SYNTH_CMD, SCT_INIT_SYNTH_CMD_LEN, sct_ProcessInitSynthCommand},
			{SCT_HW_CONFIG_INFO_CMD, SCT_HW_CONFIG_INFO_CMD_LEN, sct_ProcessHwConfigInfoCommand},
			{SCT_HW_RST_CONFIG_INFO_CMD, SCT_HW_RST_CONFIG_INFO_CMD_LEN, sct_ProcessResetHwConfigInfoCommand},
			{SCT_HW_SET_PARAM_CMD, SCT_HW_SET_PARAM_CMD_LEN, sct_ProcessSetHwConfigInfoCommand},
			{SCT_SET_I2C_LOOPBACK_CMD, SCT_SET_I2C_LOOPBACK_CMD_LEN, sct_ProcessSetI2cLoopbackCommand},
			{SCT_EEPROM_WRITE_BYTE_CMD, SCT_EEPROM_WRITE_BYTE_CMD_LEN, sct_ProcessEepromWriteByteCommand},
			{SCT_EEPROM_READ_BYTE_CMD, SCT_EEPROM_READ_BYTE_CMD_LEN, sct_ProcessEepromReadByteCommand},
			{SCT_EEPROM_READ_PAGE_CMD, SCT_EEPROM_READ_PAGE_CMD_LEN, sct_ProcessEepromReadPageCommand}
	};

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	/* Try and find a match for the command */
	for (int16_t i = 0; i < SCT_NUM_CMDS; ++i)
	{
		if (!strncmp((char *)cmd_buf, process_cmd_func_map[i].cmd_str, process_cmd_func_map[i].cmd_len))
		{
			process_cmd_func_map[i].cmd_func(cmd_buf, resp_buf);
			return;
		}
	}

	/* Didn't find a command to process... */
	sct_ProcessUnkownCommand(resp_buf);
}

/*****************************************************************************/
/**
* Send response associated with receiving an unknown command
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessUnkownCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s%s", SCT_UNKONWN_CMD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Set receive attenuator to the specified value, units of value is 0.5 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetRxAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_RX_ATT_CMD_FORMAT, &atten) == SCT_SET_RX_ATT_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetRxAtten(atten))
		{
			sprintf((char *)resp_buf, "Set rx attenuator to %hu (x0.5 dB)%s", atten, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set rx attenuator to %hu (x0.5 dB) ***%s", atten, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_ATT_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set receive path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetRxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t path = 0U;
	const char *path_str = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_RX_PATH_CMD_FORMAT, &path) == SCT_SET_RX_PATH_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetRxPath(path, &path_str))
		{
			sprintf((char *)resp_buf, "Set rx path to %hu - %s%s", path, path_str, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set rx path to %hu ***%s", path, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_PATH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set transmit attenuator to the specified value, units of value is 0.5 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetTxAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_ATT_CMD_FORMAT, &atten) == SCT_SET_TX_ATT_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetTxAtten(atten))
		{
			sprintf((char *)resp_buf, "Set tx attenuator to %hu (x0.5 dB)%s", atten, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx attenuator to %hu (x0.5 dB) ***%s", atten, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_ATT_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set transmit path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetTxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t path = 0U;
	const char *path_str = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_PATH_CMD_FORMAT, &path) == SCT_SET_TX_PATH_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetTxPath(path, &path_str))
		{
			sprintf((char *)resp_buf, "Set tx path to %hu - %s%s", path, path_str, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx path to %hu ***%s", path, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_PATH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set transmit divider to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetTxDividerCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t divider = 0U;
	const char *divider_str = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_DIV_CMD_FORMAT, &divider) == SCT_SET_TX_DIV_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetTxDivider(divider, &divider_str))
		{
			sprintf((char *)resp_buf, "Set tx divider to %hu - %s%s", divider, divider_str, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx divider to %hu ***%s", divider, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_DIV_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the specified GPO signal to a specified state, pin is set "low" if
* set state parameter is '0', else "high"
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t gpo_pin = 0U;
	int16_t set_state = 0;
	const char *gpo_pin_name_str = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_GPO_CMD_FORMAT, &gpo_pin, &set_state) == SCT_SET_GPO_CMD_FORMAT_NO)
	{
		if (iot_SetGpoPinState((iot_GpoPins_t)gpo_pin, ((set_state == 0) ? iot_gpo_low : iot_gpo_high), &gpo_pin_name_str))
		{
			sprintf((char *)resp_buf, "%s set to: %s%s", gpo_pin_name_str, ((set_state == 0) ? "0" : "1"), SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set GPO Pin! ***%s", SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_GPO_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Set test board RF path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetTestBoardRfPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t path = 0U;
	const char *path_str = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_TB_RF_PATH_CMD_FORMAT, &path) == SCT_SET_TB_RF_PATH_CMD_FORMAT_NO)
	{	/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_SetTestBoardRfPath(path, &path_str))
		{
			sprintf((char *)resp_buf, "Set test board RF path to %hu - %s%s", path, path_str, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set test board RF path to %hu ***%s", path, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TB_RF_PATH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Enables/disables the STM32 1PPS output
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_PPS_EN_CMD_FORMAT, &set_state) == SCT_SET_PPS_EN_CMD_FORMAT_NO)
	{	/* If set_state is non-zero enable the 1PPS output */
		iot_Enable1PpsOp(set_state ? true : false);
		sprintf((char *)resp_buf, "1PPS %s%s", (set_state ? "Enabled" : "Disabled"), SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);

	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_PPS_EN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the 1PPS source to internal (STM32) or external (test jig J9).
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetPpsSourceCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_PPS_SRC_CMD_FORMAT, &set_state) == SCT_SET_PPS_SRC_CMD_FORMAT_NO)
	{	/* If set_state is non-zero enable the external 1PPS source */
		iot_Set1PpsSource(set_state ? true : false);
		sprintf((char *)resp_buf, "1PPS source %s%s", (set_state ? "External (Test Jig J9)" : "Internal (STM32)"), SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_PPS_SRC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Read and return the ADC data
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcesssGetAdcDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t ch_val;
	const char *ch_name_str;

	sprintf((char *)resp_buf, "ADC Data:%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	for (iot_AdcChannelId_t i = 0; i < iot_adc_ch_qty; ++i)
	{	/* The called function range checks the parameter and returns an error string if it is invalid */
		if (iot_GetAdcScaledValue(i, &ch_val, &ch_name_str))
		{
			sprintf((char *)resp_buf, "%-6hd: %s%s", ch_val, ch_name_str, SCT_CRLF);
		}
		else
		{	/* Print error message */
			sprintf((char *)resp_buf, "*** %s ***%s", ch_name_str, SCT_CRLF);
		}
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ADC_DATA_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read synth lock detect signal
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetSynthLockDetectCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "Synth Lock Detect: %hd%s", iot_GetSynthLockDetect() ? 1 : 0, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_SYNTH_LOCK_DET_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set synth output frequency in MHz
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetSynthOpFreqCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint32_t freq_mhz = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_SYNTH_OP_FREQ_CMD_FORMAT, &freq_mhz) == SCT_SET_SYNTH_OP_FREQ_CMD_FORMAT_NO)
	{
		if (iot_SetSynthFreqMhz(freq_mhz))
		{
			sprintf((char *)resp_buf, "Set synth to %lu MHz%s", freq_mhz, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set synth frequency %lu ***%s", freq_mhz, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_SYNTH_OP_FREQ_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set synth power down mode
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetSynthPowerDownCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t enable = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_SYNTH_PWR_DOWN_CMD_FORMAT, &enable) == SCT_SET_SYNTH_PWR_DOWN_CMD_FORMAT_NO)
	{
		if (iot_SetSynthPowerDown(enable ? true : false))
		{
			sprintf((char *)resp_buf, "Set synth power down to: %s%s", (enable ? "Enabled" : "Disabled"), SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set synth power down to: %s ***%s", (enable ? "Enabled" : "Disabled"), SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_SYNTH_PWR_DOWN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Write the specified 32-bit register value to the synth
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessWriteSynthRegCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint32_t reg_val = 0U;

	if (sscanf((char *)cmd_buf, SCT_WRITE_SYNTH_REG_CMD_FORMAT, &reg_val) == SCT_WRITE_SYNTH_REG_CMD_FORMAT_NO)
	{
		if (iot_WriteSynthRegister(reg_val))
		{
			sprintf((char *)resp_buf, "Wrote synth register value: %08lX%s", reg_val, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to write synth register value:%08lX ***%s", reg_val, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_WRITE_SYNTH_REG_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Initialise the synth
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessInitSynthCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	if (iot_InitSynth())
	{
		sprintf((char *)resp_buf, "Synth successfully initialised.%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "Synth initialisation failed!%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_INIT_SYNTH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Read and return hardware configuration information
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	hci_HwConfigInfoData_t hw_config_info;

	if (iot_ReadHwConfigInfo(&hw_config_info))
	{
		sprintf((char *)resp_buf, "Hardware Configuration Information:%s%s", SCT_CRLF, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Version No: %c%c%s%s",
				((hw_config_info.hw_version > 25U) ? (int16_t)('A') : ((int16_t)hw_config_info.hw_version + (int16_t)('A'))),
				(hw_config_info.hw_version > 25U ? ((int16_t)hw_config_info.hw_version - 26 + (int16_t)('A')) : (int16_t)(' ')),
				SCT_CRLF, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Hardware Mod Version No: %u%s", hw_config_info.hw_mod_version, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Assembly Part No: %s%s", hw_config_info.assy_part_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Assembly Revision No: %s%s",hw_config_info.assy_rev_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Assembly Serial No: %s%s", hw_config_info.assy_serial_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Assembly Build Date or Batch No: %s%s", hw_config_info.assy_build_date_batch_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Hardware Configuration Information CRC: 0x%x%s", hw_config_info.hci_crc, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Hardware Configuration Information CRC Valid: %s%s", (hw_config_info.hci_crc_valid != 0U ? "True" : "False"), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Hardware Configuration Information! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_HW_CONFIG_INFO_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Clears the contents of the HCI EEPROM, sets all data values to '\0'
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessResetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	if (iot_ResetHwConfigInfo())
	{
		sprintf((char *)resp_buf, "Successfully cleared HCI EEPROM%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to clear HCI EEPROM! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_HW_RST_CONFIG_INFO_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets parameter in HCI EEPROM
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int32_t param_to_set;
	bool param_set = false;
	char param[HCI_STR_PARAM_LEN] = {0};

	if (sscanf((char *)cmd_buf, SCT_HW_SET_PARAM_CMD_FORMAT,
			(int *)&param_to_set, param) == SCT_HW_SET_PARAM_CMD_FORMAT_NO)
	{
		/* Ensure last character of string to set is null terminator */
		param[HCI_STR_PARAM_LEN - 1] = 0U;

		if (param_to_set <= sct_BuildBatchNo)
		{
			switch (param_to_set)
			{
			case sct_PartNo:
				param_set = iot_SetAssyPartNo((uint8_t *)param);
				break;

			case sct_RevNo:
				param_set = iot_SetAssyRevNo((uint8_t *)param);
				break;

			case sct_SerialNo:
				param_set = iot_SetAssySerialNo((uint8_t *)param);
				break;

			case sct_BuildBatchNo:
				param_set = iot_SetAssyBuildDataBatchNo((uint8_t *)param);
				break;

			default:
				param_set = false;
				break;
			}

			if (param_set)
			{
				sprintf((char *)resp_buf,
						"Successfully set parameter [%s] to [%s]%s",
						sct_SetHciParamStrings[param_to_set], param, SCT_CRLF);
			}
			else
			{
				sprintf((char *)resp_buf,
						"*** Failed to set parameter [%s] ***%s",
						sct_SetHciParamStrings[param_to_set], SCT_CRLF);
			}
		}
		else
		{
			sprintf((char *)resp_buf, "*** Unknown Parameter! ***%s", SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_HW_SET_PARAM_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the I2C loop back enable signal to the specified state, pin is set "low"
* if set state parameter is '0', else "high"/
*
* To prevent the I2C pull-ups back powering the Digital Board the I2C loop back
* should be enabled (default state) to isolate the I2C bus when the Digital
* Board is NOT powered up.  The loop back can be disabled once the Digital
* Board has been powered up.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetI2cLoopbackCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_I2C_LOOPBACK_CMD_FORMAT, &set_state) == SCT_SET_I2C_LOOPBACK_CMD_FORMAT_NO)
	{
		if (iot_SetI2cLoobackEnable(((set_state == 0) ? false : true)))
		{
			sprintf((char *)resp_buf, "I2C Loopback Enable set to: %s%s", ((set_state == 0) ? "0" : "1"), SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set I2C Loopback Enable! ***%s", SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_I2C_LOOPBACK_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Write a byte to the I2C EEPROM.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessEepromWriteByteCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t address = 0U;
	uint16_t data = 0U;

	if (sscanf((char *)cmd_buf, SCT_EEPROM_WRITE_BYTE_CMD_FORMAT, &address, &data) == SCT_EEPROM_WRITE_BYTE_CMD_FORMAT_NO)
	{
		uint8_t b_data = (uint8_t)data;
		if (iot_I2cEepromWriteByte(address, b_data))
		{
			sprintf((char *)resp_buf, "Write I2C EEPROM address 0x%X: 0x%02X%s", address, b_data, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** I2C EEPROM write byte failed! ***%s", SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_EEPROM_WRITE_BYTE_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read a byte from the I2C EEPROM.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessEepromReadByteCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t address = 0U;

	if (sscanf((char *)cmd_buf, SCT_EEPROM_READ_BYTE_CMD_FORMAT, &address) == SCT_EEPROM_READ_BYTE_CMD_FORMAT_NO)
	{
		uint8_t data = 0U;
		if (iot_I2cEepromReadByte(address, &data))
		{
			sprintf((char *)resp_buf, "Read I2C EEPROM address 0x%X: 0x%02X%s", address, data, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** I2C EEPROM read byte failed! ***%s", SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_EEPROM_READ_BYTE_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read a page from the I2C EEPROM.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessEepromReadPageCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t page_address = 0U;

	if (sscanf((char *)cmd_buf, SCT_EEPROM_READ_PAGE_CMD_FORMAT, &page_address) == SCT_EEPROM_READ_PAGE_CMD_FORMAT_NO)
	{
		uint8_t b_data[IOT_EEPROM_PAGE_SIZE_BYTES] = {0U};
		if (iot_I2cEepromReadPage(page_address, b_data))
		{
			sprintf((char *)resp_buf, "Read I2C EEPROM page address 0x%X:%s", page_address, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);

			for (uint16_t i = 0U; i < IOT_EEPROM_PAGE_SIZE_BYTES; ++i)
			{
				sprintf((char *)resp_buf, "0x%X: 0x%02X%s", page_address + i, b_data[i], SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
		}
		else
		{
			sprintf((char *)resp_buf, "*** I2C EEPROM read page failed! ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_EEPROM_READ_PAGE_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}
