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
#include "i2c_temp_sensor.h"
#include "eui48.h"
#include "i2c_adc_driver_bit_bash.h"
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
#define SCT_MAX_BUF_SIZE					512
#define SCT_MAX_CMD_LEN						16
#define SCT_CMD_HISTORY_LEN					10
#define SCT_NUM_CMDS						8

#define SCT_GET_ADC_DATA_CMD				"$ADC"
#define SCT_GET_ADC_DATA_CMD_LEN			4
#define SCT_GET_ADC_DATA_RESP				"!ADC"
#define SCT_GET_ADC_DATA_RESP_LEN			4

#define SCT_GET_TEMP_CMD					"$TMP"
#define SCT_GET_TEMP_CMD_LEN				4
#define SCT_GET_TEMP_RESP					"!TMP"
#define SCT_GET_TEMP_RESP_LEN				4

#define SCT_LOOPBACK_TEST_CMD				"$LBT"
#define SCT_LOOPBACK_TEST_CMD_LEN			4
#define SCT_LOOPBACK_TEST_RESP				"!LBT"
#define SCT_LOOPBACK_TEST_RESP_LEN			4

#define SCT_SET_GPO_CMD						"#GPO"
#define SCT_SET_GPO_CMD_LEN					4
#define SCT_SET_GPO_CMD_FORMAT				"#GPO %hd %hd"
#define SCT_SET_GPO_CMD_FORMAT_NO			2
#define SCT_SET_GPO_RESP					">GPO"
#define SCT_SET_GPO_RESP_LEN				4

#define SCT_GET_PPS_DET_CMD					"$PPSD"
#define SCT_GET_PPS_DET_CMD_LEN				5
#define SCT_GET_PPS_DET_RESP				"!PPSD"
#define SCT_GET_PPS_DET_RESP_LEN			5

#define SCT_SET_IF_PATH_CMD					"#IFP"
#define SCT_SET_IF_PATH_CMD_LEN				4
#define SCT_SET_IF_PATH_CMD_FORMAT			"#IFP %hu"
#define SCT_SET_IF_PATH_CMD_FORMAT_NO		1
#define SCT_SET_IF_PATH_RESP				">IFP"
#define SCT_SET_IF_PATH_RESP_LEN			4

#define SCT_GET_REF_DET_CMD					"$RFDT"
#define SCT_GET_REF_DET_CMD_LEN				5
#define SCT_GET_REF_DET_CMD_FORMAT_1		"$RFDT %hu"
#define SCT_GET_REF_DET_CMD_FORMAT_1_NO		1
#define SCT_GET_REF_DET_CMD_FORMAT_2		"$RFDT %hu %hd"
#define SCT_GET_REF_DET_CMD_FORMAT_2_NO		2
#define SCT_GET_REF_DET_RESP				"!RFDT"
#define SCT_GET_REF_DET_RESP_LEN			5

#define SCT_GET_MAC_ADDRESS_CMD				"$MAC"
#define SCT_GET_MAC_ADDRESS_CMD_LEN			4
#define SCT_GET_MAC_ADDRESS_RESP			"!MAC"
#define SCT_GET_MAC_ADDRESS_RESP_LEN		4

#define SCT_UNKONWN_CMD_RESP				"?"
#define SCT_UNKONWN_CMD_RESP_LEN			1

/* I2C definitions */
#define SCT_AD7415_TEMP_I2C_ADDR			(0x49U << 1)
#define SCT_EUI48_I2C_ADDR					(0x51U << 1)
#define SCT_LTC2991_I2C_ADDR				(0x7CU << 1)

/* DMA controller macros */
#define SCT_DMA_LIFCR_TC_FLAG(dma_stream) (1UL << ((8 * dma_stream) + 5))
#define SCT_DMA_LIFCR_HT_FLAG(dma_stream) (1UL << ((8 * dma_stream) + 4))
#define SCT_DMA_LIFCR_TE_FLAG(dma_stream) (1UL << ((8 * dma_stream) + 3))
#define SCT_DMA_HIFCR_TC_FLAG(dma_stream) (1UL << ((8 * (dma_stream - 4)) + 5))
#define SCT_DMA_HIFCR_HT_FLAG(dma_stream) (1UL << ((8 * (dma_stream - 4)) + 4))
#define SCT_DMA_HIFCR_TE_FLAG(dma_stream) (1UL << ((8 * (dma_stream - 4)) + 3))

