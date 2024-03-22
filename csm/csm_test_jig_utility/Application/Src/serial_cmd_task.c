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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SCT_MAX_BUF_SIZE		256
#define SCT_CMD_HISTORY_LEN		20

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

#define SCT_READ_GPI_CMD					"$GPI"
#define SCT_READ_GPI_CMD_LEN				4
#define SCT_READ_GPI_RESP					"!GPI"
#define SCT_READ_GPI_RESP_LEN				4

#define SCT_SET_GPO_CMD						"#GPO"
#define SCT_SET_GPO_CMD_LEN					4
#define SCT_SET_GPO_CMD_FORMAT				"#GPO %hd %hd"
#define SCT_SET_GPO_CMD_FORMAT_NO			2
#define SCT_SET_GPO_RESP					">GPO"
#define SCT_SET_GPO_RESP_LEN				4

#define SCT_SET_PPS_IP_SRC_CMD				"#PPSS"
#define SCT_SET_PPS_IP_SRC_CMD_LEN			5
#define SCT_SET_PPS_IP_SRC_CMD_FORMAT		"#PPSS %hd"
#define SCT_SET_PPS_IP_SRC_CMD_FORMAT_NO	1
#define SCT_SET_PPS_IP_SRC_RESP				">PPSS"
#define SCT_SET_PPS_IP_SRC_RESP_LEN			5

#define SCT_SET_PPS_DIR_CMD					"#PPSD"
#define SCT_SET_PPS_DIR_CMD_LEN				5
#define SCT_SET_PPS_DIR_CMD_FORMAT			"#PPSD %hd"
#define SCT_SET_PPS_DIR_CMD_FORMAT_NO		1
#define SCT_SET_PPS_DIR_RESP				">PPSD"
#define SCT_SET_PPS_DIR_RESP_LEN			5

#define SCT_SET_PPS_EN_CMD					"#PPS"
#define SCT_SET_PPS_EN_CMD_LEN				4
#define SCT_SET_PPS_EN_CMD_FORMAT			"#PPS %hd"
#define SCT_SET_PPS_EN_CMD_FORMAT_NO		1
#define SCT_SET_PPS_EN_RESP					">PPS"
#define SCT_SET_PPS_EN_RESP_LEN				4

#define SCT_READ_PPS_CMD					"$PPS"
#define SCT_READ_PPS_CMD_LEN				4
#define SCT_READ_PPS_RESP					"!PPS"
#define SCT_READ_PPS_RESP_LEN				4

#define SCT_SET_UART_IP_SRC_CMD				"#USS"
#define SCT_SET_UART_IP_SRC_CMD_LEN			4
#define SCT_SET_UART_IP_SRC_CMD_FORMAT		"#USS %hd"
#define SCT_SET_UART_IP_SRC_CMD_FORMAT_NO	1
#define SCT_SET_UART_IP_SRC_RESP			">USS"
#define SCT_SET_UART_IP_SRC_RESP_LEN		4

#define SCT_UART_START_STR_SEARCH_CMD		"#UDET"
#define SCT_UART_START_STR_SEARCH_CMD_LEN	5
#define SCT_UART_START_STR_SEARCH_RESP		">UDET"
#define SCT_UART_START_STR_SEARCH_RESP_LEN	5

#define SCT_GET_UART_STR_FOUND_CMD			"$UDET"
#define SCT_GET_UART_STR_FOUND_CMD_LEN		5
#define SCT_GET_UART_STR_FOUND_RESP			"!UDET"
#define SCT_GET_UART_STR_FOUND_RESP_LEN		5

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

#define SCT_UNKONWN_CMD_RESP				"?"
#define SCT_UNKONWN_CMD_RESP_LEN			1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef enum sct_GpoSignals
{
	power_cable_detect = 0,
	tamper_switch,
	som_sd_boot_enable,
	rcu_power_button,
	rcu_power_en_zeroise,
	keypad_power_button,
	keypad_power_en_zeroise,
	remote_power_on_in
} sct_GpoSignals_t;

