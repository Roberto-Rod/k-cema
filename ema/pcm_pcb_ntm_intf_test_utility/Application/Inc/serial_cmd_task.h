/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
#include "hw_config_info.h"
#include "fan_controller.h"
#include "dcdc_voltage_control.h"

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
	osMessageQId 		tx_data_queue;
	osMessageQId 		rx_data_queue;
	I2C_HandleTypeDef* 	i2c_device;
	GPIO_TypeDef		*fan_alert_n_gpio_port;
	uint16_t			fan_alert_n_gpio_pin;
	GPIO_TypeDef		*rf_mute_n_gpio_port;
	uint16_t			rf_mute_n_gpio_pin;
	GPIO_TypeDef		*pfi_n_gpio_port;
	uint16_t			pfi_n_gpio_pin;
	uint16_t			pps_gpio_pin;
	ADC_HandleTypeDef	*aop_adc_hadc;
} sct_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void sct_InitTask(sct_Init_t init_data);
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

#define SCT_READ_RDAC_CMD				"$RDAC"
#define SCT_READ_RDAC_CMD_LEN			5
#define SCT_READ_RDAC_RESP				"!RDAC"
#define SCT_READ_RDAC_RESP_LEN			5

#define SCT_SET_RDAC_CMD				"#RDAC"
#define SCT_SET_RDAC_CMD_LEN			5
#define SCT_SET_RDAC_CMD_FORMAT			"#RDAC %hu"
#define SCT_SET_RDAC_CMD_FORMAT_NO		1
#define SCT_SET_RDAC_RESP				">RDAC"
#define SCT_SET_RDAC_RESP_LEN			5

#define SCT_RESET_RDAC_CMD				"#RSRDAC"
#define SCT_RESET_RDAC_CMD_LEN			7
#define SCT_RESET_RDAC_RESP				">RSRDAC"
#define SCT_RESET_RDAC_RESP_LEN			7

#define SCT_READ_50TP_CMD				"$50TP"
#define SCT_READ_50TP_CMD_LEN			5
#define SCT_READ_50TP_RESP				"!50TP"
#define SCT_READ_50TP_RESP_LEN			5

#define SCT_SET_50TP_CMD				"#50TP"
#define SCT_SET_50TP_CMD_LEN			5
#define SCT_SET_50TP_RESP				">50TP"
#define SCT_SET_50TP_RESP_LEN			5

#define SCT_INIT_FAN_CTRLR				"#INIFAN"
#define SCT_INIT_FAN_CTRLR_LEN			7
#define SCT_INIT_FAN_CTRLR_RESP			">INIFAN"
#define SCT_INIT_FAN_CTRLR_RESP_LEN		7

#define SCT_FAN_PUSH_TEMP				"#FPT"
#define SCT_FAN_PUSH_TEMP_LEN			4
#define SCT_FAN_PUSH_TEMP_FORMAT		"#FPT %hi"
#define SCT_FAN_PUSH_TEMP_FORMAT_NO 	1
#define SCT_FAN_PUSH_TEMP_RESP			">FPT"
#define SCT_FAN_PUSH_TEMP_RESP_LEN		4

#define SCT_FAN_SET_DIRECT				"#FDS"
#define SCT_FAN_SET_DIRECT_LEN			4
#define SCT_FAN_SET_DIRECT_FORMAT		"#FDS %hui"
#define SCT_FAN_SET_DIRECT_FORMAT_NO 	1
#define SCT_FAN_SET_DIRECT_RESP			">FDS"
#define SCT_FAN_SET_DIRECT_RESP_LEN		4

#define SCT_FAN_GET_SPEED_CMD			"$FSP"
#define SCT_FAN_GET_SPEED_CMD_LEN		4
#define SCT_FAN_GET_SPEED_RESP			"!FSP"
#define SCT_FAN_GET_SPEED_RESP_LEN		4

#define SCT_FAN_GET_TACH_TRGT_CMD		"$FTT"
#define SCT_FAN_GET_TACH_TRGT_CMD_LEN	4
#define SCT_FAN_GET_TACH_TRGT_RESP		"!FTT"
#define SCT_FAN_GET_TACH_TRGT_RESP_LEN 	4

#define SCT_FAN_GET_TEMP_CMD			"$TMP"
#define SCT_FAN_GET_TEMP_CMD_LEN		4
#define SCT_FAN_GET_TEMP_RESP			"!TMP"
#define SCT_FAN_GET_TEMP_RESP_LEN		4

