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

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

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

#define SCT_SET_I2C_BUS_CMD					"#I2CB"
#define SCT_SET_I2C_BUS_CMD_LEN				5
#define SCT_SET_I2C_BUS_CMD_FORMAT			"#I2CB %hd"
#define SCT_SET_I2C_BUS_CMD_FORMAT_NO		1
#define SCT_SET_I2C_BUS_RESP				">I2CB"
#define SCT_SET_I2C_BUS_RESP_LEN			5

#define SCT_INIT_FAN_CTRLR					"#INIFAN"
#define SCT_INIT_FAN_CTRLR_LEN				7
#define SCT_INIT_FAN_CTRLR_RESP				">INIFAN"
#define SCT_INIT_FAN_CTRLR_RESP_LEN			7

#define SCT_FAN_GET_SPEED_CMD				"$FSP"
#define SCT_FAN_GET_SPEED_CMD_LEN			4
#define SCT_FAN_GET_SPEED_RESP				"!FSP"
#define SCT_FAN_GET_SPEED_RESP_LEN			4

#define SCT_FAN_SET_DUTY					"#FDS"
#define SCT_FAN_SET_DUTY_LEN				4
#define SCT_FAN_SET_DUTY_FORMAT				"#FDS %hui"
#define SCT_FAN_SET_DUTY_FORMAT_NO 			1
#define SCT_FAN_SET_DUTY_RESP				">FDS"
#define SCT_FAN_SET_DUTY_RESP_LEN			4

#define SCT_FAN_GET_DUTY_CMD				"$FDS"
#define SCT_FAN_GET_DUTY_CMD_LEN			4
#define SCT_FAN_GET_DUTY_CMD_RESP			"!FDS"
#define SCT_FAN_GET_DUTY_CMD_RESP_LEN		4

#define SCT_SET_FAN_PWM_SRC_CMD				"#FPS"
#define SCT_SET_FAN_PWM_SRC_CMD_LEN			4
#define SCT_SET_FAN_PWM_SRC_CMD_FORMAT		"#FPS %hd"
#define SCT_SET_FAN_PWM_SRC_CMD_FORMAT_NO	1
#define SCT_SET_FAN_PWM_SRC_RESP			">FPS"
#define SCT_SET_FAN_PWM_SRC_RESP_LEN		4

#define SCT_UNKONWN_CMD_RESP				"?"
#define SCT_UNKONWN_CMD_RESP_LEN			1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef enum sct_GpoSignals
{
    tamper_switch_buzzer = 0,
    rcu_power_button,
    som_sd_boot_enable,
    rcu_pwr_enable_zeroise_out,
    sel_i2c_s0,
    sel_i2c_s1,
    ms_1pps_direction_control,
    sel_1pps_s0,
    sel_1pps_s1,
    sel_1pps_s2,
    sel_1pps_s3,
    ms_power_enable_in,
    ms_master_select_n,
    test_point_1_out,
    test_point_2_out,
    control_ms_rf_mute_n_out,
    control_ms_rf_mute_dir,
    sel_fan_pwm_s0,
    sel_fan_pwm_s1,
    sel_fan_pwm_s2,
	gpo_signal_qty
} sct_GpoSignals_t;

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
static void sct_ProcessReadGpiCommand(uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetPpsIpSrcCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetPpsDirCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessReadPpsCommand(uint8_t *resp_buf);
static void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
static void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf);
static void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf);
static void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetI2cBusCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessInitFanControllerCommand(uint8_t *resp_buf);
static void sct_ProcessGetFanSpeedCommand(uint8_t *resp_buf);
static void sct_ProcessSetFanDutyCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetFanPwmSourceCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetFanDutyCommand(uint8_t *resp_buf);
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

const char *lg_sct_gpo_signal_names[gpo_pin_qty] = \
{
	"Tamper Switch Buzzer",
	"RCU Power Button",
	"SOM SD Boot Enable",
	"RCU Power Enable Zeroise",
    "Select I2C S0",
    "Select I2C S1",
    "Control Port 1PPS Direction",
	"Select 1PPS S0",
	"Select 1PPS S1",
	"Select 1PPS S2",
	"Select 1PPS S3",
	"Control Port Power Enable",
	"Control Port Master Select (active-low)",
	"Test Point 1",
	"Test Point 2",
	"Control Port RF Mute Out (active-low)",
	"Control Port RF Mute Direction",
	"Select Fan PWM S0",
	"Select Fan PWM S1",
	"Select Fan PWM S2"
};

