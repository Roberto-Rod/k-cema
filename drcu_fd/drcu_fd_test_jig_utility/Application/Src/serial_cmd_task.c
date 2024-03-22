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
#define SCT_MAX_BUF_SIZE					256
#define SCT_MAX_CMD_LEN						16
#define SCT_CMD_HISTORY_LEN					10
#define SCT_NUM_CMDS						5

#define SCT_SET_PPS_EN_CMD					"#PPSE"
#define SCT_SET_PPS_EN_CMD_LEN				5
#define SCT_SET_PPS_EN_CMD_FORMAT			"#PPSE %hd"
#define SCT_SET_PPS_EN_CMD_FORMAT_NO		1
#define SCT_SET_PPS_EN_RESP					">PPSE"
#define SCT_SET_PPS_EN_RESP_LEN				5

#define SCT_GET_PPS_DET_CMD					"$PPSD"
#define SCT_GET_PPS_DET_CMD_LEN				5
#define SCT_GET_PPS_DET_RESP				"!PPSD"
#define SCT_GET_PPS_DET_RESP_LEN			5

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

#define SCT_GET_GPI_CMD						"$GPI"
#define SCT_GET_GPI_CMD_LEN					4
#define SCT_GET_GPI_RESP					"!GPI"
#define SCT_GET_GPI_RESP_LEN				4

#define SCT_SET_GPO_CMD						"#GPO"
#define SCT_SET_GPO_CMD_LEN					4
#define SCT_SET_GPO_CMD_FORMAT				"#GPO %hd %hd"
#define SCT_SET_GPO_CMD_FORMAT_NO			2
#define SCT_SET_GPO_RESP					">GPO"
#define SCT_SET_GPO_RESP_LEN				4

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
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetPpsDetectedCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcesssGetAdcDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetGpiCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);

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
		char cmd_str[SCT_MAX_CMD_LEN];
		int16_t cmd_len;
		sct_ProcessCommandFuncPtr_t cmd_func;
	} process_cmd_t;

	/* Remember to modify SCT_NUM_CMDS when adding/removing commands from this array! */
	static const process_cmd_t process_cmd_func_map[SCT_NUM_CMDS] = {
			{SCT_SET_PPS_EN_CMD, SCT_SET_PPS_EN_CMD_LEN, sct_ProcessEnablePpsCommand},
			{SCT_GET_PPS_DET_CMD, SCT_GET_PPS_DET_CMD_LEN, sct_ProcessGetPpsDetectedCommand},
			{SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN, sct_ProcesssGetAdcDataCommand},
			{SCT_GET_GPI_CMD, SCT_GET_GPI_CMD_LEN, sct_ProcessGetGpiCommand},
			{SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN, sct_ProcessSetGpoCommand},
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
* Queries if the IO Task has detected a 1PPS signal and returns the result
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetPpsDetectedCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint32_t pps_delta = 0U;

	if (iot_1ppsDetected(&pps_delta))
	{
		sprintf((char *)resp_buf, "1PPS detected, delta: %lu ms%s", pps_delta, SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "1PPS NOT detected%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_PPS_DET_RESP, SCT_CRLF);
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
			sprintf((char *)resp_buf, "%-6hd : %s%s", ch_val, ch_name_str, SCT_CRLF);
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
* Read GPI input signals and print their values
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetGpiCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	iot_GpioPinState_t pin_state = iot_gpio_reset;
	const char *p_gpio_name = NULL;

	for (iot_GpiPinId_t i = 0; i < iot_gpi_qty; ++i)
	{
		pin_state =	iot_GetGpiPinState(i, &p_gpio_name);
		sprintf((char *)resp_buf, "%d - %s%s", pin_state, ((p_gpio_name == NULL)? "" : p_gpio_name), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_GPI_RESP, SCT_CRLF);
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
	int16_t gpo_pin = 0;
	int16_t set_state = iot_gpio_reset;
	const char *p_gpio_name = NULL;

	if (sscanf((char *)cmd_buf, SCT_SET_GPO_CMD_FORMAT, &gpo_pin, &set_state) == SCT_SET_GPO_CMD_FORMAT_NO)
	{
		/* Validate the gpo_pin parameter */
		if (((iot_GpoPinId_t)gpo_pin >= 0) && ((iot_GpoPinId_t)gpo_pin < iot_gpo_qty))
		{
			iot_SetGpoPinState((iot_GpoPinId_t)gpo_pin, (iot_GpioPinState_t)set_state, &p_gpio_name);
			sprintf((char *)resp_buf, "%s set to: %s%s",
					((p_gpio_name == NULL) ? "" : p_gpio_name),
					(((iot_GpioPinState_t)set_state == iot_gpio_reset) ? "0" : "1"), SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Unknown GPO Pin! ***%s", SCT_CRLF);
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

