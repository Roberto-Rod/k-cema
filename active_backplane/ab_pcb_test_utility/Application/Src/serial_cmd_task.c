/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file serial_cmd_task.c
*
* Provides serial command task handling.
* <br><br>
* Processes received serial bytes and converts them to commands, performs
* command error handling. Command "$HELP" returns list of available commands.
*
* Project   : K-CEMA
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
* @todo None
*
******************************************************************************/
#include "serial_cmd_task.h"
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
#define SCT_CMD_HISTORY_LEN		2

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
#define SCT_HW_CONFIG_INFO_CMD				"$HCI"
#define SCT_HW_CONFIG_INFO_CMD_LEN			4
#define SCT_HW_CONFIG_INFO_RESP				"!HCI"
#define SCT_HW_CONFIG_INFO_RESP_LEN			4

#define SCT_HW_RST_CONFIG_INFO_CMD			"#RHCI"
#define SCT_HW_RST_CONFIG_INFO_CMD_LEN 		5
#define SCT_HW_RST_CONFIG_INFO_RESP			">RHCI"
#define SCT_HW_RST_CONFIG_INFO_RESP_LEN		4

#define SCT_HW_SET_PARAM_CMD				"#SHCI"
#define SCT_HW_SET_PARAM_CMD_LEN			5
#define SCT_HW_SET_PARAM_CMD_FORMAT			"#SHCI %d %16s"
#define SCT_HW_SET_PARAM_CMD_FORMAT_NO		2
#define SCT_HW_SET_PARAM_RESP				">SHCI"
#define SCT_HW_SET_PARAM_RESP_LEN			5

#if 0
#define SCT_GET_PPS_CMD						"$PPS"
#define SCT_GET_PPS_CMD_LEN					4
#define SCT_GET_PPS_RESP					"!PPS"
#define SCT_GET_PPS_RESP_LEN				4
#endif

#define SCT_SET_PPS_EN_CMD					"#PPS"
#define SCT_SET_PPS_EN_CMD_LEN				4
#define SCT_SET_PPS_EN_CMD_FORMAT			"#PPS %hd"
#define SCT_SET_PPS_EN_CMD_FORMAT_NO		1
#define SCT_SET_PPS_EN_RESP					">PPS"
#define SCT_SET_PPS_EN_RESP_LEN				4

#define SCT_SET_RACK_ADDRESS_CMD			"#RADR"
#define SCT_SET_RACK_ADDRESS_CMD_LEN		5
#define SCT_SET_RACK_ADDRESS_CMD_FORMAT		"#RADR %hu"
#define SCT_SET_RACK_ADDRESS_CMD_FORMAT_NO 	1
#define SCT_SET_RACK_ADDRESS_RESP			">RADR"
#define SCT_SET_RACK_ADDRESS_RESP_LEN		5

#define SCT_SET_DCDC_OFF_CMD				"#DCDC"
#define SCT_SET_DCDC_OFF_CMD_LEN			5
#define SCT_SET_DCDC_OFF_CMD_FORMAT			"#DCDC %hu"
#define SCT_SET_DCDC_OFF_CMD_FORMAT_NO 		1
#define SCT_SET_DCDC_OFF_RESP				">DCDC"
#define SCT_SET_DCDC_OFF_RESP_LEN			5

#define SCT_SET_SYSTEM_RESET_CMD			"#SRST"
#define SCT_SET_SYSTEM_RESET_CMD_LEN		5
#define SCT_SET_SYSTEM_RESET_CMD_FORMAT		"#SRST %hu"
#define SCT_SET_SYSTEM_RESET_CMD_FORMAT_NO 1
#define SCT_SET_SYSTEM_RESET_RESP			">SRST"
#define SCT_SET_SYSTEM_RESET_RESP_LEN		5

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

#define SCT_GET_MAC_ADDR_CMD				"$MAC"
#define SCT_GET_MAC_ADDR_CMD_LEN			4
#define SCT_GET_MAC_ADDR_RESP				"!MAC"
#define SCT_GET_MAC_ADDR_RESP_LEN			4

#define SCT_UNKONWN_CMD_RESP				"?"
#define SCT_UNKONWN_CMD_RESP_LEN			1

/* I2C device addresses... */
#define SCT_PCA9500_EEPROM_I2C_ADDR 		0x50U << 1
#define SCT_PCA9500_GPIO_I2C_ADDR			0x20U << 1
#define SCT_MICRO_EUI48_EEPROM_ADDR			0x51U << 1
#define SCT_SWITCH_EUI48_EEPROM_ADDR		0x52U << 1

