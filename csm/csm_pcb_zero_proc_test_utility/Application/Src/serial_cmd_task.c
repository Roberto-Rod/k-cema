/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file serial_cmd_task.c
*
* Provides serial command task handling.
*
* Processes received serial bytes and converts them to commands, performs
* command error handling. Command "$HELP" returns list of available commands.
*
* Project   : K-CEMA
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#define __SERIAL_CMD_TASK_C

#include "serial_cmd_task.h"
#include "version.h"
#include "hw_config_info.h"
#include "tamper_driver.h"
#include "i2c_adc_driver.h"
#include "keypad_test_board.h"
#include "i2c_temp_sensor.h"
#include "i2c_poe_driver.h"
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

#define SCT_SET_BZR_CMD					"#BZR"
#define SCT_SET_BZR_CMD_LEN				4
#define SCT_SET_BZR_CMD_FORMAT			"#BZR %hd"
#define SCT_SET_BZR_CMD_FORMAT_NO		1
#define SCT_SET_BZR_RESP				">BZR"
#define SCT_SET_BZR_RESP_LEN			4

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

#define SCT_SET_ZGPO_CMD				"#ZGPO"
#define SCT_SET_ZGPO_CMD_LEN			5
#define SCT_SET_ZGPO_CMD_FORMAT			"#ZGPO %hd"
#define SCT_SET_ZGPO_CMD_FORMAT_NO		1
#define SCT_SET_ZGPO_RESP				">ZGPO"
#define SCT_SET_ZGPO_RESP_LEN			5

#define SCT_GET_ZGPO_CMD				"$ZGPO"
#define SCT_GET_ZGPO_CMD_LEN			4
#define SCT_GET_ZGPO_RESP				"!ZGPO"
#define SCT_GET_ZGPO_RESP_LEN			4

#define SCT_READ_ANTI_TAMPER_CMD		"$RAT"
#define SCT_READ_ANTI_TAMPER_CMD_LEN	4
#define SCT_READ_ANTI_TAMPER_RESP		"!RAT"
#define SCT_READ_ANTI_TAMPER_RESP_LEN	4

#define SCT_READ_AT_RAM_CMD				"$RATR"
#define SCT_READ_AT_RAM_CMD_LEN			5
#define SCT_READ_AT_RAM_RESP			"!RATR"
#define SCT_READ_AT_RAM_RESP_LEN		5

#define SCT_SET_ANTI_TAMPER_CMD			"#SAT"
#define SCT_SET_ANTI_TAMPER_CMD_LEN		4
#define SCT_SET_ANTI_TAMPER_CMD_FORMAT	"#SAT %hd %hd %hd"
#define SCT_SET_ANTI_TAMPER_CMD_FORMAT_NO 3
#define SCT_SET_ANTI_TAMPER_RESP		">SAT"
#define SCT_SET_ANTI_TAMPER_RESP_LEN	4

#define SCT_SET_AT_RAM_CMD				"#SATR"
#define SCT_SET_AT_RAM_CMD_LEN 			5
#define SCT_SET_AT_RAM_RESP				">SATR"
#define SCT_SET_AT_RAM_RESP_LEN			5

#define SCT_READ_RTC_CMD				"$RTC"
#define SCT_READ_RTC_CMD_LEN			4
#define SCT_READ_RTC_RESP				"!RTC"
#define SCT_READ_RTC_RESP_LEN			4

#define SCT_READ_PPS_CMD				"$PPS"
#define SCT_READ_PPS_CMD_LEN			4
#define SCT_READ_PPS_RESP				"!PPS"
#define SCT_READ_PPS_RESP_LEN			4

#define SCT_GET_ADC_DATA_CMD			"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN		4
#define SCT_GET_ADC_DATA_RESP			"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN		4