/* ADC definitions */
#define SCT_ADC_ADC_STEPS					4096
#define SCT_VDD_CALIB_MV 					((int32_t) (VREFINT_CAL_VREF))
#define SCT_ANALOGUE_READINGS_NUM			13
#define SCT_ANALOGUE_READING_NAME_MAX_LEN	32

/* Temperature sensor and voltage reference calibration value addresses */
#define SCT_TEMP110_CAL_ADDR	TEMPSENSOR_CAL2_ADDR
#define SCT_TEMP30_CAL_ADDR 	TEMPSENSOR_CAL1_ADDR
#define SCT_TEMP110_TEMP		TEMPSENSOR_CAL2_TEMP
#define SCT_TEMP30_TEMP			TEMPSENSOR_CAL1_TEMP
#define SCT_VREFINT_CAL_ADDR 	VREFINT_CAL_ADDR

/* 1PPS accuracy limits */
#define SCT_1PPS_DELTA_MIN				999U
#define SCT_1PPS_DELTA_MAX				1001U

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

typedef enum sct_AdcChannelId
{
	sct_adc_bit_p12v = 0,
	sct_adc_bit_p3v3,
	sct_adc_bit_n3v3,
	sct_adc_bit_p5v0,
	sct_adc_bit_p3v3_if,
	sct_adc_bit_p3v3_tx,
	sct_adc_bit_p5v0_tx,
	sct_adc_temperature,
	sct_adc_vref_int,		/* This should always be the last entry in lg_iot_adc_channels */
	sct_adc_ch_qty
} iot_AdcChannelId_t;

typedef struct sct_AdcChannel
{
	iot_AdcChannelId_t	adc_ch;
	int32_t				multiplier;
	int32_t				divider;
	int32_t				offset;
	int32_t				raw_value;
	int16_t				scaled_value;
	char				name[SCT_ANALOGUE_READING_NAME_MAX_LEN];
} iot_AdcChannel_t;