/* 1PPS accuracy limits */
#define SCT_1PPS_DELTA_MIN					990U
#define SCT_1PPS_DELTA_MAX					1010U

/* ADC definitions */
#define SCT_ADC_NUM_CHANNELS				2
#define SCT_ADC_VREF_MV						3300
#define SCT_ADC_VREFINT_MV					1210
#define SCT_ADC_ADC_BITS					4096
#define SCT_ADC_VREF_INT_CHANNEL_IDX		0
#define SCT_ADC_RAIL_3V3_CHANNEL_IDX		1
#define SCT_ADC_SCALE_MUL					0
#define SCT_ADC_SCALE_DIV					1

static const int32_t SCT_ADC_SCALE_FACTORS[SCT_ADC_NUM_CHANNELS][2] = {
	{1, SCT_ADC_ADC_BITS},	/* Vrefint multiplier and divider */
	{2, SCT_ADC_ADC_BITS}	/* +3V3 rail multiplier and divider */
};

static const char *SCT_ADC_CHANNEL_NAMES[SCT_ADC_NUM_CHANNELS] = {
	"VREFINT (mV)\t",
	"BUT +3V3 (mV)\t"
};

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
void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
void sct_FlushRespBuf(uint8_t *resp_buf);
void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf);
void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf);
void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
#if 0
void sct_ProcessGetPpsCommand(uint8_t *resp_buf);
#endif
static void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRackAddressCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetDcdcOffCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetSystemResetCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_SetSysReset(bool reset);
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
void sct_ProcesGetMacAddressCommand(uint8_t *resp_buf);
void sct_ProcessUnkownCommand(uint8_t *resp_buf);
static void sct_I2cReInit(void);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sct_Init_t lg_sct_init_data = {NULL, NULL, NULL};
bool lg_sct_initialised = false;
volatile uint32_t lg_sct_1pps_delta = 0U;
volatile uint32_t lg_sct_1pps_previous = 0U;
hci_HwConfigInfo_t	lg_sct_hci = {0};
e48_E48Info_t lg_sct_micro_mac_e48 = {0};
e48_E48Info_t lg_sct_switch_mac_e48 = {0};

uint8_t 	lg_sct_cmd_buf[SCT_CMD_HISTORY_LEN][SCT_MAX_BUF_SIZE] = {0U};
int16_t		lg_sct_cmd_buf_hist_idx = 0;
uint16_t	lg_sct_cmd_buf_idx = 0U;

/*****************************************************************************/
/**
* Initialise the serial command task.
*
* @param    init_data    Initialisation data for the task
* @return   None
* @note     None
*
******************************************************************************/
void sct_InitTask(sct_Init_t init_data)
{
	memcpy((void *)&lg_sct_init_data, (void *)&init_data, sizeof(sct_Init_t));

	hci_Init(	&lg_sct_hci, init_data.i2c_device,
				SCT_PCA9500_GPIO_I2C_ADDR, SCT_PCA9500_EEPROM_I2C_ADDR);
	e48_Init(&lg_sct_micro_mac_e48, init_data.i2c_device, SCT_MICRO_EUI48_EEPROM_ADDR);
	e48_Init(&lg_sct_switch_mac_e48, init_data.i2c_device, SCT_SWITCH_EUI48_EEPROM_ADDR);

	lg_sct_initialised = true;
}

/*****************************************************************************/
/**
* Serial command function.
*
* @param    argument    Not used
* @return   None
* @note     None
*
******************************************************************************/
void sct_SerialCmdTask(void const *argument)
{
	osEvent event;
	static uint8_t resp_buf[SCT_MAX_BUF_SIZE] = {0U};

	if (!lg_sct_initialised)
	{
		for(;;)
		{
		}
	}

  	HAL_Delay(100);
  	sprintf((char *)resp_buf, "%s%s", SCT_CLS, SCT_HOME);
	sct_FlushRespBuf(resp_buf);
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
void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf)
{
	/* To help with human-entered command strings, backspace key erases last character */
	if (data == SCT_BACKSPACE)
	{
		if (lg_sct_cmd_buf_idx > 0U)
		{
			--lg_sct_cmd_buf_idx;
		}

		sprintf((char *)resp_buf, "\b \b");
		sct_FlushRespBuf(resp_buf);
	}
	else if (data == SCT_ENTER)
	{
		/* Add null termination to command buffer and process command */
		lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][lg_sct_cmd_buf_idx] = '\0';
		sct_ProcessCommand(&lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx++][0], resp_buf);

		/* Reset indexes ready for next command */
		lg_sct_cmd_buf_idx = 0U;

		if (lg_sct_cmd_buf_hist_idx >= SCT_CMD_HISTORY_LEN)
		{
			lg_sct_cmd_buf_hist_idx = 0;
		}
	}
