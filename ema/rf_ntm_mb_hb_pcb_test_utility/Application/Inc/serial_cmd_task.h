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
#include "spi_xcvr_driver.h"

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
	SPI_HandleTypeDef   *spi_device;
	GPIO_TypeDef    	*i2c_reset_gpio_port;
	uint16_t			i2c_reset_gpio_pin;
	GPIO_TypeDef		*xcvr_ncs_gpio_port;
	uint16_t			xcvr_ncs_gpio_pin;
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

#define SCT_GET_ADC_DATA_CMD			"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN		4
#define SCT_GET_ADC_DATA_RESP			"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN		4

#define SCT_GET_BOARD_ID_CMD			"$BID"
#define SCT_GET_BOARD_ID_CMD_LEN		4
#define SCT_GET_BOARD_ID_RESP			"!BID"
#define SCT_GET_BOARD_ID_RESP_LEN		4

#define SCT_SET_DDS_ATT_CMD				"#DATT"
#define SCT_SET_DDS_ATT_CMD_LEN			5
#define SCT_SET_DDS_ATT_CMD_FORMAT		"#DATT %hu"
#define SCT_SET_DDS_ATT_CMD_FORMAT_NO 	1
#define SCT_SET_DDS_ATT_RESP			">DATT"
#define SCT_SET_DDS_ATT_RESP_LEN		5

#define SCT_SET_TX_ATT_FINE_CMD			"#TFAT"
#define SCT_SET_TX_ATT_FINE_CMD_LEN		5
#define SCT_SET_TX_ATT_FINE_CMD_FORMAT	"#TFAT %hu"
#define SCT_SET_TX_ATT_FINE_CMD_FORMAT_NO 1
#define SCT_SET_TX_ATT_FINE_RESP		">TFAT"
#define SCT_SET_TX_ATT_FINE_RESP_LEN	5

#define SCT_SET_TX_ATT_COARSE_CMD		"#TCAT"
#define SCT_SET_TX_ATT_COARSE_CMD_LEN	5
#define SCT_SET_TX_ATT_COARSE_CMD_FORMAT "#TCAT %hu"
#define SCT_SET_TX_ATT_COARSE_CMD_FORMAT_NO 1
#define SCT_SET_TX_ATT_COARSE_RESP		">TCAT"
#define SCT_SET_TX_ATT_COARSE_RESP_LEN	5

#define SCT_SET_RX_LNA_BYPASS_CMD		"#RLBY"
#define SCT_SET_RX_LNA_BYPASS_CMD_LEN	5
#define SCT_SET_RX_LNA_BYPASS_CMD_FORMAT "#RLBY %hu"
#define SCT_SET_RX_LNA_BYPASS_CMD_FORMAT_NO 1
#define SCT_SET_RX_LNA_BYPASS_RESP		">RLBY"
#define SCT_SET_RX_LNA_BYPASS_RESP_LEN	5

#define SCT_SET_RX_PRESEL_CMD			"#RXPS"
#define SCT_SET_RX_PRESEL_CMD_LEN		5
#define SCT_SET_RX_PRESEL_CMD_FORMAT	"#RXPS %hu"
#define SCT_SET_RX_PRESEL_CMD_FORMAT_NO	1
#define SCT_SET_RX_PRESEL_RESP			">RXPS"
#define SCT_SET_RX_PRESEL_RESP_LEN		5

#define SCT_SET_TX_PATH_CMD				"#TXP"
#define SCT_SET_TX_PATH_CMD_LEN			4
#define SCT_SET_TX_PATH_CMD_FORMAT		"#TXP %hu"
#define SCT_SET_TX_PATH_CMD_FORMAT_NO	1
#define SCT_SET_TX_PATH_RESP			">TXP"
#define SCT_SET_TX_PATH_RESP_LEN		4

#define SCT_SET_RX_EN_CMD				"#RXEN"
#define SCT_SET_RX_EN_CMD_LEN			5
#define SCT_SET_RX_EN_CMD_FORMAT		"#RXEN %hu"
#define SCT_SET_RX_EN_CMD_FORMAT_NO 	1
#define SCT_SET_RX_EN_RESP				">RXEN"
#define SCT_SET_RX_EN_RESP_LEN			5

#define SCT_SET_TX_EN_CMD				"#TXEN"
#define SCT_SET_TX_EN_CMD_LEN			5
#define SCT_SET_TX_EN_CMD_FORMAT		"#TXEN %hu"
#define SCT_SET_TX_EN_CMD_FORMAT_NO 	1
#define SCT_SET_TX_EN_RESP				">TXEN"
#define SCT_SET_TX_EN_RESP_LEN			5

#define SCT_SET_XCVR_RESET_CMD			"#XRST"
#define SCT_SET_XCVR_RESET_CMD_LEN		5
#define SCT_SET_XCVR_RESET_CMD_FORMAT	"#XRST %hu"
#define SCT_SET_XCVR_RESET_CMD_FORMAT_NO 1
#define SCT_SET_XCVR_RESET_RESP			">XRST"
#define SCT_SET_XCVR_RESET_RESP_LEN		5

#define SCT_GET_XCVR_VID_CMD			"$XVID"
#define SCT_GET_XCVR_VID_CMD_LEN		5
#define SCT_GET_XCVR_VID_RESP			"!XVID"
#define SCT_GET_XCVR_VID_RESP_LEN		5

#define SCT_GET_GP_INTERRUPT_CMD		"$GINT"
#define SCT_GET_GP_INTERRUPT_CMD_LEN	5
#define SCT_GET_GP_INTERRUPT_RESP		"!GINT"
#define SCT_GET_GP_INTERRUPT_RESP_LEN	5

#define SCT_UNKONWN_CMD_RESP			"?"
#define SCT_UNKONWN_CMD_RESP_LEN		1

#define SCT_PCA9500_EEPROM_I2C_ADDR 	0x50U << 1
#define SCT_PCA9500_GPIO_I2C_ADDR		0x20U << 1
#define SCT_LTC2991_ADC_I2C_ADDR		0x4CU << 1

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
void sct_ProcesssGetAdcDataCommand(uint8_t *resp_buf);
void sct_ProcessGetBoardIdCommand(uint8_t *resp_buf);
void sct_ProcessSetDdsAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetTxFineAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetTxCoarseAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRxLnaBypassCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRxPreselectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetTxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetRxEnableCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetTxEnableCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessSetXcvrResetCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
void sct_ProcessGetXcvrVendorIdCommand(uint8_t *resp_buf);
void sct_ProcessGetGpInterruptCommand(uint8_t *resp_buf);
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
sxc_SpiXcvrDriver_t	lg_sct_spi_xcvr = {0};

static uint8_t 	lg_sct_cmd_buf_curr[SCT_MAX_BUF_SIZE] = {0U};
static uint8_t 	lg_sct_cmd_buf_hist[SCT_CMD_HISTORY_LEN][SCT_MAX_BUF_SIZE] = {0U};
static int16_t	lg_sct_cmd_buf_hist_idx = 0;
static int16_t	lg_sct_cmd_buf_hist_scroll_idx = 0;
static int16_t	lg_sct_cmd_buf_curr_idx = 0;

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