/*****************************************************************************/
/**
* Initialise the serial command task.
*
* @param    init_data    Initialisation data for the task
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
	sprintf((char *)resp_buf, "%s %s - v%d.%d.%d%s",
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
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_HW_CONFIG_INFO_CMD, SCT_HW_CONFIG_INFO_CMD_LEN))
	{
		sct_ProcessHwConfigInfoCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_HW_RST_CONFIG_INFO_CMD, SCT_HW_RST_CONFIG_INFO_CMD_LEN))
	{
		 sct_ProcessResetHwConfigInfoCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_HW_SET_PARAM_CMD, SCT_HW_SET_PARAM_CMD_LEN))
	{
		sct_ProcessSetHwConfigInfoCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_I2C_BUS_CMD, SCT_SET_I2C_BUS_CMD_LEN))
	{
		sct_ProcessSetI2cBusCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_INIT_FAN_CTRLR, SCT_INIT_FAN_CTRLR_LEN))
	{
		sct_ProcessInitFanControllerCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_GET_SPEED_CMD, SCT_FAN_GET_SPEED_CMD_LEN))
	{
		sct_ProcessGetFanSpeedCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_SET_DUTY, SCT_FAN_SET_DUTY_LEN))
	{
		sct_ProcessSetFanDutyCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_FAN_PWM_SRC_CMD, SCT_SET_FAN_PWM_SRC_CMD_LEN))
	{
		sct_ProcessSetFanPwmSourceCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_GET_DUTY_CMD, SCT_FAN_GET_DUTY_CMD_LEN))
	{
		sct_ProcessGetFanDutyCommand(resp_buf);
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
*
******************************************************************************/
static void sct_ProcessReadGpiCommand(uint8_t *resp_buf)
{
	iot_GpioPinState_t pin_state = reset;
	iot_GpiPinId_t i = 0;
	const char *p_chanel_name = NULL;

	for (i = ntm1_fan_alert; i <= ntm3_pfi_n; ++i)
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
		case tamper_switch_buzzer:
		    gpo_pin = tamper_sw_buzzer;
		    break;

		case rcu_power_button:
            gpo_pin = rcu_pwr_btn;
            break;

		case som_sd_boot_enable:
            gpo_pin = som_sd_boot_en;
            break;

		case rcu_pwr_enable_zeroise_out:
            gpo_pin = rcu_pwr_en_zer_out;
            break;

		case sel_i2c_s0:
            gpo_pin = select_i2c_s0;
            break;

		case sel_i2c_s1:
            gpo_pin = select_i2c_s1;
            break;

		case ms_1pps_direction_control:
            gpo_pin = ms_1pps_dir_ctrl;
            break;

		case sel_1pps_s0:
            gpo_pin = select_1pps_s0;
            break;

		case sel_1pps_s1:
            gpo_pin = select_1pps_s1;
            break;

		case sel_1pps_s2:
            gpo_pin = select_1pps_s2;
            break;

		case sel_1pps_s3:
            gpo_pin = select_1pps_s3;
            break;

		case ms_power_enable_in:
            gpo_pin = ms_pwr_en_in;
            break;

		case ms_master_select_n:
            gpo_pin = ms_master_n;
            break;

		case test_point_1_out:
            gpo_pin = test_point_1;
            break;

		case test_point_2_out:
            gpo_pin = test_point_2;
            break;

		case control_ms_rf_mute_n_out:
            gpo_pin = ms_rf_mute_n_out;
            break;

		case control_ms_rf_mute_dir:
            gpo_pin = ms_rf_mute_dir;
            break;

		case sel_fan_pwm_s0:
            gpo_pin = select_fan_pwm_s0;
            break;

		case sel_fan_pwm_s1:
            gpo_pin = select_fan_pwm_s1;
            break;

		case sel_fan_pwm_s2:
            gpo_pin = select_fan_pwm_s2;
            break;

		default:
			gpo_pin = -1;
			break;
		}

		/* Validate the gpo_pin parameter and set pin state */
		if ((gpo_pin >= tamper_sw_buzzer) && (gpo_pin < gpo_pin_qty))
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

		for (signal_id = tamper_switch_buzzer; signal_id < gpo_signal_qty; ++signal_id)
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
* 	- 2: NTM1
* 	- 3: NTM2
* 	- 4: NTM3
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
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
			iot_SetGpoPinState(select_1pps_s0, reset);
			iot_SetGpoPinState(select_1pps_s1, set);
			sprintf((char *)resp_buf, "Control Master/Slave 1PPS Source Selected%s", SCT_CRLF);
			break;

		case 2:
			iot_SetGpoPinState(select_1pps_s0, set);
			iot_SetGpoPinState(select_1pps_s2, reset);
			iot_SetGpoPinState(select_1pps_s3, reset);
			sprintf((char *)resp_buf, "NTM1 1PPS Source Selected%s", SCT_CRLF);
			break;

		case 3:
			iot_SetGpoPinState(select_1pps_s0, set);
			iot_SetGpoPinState(select_1pps_s2, set);
			iot_SetGpoPinState(select_1pps_s3, reset);
			sprintf((char *)resp_buf, "NTM2 1PPS Source Selected%s", SCT_CRLF);
			break;

		case 4:
			iot_SetGpoPinState(select_1pps_s0, set);
			iot_SetGpoPinState(select_1pps_s3, set);
			sprintf((char *)resp_buf, "NTM3 1PPS Source Selected%s", SCT_CRLF);
			break;

		default:
			sprintf((char *)resp_buf, "*** Invalid 1PPS Source! ***%s", SCT_CRLF);
			break;
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #PPSS <PPS Source [0|1|2|3|4]> <ENTER>:%s", SCT_CRLF);
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
*
******************************************************************************/
static void sct_ProcessSetPpsDirCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t direction = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_PPS_DIR_CMD_FORMAT, &direction);

	if (no_params == SCT_SET_PPS_DIR_CMD_FORMAT_NO)
	{	/* If set_state is non-zero set the CSM Slave as 1PPS output */
		iot_SetGpoPinState(ms_1pps_dir_ctrl, (direction ? set : reset));
		sprintf((char *)resp_buf, "Control Master/Slave 1PPS direction %s%s", (direction ? "Output" : "Input"), SCT_CRLF);
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
* Read and return the ADC data
*
* @param    resp_buf buffer for transmitting command response
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
* Read and return hardware configuration information
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf)
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
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf)
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
* Sets the multiplexed source for the NTM I2C bus interfaces:
* 	- 0: None
* 	- 1: NTM1
* 	- 2: NTM2
* 	- 3: NTM3
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetI2cBusCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t source = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_I2C_BUS_CMD_FORMAT, &source);

	if (no_params == SCT_SET_PPS_IP_SRC_CMD_FORMAT_NO)
	{	/* Validate the pps_source parameter and set GPIO pin states accordingly */
		if (((iot_I2cBusSource_t)source >= i2c_bus_none) && ((iot_I2cBusSource_t)source <= i2c_bus_ntm3))
		{
			iot_SetI2cBus((iot_I2cBusSource_t)source);
			sprintf((char *)resp_buf, "I2C Bus %d Selected%s", source, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Invalid I2C Bus! ***%s", SCT_CRLF);
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #I2CB <I2C Bus [0|1|2|3]> <ENTER>:%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_I2C_BUS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Initialise the fan controller IC
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessInitFanControllerCommand(uint8_t *resp_buf)
{
	if (iot_InitialiseFanController())
	{
		sprintf((char *)resp_buf, "EMC2104 fan controller successfully initialised%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to initialise EMC2104 fan controller! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_INIT_FAN_CTRLR_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read the fan speeds from the fan controller
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetFanSpeedCommand(uint8_t *resp_buf)
{
	uint16_t fan1_clk_count = 0U, fan2_clk_count = 0U;

	if (iot_ReadFanSpeedCounts(&fan1_clk_count, &fan2_clk_count))
	{
		sprintf((char *)resp_buf, "Fan 1 Speed Count: %u%sFan 2 Speed Count: %u%s",
				fan1_clk_count, SCT_CRLF, fan2_clk_count, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Fan 1 Speed RPM: %u%sFan 2 Speed RPM: %u%s",
				15734640U / fan1_clk_count, SCT_CRLF, 15734640U / fan2_clk_count, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read fan speeds! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_GET_SPEED_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the fan speed to direct mode using specified PWM duty cycle value.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetFanDutyCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t pwm = 0;

	if (sscanf((char *)cmd_buf, SCT_FAN_SET_DUTY_FORMAT, &pwm) == SCT_FAN_SET_DUTY_FORMAT_NO)
	{
		if (iot_SetFanSpeedDuty(pwm))
		{
			sprintf((char *)resp_buf, "Set direct fan drive duty setting: %hu%s", pwm, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set direct fan drive duty setting! ***%s", SCT_CRLF);
		}
	}
	else
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #FDS <PWM Duty [0..100]> <ENTER>:%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_SET_DUTY_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the multiplexed source for the fan PWM signal:
* 	- 0: Fan 1.1
* 	- 1: Fan 2.1
* 	- 2: Fan 2.2
* 	- 3: Fan 3.1
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetFanPwmSourceCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t source = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_FAN_PWM_SRC_CMD_FORMAT, &source);

	if (no_params == SCT_SET_FAN_PWM_SRC_CMD_FORMAT_NO)
	{	/* Validate the pps_source parameter and set GPIO pin states accordingly */
		if (((iot_FanPwmSource_t)source >= fan_pwm_1_1) && ((iot_FanPwmSource_t)source <= fan_pwm_3_1))
		{
			iot_SetFanPwmSource((iot_FanPwmSource_t)source);
			sprintf((char *)resp_buf, "Fan PWM Source %d Selected%s", source, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Invalid I2C Bus! ***%s", SCT_CRLF);
		}
	}
	else if (no_params == -1)
	{
		/* If there was an error with the number of parameters print help message */
		sprintf((char *)resp_buf, "Command format #FPS <Fan PWM Source [0|1|2|3]> <ENTER>:%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_FAN_PWM_SRC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Measures the duty-cycle of the PWM signal connected to the PWM timer input.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetFanDutyCommand(uint8_t *resp_buf)
{
	uint32_t fan_duty = iot_MeasureFanPwmDuty();
	sprintf((char *)resp_buf, "Fan PWM Duty %lu %%%s", fan_duty, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_GET_DUTY_CMD_RESP, SCT_CRLF);
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