#define SCT_FAN_STATUS_CMD				"$FST"
#define SCT_FAN_STATUS_CMD_LEN			4
#define SCT_FAN_STATUS_RESP				"!FST"
#define SCT_FAN_STATUS_RESP_LEN			4

#define SCT_READ_DOP_CMD				"$DOP"
#define SCT_READ_DOP_CMD_LEN			4
#define SCT_READ_DOP_RESP				"!DOP"
#define SCT_READ_DOP_RESP_LEN			4

#define SCT_READ_PPS_CMD				"$PPS"
#define SCT_READ_PPS_CMD_LEN			4
#define SCT_READ_PPS_RESP				"!PPS"
#define SCT_READ_PPS_RESP_LEN			4

#define SCT_READ_AOP_CMD				"$AOP"
#define SCT_READ_AOP_CMD_LEN			4
#define SCT_READ_AOP_RESP				"!AOP"
#define SCT_READ_AOP_RESP_LEN			4

#define SCT_HELP_CMD					"$HELP"
#define SCT_HELP_CMD_LEN				5
#define SCT_HELP_RESP					"!HELP"
#define SCT_HELP_RESP_LEN				5

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

/* I2C device addresses... */
#define SCT_PCA9500_EEPROM_I2C_ADDR 	(0x57U << 1)
#define SCT_PCA9500_GPIO_I2C_ADDR		(0x27U << 1)
#define SCT_EMC2104_I2C_ADDR    		(0x2FU << 1)
#define SCT_AD5272_I2C_ADDR       		(0x2CU << 1)

/* 1PPS accuracy limits */
#define SCT_1PPS_DELTA_MIN				999U
#define SCT_1PPS_DELTA_MAX				1001U

/* ADC channel definitions */
#define SCT_AOP_NUM_CHANNELS			3
#define SCT_AOP_AVERAGE_LENGTH			5
#define SCT_AOP_VREFINT_MV				1210
#define SCT_AOP_ADC_BITS				4096
#define SCT_AOP_VREF_INT_CHANNEL_IDX	0
#define SCT_AOP_RAIL_3V4_CHANNEL_IDX	1
#define SCT_AOP_RAIL_28V_CHANNEL_IDX	2
#define SCT_AOP_SCALE_MUL				0
#define SCT_AOP_SCALE_DIV				1
#define SCT_AOP_ERROR_LOW				0
#define SCT_AOP_ERROR_HIGH				1

static const int32_t SCT_AOP_SCALE_FACTORS[SCT_AOP_NUM_CHANNELS][2] =
{
		{1, SCT_AOP_ADC_BITS - 1},		/* Vrefint multiplier and divider */
		{3, SCT_AOP_ADC_BITS - 1},		/* +3V4_STBY rail multiplier and divider */
		{11, SCT_AOP_ADC_BITS - 1}		/* +28V rail multiplier and divider */
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
void sct_ProcessReadRdacCommand(uint8_t *resp_buf);
void sct_ProcessSetRdacCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessResetRdacCommand(uint8_t *resp_buf);
void sct_ProcessRead50TpCommand(uint8_t *resp_buf);
void sct_ProcessSet50TpCommand(uint8_t *resp_buf);
void sct_ProcessInitFanControllerCommand(uint8_t *resp_buf);
void sct_ProcessPushFanTempCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetFanDirectCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetFanSpeedCommand(uint8_t *resp_buf);
void sct_ProcessGetFanTachTargetCommand(uint8_t *resp_buf);
void sct_ProcessGetFanTempCommand(uint8_t *resp_buf);
void sct_ProcessGetFanStatusCommand(uint8_t *resp_buf);
void sct_ProcessReadDigitalOutputsCommand(uint8_t *resp_buf);
void sct_ProcessReadPpsCommand(uint8_t *resp_buf);
void sct_ProcessReadAnalogOutputsCommand(uint8_t *resp_buf);
void sct_ProcessUnkownCommand(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sct_Init_t lg_sct_init_data = {0};
bool lg_sct_initialised = false;
volatile uint32_t lg_sct_1pps_delta = 0U;
volatile uint32_t lg_sct_1pps_previous = 0U;

hci_HwConfigInfo_t			lg_sct_hci = {0};
fc_FanCtrlrDriver_t			lg_sct_fan_ctrlr = {0};
dvc_DcdcVoltCtrlDriver_t	lg_sct_dcdc_volt_ctrl = {0};

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