#if 0
	else if (data == SCT_UP_ARROW)
	{
		/* Clear line and move cursor home */
		sprintf((char *)resp_buf, "%s%s", SCT_ERASE_LINE, SCT_LINE_HOME);
		sct_FlushRespBuf(resp_buf);

		/* Modify history index */
		--lg_sct_cmd_buf_hist_idx;

		if (lg_sct_cmd_buf_hist_idx < 0)
		{
			lg_sct_cmd_buf_hist_idx = SCT_CMD_HISTORY_LEN - 1;
		}

		/* Echo back to user and modify buffer index */
		sct_FlushRespBuf(&lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][lg_sct_cmd_buf_idx]);

		lg_sct_cmd_buf_idx = 0U;
		while (lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][lg_sct_cmd_buf_idx] != '\0')
		{
			++lg_sct_cmd_buf_idx;
		}
	}
#endif
	else
	{
		/* Add received byte to command buffer */
		lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][lg_sct_cmd_buf_idx++] = toupper(data);

		if (lg_sct_cmd_buf_idx >= SCT_MAX_BUF_SIZE)
		{
			lg_sct_cmd_buf_idx = 0U;
		}

		/* Echo received data */
		sprintf((char *)resp_buf, "%c", data);
		sct_FlushRespBuf(resp_buf);
	}
}