/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
static void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
static void sct_FlushRespBuf(uint8_t *resp_buf);
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessReadGpiCommand(uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetPpsIpSrcCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetPpsDirCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessReadPpsCommand(uint8_t *resp_buf);
static void sct_ProcessSetUartIpSrcCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessUartStartStringSearch(uint8_t *resp_buf);
static void sct_ProcessGetUartStringFound(uint8_t *resp_buf);
static void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
static void sct_ProcessUnkownCommand(uint8_t *resp_buf);

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

const char *lg_sct_gpo_signal_names[remote_power_on_in + 1] = \
{
	"Power Cable Detect",
	"Tamper Switch",
	"SOM SD Boot Enable",
	"RCU Power Button",
	"RCU Power Enable Zeroise",
	"Keypad Power Button",
	"Keypad Power Enable Zeroise",
	"Remote Power On In"
};

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
* @return   None
*
******************************************************************************/
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	/* Try and find a match for the command */
	if (!strncmp((char *)cmd_buf, SCT_READ_GPI_CMD, SCT_READ_GPI_CMD_LEN))
	{
		sct_ProcessReadGpiCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN))
	{
		sct_ProcessSetGpoCommand(cmd_buf, resp_buf);
	}
	/* Set PPS command ordering is important, check for longest command first */
	else if (!strncmp((char *)cmd_buf, SCT_SET_PPS_IP_SRC_CMD, SCT_SET_PPS_IP_SRC_CMD_LEN))
	{
		sct_ProcessSetPpsIpSrcCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_PPS_DIR_CMD, SCT_SET_PPS_DIR_CMD_LEN))
	{
		sct_ProcessSetPpsDirCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_PPS_EN_CMD, SCT_SET_PPS_EN_CMD_LEN))
	{
		sct_ProcessEnablePpsCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_PPS_CMD, SCT_READ_PPS_CMD_LEN))
	{
		sct_ProcessReadPpsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_UART_IP_SRC_CMD, SCT_SET_UART_IP_SRC_CMD_LEN))
	{
		sct_ProcessSetUartIpSrcCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_UART_START_STR_SEARCH_CMD, SCT_UART_START_STR_SEARCH_CMD_LEN))
	{
		sct_ProcessUartStartStringSearch(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_UART_STR_FOUND_CMD, SCT_GET_UART_STR_FOUND_CMD_LEN))
	{
		sct_ProcessGetUartStringFound(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(resp_buf);
	}
	else
	{
		sct_ProcessUnkownCommand(resp_buf);
	}
}

