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
#include "stm32l4xx_hal.h"
#include "test_board_gpio.h"
#include "hw_config_info.h"
#include "i2c_adc_driver.h"
#include "i2c_dac_driver.h"
#include "spi_synth_driver.h"
#include "spi_adc_driver.h"

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
	I2C_HandleTypeDef  	*i2c_device;
	GPIO_TypeDef    	*i2c_reset_gpio_port;
	uint16_t			i2c_reset_gpio_pin;
	SPI_HandleTypeDef	*spi_device;
	GPIO_TypeDef		*global_ncs_gpio_port;
	uint16_t			global_ncs_gpio_pin;
	GPIO_TypeDef		*synth1_ncs_gpio_port;
	uint16_t			synth1_ncs_gpio_pin;
	GPIO_TypeDef		*synth2_ncs_gpio_port;
	uint16_t			synth2_ncs_gpio_pin;
	GPIO_TypeDef		*mxr_lev_adc_ncs_gpio_port;
	uint16_t			mxr_lev_adc_ncs_gpio_pin;
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
#define SCT_HW_RST_CONFIG_INFO_RESP_LEN	4

#define SCT_HW_SET_PARAM_CMD			"#SHCI"
#define SCT_HW_SET_PARAM_CMD_LEN		5
#define SCT_HW_SET_PARAM_CMD_FORMAT		"#SHCI %d %16s"
#define SCT_HW_SET_PARAM_CMD_FORMAT_NO	2
#define SCT_HW_SET_PARAM_RESP			">SHCI"
#define SCT_HW_SET_PARAM_RESP_LEN		5

#define SCT_GET_BOARD_ID_CMD			"$BID"
#define SCT_GET_BOARD_ID_CMD_LEN		4
#define SCT_GET_BOARD_ID_RESP			"!BID"
#define SCT_GET_BOARD_ID_RESP_LEN		4

#define SCT_SET_RX_PWR_EN_CMD			"#RXPE"
#define SCT_SET_RX_PWR_EN_CMD_LEN		5
#define SCT_SET_RX_PWR_EN_CMD_FORMAT	"#RXPE %hu"
#define SCT_SET_RX_PWR_EN_CMD_FORMAT_NO	1
#define SCT_SET_RX_PWR_EN_RESP			">RXPE"
#define SCT_SET_RX_PWR_EN_RESP_LEN		5

#define SCT_GET_ADC_DATA_CMD			"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN		4
#define SCT_GET_ADC_DATA_RESP			"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN		4

#define SCT_SET_DAC_CMD					"#DAC"
#define SCT_SET_DAC_CMD_LEN				4
#define SCT_SET_DAC_CMD_FORMAT			"#DAC %hu"
#define SCT_SET_DAC_CMD_FORMAT_NO		1
#define SCT_SET_DAC_RESP				">DAC"
#define SCT_SET_DAC_RESP_LEN			4

#define SCT_SET_DACE_CMD				"#DACE"
#define SCT_SET_DACE_CMD_LEN			5
#define SCT_SET_DACE_CMD_FORMAT			"#DACE %hu %hu %hu %hu %hu"
#define SCT_SET_DACE_CMD_FORMAT_NO		5
#define SCT_SET_DACE_RESP				">DACE"
#define SCT_SET_DACE_RESP_LEN			5

#define SCT_READ_DAC_CMD				"$DAC"
#define SCT_READ_DAC_CMD_LEN			4
#define SCT_READ_DAC_CMD_FORMAT			"$DAC %hu"
#define SCT_READ_DAC_CMD_FORMAT_NO		1
#define SCT_READ_DAC_RESP				"!DAC"
#define SCT_READ_DAC_RESP_LEN			4

#define SCT_GET_LOCK_DETS_CMD			"$LDS"
#define SCT_GET_LOCK_DETS_CMD_LEN		4
#define SCT_GET_LOCK_DETS_RESP			"!LDS"
#define SCT_GET_LOCK_DETS_RESP_LEN		4

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

#define SCT_SYNTH_SEL_CMD				"#SSEL"
#define SCT_SYNTH_SEL_CMD_LEN			5
#define SCT_SYNTH_SEL_CMD_FORMAT		"#SSEL %hd"
#define SCT_SYNTH_SEL_CMD_FORMAT_NO		1
#define SCT_SYNTH_SEL_RESP				">SSEL"
#define SCT_SYNTH_SEL_RESP_LEN			5