/*****************************************************************************/
/**
* Flush contents of response buffer to tx queue.
*
* @param    resp_buf buffer to flush
* @return   None
* @note     None
*
******************************************************************************/
void sct_FlushRespBuf(uint8_t *resp_buf)
{
	int16_t i = 0;

	while ((i < SCT_MAX_BUF_SIZE)  && (resp_buf[i] != '\0'))
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
* @note     None
*
******************************************************************************/
void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
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
#if 0
	else if (!strncmp((char *)cmd_buf, SCT_GET_PPS_CMD, SCT_GET_PPS_CMD_LEN))
	{
		sct_ProcessGetPpsCommand(cmd_buf);
	}
#endif
	else if (!strncmp((char *)cmd_buf, SCT_SET_PPS_EN_CMD, SCT_SET_PPS_EN_CMD_LEN))
	{
		sct_ProcessEnablePpsCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RACK_ADDRESS_CMD, SCT_SET_RACK_ADDRESS_CMD_LEN))
	{
		sct_ProcessSetRackAddressCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_DCDC_OFF_CMD, SCT_SET_DCDC_OFF_CMD_LEN))
	{
		sct_ProcessSetDcdcOffCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_SYSTEM_RESET_CMD, SCT_SET_SYSTEM_RESET_CMD_LEN))
	{
		sct_ProcessSetSystemResetCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(cmd_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_MAC_ADDR_CMD, SCT_GET_MAC_ADDR_CMD_LEN))
	{
		sct_ProcesGetMacAddressCommand(cmd_buf);
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
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf)
{
	hci_HwConfigInfoData_t hw_config_info;

	sct_I2cReInit();

	if (hci_ReadHwConfigInfo(&lg_sct_hci, &hw_config_info))
	{
		sprintf((char *)resp_buf, "Hardware Configuration Information:%s%s", SCT_CRLF, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Hardware Version No: %c%c%s%s",
				((hw_config_info.hw_version > 25U) ? (int16_t)('A') : ((int16_t)hw_config_info.hw_version + (int16_t)('A'))),
				(hw_config_info.hw_version > 25U ? ((int16_t)hw_config_info.hw_version - 26 + (int16_t)('A')) : (int16_t)(' ')),
				SCT_CRLF, SCT_CRLF);
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
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf)
{
	sct_I2cReInit();

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
* @note     None
*
******************************************************************************/
void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int32_t param_to_set;
	bool param_set = false;
	char param[HCI_STR_PARAM_LEN] = {0};

	if (sscanf((char *)cmd_buf, SCT_HW_SET_PARAM_CMD_FORMAT,
			(int *)&param_to_set, param) == SCT_HW_SET_PARAM_CMD_FORMAT_NO)
	{
		/* Ensure last character of string to set is null terminator */
		param[HCI_STR_PARAM_LEN - 1] = 0U;

		sct_I2cReInit();

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

#if 0
/*****************************************************************************/
/**
* Check if the 1PPS output from the KT-000-0139-00 board test firmware is
* present
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetPpsCommand(uint8_t *resp_buf)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(EXTI15_10_IRQn);
	uint32_t pps_delta = lg_sct_1pps_delta;
	uint32_t pps_previous = lg_sct_1pps_previous;
	HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);
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

	sprintf((char *)resp_buf, "%s%s", SCT_GET_PPS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}
#endif

/*****************************************************************************/
/**
* Enables/disables the 1PPS output to the Active Backplane
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
void sct_ProcessEnablePpsCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t set_state = 0;
	int32_t no_params = sscanf((char *)cmd_buf, SCT_SET_PPS_EN_CMD_FORMAT, &set_state);

	if (no_params == SCT_SET_PPS_EN_CMD_FORMAT_NO)
	{
		/* If set_state is non-zero enable the 1PPS output */
		if (set_state)
		{
			HAL_TIMEx_PWMN_Start_IT(lg_sct_init_data.ab_1pps_out_htim,
									lg_sct_init_data.ab_1pps_out_channel);
		}
		else
		{
			HAL_TIMEx_PWMN_Stop_IT(lg_sct_init_data.ab_1pps_out_htim,
								   lg_sct_init_data.ab_1pps_out_channel);
		}
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
* Sets the Rack Address discrete input to the KT-000-0139-00. '0' or '1'
*
* @param    None
* @return   None
* @note     Should probably check init device return values!
*
******************************************************************************/
void sct_ProcessSetRackAddressCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t set_state = 0U;
	GPIO_PinState pin_state = GPIO_PIN_RESET;

	if (sscanf((char *)cmd_buf, SCT_SET_RACK_ADDRESS_CMD_FORMAT, &set_state) ==
			SCT_SET_RACK_ADDRESS_CMD_FORMAT_NO)
	{
		if (set_state)
		{
			pin_state = GPIO_PIN_SET;
		}

		HAL_GPIO_WritePin(	lg_sct_init_data.rack_addr_gpio_port,
							lg_sct_init_data.rack_addr_gpio_pin,
							pin_state);

		sprintf((char *)resp_buf, "Set Rack Address to: %s%s",
				(set_state ? "1" : "0") , SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RACK_ADDRESS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the DCDC Off active-low discrete input to the KT-000-0139-00 to turn
* DC-DC on/off
*
* @param    None
* @return   None
* @note     Should probably check init device return values!
*
******************************************************************************/
void sct_ProcessSetDcdcOffCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t set_state = 0U;
	GPIO_PinState pin_state = GPIO_PIN_RESET;

	if (sscanf((char *)cmd_buf, SCT_SET_DCDC_OFF_CMD_FORMAT, &set_state) ==
			SCT_SET_DCDC_OFF_CMD_FORMAT_NO)
	{
		if (set_state)
		{
			pin_state = GPIO_PIN_SET;
		}

		HAL_GPIO_WritePin(	lg_sct_init_data.dcdc_off_n_gpio_port,
							lg_sct_init_data.dcdc_off_n_gpio_pin,
							pin_state);

		sprintf((char *)resp_buf, "Set DCDC to: %s%s",
				(set_state ? "ON" : "OFF") , SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_DCDC_OFF_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the active-low system reset discrete input to the KT-000-0139-00
*
* @param    None
* @return   None
* @note     Should probably check init device return values!
*
******************************************************************************/
void sct_ProcessSetSystemResetCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t set_state = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_SYSTEM_RESET_CMD_FORMAT, &set_state) ==
			SCT_SET_SYSTEM_RESET_CMD_FORMAT_NO)
	{
		if (set_state)
		{
			sct_SetSysReset(true);
		}
		else
		{
			sct_SetSysReset(false);
		}

		sprintf((char *)resp_buf, "Set System Reset to: %s%s",
				(set_state ? "TRUE" : "FALSE") , SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_SYSTEM_RESET_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the KT-000-0139-00 active-low reset signal
*
* @param    reset true to assert active-low reset, false to de-assert
* @return   None
* @note     None
*
******************************************************************************/
void sct_SetSysReset(bool reset)
{
	 HAL_GPIO_WritePin(	lg_sct_init_data.system_reset_n_gpio_port,
						lg_sct_init_data.system_reset_n_gpio_pin,
						(reset ? GPIO_PIN_RESET : GPIO_PIN_SET));
}


/*****************************************************************************/
/**
* Read and return the ADC data
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf)
{
	int32_t raw_adc_reading[SCT_ADC_NUM_CHANNELS] = {0};
	int32_t scaled_adc_reading[SCT_ADC_NUM_CHANNELS] = {0};
	int32_t vref_ext = 0;
	int16_t i;

	/* Start the ADC sampling and perform calibration to improve result accuracy */
	HAL_ADCEx_Calibration_Start(lg_sct_init_data.adc_device, ADC_SINGLE_ENDED);
	HAL_ADC_Start(lg_sct_init_data.adc_device);

	/* Get a sample for each ADC channel and add it to the averaging buffer */
	for (i = 0; i < SCT_ADC_NUM_CHANNELS; ++i)
	{
		HAL_ADC_PollForConversion(lg_sct_init_data.adc_device, 10U);
		raw_adc_reading[i] = (int32_t)HAL_ADC_GetValue(lg_sct_init_data.adc_device);
	}

	HAL_ADC_Stop(lg_sct_init_data.adc_device);

	/* Use the Vrefint reading to calculate the Vrefext in mV */
	vref_ext = (SCT_ADC_VREFINT_MV * (SCT_ADC_ADC_BITS - 1)) / raw_adc_reading[SCT_ADC_VREF_INT_CHANNEL_IDX];

	/* Calculate scaled values */
	for (i = 0; i < SCT_ADC_NUM_CHANNELS; ++i)
	{
		scaled_adc_reading[i] = (raw_adc_reading[i] * SCT_ADC_SCALE_FACTORS[i][SCT_ADC_SCALE_MUL] * vref_ext) /
								 SCT_ADC_SCALE_FACTORS[i][SCT_ADC_SCALE_DIV];
	}

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "ADC Data:%s%s", SCT_CRLF, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	for (i = 0; i < SCT_ADC_NUM_CHANNELS; ++i)
	{
		sprintf((char *)resp_buf, "%s: %ld%s", SCT_ADC_CHANNEL_NAMES[i], scaled_adc_reading[i], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ADC_DATA_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return MAC address information
*
* @param    resp_buf buffer for transmitting command response
* @return   None
*
******************************************************************************/
void sct_ProcesGetMacAddressCommand(uint8_t *resp_buf)
{
	uint8_t buf[E48_DATA_LEN_BYTES] = {0U};

	sct_I2cReInit();

	if (e48_GetEui48(&lg_sct_micro_mac_e48, buf))
	{
		sprintf((char *)resp_buf, "Micro MAC Address:\t%.2X-%.2X-%.2X-%.2X-%.2X-%.2X%s",
				buf[0],
		        buf[1],
		        buf[2],
		        buf[3],
		        buf[4],
		        buf[5],
				SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Micro MAC Address! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	if (e48_GetEui48(&lg_sct_switch_mac_e48, buf))
	{
		sprintf((char *)resp_buf, "Switch MAC Address:\t%.2X-%.2X-%.2X-%.2X-%.2X-%.2X%s",
				buf[0],
		        buf[1],
		        buf[2],
		        buf[3],
		        buf[4],
		        buf[5],
				SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Switch MAC Address! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_MAC_ADDR_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Send response associated with receiving an unknown command
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessUnkownCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s%s", SCT_UNKONWN_CMD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


static void sct_I2cReInit(void)
{
	(void) HAL_I2C_DeInit(lg_sct_init_data.i2c_device);
	(void) HAL_I2C_Init(lg_sct_init_data.i2c_device);
	(void) HAL_I2CEx_ConfigAnalogFilter(lg_sct_init_data.i2c_device, I2C_ANALOGFILTER_ENABLE);
	(void) HAL_I2CEx_ConfigDigitalFilter(lg_sct_init_data.i2c_device, 0);
}

#if 0
/*****************************************************************************/
/**
* Handle HAL EXTI GPIO Callback as these are used to change LED state
*
* @param    argument    Not used
* @return   None
* @note     None
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
#endif