#define SCT_SET_KEYPAD_PWR_BTN_CMD				"#SKPB"
#define SCT_SET_KEYPAD_PWR_BTN_CMD_LEN			5
#define SCT_SET_KEYPAD_PWR_BTN_CMD_FORMAT		"#SKPB %hd"
#define SCT_SET_KEYPAD_PWR_BTN_CMD_FORMAT_NO	1
#define SCT_SET_KEYPAD_PWR_BTN_RESP				">SKPB"
#define SCT_SET_KEYPAD_PWR_BTN_RESP_LEN			5

#define SCT_TEST_KEYPAD_CMD				"#TKP"
#define SCT_TEST_KEYPAD_CMD_LEN			4
#define SCT_TEST_KEYPAD_RESP			"!TKP"
#define SCT_TEST_KEYPAD_RESP_LEN		4

#define SCT_GET_BATT_TEMP_CMD			"$BTMP"
#define SCT_GET_BATT_TEMP_CMD_LEN		5
#define SCT_GET_BATT_TEMP_RESP			"!BTMP"
#define SCT_GET_BATT_TEMP_RESP_LEN		5

#define SCT_GET_TEMP_CMD				"$TMP"
#define SCT_GET_TEMP_CMD_LEN			4
#define SCT_GET_TEMP_RESP				"!TMP"
#define SCT_GET_TEMP_RESP_LEN			4

#define SCT_GET_POE_PORT_STATUS_CMD				"$POEP"
#define SCT_GET_POE_PORT_STATUS_CMD_LEN			5
#define SCT_GET_POE_PORT_STATUS_CMD_FORMAT		"$POEP %hd"
#define SCT_GET_POE_PORT_STATUS_CMD_FORMAT_NO	1
#define SCT_GET_POE_PORT_STATUS_RESP			"!POEP"
#define SCT_GET_POE_PORT_STATUS_RESP_LEN		5

#define SCT_GET_POE_DEVICE_STATUS_CMD			"$POED"
#define SCT_GET_POE_DEVICE_STATUS_CMD_LEN		5
#define SCT_GET_POE_DEVICE_STATUS_RESP			"!POED"
#define SCT_GET_POE_DEVICE_STATUS_RESP_LEN		5

#define SCT_SET_POE_POWER_ALLOC_CMD				"#POEP"
#define SCT_SET_POE_POWER_ALLOC_CMD_LEN			5
#define SCT_SET_POE_POWER_ALLOC_CMD_FORMAT		"#POEP %hd"
#define SCT_SET_POE_POWER_ALLOC_CMD_FORMAT_NO	1
#define SCT_SET_POE_POWER_ALLOC_RESP			">POEP"
#define SCT_SET_POE_POWER_ALLOC_RESP_LEN		5

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

#define SCT_PCA9500_EEPROM_I2C_ADDR 	0x52U << 1
#define SCT_PCA9500_GPIO_I2C_ADDR		0x22U << 1
#define SCT_ANTI_TAMPER_I2C_ADDR		0x68U << 1
#define SCT_CABLE_DETECT_I2C_ADDR		0x68U << 1
#define SCT_MCP23017_DEV0_I2C_ADDR		0x20U << 1
#define SCT_MCP23017_DEV1_I2C_ADDR		0x21U << 1
#define SCT_ZEROISE_FPGA_I2C_ADDR		0x17U << 1
#define SCT_LTC2991_ADC_I2C_ADDR		0x48U << 1
#define SCT_AD7415_TEMP_I2C_ADDR		0x49U << 1
#define SCT_SI4374_I2C_ADDR				0x22U << 1

