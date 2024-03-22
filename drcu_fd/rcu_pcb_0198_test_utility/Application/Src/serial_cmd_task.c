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
#include "hw_config_info.h"
#include "i2c_temp_sensor.h"
#include "tamper_driver.h"
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
#define SCT_CMD_HISTORY_LEN		5

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
#define SCT_HW_CONFIG_INFO_CMD			"$HCI"
#define SCT_HW_CONFIG_INFO_CMD_LEN		4
#define SCT_HW_CONFIG_INFO_RESP			"!HCI"
#define SCT_HW_CONFIG_INFO_RESP_LEN		4

#define SCT_HW_RST_CONFIG_INFO_CMD		"#RHCI"
#define SCT_HW_RST_CONFIG_INFO_CMD_LEN 	5
#define SCT_HW_RST_CONFIG_INFO_RESP		">RHCI"
#define SCT_HW_RST_CONFIG_INFO_RESP_LEN	5

#define SCT_HW_SET_PARAM_CMD			"#SHCI"
#define SCT_HW_SET_PARAM_CMD_LEN		5
#define SCT_HW_SET_PARAM_CMD_FORMAT		"#SHCI %d %15s"
#define SCT_HW_SET_PARAM_CMD_FORMAT_NO	2
#define SCT_HW_SET_PARAM_RESP			">SHCI"
#define SCT_HW_SET_PARAM_RESP_LEN		5

#define SCT_READ_GPI_CMD				"$GPI"
#define SCT_READ_GPI_CMD_LEN			4
#define SCT_READ_GPI_RESP				"!GPI"
#define SCT_READ_GPI_RESP_LEN			4

#define SCT_SET_GPO_CMD					"#GPO"
#define SCT_SET_GPO_CMD_LEN				4
#define SCT_SET_GPO_CMD_FORMAT			"#GPO %hd %hd"
#define SCT_SET_GPO_CMD_FORMAT_NO		2
#define SCT_SET_GPO_RESP				">GPO"
#define SCT_SET_GPO_RESP_LEN			4

#define SCT_READ_PPS_CMD				"$PPS"
#define SCT_READ_PPS_CMD_LEN			4
#define SCT_READ_PPS_RESP				"!PPS"
#define SCT_READ_PPS_RESP_LEN			4

#define SCT_GET_BATT_TEMP_CMD			"$BTMP"
#define SCT_GET_BATT_TEMP_CMD_LEN		5
#define SCT_GET_BATT_TEMP_RESP			"!BTMP"
#define SCT_GET_BATT_TEMP_RESP_LEN		5

#define SCT_GET_TEMP_CMD				"$TMP"
#define SCT_GET_TEMP_CMD_LEN			4
#define SCT_GET_TEMP_RESP				"!TMP"
#define SCT_GET_TEMP_RESP_LEN			4

#define SCT_READ_ANTI_TAMPER_CMD		"$RAT"
#define SCT_READ_ANTI_TAMPER_CMD_LEN	4
#define SCT_READ_ANTI_TAMPER_RESP		"!RAT"
#define SCT_READ_ANTI_TAMPER_RESP_LEN	4

#define SCT_SET_ANTI_TAMPER_CMD			"#SAT"
#define SCT_SET_ANTI_TAMPER_CMD_LEN		4
#define SCT_SET_ANTI_TAMPER_CMD_FORMAT	"#SAT %hd %hd"
#define SCT_SET_ANTI_TAMPER_CMD_FORMAT_NO 2
#define SCT_SET_ANTI_TAMPER_RESP		">SAT"
#define SCT_SET_ANTI_TAMPER_RESP_LEN	4

#define SCT_READ_RTC_CMD				"$RTC"
#define SCT_READ_RTC_CMD_LEN			4
#define SCT_READ_RTC_RESP				"!RTC"
#define SCT_READ_RTC_RESP_LEN			4

#define SCT_SET_BZR_CMD					"#BZR"
#define SCT_SET_BZR_CMD_LEN				4
#define SCT_SET_BZR_CMD_FORMAT			"#BZR %hd"
#define SCT_SET_BZR_CMD_FORMAT_NO		1
#define SCT_SET_BZR_RESP				">BZR"
#define SCT_SET_BZR_RESP_LEN			4

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

/* I2C definitions */
#define SCT_PCA9500_EEPROM_I2C_ADDR 	0x56U << 1
#define SCT_PCA9500_GPIO_I2C_ADDR		0x26U << 1
#define SCT_AD7415_TEMP_I2C_ADDR		0x49U << 1
#define SCT_ANTI_TAMPER_I2C_ADDR		0x68U << 1

#define SCT_I2C_TIMEOUT_MS				100U

/* 1PPS accuracy limits */
#define SCT_1PPS_DELTA_MIN				999U
#define SCT_1PPS_DELTA_MAX				1001U