/*****************************************************************************/
/**
* Read GPI input signals and print their values
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessReadGpiCommand(uint8_t *resp_buf)
{
	iot_GpioPinState_t pin_state = reset;
	iot_GpiPinId_t i = 0;
	const char *p_chanel_name = NULL;

	for (i = csm_master_rack_addr; i <= csm_slave_rack_addr; ++i)
	{
		pin_state =	iot_GetGpiPinState(i, &p_chanel_name);
		sprintf((char *)resp_buf, "%d - %s%s", pin_state, p_chanel_name, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_GPI_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the specified GPO signal to a specified state, pin is set "low" if
* set state parameter is '0', else "high"
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t signal = 0;
	int16_t set_state = 0;
	iot_GpoPinId_t gpo_pin;
	sct_GpoSignals_t signal_id;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_GPO_CMD_FORMAT, &signal, &set_state);

	if (no_params == SCT_SET_GPO_CMD_FORMAT_NO)
	{
		/* Map serial interface signal id to IO task pin id */
		switch ((sct_GpoSignals_t)signal)
		{
		case power_cable_detect:
			gpo_pin = csm_master_cable_det;
			break;

		case tamper_switch:
			gpo_pin = tamper_sw;
			break;

		case  som_sd_boot_enable:
			gpo_pin = som_sd_boot_en;
			break;

		case rcu_power_button:
			gpo_pin = rcu_pwr_btn;
			break;

		case rcu_power_en_zeroise:
			gpo_pin = rcu_pwr_en_zer;
			break;

		case keypad_power_button:
			gpo_pin = keypad_pwr_btn;
			break;

		case keypad_power_en_zeroise:
			gpo_pin = keypad_pwr_en_zer;
			break;

		case remote_power_on_in:
			gpo_pin = remote_pwr_on_in;
			break;

		default:
			gpo_pin = -1;
			break;
		}

		/* Validate the gpo_pin parameter and set pin state */
		if ((gpo_pin >= csm_slave_1pps_dir) && (gpo_pin <= remote_pwr_on_in))
		{
			iot_SetGpoPinState(gpo_pin, (set_state == 0 ? reset : set));

			sprintf((char *)resp_buf, "%s set to: %s%s",
					lg_sct_gpo_signal_names[signal], ((set_state == 0) ? "0" : "1"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Unknown GPO Pin! ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #GPO <Signal ID> <0|1> <ENTER>:%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Available Signals IDs (integer value):%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		for (signal_id = power_cable_detect; signal_id <= keypad_power_en_zeroise; ++signal_id)
		{
			sprintf((char *)resp_buf, "%d - %s%s",
					signal_id, lg_sct_gpo_signal_names[signal_id], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_GPO_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the multiplexed source for the 1PPS input from the CSM:
* 	- 0: RCU
* 	- 1: CSM Master
* 	- 2: CSM Slave
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessSetPpsIpSrcCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t pps_source = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_PPS_IP_SRC_CMD_FORMAT, &pps_source);

	if (no_params == SCT_SET_PPS_IP_SRC_CMD_FORMAT_NO)
	{	/* Validate the pps_source parameter and set GPIO pin states accordingly */
		switch (pps_source)
		{
		case 0:
			iot_SetGpoPinState(select_1pps_s0, reset);
			iot_SetGpoPinState(select_1pps_s1, reset);
			sprintf((char *)resp_buf, "RCU 1PPS Source Selected%s", SCT_CRLF);
			break;

		case 1:
			iot_SetGpoPinState(select_1pps_s0, set);
			iot_SetGpoPinState(select_1pps_s1, reset);
			sprintf((char *)resp_buf, "CSM Master 1PPS Source Selected%s", SCT_CRLF);
			break;

		case 2:
			iot_SetGpoPinState(select_1pps_s0, reset);
			iot_SetGpoPinState(select_1pps_s1, set);
			sprintf((char *)resp_buf, "CSM Slave 1PPS Source Selected%s", SCT_CRLF);
			break;

		default:
			sprintf((char *)resp_buf, "*** Invalid 1PPS Source! ***%s", SCT_CRLF);
			break;
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #PPSS <PPS Source [0|1|2]> <ENTER>:%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_PPS_IP_SRC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the direction of the CSM Slave 1PPS signal which is bi-directional.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessSetPpsDirCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t direction = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_PPS_DIR_CMD_FORMAT, &direction);

	if (no_params == SCT_SET_PPS_DIR_CMD_FORMAT_NO)
	{	/* If set_state is non-zero set the CSM Slave as 1PPS output */
		iot_SetGpoPinState(csm_slave_1pps_dir, (direction ? set : reset));
		sprintf((char *)resp_buf, "CSM Slave 1PPS direction %s%s", (direction ? "Output" : "Input"), SCT_CRLF);
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #PPSD <Direction [0|1]> <ENTER>:%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);

	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_PPS_DIR_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Enables/disables the 1PPS output to the CSM
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_PPS_EN_CMD_FORMAT, &set_state);

	if (no_params == SCT_SET_PPS_EN_CMD_FORMAT_NO)
	{	/* If set_state is non-zero enable the 1PPS output */
		iot_Enable1PpsOp(set_state ? true : false);
		sprintf((char *)resp_buf, "1PPS %s%s", (set_state ? "Enabled" : "Disabled"), SCT_CRLF);
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #PPS <Enable [0|1]> <ENTER>:%s", SCT_CRLF);
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
* Queries if the IO Task has detected a 1PPS signal and returns the result
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessReadPpsCommand(uint8_t *resp_buf)
{
	uint32_t pps_delta = 0U;

	if (iot_PpsDetected(&pps_delta))
	{
		sprintf((char *)resp_buf, "1PPS detected, delta: %lu ms%s", pps_delta, SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "1PPS NOT detected%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_READ_PPS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the multiplexed source for the UART input from the CSM:
* 	- 0: CSM Master
* 	- 1: CSM Slave
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessSetUartIpSrcCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t uart_source = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_UART_IP_SRC_CMD_FORMAT, &uart_source);

	if (no_params == SCT_SET_UART_IP_SRC_CMD_FORMAT_NO)
	{	/* Validate the uart_source parameter and set GPIO pin states accordingly */
		switch (uart_source)
		{
		case 0:
			iot_SetGpoPinState(select_uart_s0, reset);
			sprintf((char *)resp_buf, "CSM Master UART Source Selected%s", SCT_CRLF);
			break;

		case 1:
			iot_SetGpoPinState(select_uart_s0, set);
			sprintf((char *)resp_buf, "CSM Slave UART Source Selected%s", SCT_CRLF);
			break;

		default:
			sprintf((char *)resp_buf, "*** Invalid UART Source! ***%s", SCT_CRLF);
			break;
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #USS <UART Source [0|1]> <ENTER>:%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_UART_IP_SRC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Starts the UART string search task looking for the expected string.
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessUartStartStringSearch(uint8_t *resp_buf)
{
	extern const char *IOT_UART_EXPECTED_STRING;

	iot_UartStartStringSearch();
	sprintf((char *)resp_buf, "Started searching for string: %s%s", IOT_UART_EXPECTED_STRING, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_UART_START_STR_SEARCH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Query if the UART string search has found the expected string.
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessGetUartStringFound(uint8_t *resp_buf)
{
	extern const char *IOT_UART_EXPECTED_STRING;

	sprintf((char *)resp_buf, "String %s: %s%s",
			iot_UartIsStringFound() ? "found" : "NOT found",
			IOT_UART_EXPECTED_STRING, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_UART_STR_FOUND_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return the ADC data
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf)
{
	int16_t i = 0;
	uint16_t analogue_reading = 0U;
	const char *p_analogue_reading_name;

	sprintf((char *)resp_buf, "ADC Data:%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	for (i = 0; i < IOT_ANALOGUE_READINGS_NUM; ++i)
	{
		iot_GetAnalogueReading(i, &analogue_reading, &p_analogue_reading_name);
		sprintf((char *)resp_buf, "%u\t%s%s", analogue_reading, p_analogue_reading_name, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ADC_DATA_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Send response associated with receiving an unknown command
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
static void sct_ProcessUnkownCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s%s", SCT_UNKONWN_CMD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}