#define SCT_ZEROISE_FPGA_WR_CMD_LEN		2U
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
void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
void sct_FlushRespBuf(uint8_t *resp_buf);
void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf);
void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf);
void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetBuzzerStateCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessReadGpiCommand(uint8_t *resp_buf);
void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetZeroiseFpgaGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetZeroiseFpgaGpoCommand(uint8_t *resp_buf);
void sct_ProcessReadAntiTamperCommand(uint8_t *resp_buf);
void sct_ProcessReadAntiTamperRamCommand(uint8_t *resp_buf);
void sct_ProcessSetAntiTamperCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetAntiTamperRamCommand(uint8_t *resp_buf);
void sct_ProcessReadRtcCommand(uint8_t *resp_buf);
void sct_ProcessReadPpsCommand(uint8_t *resp_buf);
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
void sct_ProcessSetKeypadPwrBtnCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessTestKeypadCommand(uint8_t *resp_buf);
void sct_ProcesssGetBatteryTempCommand(uint8_t *resp_buf);
static void sct_ProcessGetTempCommand(uint8_t *resp_buf);
void sct_ProcessGetPoePortStatusCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetPoeDeviceStatusCommand(uint8_t *resp_buf);
void sct_ProcessSetPoePowerAllocationCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessUnkownCommand(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static sct_Init_t lg_sct_init_data = {NULL, NULL, NULL};
static bool lg_sct_initialised = false;
static bool lg_sct_pwr_btn_toggle_in_progress = false;

static volatile uint32_t lg_sct_1pps_delta = 0U;
static volatile uint32_t lg_sct_1pps_previous = 0U;

static hci_HwConfigInfo_t		lg_sct_hci = {0};
static td_TamperDriver_t		lg_sct_anti_tamper = {0};
static td_TamperDriver_t		lg_sct_cable_detect = {0};
static iad_I2cAdcDriver_t 		lg_sct_i2c_adc = {0};
static ktb_KeypadTestBoard_t	lg_sct_keypad_test_board = {0};
static its_I2cTempSensor_t		lg_sct_batt_temp_sensor = {0};
static ipd_I2cPoeDriver_t		lg_sct_poe = {0};

static uint8_t 	lg_sct_cmd_buf[SCT_CMD_HISTORY_LEN][SCT_MAX_BUF_SIZE] = {0U};
static int16_t	lg_sct_cmd_buf_hist_idx = 0;
static uint16_t	lg_sct_cmd_buf_idx = 0U;


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

	hci_Init(	&lg_sct_hci, lg_sct_init_data.i2c_device1,
				SCT_PCA9500_GPIO_I2C_ADDR,
				SCT_PCA9500_EEPROM_I2C_ADDR);

	(void) iad_InitInstance(&lg_sct_i2c_adc, lg_sct_init_data.i2c_device1,
							SCT_LTC2991_ADC_I2C_ADDR);

	(void) td_InitInstance(	&lg_sct_anti_tamper, lg_sct_init_data.i2c_device1,
							SCT_ANTI_TAMPER_I2C_ADDR);

	(void) td_InitInstance(	&lg_sct_cable_detect, lg_sct_init_data.i2c_device0,
							SCT_CABLE_DETECT_I2C_ADDR);

	(void) ktb_InitInstance(&lg_sct_keypad_test_board,
							lg_sct_init_data.i2c_device0,
							SCT_MCP23017_DEV0_I2C_ADDR,
							lg_sct_init_data.i2c_reset_gpio_port,
							lg_sct_init_data.i2c_reset_gpio_pin);

	(void) its_Init(&lg_sct_batt_temp_sensor,
					lg_sct_init_data.i2c_device0,
					SCT_AD7415_TEMP_I2C_ADDR);

	(void) ipd_Init(&lg_sct_poe,
					lg_sct_init_data.i2c_device0,
					SCT_SI4374_I2C_ADDR);

	lg_sct_initialised = true;
}