/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
static void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf);
static void sct_FlushRespBuf(uint8_t *resp_buf);
static void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessUnkownCommand(uint8_t *resp_buf);
static void sct_ProcesssGetAdcDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetTempCommand(uint8_t *cmd_buf,uint8_t *resp_buf);
static void sct_ProcessLoopbackTestCommand(uint8_t *cmd_buf,uint8_t *resp_buf);
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetPpsDetectedCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessSetIfPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_ProcessGetRfDetectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf);
static void sct_Delay0us1(uint16_t count);
static void sct_ProcesssGetMacAddressCommand(uint8_t *cmd_buf, uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static sct_Init_t lg_sct_init_data = {0U};
static bool lg_sct_initialised = false;

static its_I2cTempSensor_t		lg_sct_temp_sensor = {0};
static e48_Eui48Drv_t			lg_sct_eui48 = {0};
static iad_I2cAdcDriver_t		lg_sct_i2c_adc = {0};

static iot_AdcChannel_t lg_sct_adc_channels[sct_adc_ch_qty] = {
		{sct_adc_bit_p12v,	 	57, 	SCT_ADC_ADC_STEPS * 10,	0, 0, 0, "BIT +12V Voltage (mV)"},
		{sct_adc_bit_p3v3, 		2,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "BIT +3V3 Voltage (mV)"},
		{sct_adc_bit_n3v3, 		-1,  	SCT_ADC_ADC_STEPS,      -1200, 0, 0, "BIT -3V3 Voltage (mV)"},
		{sct_adc_bit_p5v0, 		2,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "BIT +5V0 Voltage (mV)"},
		{sct_adc_bit_p3v3_if,	2,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "BIT +3V3 IF Voltage (mV)"},
		{sct_adc_bit_p3v3_tx, 	2,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "BIT +3V3 Tx Voltage (mV)"},
		{sct_adc_bit_p5v0_tx, 	2,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "BIT +5V0 Tx Voltage (mV)"},
		{sct_adc_temperature, 	1,		SCT_ADC_ADC_STEPS, 		0, 0, 0, "STM32 Temperature (deg C)"},
		{sct_adc_vref_int, 	    1,  	SCT_ADC_ADC_STEPS, 		0, 0, 0, "STM32 Vref Internal Voltage (mV)"}	/* Vref internal should always be the last channel */
};
static uint16_t lg_sct_adc_buf[sct_adc_ch_qty] = {0};
/* This value will be set to the measured value when the ADC command is processed */
static int32_t lg_sct_adc_vref_ext_mv = 3300;

static volatile uint32_t lg_sct_1pps_delta = 0U;
static volatile uint32_t lg_sct_1pps_previous = 0U;

static volatile bool lg_sct_rf_det_dwell_time_expired = false;

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

	(void) its_Init(&lg_sct_temp_sensor, lg_sct_init_data.i2c_device, SCT_AD7415_TEMP_I2C_ADDR);
	(void) e48_Init(&lg_sct_eui48, lg_sct_init_data.i2c_device, SCT_EUI48_I2C_ADDR);
	(void) iad_InitInstance(&lg_sct_i2c_adc, lg_sct_init_data.lb_i2c_scl_pin_port, lg_sct_init_data.lb_i2c_scl_pin,
			 	 	 	 	 lg_sct_init_data.lb_i2c_sda_pin_port, lg_sct_init_data.lb_i2c_scl_pin, SCT_LTC2991_I2C_ADDR);

	/* Configure the ADC DMA channel, the ADC channels are configured by the STM32CubeMX auto-generated code in main.c */
	uint32_t dma_reg_addr = LL_ADC_DMA_GetRegAddr(lg_sct_init_data.bit_adc_device, LL_ADC_DMA_REG_REGULAR_DATA);
    LL_DMA_SetPeriphAddress(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream, dma_reg_addr);
    LL_DMA_SetMemoryAddress(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream, (uint32_t)&lg_sct_adc_buf[0]);

    /* Enable DMA Transfer Complete interrupt */
    LL_DMA_EnableIT_TC(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream);
    LL_DMA_EnableIT_TE(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream);

    /* Enable the ADCs */
	if (!LL_ADC_IsEnabled(lg_sct_init_data.bit_adc_device))
	{
		LL_ADC_Enable(lg_sct_init_data.bit_adc_device);
	}

	if (!LL_ADC_IsEnabled(lg_sct_init_data.rf_det_adc_device))
	{
		LL_ADC_Enable(lg_sct_init_data.rf_det_adc_device);
	}

	/* Need to leave the RF Detector Enabled all the time to avoid issues with first readings after power up! */
	HAL_GPIO_WritePin(lg_sct_init_data.rx_path_det_en_port, lg_sct_init_data.rx_path_det_en_pin, GPIO_PIN_SET);

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
	uint8_t data = 0U;

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
		if (osMessageQueueGet(lg_sct_init_data.rx_data_queue, &data, 0U, osWaitForever) == osOK)
		{
			sct_ProcessReceivedByte(data, resp_buf);
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
		(void) osMessageQueuePut(lg_sct_init_data.tx_data_queue, &resp_buf[i], 0U, 0U);
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
			{SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN, sct_ProcesssGetAdcDataCommand},
			{SCT_GET_TEMP_CMD, SCT_GET_TEMP_CMD_LEN, sct_ProcessGetTempCommand},
			{SCT_LOOPBACK_TEST_CMD, SCT_LOOPBACK_TEST_CMD_LEN, sct_ProcessLoopbackTestCommand},
			{SCT_SET_GPO_CMD, SCT_SET_GPO_CMD_LEN, sct_ProcessSetGpoCommand},
			{SCT_GET_PPS_DET_CMD, SCT_GET_PPS_DET_CMD_LEN, sct_ProcessGetPpsDetectedCommand},
			{SCT_SET_IF_PATH_CMD, SCT_SET_IF_PATH_CMD_LEN, sct_ProcessSetIfPathCommand},
			{SCT_GET_REF_DET_CMD, SCT_GET_REF_DET_CMD_LEN, sct_ProcessGetRfDetectorCommand},
			{SCT_GET_MAC_ADDRESS_CMD, SCT_GET_MAC_ADDRESS_CMD_LEN, sct_ProcesssGetMacAddressCommand}
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
* Read and return the ADC data
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcesssGetAdcDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	osStatus_t status;

	/* Reset the DMA controller for the next ADC conversion sequence, clear irq flags and reset transfer count */
	LL_DMA_DisableStream(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream);
	if (lg_sct_init_data.bit_adc_dma_stream < LL_DMA_STREAM_4)
	{
		WRITE_REG(lg_sct_init_data.bit_adc_dma_device->LIFCR, SCT_DMA_LIFCR_TC_FLAG(lg_sct_init_data.bit_adc_dma_stream) |
															  SCT_DMA_LIFCR_HT_FLAG(lg_sct_init_data.bit_adc_dma_stream) |
														      SCT_DMA_LIFCR_TE_FLAG(lg_sct_init_data.bit_adc_dma_stream));
	}
	else
	{
		WRITE_REG(lg_sct_init_data.bit_adc_dma_device->HIFCR, SCT_DMA_HIFCR_TC_FLAG(lg_sct_init_data.bit_adc_dma_stream) |
															  SCT_DMA_HIFCR_HT_FLAG(lg_sct_init_data.bit_adc_dma_stream) |
															  SCT_DMA_HIFCR_TE_FLAG(lg_sct_init_data.bit_adc_dma_stream));
	}
	LL_DMA_SetDataLength(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream, sct_adc_ch_qty);
	LL_DMA_EnableStream(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream);

	/* Start the ADC conversion sequence */
	(void) osSemaphoreAcquire(lg_sct_init_data.bit_adc_semaphore, 0U);
	/* Need to toggle the DMA bit in the CR2 to start a new transfer */
	LL_ADC_REG_SetDMATransfer(lg_sct_init_data.bit_adc_device, LL_ADC_REG_DMA_TRANSFER_NONE);
	LL_ADC_REG_SetDMATransfer(lg_sct_init_data.bit_adc_device, LL_ADC_REG_DMA_TRANSFER_LIMITED);

	LL_ADC_REG_StartConversionSWStart(lg_sct_init_data.bit_adc_device);

	/* Wait until the ADC conversion sequence is complete, should complete in ~50 us */
	status = osSemaphoreAcquire(lg_sct_init_data.bit_adc_semaphore, 10U);

	/* If an overrun error has occurred clear it */
	if (LL_ADC_IsActiveFlag_OVR(lg_sct_init_data.bit_adc_device))
	{
		LL_ADC_ClearFlag_OVR(lg_sct_init_data.bit_adc_device);
	}

	if ((status == osOK) && (LL_DMA_GetDataLength(lg_sct_init_data.bit_adc_dma_device, lg_sct_init_data.bit_adc_dma_stream) == 0U))
	{
		sprintf((char *)resp_buf, "ADC Data:%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		/* Fetch data from the ADC buffer */
		for (int16_t i = 0; i < sct_adc_ch_qty; ++i)
		{
			lg_sct_adc_channels[i].raw_value = (int32_t)lg_sct_adc_buf[i];
		}

		/* Use the Vrefint reading and calibration value to calculate the Vrefext in mV */
		lg_sct_adc_channels[sct_adc_vref_int].scaled_value = (int16_t)((SCT_VDD_CALIB_MV * (int32_t)*SCT_VREFINT_CAL_ADDR) / lg_sct_adc_channels[sct_adc_vref_int].raw_value);

		/* Scale the remaining ADC channels */
		for (int16_t i = 0; i < sct_adc_vref_int; ++i)
		{
			if (i == sct_adc_temperature)
			{
				/* Calculate  the temperature */
				int32_t temperature = ((lg_sct_adc_channels[i].raw_value * lg_sct_adc_channels[sct_adc_vref_int].scaled_value / SCT_VDD_CALIB_MV) - (int32_t) *SCT_TEMP30_CAL_ADDR);
				temperature = temperature * (int32_t)(SCT_TEMP110_TEMP - SCT_TEMP30_TEMP);
				temperature = temperature / (int32_t)(*SCT_TEMP110_CAL_ADDR - *SCT_TEMP30_CAL_ADDR);
				lg_sct_adc_channels[i].scaled_value = temperature + SCT_TEMP30_TEMP;
			}
			else
			{
				int32_t raw_value = lg_sct_adc_channels[i].raw_value;
				int32_t multiplier = lg_sct_adc_channels[i].multiplier;
				int32_t vref_ext_mv = (int32_t)lg_sct_adc_channels[sct_adc_vref_int].scaled_value;
				int32_t divider = lg_sct_adc_channels[i].divider;
				int32_t offset = lg_sct_adc_channels[i].offset;
				lg_sct_adc_channels[i].scaled_value = ((raw_value * multiplier * vref_ext_mv) / divider) + offset;

				/* Store the Vref External value for use with the RF Detector */
				lg_sct_adc_vref_ext_mv = vref_ext_mv;
			}

			sprintf((char *)resp_buf, "%-6hd : %s%s", lg_sct_adc_channels[i].scaled_value, lg_sct_adc_channels[i].name, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}

		sprintf((char *)resp_buf, "%-6hd : %s%s", lg_sct_adc_channels[sct_adc_vref_int].scaled_value, lg_sct_adc_channels[sct_adc_vref_int].name, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** ADC conversion sequence failed! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_ADC_DATA_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Handler for the ADC DMA interrupts.
*
* @param	adc_device ADC device associated with this DMA interrupt.
*
******************************************************************************/
void sct_AdcDMAIrqHandler(ADC_TypeDef *adc_device)
{
	if (adc_device == lg_sct_init_data.bit_adc_device)
	{
		uint32_t adc_dma_stream = lg_sct_init_data.bit_adc_dma_stream;
		DMA_TypeDef	*adc_dma_device = lg_sct_init_data.bit_adc_dma_device;

		if (adc_dma_stream < LL_DMA_STREAM_4)
		{
		    if (READ_BIT(adc_dma_device->LISR, SCT_DMA_LIFCR_TE_FLAG(adc_dma_stream)) == SCT_DMA_LIFCR_TE_FLAG(adc_dma_stream))
		    {
		        /* Clear transfer error flag */
		        WRITE_REG(adc_dma_device->LIFCR, SCT_DMA_LIFCR_TE_FLAG(adc_dma_stream));
		        /* Clear the data in the ADC buffer */
		        memset(lg_sct_adc_buf, 0, sizeof(lg_sct_adc_buf));
		        /* Conversion complete, signal the task */
		        (void) osSemaphoreRelease(lg_sct_init_data.bit_adc_semaphore);
		    }
		    else if (LL_DMA_IsEnabledIT_TC(adc_dma_device, adc_dma_stream) &&
		    			(READ_BIT(adc_dma_device->LISR, SCT_DMA_LIFCR_TC_FLAG(adc_dma_stream)) == SCT_DMA_LIFCR_TC_FLAG(adc_dma_stream)))
		    {
		       /* Clear transfer complete flag */
		       WRITE_REG(adc_dma_device->LIFCR, SCT_DMA_LIFCR_TC_FLAG(adc_dma_stream));
		       /* Conversion complete, signal the task */
		       (void) osSemaphoreRelease(lg_sct_init_data.bit_adc_semaphore);
		    }
		}
		else
		{
		    if (READ_BIT(adc_dma_device->HISR, SCT_DMA_HIFCR_TE_FLAG(adc_dma_stream)) == SCT_DMA_HIFCR_TE_FLAG(adc_dma_stream))
		    {
		        /* Clear transfer error flag */
		        WRITE_REG(adc_dma_device->HIFCR, SCT_DMA_HIFCR_TE_FLAG(adc_dma_stream));
		        /* Clear the data in the ADC buffer */
		        memset(lg_sct_adc_buf, 0, sizeof(lg_sct_adc_buf));
		        /* Conversion complete, signal the task */
		        (void) osSemaphoreRelease(lg_sct_init_data.bit_adc_semaphore);
		    }
		    else if (LL_DMA_IsEnabledIT_TC(adc_dma_device, adc_dma_stream) &&
		    			(READ_BIT(adc_dma_device->HISR, SCT_DMA_HIFCR_TC_FLAG(adc_dma_stream)) == SCT_DMA_HIFCR_TC_FLAG(adc_dma_stream)))
		    {
		       /* Clear transfer complete flag */
		       WRITE_REG(adc_dma_device->HIFCR, SCT_DMA_HIFCR_TC_FLAG(adc_dma_stream));
		       /* Conversion complete, signal the task */
		       (void) osSemaphoreRelease(lg_sct_init_data.bit_adc_semaphore);
		    }
		}
	}
}


/*****************************************************************************/
/**
* Read and return the AD7415 temperature sensor.
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetTempCommand(uint8_t *cmd_buf,uint8_t *resp_buf)
{
	int16_t temp = 0;

	if (its_ReadTemperature(&lg_sct_temp_sensor, &temp))
	{
		sprintf((char *)resp_buf, "AD7415 Temperature: %hd%s", temp, SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read AD7415! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_TEMP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Perform a loopback test and return the result
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessLoopbackTestCommand(uint8_t *cmd_buf,uint8_t *resp_buf)
{
	sct_LbTestIoPair_t *p_lb_test_io_pair, *p_lb_check_io_pair;
	GPIO_PinState pin_state;
	bool test_pass;
	/* Test GPIO loop back signals... */
	/* Set all the outputs low... */
	for (int16_t i = 0; i < SCT_LB_TEST_PAIR_NUM; ++i)
	{
		p_lb_test_io_pair = &lg_sct_init_data.lb_test_io_pairs[i];
		HAL_GPIO_WritePin(p_lb_test_io_pair->pin_a_port, p_lb_test_io_pair->pin_a_pin, GPIO_PIN_RESET);
	}

	/* Set each output in turn and check that it is set */
	for (int16_t i = 0; i < SCT_LB_TEST_PAIR_NUM; ++i)
	{
		test_pass = true;

		p_lb_test_io_pair = &lg_sct_init_data.lb_test_io_pairs[i];
		HAL_GPIO_WritePin(p_lb_test_io_pair->pin_a_port, p_lb_test_io_pair->pin_a_pin, GPIO_PIN_SET);

		for (int16_t j = 0; j < SCT_LB_TEST_PAIR_NUM; ++j)
		{
			p_lb_check_io_pair = &lg_sct_init_data.lb_test_io_pairs[j];
			pin_state = HAL_GPIO_ReadPin(p_lb_check_io_pair->pin_b_port, p_lb_check_io_pair->pin_b_pin);
			test_pass &= (j == i ? (pin_state == GPIO_PIN_SET) : (pin_state == GPIO_PIN_RESET));
		}

		HAL_GPIO_WritePin(p_lb_test_io_pair->pin_a_port, p_lb_test_io_pair->pin_a_pin, GPIO_PIN_RESET);

		sprintf((char *)resp_buf, "%s - IO_PAIR_%hd%s", (test_pass ? "PASS" : "FAIL"), (i + 1), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	/* Read the loop back board ADC */
	iad_I2cAdcData_t adc_data = {0};
	if (iad_ReadAdcData(&lg_sct_i2c_adc, &adc_data))
	{

	}

	sprintf((char *)resp_buf, "%s - Overall Test Result%s", test_pass ? "PASS" : "FAIL", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_LOOPBACK_TEST_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the specified GPO signal to a specified state, pin is set "low" if
* set state parameter is '0', else "high"
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @todo read the LTC2991 on the loobpack board using bit-bash I2C interface
*
******************************************************************************/
static void sct_ProcessSetGpoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t gpo_pin = 0U;
	int16_t set_state = 0;

	if (sscanf((char *)cmd_buf, SCT_SET_GPO_CMD_FORMAT, &gpo_pin, &set_state) == SCT_SET_GPO_CMD_FORMAT_NO)
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


/*****************************************************************************/
/**
* Check if the 1PPS output from the SoM is present
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
*
******************************************************************************/
static void sct_ProcessGetPpsDetectedCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(lg_sct_init_data.pps_gpio_irq);
	uint32_t pps_delta = lg_sct_1pps_delta;
	uint32_t pps_previous = lg_sct_1pps_previous;
	HAL_NVIC_EnableIRQ(lg_sct_init_data.pps_gpio_irq);
	uint32_t now = osKernelGetTickCount();

	if ((now - pps_previous) > SCT_1PPS_DELTA_MAX)
	{
		sprintf((char *)resp_buf, "1PPS NOT detected%s", SCT_CRLF);
	}
	else
	{
		sprintf((char *)resp_buf, "1PPS detected, delta: %lu ms%s", pps_delta, SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_PPS_DET_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Handle HAL EXTI GPIO Callback as these are used to monitor presence of 1PPS
* input signal
*
* @param    GPIO_Pin the ID of the GPIO pin that caused the EXTI interrupt.
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	volatile uint32_t now = osKernelGetTickCount();

	if (lg_sct_initialised)
	{
		if (GPIO_Pin == lg_sct_init_data.pps_gpio_pin)
		{
			lg_sct_1pps_delta = now - lg_sct_1pps_previous;
			lg_sct_1pps_previous = now;
		}
	}
}


/*****************************************************************************/
/**
* Set IF path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessSetIfPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t path = 0U;

	typedef struct if_path
	{
		GPIO_PinState rx_path_sw_3_a;
		GPIO_PinState rx_path_sw_3_b;
		GPIO_PinState rx_path_sw_4_a;
		GPIO_PinState rx_path_sw_4_b;
		GPIO_PinState rx_path_sw_5_vc;
		GPIO_PinState rx_path_sw_6_vc;
		char name[32];
	} if_path_t;

	static const if_path_t if_path_map[4] = {
			{GPIO_PIN_RESET,	GPIO_PIN_RESET,	GPIO_PIN_SET, 	GPIO_PIN_SET, 	GPIO_PIN_SET, 	GPIO_PIN_RESET, "IF0: 916-917 MHz"},
			{GPIO_PIN_SET, 		GPIO_PIN_RESET, GPIO_PIN_RESET,	GPIO_PIN_SET, 	GPIO_PIN_RESET, GPIO_PIN_SET, 	"IF1: 910-920 MHz"},
			{GPIO_PIN_SET,		GPIO_PIN_SET, 	GPIO_PIN_SET, 	GPIO_PIN_RESET,	GPIO_PIN_RESET,	GPIO_PIN_RESET, "IF2: 2305-2315 MHz"},
			{GPIO_PIN_RESET, 	GPIO_PIN_SET, 	GPIO_PIN_RESET, GPIO_PIN_RESET, GPIO_PIN_RESET, GPIO_PIN_RESET, "IF3: 2350-2360 MHz"},
	};

	if (sscanf((char *)cmd_buf, SCT_SET_IF_PATH_CMD_FORMAT, &path) == SCT_SET_IF_PATH_CMD_FORMAT_NO)
	{
		/* The called function range checks the parameter and returns an error string if it is invalid */
		if ((path >= 0U) && (path <= 3U))
		{
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_3_a_port, lg_sct_init_data.rx_path_sw_3_a_pin, if_path_map[path].rx_path_sw_3_a);
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_3_b_port, lg_sct_init_data.rx_path_sw_3_b_pin, if_path_map[path].rx_path_sw_3_b);
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_4_a_port, lg_sct_init_data.rx_path_sw_4_a_pin, if_path_map[path].rx_path_sw_4_a);
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_4_b_port, lg_sct_init_data.rx_path_sw_4_b_pin, if_path_map[path].rx_path_sw_4_b);
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_5_vc_port, lg_sct_init_data.rx_path_sw_5_vc_pin, if_path_map[path].rx_path_sw_5_vc);
			HAL_GPIO_WritePin(lg_sct_init_data.rx_path_sw_6_vc_port, lg_sct_init_data.rx_path_sw_6_vc_pin, if_path_map[path].rx_path_sw_6_vc);

			sprintf((char *)resp_buf, "Set IF path to %hu - %s%s", path, if_path_map[path].name, SCT_CRLF);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Invalid IF path: %hu ***%s", path, SCT_CRLF);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_SET_IF_PATH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sample the RF detector for the specified time and return the reading.
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcessGetRfDetectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	bool valid_cmd = false;
	uint16_t dwell_0_us_1 = 0U;
	int16_t sample_time = 0;

	if (sscanf((char *)cmd_buf, SCT_GET_REF_DET_CMD_FORMAT_2, &dwell_0_us_1, &sample_time) == SCT_GET_REF_DET_CMD_FORMAT_2_NO)
	{
		/* Modify the ADC sample time, valid range. */
		LL_ADC_SetChannelSamplingTime(lg_sct_init_data.rf_det_adc_device, lg_sct_init_data.rf_det_adc_channel, sample_time);
		int16_t no_cycles;
		switch (sample_time)
		{
		case 0:
			no_cycles = 3;
			break;
		case 1:
			no_cycles = 15;
			break;
		case 2:
			no_cycles = 28;
			break;
		case 3:
			no_cycles = 56;
			break;
		case 4:
			no_cycles = 84;
			break;
		case 5:
			no_cycles = 112;
			break;
		case 6:
			no_cycles = 144;
			break;
		case 7:
			no_cycles = 480;
			break;
		default:
			no_cycles = 0;
			break;
		}
		sprintf((char *)resp_buf, "%hd Cycles - ADC Sample Time%s", no_cycles, SCT_CRLF);
		valid_cmd = true;
	}
	else if (sscanf((char *)cmd_buf, SCT_GET_REF_DET_CMD_FORMAT_1, &dwell_0_us_1) == SCT_GET_REF_DET_CMD_FORMAT_1_NO)
	{
		LL_ADC_SetChannelSamplingTime(lg_sct_init_data.rf_det_adc_device, lg_sct_init_data.rf_det_adc_channel, LL_ADC_SAMPLINGTIME_112CYCLES);
		sprintf((char *)resp_buf, "112 Cycles - ADC Sample Time%s", SCT_CRLF);
		valid_cmd = true;
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		valid_cmd = false;
	}
	sct_FlushRespBuf(resp_buf);

	if (valid_cmd)
	{
		/* Discharge the RF power detector, discharge time is 33 us, using 1-cycle of the 100 us RF detector timer for discharge */
		HAL_GPIO_WritePin(lg_sct_init_data.rx_path_pk_det_dischrg_port, lg_sct_init_data.rx_path_pk_det_dischrg_pin, GPIO_PIN_SET);
		sct_Delay0us1(2U);
		HAL_GPIO_WritePin(lg_sct_init_data.rx_path_pk_det_dischrg_port, lg_sct_init_data.rx_path_pk_det_dischrg_pin, GPIO_PIN_RESET);

		/* Wait for the dwell time */
		sct_Delay0us1(dwell_0_us_1 - 1U);

		/* Read the RF detector voltage */
		LL_ADC_REG_StartConversionSWStart(lg_sct_init_data.rf_det_adc_device);
		while (!LL_ADC_IsActiveFlag_EOCS(lg_sct_init_data.rf_det_adc_device));
		uint16_t adc_data = LL_ADC_REG_ReadConversionData12(lg_sct_init_data.rf_det_adc_device);

		sprintf((char *)resp_buf, "%hu - Raw ADC value%s", adc_data, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		int32_t raw_value = adc_data;
		int32_t multiplier = 1;
		int32_t vref_ext_mv = lg_sct_adc_vref_ext_mv;
		int32_t divider = SCT_ADC_ADC_STEPS;
		int32_t offset = 0;
		int32_t voltage_mv = ((raw_value * multiplier * vref_ext_mv) / divider) + offset;

		sprintf((char *)resp_buf, "%ld - Voltage (mV)%s", voltage_mv, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_REF_DET_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

static void sct_Delay0us1(uint16_t count)
{
#if 0
	lg_sct_init_data.rf_det_timer->Instance->CR1 |= (TIM_CR1_URS | TIM_CR1_OPM);
	lg_sct_init_data.rf_det_timer->Init.Period = 1U;
	lg_sct_rf_det_dwell_time_expired = false;
	(void) HAL_TIM_Base_Init(lg_sct_init_data.rf_det_timer);
	(void) HAL_TIM_Base_Start_IT(lg_sct_init_data.rf_det_timer);
	while (!lg_sct_rf_det_dwell_time_expired)
	{
		(void) osThreadYield();
	}
	HAL_TIM_Base_Stop_IT(lg_sct_init_data.rf_det_timer);
#endif
	/* Set the delay, clear the count and generate an update event to load the values */
	lg_sct_init_data.rf_det_timer->Instance->ARR = count;
	lg_sct_init_data.rf_det_timer->Instance->CNT = 0U;
	lg_sct_init_data.rf_det_timer->Instance->CR1 |= TIM_CR1_URS;
	lg_sct_init_data.rf_det_timer->Instance->EGR |= TIM_EGR_UG;
	/* Clear the update event flag */
	lg_sct_init_data.rf_det_timer->Instance->SR = 0U;
	/* Start the timer counter */
	lg_sct_init_data.rf_det_timer->Instance->CR1 |= TIM_CR1_CEN;
	lg_sct_init_data.rf_det_timer->Instance->SR = 0U;
	/* Loop until the update event flag is set */
	while (!(TIM6->SR & TIM_SR_UIF))
	{
		//(void) osThreadYield();
	}
	/* Stop the timer */
	lg_sct_init_data.rf_det_timer->Instance->CR1 &= ~TIM_CR1_CEN;
}


/*****************************************************************************/
/**
* Callback when the RF detector dwell timer expires.
*
* @param    htim handle of the timer that issued the callback.
*
******************************************************************************/
void sct_RfDetTmrCallback(TIM_HandleTypeDef *htim)
{
	if (htim == lg_sct_init_data.rf_det_timer)
	{
		if (__HAL_TIM_GET_FLAG(lg_sct_init_data.rf_det_timer, TIM_FLAG_UPDATE))
		{
			__HAL_TIM_CLEAR_FLAG(lg_sct_init_data.rf_det_timer, TIM_FLAG_UPDATE);
			lg_sct_rf_det_dwell_time_expired = true;
		}
	}
}


/*****************************************************************************/
/**
* Read and return the EUI48 MAC address.
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
*
******************************************************************************/
static void sct_ProcesssGetMacAddressCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint8_t mac_address[E48_DATA_LEN_BYTES] = {0U};

	if (e48_GetEui48(&lg_sct_eui48, mac_address))
	{
	    sprintf((char *)resp_buf, "MAC address: %.2x-%.2x-%.2x-%.2x-%.2x-%.2x\r\n",
	            mac_address[0], mac_address[1], mac_address[2], mac_address[3], mac_address[4], mac_address[5]);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read the MAC address! ***%s", SCT_CRLF);

	}
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_GET_MAC_ADDRESS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}