/* ADC channel definitions */
#define SCT_VDD_CALIB_MV ((uint16_t) (3000))
#define SCT_NUM_ADC_CHANNELS				2
#define SCT_VREFINT_READING_IDX				0
#define SCT_TEMPERATURE_READING_IDX			1

/* Temperature sensor and voltage reference calibration value addresses */
#define SCT_TEMP130_CAL_ADDR ((uint16_t*) ((uint32_t) 0x1FF8007E))
#define SCT_TEMP30_CAL_ADDR ((uint16_t*) ((uint32_t) 0x1FF8007A))
#define SCT_VREFINT_CAL_ADDR ((uint16_t*) ((uint32_t) 0x1FF80078))

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
static void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
static void sct_FlushRespBuf(uint8_t *resp_buf);
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf);
static void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf);
static void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessReadGpiCommand(uint8_t *resp_buf);
static void sct_ProcessReadPpsCommand(uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcesssGetBatteryTempCommand(uint8_t *resp_buf);
static void sct_ProcessGetTempCommand(uint8_t *resp_buf);
static void sct_ProcessReadAntiTamperCommand(uint8_t *resp_buf);
static void sct_ProcessSetAntiTamperCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessReadRtcCommand(uint8_t *resp_buf);
static void sct_ProcessSetBuzzerStateCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessUnkownCommand(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static sct_Init_t lg_sct_init_data = {0U};
static bool lg_sct_initialised = false;

static hci_HwConfigInfo_t		lg_sct_hci = {0};
static its_I2cTempSensor_t		lg_sct_batt_temp_sensor = {0};
static td_TamperDriver_t		lg_sct_anti_tamper = {0};

static volatile uint32_t lg_sct_1pps_delta = 0U;
static volatile uint32_t lg_sct_1pps_previous = 0U;

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
*
******************************************************************************/
void sct_InitTask(sct_Init_t init_data)
{
	memcpy((void *)&lg_sct_init_data, (void *)&init_data, sizeof(sct_Init_t));
	lg_sct_initialised = true;

	hci_Init(	&lg_sct_hci, lg_sct_init_data.i2c_device0,
				SCT_PCA9500_GPIO_I2C_ADDR,
				SCT_PCA9500_EEPROM_I2C_ADDR);

	(void) its_Init(&lg_sct_batt_temp_sensor,
					lg_sct_init_data.i2c_device0,
					SCT_AD7415_TEMP_I2C_ADDR);

	(void) td_InitInstance(	&lg_sct_anti_tamper, lg_sct_init_data.i2c_device0,
							SCT_ANTI_TAMPER_I2C_ADDR);

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
	if (!strncmp((char *)cmd_buf, SCT_HW_CONFIG_INFO_CMD, SCT_HW_CONFIG_INFO_CMD_LEN))
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
	else if (!strncmp((char *)cmd_buf, SCT_READ_GPI_CMD, SCT_READ_GPI_CMD_LEN))
	{
		sct_ProcessReadGpiCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN))
	{
		sct_ProcessSetGpoCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_PPS_CMD, SCT_READ_PPS_CMD_LEN))
	{
		sct_ProcessReadPpsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_BATT_TEMP_CMD, SCT_GET_BATT_TEMP_CMD_LEN))
	{
		sct_ProcesssGetBatteryTempCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_TEMP_CMD, SCT_GET_TEMP_CMD_LEN))
	{
		sct_ProcessGetTempCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_ANTI_TAMPER_CMD, SCT_READ_ANTI_TAMPER_CMD_LEN))
	{
		sct_ProcessReadAntiTamperCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_ANTI_TAMPER_CMD, SCT_SET_ANTI_TAMPER_CMD_LEN))
	{
		sct_ProcessSetAntiTamperCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_RTC_CMD, SCT_READ_RTC_CMD_LEN))
	{
		sct_ProcessReadRtcCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_BZR_CMD, SCT_SET_BZR_CMD_LEN))
	{
		sct_ProcessSetBuzzerStateCommand(cmd_buf, resp_buf);
	}
	else
	{
		sct_ProcessUnkownCommand(resp_buf);
	}
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

	if (hci_ReadHwConfigInfo(&lg_sct_hci, &hw_config_info))
	{
		sprintf((char *)resp_buf, "Hardware Configuration Information:%s%s", SCT_CRLF, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Version No: %c%c%s",
				((hw_config_info.hw_version > 25U) ? (int16_t)('A') : ((int16_t)hw_config_info.hw_version + (int16_t)('A'))),
				(hw_config_info.hw_version > 25U ? ((int16_t)hw_config_info.hw_version - 26 + (int16_t)('A')) : (int16_t)(' ')),
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Mod Version No: %u%s",
				hw_config_info.hw_mod_version, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Assembly Part No: %s%s",
				hw_config_info.assy_part_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Assembly Revision No: %s%s",
				hw_config_info.assy_rev_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Assembly Serial No: %s%s",
				hw_config_info.assy_serial_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Assembly Build Date or Batch No: %s%s",
				hw_config_info.assy_build_date_batch_no, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Configuration Information CRC: 0x%x%s",
				hw_config_info.hci_crc, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Configuration Information CRC Valid: %s%s",
				(hw_config_info.hci_crc_valid != 0U ? "True" : "False"), SCT_CRLF);
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
	if (hci_ResetHwConfigInfo(&lg_sct_hci))
	{
		sprintf((char *)resp_buf, "Successfully cleared HCI EEPROM%s",
				SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to clear HCI EEPROM! ***%s",
				SCT_CRLF);
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
				param_set = hci_SetAssyPartNo(	&lg_sct_hci,
												(uint8_t *)param);
				break;

			case sct_RevNo:
				param_set = hci_SetAssyRevNo(	&lg_sct_hci,
												(uint8_t *)param);
				break;

			case sct_SerialNo:
				param_set = hci_SetAssySerialNo(&lg_sct_hci,
												(uint8_t *)param);
				break;

			case sct_BuildBatchNo:
				param_set = hci_SetAssyBuildDataBatchNo(
												&lg_sct_hci,
												(uint8_t *)param);
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
			sprintf((char *)resp_buf, "*** Unknown Parameter! ***%s",
					SCT_CRLF);
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
* Read micro GPI input signals and print their values
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessReadGpiCommand(uint8_t *resp_buf)
{
	GPIO_PinState pin_state = GPIO_PIN_RESET;
	int16_t i = 0;

	for (i = 0; i < SCT_GPI_PIN_NUM; ++i)
	{
		pin_state =	HAL_GPIO_ReadPin(	lg_sct_init_data.gpi_pins[i].port,
										lg_sct_init_data.gpi_pins[i].pin);
		sprintf((char *)resp_buf, "%d - %s%s", pin_state,
				lg_sct_init_data.gpi_pins[i].name, SCT_CRLF);
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
void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t gpo_pin = 0U;
	int16_t set_state = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_GPO_CMD_FORMAT, &gpo_pin, &set_state) ==
			SCT_SET_GPO_CMD_FORMAT_NO)
	{
		/* Validate the gpo_pin parameter */
		if ((gpo_pin >= 0) && (gpo_pin < SCT_GPO_PIN_NUM))
		{
			HAL_GPIO_WritePin(	lg_sct_init_data.gpo_pins[gpo_pin].port,
								lg_sct_init_data.gpo_pins[gpo_pin].pin,
								((set_state == 0) ? GPIO_PIN_RESET : GPIO_PIN_SET));

			sprintf((char *)resp_buf, "%s set to: %s%s",
					lg_sct_init_data.gpo_pins[gpo_pin].name,
					((set_state == 0) ? "0" : "1"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Unknown GPO Pin! ***%s", SCT_CRLF);
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
* Check if the 1PPS output from the SoM is present
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessReadPpsCommand(uint8_t *resp_buf)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(lg_sct_init_data.pps_gpio_irq);
	uint32_t pps_delta = lg_sct_1pps_delta;
	uint32_t pps_previous = lg_sct_1pps_previous;
	HAL_NVIC_EnableIRQ(lg_sct_init_data.pps_gpio_irq);
	uint32_t now = osKernelSysTick();

	if ((now - pps_previous) > SCT_1PPS_DELTA_MAX)
	{
		sprintf((char *)resp_buf, "1PPS NOT detected%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "1PPS detected, delta: %lu ms%s", pps_delta, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_PPS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return the battery temperature.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcesssGetBatteryTempCommand(uint8_t *resp_buf)
{
	int16_t temp = 0;

	if (its_ReadTemperature(&lg_sct_batt_temp_sensor, &temp))
	{
		sprintf((char *)resp_buf, "Battery Temperature: %hd%s", temp, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read temperature sensor! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_BATT_TEMP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return the internal temperature sensor.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetTempCommand(uint8_t *resp_buf)
{
	int32_t adc_reading[SCT_NUM_ADC_CHANNELS];
	int32_t temperature;
	int32_t vref_ext_mv = 0;
	int16_t i;

	HAL_ADC_Start(lg_sct_init_data.adc_device);

	for (i = 0; i < SCT_NUM_ADC_CHANNELS; ++i)
	{
		/* Wait for the conversion to complete */
		HAL_ADC_PollForConversion(lg_sct_init_data.adc_device, 10U);
		adc_reading[i] = (int32_t)HAL_ADC_GetValue(lg_sct_init_data.adc_device);
	}

	HAL_ADC_Stop(lg_sct_init_data.adc_device);

	/* Use the Vrefint reading and calibration value to calculate the Vrefext in mV */
	vref_ext_mv = (SCT_VDD_CALIB_MV * (int32_t) *SCT_VREFINT_CAL_ADDR) / adc_reading[SCT_VREFINT_READING_IDX];

	/* Calculate  the temperature */
 	temperature = ((adc_reading[SCT_TEMPERATURE_READING_IDX] * vref_ext_mv / SCT_VDD_CALIB_MV) - (int32_t) *SCT_TEMP30_CAL_ADDR);
	temperature = temperature * (int32_t)(130 - 30);
	temperature = temperature / (int32_t)(*SCT_TEMP130_CAL_ADDR - *SCT_TEMP30_CAL_ADDR);
	temperature = temperature + 30;

	sprintf((char *)resp_buf, "Temperature: %ld%s", temperature, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_TEMP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read anti-tamper IC registers and return their values
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessReadAntiTamperCommand(uint8_t *resp_buf)
{
	uint8_t buf = 0U;

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_TAMPER1_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Tamper 1%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_TAMPER2_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Tamper 2%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_ALARM_MONTH_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Alarm Month%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_DAY_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Day%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_SECONDS_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Seconds%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_ALARM_HOUR_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Alarm Hour%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_anti_tamper, TD_FLAGS_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Anti-tamper Flags%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_ANTI_TAMPER_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the specified anti-tamper channel, parameters are:
* channel - '0' for channel 1; or '2' for channel 1
* enable - '0' to disable; else enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetAntiTamperCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t channel = -1;
	int16_t enable = 0;
	td_TamperDriver_t *p_inst = NULL;
	/* Default tamper sensor is Normally Open, Tamper to GND */
	bool tcm = true;
	bool tpm = false;

	if (sscanf(	(char *)cmd_buf, SCT_SET_ANTI_TAMPER_CMD_FORMAT,
				&channel, &enable) == SCT_SET_ANTI_TAMPER_CMD_FORMAT_NO)
	{
		/* Validate device and channel parameter values */
		if ((channel >= 0) && (channel <= 1))
		{
			p_inst = &lg_sct_anti_tamper;
			if (channel == 0)
			{	/* Case switch is Normally Closed to GND */
				tcm = false;
				tpm = true;
			}

			if (td_TamperEnable(p_inst, channel, tpm, tcm, (enable == 0 ? false : true)))
			{
				sprintf((char *)resp_buf, "Tamper Device Channel %hd %s%s",
						channel, (enable == 0 ? "DISABLED" : "ENABLED"), SCT_CRLF);
			}
			else
			{
				sprintf((char *)resp_buf, "*** Failed to set Tamper Device Channel %hd %s! ***%s",
						channel, (enable == 0 ? "DISABLED" : "ENABLED"), SCT_CRLF);
			}

			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Parameter Value Error! ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_ANTI_TAMPER_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read anti-tamper IC RTC registers and return their values
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessReadRtcCommand(uint8_t *resp_buf)
{
	td_Time curr_time = {0};

	if(td_GetTime(&lg_sct_anti_tamper, &curr_time))
	{
		sprintf((char *)resp_buf,
				"Tamper Device RTC: %u%u:%u%u:%u%u%s",
				curr_time.tens_hours,
				curr_time.hours,
				curr_time.tens_minutes,
				curr_time.minutes,
				curr_time.tens_seconds,
				curr_time.seconds,
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Tamper Device RTC! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_RTC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the buzzer enable signal state, disable if serial command parameter is
* zero, else enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessSetBuzzerStateCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0U;
	GPIO_PinState pin_state = GPIO_PIN_RESET;

	if (sscanf((char *)cmd_buf, SCT_SET_BZR_CMD_FORMAT, &set_state) ==
			SCT_SET_BZR_CMD_FORMAT_NO)
	{
		if (set_state == 0U)
		{
			pin_state = GPIO_PIN_RESET;
			sprintf((char *)resp_buf, "Buzzer disabled%s", SCT_CRLF);
		}
		else
		{
			pin_state = GPIO_PIN_SET;
			sprintf((char *)resp_buf, "Buzzer enabled%s", SCT_CRLF);
		}
		HAL_GPIO_WritePin(	lg_sct_init_data.buzzer_gpio_port,
							lg_sct_init_data.buzzer_gpio_pin, pin_state);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_BZR_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
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
* Handle HAL EXTI GPIO Callback as these are used to monitor presence of 1PPS
* input signal
*
* @param    argument    Not used
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	volatile uint32_t now = osKernelSysTick();

	if (lg_sct_initialised)
	{
		if (GPIO_Pin == lg_sct_init_data.pps_gpio_pin)
		{
			lg_sct_1pps_delta = now - lg_sct_1pps_previous;
			lg_sct_1pps_previous = now;
		}
	}
}