/*****************************************************************************/
/**
* Serial command function.
*
* @param    argument    Not used
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
		sct_ProcessCommand(&lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][0], resp_buf);

		/* Reset indexes ready for next command */
		lg_sct_cmd_buf_idx = 0U;

		if (++lg_sct_cmd_buf_hist_idx >= SCT_CMD_HISTORY_LEN)
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
		lg_sct_cmd_buf[lg_sct_cmd_buf_hist_idx][lg_sct_cmd_buf_idx] = toupper(data);

		if (++lg_sct_cmd_buf_idx >= SCT_MAX_BUF_SIZE)
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
*
******************************************************************************/
void sct_FlushRespBuf(uint8_t *resp_buf)
{
	int16_t i = 0;

	while ((i < SCT_MAX_BUF_SIZE) && (resp_buf[i] != '\0'))
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
	else if (!strncmp((char *)cmd_buf, SCT_SET_BZR_CMD, SCT_SET_BZR_CMD_LEN))
	{
		sct_ProcessSetBuzzerStateCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_GPI_CMD, SCT_READ_GPI_CMD_LEN))
	{
		sct_ProcessReadGpiCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN))
	{
		sct_ProcessSetGpoCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_ZGPO_CMD, SCT_SET_ZGPO_CMD_LEN))
	{
		sct_ProcessSetZeroiseFpgaGpoCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_ZGPO_CMD, SCT_GET_ZGPO_CMD_LEN))
	{
		sct_ProcessGetZeroiseFpgaGpoCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_AT_RAM_CMD, SCT_READ_AT_RAM_CMD_LEN))
	{
		sct_ProcessReadAntiTamperRamCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_ANTI_TAMPER_CMD, SCT_READ_ANTI_TAMPER_CMD_LEN))
	{
		sct_ProcessReadAntiTamperCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_AT_RAM_CMD, SCT_SET_AT_RAM_CMD_LEN))
	{
		sct_ProcessSetAntiTamperRamCommand(cmd_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_ANTI_TAMPER_CMD, SCT_SET_ANTI_TAMPER_CMD_LEN))
	{
		sct_ProcessSetAntiTamperCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_RTC_CMD, SCT_READ_RTC_CMD_LEN))
	{
		sct_ProcessReadRtcCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_PPS_CMD, SCT_READ_PPS_CMD_LEN))
	{
		sct_ProcessReadPpsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(cmd_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_KEYPAD_PWR_BTN_CMD, SCT_SET_KEYPAD_PWR_BTN_CMD_LEN))
	{
		sct_ProcessSetKeypadPwrBtnCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_TEST_KEYPAD_CMD, SCT_TEST_KEYPAD_CMD_LEN))
	{
		sct_ProcessTestKeypadCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_BATT_TEMP_CMD, SCT_GET_BATT_TEMP_CMD_LEN))
	{
		sct_ProcesssGetBatteryTempCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_TEMP_CMD, SCT_GET_TEMP_CMD_LEN))
	{
		sct_ProcessGetTempCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_POE_PORT_STATUS_CMD, SCT_GET_POE_PORT_STATUS_CMD_LEN))
	{
		sct_ProcessGetPoePortStatusCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_POE_DEVICE_STATUS_CMD, SCT_GET_POE_DEVICE_STATUS_CMD_LEN))
	{
		sct_ProcessGetPoeDeviceStatusCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_POE_POWER_ALLOC_CMD, SCT_SET_POE_POWER_ALLOC_CMD_LEN))
	{
		sct_ProcessSetPoePowerAllocationCommand(cmd_buf, resp_buf);
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
void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf)
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
void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf)
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
* Sets the buzzer enable signal state, disable if serial command parameter is
* zero, else enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetBuzzerStateCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
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
* Sets the Zeroise FPGA GPO test signal to a specified state, pin is set "low"
* if set state parameter is '0', else "high"
*
* The 1 MHz RC output will also be enabled/disabled based on the set state
* parameter: '0' = disabled, else enabled
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetZeroiseFpgaGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t set_state = 0;
	uint8_t buf[SCT_ZEROISE_FPGA_WR_CMD_LEN] = {0U};

	if (sscanf((char *)cmd_buf, SCT_SET_ZGPO_CMD_FORMAT, &set_state) ==
			SCT_SET_ZGPO_CMD_FORMAT_NO)
	{
		buf[0] = 0xFFU;
		buf[1] = (uint8_t)(set_state & 0xFFU);

		if (HAL_I2C_Master_Transmit(lg_sct_init_data.i2c_device0,
									SCT_ZEROISE_FPGA_I2C_ADDR,
									buf, SCT_ZEROISE_FPGA_WR_CMD_LEN,
									SCT_I2C_TIMEOUT_MS) == HAL_OK)
		{
			sprintf((char *)resp_buf, "Zeroise FPGA GPO register set to: %.2x%s",
					set_state, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf,
					"*** Failed to set Zeroise FPGA GPO (TP23) ***%s", SCT_CRLF);
		}
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_ZGPO_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Gets the Zeroise FPGA GPO test signal set state
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessGetZeroiseFpgaGpoCommand(uint8_t *resp_buf)
{
	uint8_t buf[4] = {0U};

	if (HAL_I2C_Mem_Read(	lg_sct_init_data.i2c_device0,
							SCT_ZEROISE_FPGA_I2C_ADDR,
							0xFCU, 1U, buf, 4U, I2C_TIMEOUT) == HAL_OK)
	{
		sprintf((char *)resp_buf, "0x%.2x - Fw Build Version register%s",
				buf[0], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "0x%.2x - Fw Minor Version register%s",
				buf[1], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "0x%.2x - Fw Major Version register%s",
				buf[2], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "0x%.2x - GPO register%s",
				buf[3], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf,
				"*** Failed to get Zeroise FPGA GPO ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ZGPO_RESP, SCT_CRLF);
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

	if (td_ReadRegister(&lg_sct_cable_detect, TD_TAMPER1_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Tamper 1%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_TAMPER2_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Tamper 2%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_ALARM_MONTH_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Alarm Month%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_DAY_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Day%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_SECONDS_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Seconds%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_ALARM_HOUR_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Alarm Hour%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if (td_ReadRegister(&lg_sct_cable_detect, TD_FLAGS_REG, &buf))
	{
		sprintf((char *)resp_buf, "%.2x - Cable Detect Flags%s", buf, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_ANTI_TAMPER_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Reads anti-tamper SRAM of both M42ST87W devices and reports read values, checks
* that the SRAM values have been initialised with values by the #SATR
* command, 0 to 127, reports PASS if they have.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessReadAntiTamperRamCommand(uint8_t *resp_buf)
{
	uint8_t i = 0U;
	uint8_t buf = 0U;
	bool test_pass = true;

	for (i = 0U; i < TD_SRAM_LEN; ++i)
	{
		(void) td_ReadRegister(&lg_sct_cable_detect, TD_SRAM_START + i, &buf);
		sprintf((char *)resp_buf, "at a:%.2x;d:%.2x %s%s",
				TD_SRAM_START + i, buf, (buf == i ? "T" : "F"), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		test_pass &= (buf == i ? true : false);
	}

	for (i = 0U; i < TD_SRAM_LEN; ++i)
	{
		(void) td_ReadRegister(&lg_sct_cable_detect, TD_SRAM_START + i, &buf);
		sprintf((char *)resp_buf, "cd a:%.2x;d:%.2x %s%s",
				TD_SRAM_START + i, buf, (buf == i ? "T" : "F"), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		test_pass &= (buf == i ? true : false);
	}

	sprintf((char *)resp_buf, "Test Result: %s%s",
			(test_pass ? "PASS" : "FAIL"), SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_READ_AT_RAM_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the specified anti-tamper channel, parameters are:
* device - '0' for anti-tamper; or '1' for cable detect
* channel - '0' for channel 1; or '2' for channel 1
* enable - '0' to disable; else enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetAntiTamperCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t device = -1;
	int16_t channel = -1;
	int16_t enable = 0;
	td_TamperDriver_t *p_inst = NULL;
	/* Default tamper sensor is Normally Open, Tamper to GND */
	bool tcm = true;
	bool tpm = false;

	if (sscanf(	(char *)cmd_buf, SCT_SET_ANTI_TAMPER_CMD_FORMAT,
				&device, &channel, &enable) == SCT_SET_ANTI_TAMPER_CMD_FORMAT_NO)
	{
		/* Validate device and channel parameter values */
		if ((device >= 0) && (device <= 1) &&
			(channel >= 0) && (channel <= 1))
		{
			if (device == 0)
			{
				p_inst = &lg_sct_anti_tamper;
				if (channel == 0)
				{	/* Case switch on Rev B.1 board is Normally Closed to GND */
					tcm = false;
					tpm = true;
				}
			}
			else
			{
				p_inst = &lg_sct_cable_detect;
			}

			if (td_TamperEnable(p_inst, channel, tpm, tcm, (enable == 0 ? false : true)))
			{
				sprintf((char *)resp_buf, "Tamper device %s channel %hd %s%s",
						(device == 0 ? "ANTI-TAMPER" : "CABLE DETECT"), channel,
						(enable == 0 ? "DISABLED" : "ENABLED"), SCT_CRLF);
			}
			else
			{
				sprintf((char *)resp_buf, "*** Failed to set tamper device %s channel %hd %s! ***%s",
						(device == 0 ? "ANTI-TAMPER" : "CABLE DETECT"), channel,
						(enable == 0 ? "DISABLED" : "ENABLED"), SCT_CRLF);
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
* Initialises SRAM of both M42ST87W devices with ascending number sequence,
* 0 to 127
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetAntiTamperRamCommand(uint8_t *resp_buf)
{
	uint8_t i = 0U;

	for (i = 0U; i < TD_SRAM_LEN; ++i)
	{
		(void) td_WriteRegister(&lg_sct_anti_tamper, TD_SRAM_START + i, i);
		(void) td_WriteRegister(&lg_sct_cable_detect, TD_SRAM_START + i, i);
		sprintf((char *)resp_buf, "a:%.2x;\td:%.2x%s", TD_SRAM_START + i, i, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_AT_RAM_RESP, SCT_CRLF);
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
				"Anti-tamper RTC: %u%u:%u%u:%u%u%s",
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
		sprintf((char *)resp_buf, "*** Failed to read Anti-tamper RTC! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	if(td_GetTime(&lg_sct_cable_detect, &curr_time))
	{
		sprintf((char *)resp_buf,
				"Power Cable Detect RTC: %u%u:%u%u:%u%u%s",
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
		sprintf((char *)resp_buf, "*** Failed to read Power Cable Detect RTC! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_RTC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Check if the 1PPS output from the SoM is present
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessReadPpsCommand(uint8_t *resp_buf)
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
* Read and return the ADC data
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf)
{
	iad_I2cAdcData_t adc_data;
	int16_t i = 0;
	const char **adc_ch_names = iad_GetChannelNames();

	if (iad_ReadAdcData(&lg_sct_i2c_adc, &adc_data))
	{
		sprintf((char *)resp_buf, "ADC Data:%s%s", SCT_CRLF, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		for (i = 0U; i < IAD_LTC2991_SE_CH_NUM; ++i)
		{
			sprintf((char *)resp_buf, "%s: %u%s",
					adc_ch_names[i], adc_data.adc_ch_mv[i], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}

		sprintf((char *)resp_buf, "%s: %u%s",
				adc_ch_names[IAD_LTC2991_VCC_RD_IDX], adc_data.adc_ch_vcc_mv, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "%s: %u%s",
				adc_ch_names[IAD_LTC2991_INT_TEMP_RD_IDX], adc_data.adc_ch_int_temp_k, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read ADC data! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ADC_DATA_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Assert the Keypad Power Button, if the parameter is '0' assert for
* 10-seconds to power down the board, else toggle for 1-second to power the
* board on.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetKeypadPwrBtnCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t toggle_cmd = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_KEYPAD_PWR_BTN_CMD_FORMAT, &toggle_cmd) ==
			SCT_SET_KEYPAD_PWR_BTN_CMD_FORMAT_NO)
	{
		if (!lg_sct_pwr_btn_toggle_in_progress)
		{
			/* Timer pre-scaled so that counter value is resolution of ms */
			lg_sct_init_data.pwr_btn_timer->Init.Period = toggle_cmd ? 1100U : 11000U;
			(void) HAL_TIM_Base_Init(lg_sct_init_data.pwr_btn_timer);
			(void) HAL_TIM_Base_Start_IT(lg_sct_init_data.pwr_btn_timer);

			(void) ktb_InitDevice(&lg_sct_keypad_test_board);
			(void) ktb_SetButton(&lg_sct_keypad_test_board, ktb_btn_power, true);

			lg_sct_pwr_btn_toggle_in_progress = true;

			sprintf((char *)resp_buf, "Toggling Power Button: %s%s",
					(toggle_cmd ? "ON" : "OFF"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "Power Button Toggle in Progress!%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_KEYPAD_PWR_BTN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

void sct_KeypadPwrBtnCallback(void)
{
	ktb_DisableDevice(&lg_sct_keypad_test_board);
	lg_sct_pwr_btn_toggle_in_progress = false;
}


/*****************************************************************************/
/**
* Test the Keypad Button Inputs using the loopback test board.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessTestKeypadCommand(uint8_t *resp_buf)
{
	ktb_Buttons_t i;
	int16_t gpi_idx;
	bool button_test;
	const char **btn_names = ktb_GetButtonNames();

	(void) ktb_InitDevice(&lg_sct_keypad_test_board);

	for (i = ktb_btn_0; i <= ktb_btn_2; ++i)
	{
		gpi_idx = i - ktb_btn_0 + 4;

		(void) ktb_SetButton(&lg_sct_keypad_test_board, i, false);
		HAL_Delay(200U);
		button_test = (HAL_GPIO_ReadPin(lg_sct_init_data.gpi_pins[gpi_idx].port, lg_sct_init_data.gpi_pins[gpi_idx].pin) == GPIO_PIN_SET);

		(void) ktb_SetButton(&lg_sct_keypad_test_board, i, true);
		HAL_Delay(200U);
		button_test &= (HAL_GPIO_ReadPin(lg_sct_init_data.gpi_pins[gpi_idx].port, lg_sct_init_data.gpi_pins[gpi_idx].pin) == GPIO_PIN_RESET);

		(void) ktb_SetButton(&lg_sct_keypad_test_board, i, false);
		HAL_Delay(200U);
		button_test &= (HAL_GPIO_ReadPin(lg_sct_init_data.gpi_pins[gpi_idx].port, lg_sct_init_data.gpi_pins[gpi_idx].pin) == GPIO_PIN_SET);

		sprintf((char *)resp_buf, "%s - %s%s",button_test ? "PASS" : "FAIL" ,btn_names[i], SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	ktb_DisableDevice(&lg_sct_keypad_test_board);

	sprintf((char *)resp_buf, "%s%s", SCT_TEST_KEYPAD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return the battery temperature.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcesssGetBatteryTempCommand(uint8_t *resp_buf)
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
* Read and return the status for the requested PoE port.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessGetPoePortStatusCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t port = 0;
	ipd_PortStatus_t port_power_status = {0};

	if (sscanf((char *)cmd_buf, SCT_GET_POE_PORT_STATUS_CMD_FORMAT, &port) ==
			SCT_GET_POE_PORT_STATUS_CMD_FORMAT_NO)
	{
		if (ipd_IsPortValid(port))
		{
			if (ipd_GetPortPowerStatus(&lg_sct_poe, port, &port_power_status))
			{
				sprintf((char *)resp_buf, "PoE Port %hd Status:%s", port, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Port Mode:\t%d%s", port_power_status.mode, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Power Enable:\t%d%s", port_power_status.power_enable, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Power Good:\t%d%s", port_power_status.power_good, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Power On Fault:\t%d%s", port_power_status.power_on_fault, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "2P4P Mode:\t%d%s", port_power_status.port_2p4p_mode, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Pwr Allocation:\t%u%s", port_power_status.power_allocation, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Class Status:\t%d%s", port_power_status.class_status, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Detect Status:\t%d%s", port_power_status.detection_status, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Voltage (mV):\t%lu%s", port_power_status.voltage, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
				sprintf((char *)resp_buf, "Current (mA):\t%lu%s", port_power_status.current_ma, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
			else
			{
				sprintf((char *)resp_buf, "*** Failed to Get PoE Port %hd Status! ***%s", port, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
		}
		else
		{
			sprintf((char *)resp_buf, "*** Invalid PoE Port Number - %hd! ***%s", port, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_POE_PORT_STATUS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Read and return the device status.
*
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessGetPoeDeviceStatusCommand(uint8_t *resp_buf)
{
	ipd_DeviceStatus_t device_status = {0};

	if (ipd_GetDeviceStatus(&lg_sct_poe, &device_status))
	{
		sprintf((char *)resp_buf, "PoE Port Device Status:%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Temp (0.1 dC):\t%lu%s", device_status.temperature, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Voltage (mV):\t%lu%s", device_status.voltage, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to Get PoE Device Status! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	 }

	sprintf((char *)resp_buf, "%s%s", SCT_GET_POE_DEVICE_STATUS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Set the Power Allocation Mode for the PoE PSE device.  Parameter values:
*
* 0 - RCU and Programming 30 W Class 4
* 1 - RCU 45 W Class 4 and Programming 15 W Class 3
* 2 - RCU 15 W Class 3 and Programming 45 W Class 4
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
void sct_ProcessSetPoePowerAllocationCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	bool success = true;
	int16_t power_alloc_mode = 0;
	ipd_PowerAllocation_t first_port_pa_mode;
	ipd_PowerAllocation_t second_port_pa_mode;
	int16_t first_port;
	int16_t second_port;
	static int16_t last_power_alloc_mode = 0;	/* Auto Default Hardware Value */


	if (sscanf((char *)cmd_buf, SCT_SET_POE_POWER_ALLOC_CMD_FORMAT, &power_alloc_mode) ==
			SCT_SET_POE_POWER_ALLOC_CMD_FORMAT_NO)
	{
		if ((power_alloc_mode >= 0) && (power_alloc_mode <= 2))
		{
			switch (power_alloc_mode)
			{
			case 0:
				if (last_power_alloc_mode == 2)
				{
					first_port = 5;
					second_port = 1;
				}
				else
				{
					first_port = 1;
					second_port = 5;
				}
				first_port_pa_mode = ipd_pa_ss_class4_ds_class3;
				second_port_pa_mode = ipd_pa_ss_class4_ds_class3;
				break;

			case 1:
				first_port = 5;
				second_port = 1;
				first_port_pa_mode = ipd_pa_ss_class3_ds_class2;
				second_port_pa_mode = ipd_pa_ss_class5_ds_class4_class3;
				break;

			case 2:
				first_port = 1;
				second_port = 5;
				first_port_pa_mode = ipd_pa_ss_class3_ds_class2;
				second_port_pa_mode = ipd_pa_ss_class5_ds_class4_class3;
				break;

			default:
				/* Can't ever get here - set ports to minimum power! */
				first_port = 1;
				second_port = 5;
				first_port_pa_mode = ipd_pa_ss_class3_ds_class2;
				second_port_pa_mode = ipd_pa_ss_class3_ds_class2;
				break;
			}

			last_power_alloc_mode = power_alloc_mode;

			success = ipd_SetPortPowerAllocation(&lg_sct_poe, first_port, first_port_pa_mode);
			success = success && ipd_SetPortPowerAllocation(&lg_sct_poe, second_port, second_port_pa_mode);

			if (success)
			{
				sprintf((char *)resp_buf, "Set PoE Power Allocation Mode - %hd%s", power_alloc_mode, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
			else
			{
				sprintf((char *)resp_buf, "*** Failed to Set PoE Power Allocation Mode - %hd! ***%s", power_alloc_mode, SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
		}
		else
		{
			sprintf((char *)resp_buf, "*** Invalid PoE Power Allocation Mode - %hd! ***%s", power_alloc_mode, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_POE_POWER_ALLOC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Send response associated with receiving an unknown command
*
******************************************************************************/
void sct_ProcessUnkownCommand(uint8_t *resp_buf)
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