#define SCT_SET_SYNTH_FREQ_CMD			"#SFQ"
#define SCT_SET_SYNTH_FREQ_CMD_LEN		4
#define SCT_SET_SYNTH_FREQ_CMD_FORMAT	"#SFQ %hd %lu"
#define SCT_SET_SYNTH_FREQ_CMD_FORMAT_NO 2
#define SCT_SET_SYNTH_FREQ_RESP			">SFQ"
#define SCT_SET_SYNTH_FREQ_RESP_LEN		4

#define SCT_SET_PRESEL_CMD				"#PSLR"
#define SCT_SET_PRESEL_CMD_LEN			5
#define SCT_SET_PRESEL_CMD_FORMAT		"#PSLR %hu"
#define SCT_SET_PRESEL_CMD_FORMAT_NO	1
#define SCT_SET_PRESEL_RESP				">PSLR"
#define SCT_SET_PRESEL_RESP_LEN			5

#define SCT_SET_RF_ATTEN_CMD			"#RATT"
#define SCT_SET_RF_ATTEN_CMD_LEN		5
#define SCT_SET_RF_ATTEN_CMD_FORMAT		"#RATT %hu"
#define SCT_SET_RF_ATTEN_CMD_FORMAT_NO	1
#define SCT_SET_RF_ATTEN_RESP			">RATT"
#define SCT_SET_RF_ATTEN_RESP_LEN		5

#define SCT_SET_IF_ATTEN_CMD			"#IATT"
#define SCT_SET_IF_ATTEN_CMD_LEN		5
#define SCT_SET_IF_ATTEN_CMD_FORMAT		"#IATT %hu"
#define SCT_SET_IF_ATTEN_CMD_FORMAT_NO	1
#define SCT_SET_IF_ATTEN_RESP			">IATT"
#define SCT_SET_IF_ATTEN_RESP_LEN		5

#define SCT_SET_LNA_BYPASS_CMD			"#LNBY"
#define SCT_SET_LNA_BYPASS_CMD_LEN		5
#define SCT_SET_LNA_BYPASS_CMD_FORMAT	"#LNBY %hu"
#define SCT_SET_LNA_BYPASS_CMD_FORMAT_NO 1
#define SCT_SET_LNA_BYPASS_RESP			">LNBY"
#define SCT_SET_LNA_BYPASS_RESP_LEN		5

#define SCT_GET_MXR_LEVEL_CMD			"$MXL"
#define SCT_GET_MXR_LEVEL_CMD_LEN		4
#define SCT_GET_MXR_LEVEL_RESP			"!MXL"
#define SCT_GET_MXR_LEVEL_RESP_LEN		4

#define SCT_PCA9500_EEPROM_I2C_ADDR 	0x50U << 1
#define SCT_PCA9500_GPIO_I2C_ADDR		0x20U << 1
#define SCT_LTC2991_ADC_I2C_ADDR		0x4CU << 1
#define SCT_MCP4728_DAC_I2C_ADDR		0x60U << 1

#define SCT_SET_DAC_VAL_MIN				300U
#define SCT_SET_DAC_VAL_MAX				3000U

#define	SCT_NUM_SPI_SYNTHS				2

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
void sct_ProcessGetBoardIdCommand(uint8_t *resp_buf);
void sct_ProcessSetRxPwrEnCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
void sct_ProcesssSetDacDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcesssReadDacDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcesssSetDacEepromDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetLockDetectsCommand(uint8_t *resp_buf);
void sct_ProcessSelectSynthCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRfCentreFreqCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetPreselectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRfAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetIfAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetLnaBypassCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetMixerLevelCommand(uint8_t *resp_buf);
void sct_ProcessUnkownCommand(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
sct_Init_t lg_sct_init_data = {NULL, NULL, NULL};
bool lg_sct_initialised = false;

tbg_TestBoardGpio_t lg_sct_tb_gpio = {0};
hci_HwConfigInfo_t	lg_sct_hci = {0};
iad_I2cAdcDriver_t 	lg_sct_i2c_adc = {0};
idd_I2cDacDriver_t	lg_sct_dac = {0};
ssd_SpiSynthDriver_t lg_sct_synth[SCT_NUM_SPI_SYNTHS] = {0};
sad_SpiAdcDriver_t 	lg_sct_spi_dac = {0};

uint8_t 	lg_sct_cmd_buf[SCT_CMD_HISTORY_LEN][SCT_MAX_BUF_SIZE] = {0U};
int16_t		lg_sct_cmd_buf_hist_idx = 0;
uint16_t	lg_sct_cmd_buf_idx = 0U;

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
