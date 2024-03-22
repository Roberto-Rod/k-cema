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
#define __SERIAL_CMD_TASK_C

#include "serial_cmd_task.h"
#include "version.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

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
	lg_sct_init_data.tx_data_queue 			= init_data.tx_data_queue;
	lg_sct_init_data.rx_data_queue 			= init_data.rx_data_queue;
	lg_sct_init_data.i2c_device 			= init_data.i2c_device;
	lg_sct_init_data.i2c_reset_gpio_port 	= init_data.i2c_reset_gpio_port;
	lg_sct_init_data.i2c_reset_gpio_pin 	= init_data.i2c_reset_gpio_pin;
	lg_sct_init_data.spi_device				= init_data.spi_device;
	lg_sct_init_data.global_ncs_gpio_port	= init_data.global_ncs_gpio_port;
	lg_sct_init_data.global_ncs_gpio_pin	= init_data.global_ncs_gpio_pin;
	lg_sct_init_data.synth1_ncs_gpio_port	= init_data.synth1_ncs_gpio_port;
	lg_sct_init_data.synth1_ncs_gpio_pin	= init_data.synth1_ncs_gpio_pin;
	lg_sct_init_data.synth2_ncs_gpio_port	= init_data.synth2_ncs_gpio_port;
	lg_sct_init_data.synth2_ncs_gpio_pin	= init_data.synth2_ncs_gpio_pin;
	lg_sct_init_data.mxr_lev_adc_ncs_gpio_port	= init_data.mxr_lev_adc_ncs_gpio_port;
	lg_sct_init_data.mxr_lev_adc_ncs_gpio_pin	= init_data.mxr_lev_adc_ncs_gpio_pin;

	tbg_Init(	&lg_sct_tb_gpio,
				init_data.i2c_device,
				init_data.i2c_reset_gpio_port,
				init_data.i2c_reset_gpio_pin);

	hci_Init(	&lg_sct_hci, init_data.i2c_device,
				SCT_PCA9500_GPIO_I2C_ADDR,
				SCT_PCA9500_EEPROM_I2C_ADDR);

	(void) iad_InitInstance(&lg_sct_i2c_adc, lg_sct_init_data.i2c_device, SCT_LTC2991_ADC_I2C_ADDR);

	(void) idd_Init(&lg_sct_dac, lg_sct_init_data.i2c_device, SCT_MCP4728_DAC_I2C_ADDR);

	/* Enable the SPI nCS buffers */
	HAL_GPIO_WritePin(	lg_sct_init_data.global_ncs_gpio_port,
						lg_sct_init_data.global_ncs_gpio_pin,
						GPIO_PIN_RESET);

	(void) ssd_InitInstance(&lg_sct_synth[0],
							lg_sct_init_data.spi_device,
							lg_sct_init_data.synth1_ncs_gpio_port,
							lg_sct_init_data.synth1_ncs_gpio_pin);

	(void) ssd_InitInstance(&lg_sct_synth[1],
							lg_sct_init_data.spi_device,
							lg_sct_init_data.synth2_ncs_gpio_port,
							lg_sct_init_data.synth2_ncs_gpio_pin);

	(void) sad_InitInstance(&lg_sct_spi_dac,
							lg_sct_init_data.spi_device,
							lg_sct_init_data.mxr_lev_adc_ncs_gpio_port,
							lg_sct_init_data.mxr_lev_adc_ncs_gpio_pin);

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
* Flush contents of response buffer to tx queue.
*
* @param    data received byte to process
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReceivedByte(uint8_t data, uint8_t *resp_buf)
{
	/* To help with human-entered command strings, backspace key erases last character */
	if ((data == SCT_BACKSPACE) && (lg_sct_cmd_buf_idx > 0U))
	{
		--lg_sct_cmd_buf_idx;
		sprintf((char *)resp_buf, "\b \b");
		sct_FlushRespBuf(resp_buf);
	}
	else if ((data == SCT_BACKSPACE) && (lg_sct_cmd_buf_idx == 0U))
	{
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
* @param    None
* @return   None
* @note     None
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
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
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
	else if (!strncmp((char *)cmd_buf, SCT_GET_BOARD_ID_CMD, SCT_GET_BOARD_ID_CMD_LEN))
	{
		sct_ProcessGetBoardIdCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RX_PWR_EN_CMD, SCT_SET_RX_PWR_EN_CMD_LEN))
	{
		sct_ProcessSetRxPwrEnCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(cmd_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_DACE_CMD, SCT_SET_DACE_CMD_LEN))
	{
		sct_ProcesssSetDacEepromDataCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_DAC_CMD, SCT_SET_DAC_CMD_LEN))
	{
		sct_ProcesssSetDacDataCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_DAC_CMD, SCT_READ_DAC_CMD_LEN))
	{
		sct_ProcesssReadDacDataCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_LOCK_DETS_CMD, SCT_GET_LOCK_DETS_CMD_LEN))
	{
		sct_ProcessGetLockDetectsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SYNTH_SEL_CMD, SCT_SYNTH_SEL_CMD_LEN))
	{
		sct_ProcessSelectSynthCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_SYNTH_FREQ_CMD, SCT_SET_SYNTH_FREQ_CMD_LEN))
	{
		sct_ProcessSetRfCentreFreqCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_PRESEL_CMD, SCT_SET_PRESEL_CMD_LEN))
	{
		sct_ProcessSetPreselectorCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RF_ATTEN_CMD, SCT_SET_RF_ATTEN_CMD_LEN))
	{
		sct_ProcessSetRfAttenCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_IF_ATTEN_CMD, SCT_SET_IF_ATTEN_CMD_LEN))
	{
		sct_ProcessSetIfAttenCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_LNA_BYPASS_CMD, SCT_SET_LNA_BYPASS_CMD_LEN))
	{
		sct_ProcessSetLnaBypassCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_MXR_LEVEL_CMD, SCT_GET_MXR_LEVEL_CMD_LEN))
	{
		sct_ProcessGetMixerLevelCommand(resp_buf);
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
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessHwConfigInfoCommand(uint8_t *resp_buf)
{
	hci_HwConfigInfoData_t hw_config_info;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

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
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessResetHwConfigInfoCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

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
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetHwConfigInfoCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int32_t param_to_set;
	bool param_set = false;
	char param[HCI_STR_PARAM_LEN] = {0};

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

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
* Read Board ID GPIs and return value
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetBoardIdCommand(uint8_t *resp_buf)
{
	uint16_t board_id = 0xFFFFU;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (tbg_ReadBoardId(&lg_sct_tb_gpio, &board_id))
	{
		sprintf((char *)resp_buf, "Board ID: %hu%s", board_id, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Board ID! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_BOARD_ID_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Sets the Rx power enable signal state, disable if serial command parameter is
* zero, else enable
*
* @param    None
* @return   None
* @note     Should probably check init device return values!
*
******************************************************************************/
void sct_ProcessSetRxPwrEnCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t set_state = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_RX_PWR_EN_CMD_FORMAT, &set_state) ==
			SCT_SET_RX_PWR_EN_CMD_FORMAT_NO)
	{
		if (tbg_RxPowerEnable(&lg_sct_tb_gpio, (set_state ? true : false)))
		{
			if (set_state)
			{
				/* Initialise peripherals on the board */
				osDelay(10U);
				(void) iad_InitDevice(&lg_sct_i2c_adc);
				(void) ssd_InitDevice(&lg_sct_synth[0]);
				(void) ssd_InitDevice(&lg_sct_synth[1]);
				(void) sad_InitDevice(&lg_sct_spi_dac);
			}

			sprintf((char *)resp_buf, "Set Rx power enable to: %s%s",
					(set_state ? "ENABLED" : "DISABLED") , SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set Rx power enable to: %s ***%s",
					(set_state ? "ENABLED" : "DISABLED"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_PWR_EN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
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
	iad_I2cAdcData_t adc_data;
	int16_t i = 0;
	const char **adc_ch_names = iad_GetChannelNames();

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

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
* Set the DAC value, DAC range is limited to 300 -> 3,000 mV
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcesssSetDacDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	idd_I2cDacFwrData_t dac_data;
	uint16_t dac_val = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_DAC_CMD_FORMAT, &dac_val) ==
			SCT_SET_DAC_CMD_FORMAT_NO)
	{
		/* Build DAC data to write, DAC channel A is the only one used on the
		 * KT-000-0136-00 board so power off channels B to D, always power channel A */
		dac_data.ch_mv[1] = dac_data.ch_mv[2] = dac_data.ch_mv[3] = 0U;
		dac_data.pwr_dwn[1] = dac_data.pwr_dwn[2] = dac_data.pwr_dwn[3] = true;
		dac_data.pwr_dwn[0] = false;

		/* Cap the DAC value */
		if (dac_val > SCT_SET_DAC_VAL_MAX)
		{
			dac_data.ch_mv[0] = SCT_SET_DAC_VAL_MAX;
		}
		else if (dac_val < SCT_SET_DAC_VAL_MIN)
		{
			dac_data.ch_mv[0] = SCT_SET_DAC_VAL_MIN;
		}
		else
		{
			dac_data.ch_mv[0] = dac_val;
		}

		if (idd_FastWriteDacs(&lg_sct_dac, dac_data))
		{
			sprintf((char *)resp_buf, "Set DAC to: %hu%s",
					dac_data.ch_mv[0], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set DAC ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_DAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the DAC and program the EEPROM, DAC range is limited to 300 -> 3,000 mV
* Specified DAC channel:
* 1 = Ch A
* ...
* 4 = CH D
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcesssSetDacEepromDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t	ch_mv = 0U;
	uint16_t	int_vref = 0U;
	uint16_t	gain_2 = 0U;
	uint16_t	pwr_dwn_mode = 0U;
	uint16_t 	chan = 1U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_DACE_CMD_FORMAT,
			&chan, &ch_mv, &int_vref, &gain_2, &pwr_dwn_mode)
			== SCT_SET_DACE_CMD_FORMAT_NO)
	{
		/* Cap the DAC value */
		if (ch_mv > SCT_SET_DAC_VAL_MAX)
		{
			ch_mv = SCT_SET_DAC_VAL_MAX;
		}
		else if (ch_mv < SCT_SET_DAC_VAL_MIN)
		{
			ch_mv = SCT_SET_DAC_VAL_MIN;
		}
		else
		{
		}

		if (idd_WriteDacEeprom(	&lg_sct_dac,
								ch_mv, (bool)int_vref, (bool)gain_2,
								(uint8_t)pwr_dwn_mode, chan - 1U))
		{
			sprintf((char *)resp_buf, "Set DAC and EEPROM channel %hu to:%s",
					chan, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ch_mv:\t\t%hu%s",
					ch_mv, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "int_vref:\t%s%s",
					(int_vref ? "true" : "false"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "gain_2:\t\t%s%s",
					(gain_2 ? "true" : "false"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "pwr_dwn_mode:\t%hu%s",
					pwr_dwn_mode, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set DAC ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_DAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return data for the specified DAC channel:
* 1 = Ch A
* ...
* 4 = CH D
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcesssReadDacDataCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	idd_I2cDacData_t dac_data;
	uint16_t chan = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_READ_DAC_CMD_FORMAT, &chan) ==
			SCT_READ_DAC_CMD_FORMAT_NO)
	{
		if (idd_ReadDac(&lg_sct_dac, &dac_data, chan - 1U))
		{
			sprintf((char *)resp_buf, "ch_mv:\t\t%hu%s", dac_data.ch_mv, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "vref:\t\t%hu%s", dac_data.vref, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "gain:\t\t%hu%s", dac_data.gain, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "pwr_dwn_mode:\t%hu%s", dac_data.pwr_dwn_mode, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "rdy_nbusy:\t%hu%s", dac_data.rdy_nbusy, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "por:\t\t%hu%s", dac_data.por, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "addr_bit:\t%hu%s", dac_data.addr_bit, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_ch_mv:\t%hu%s", dac_data.ee_ch_mv, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_vref:\t%hu%s", dac_data.ee_vref, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_gain:\t%hu%s", dac_data.ee_gain, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_pwr_dwn_mode:%hu%s", dac_data.ee_pwr_dwn_mode, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_rdy_nbusy:\t%hu%s", dac_data.ee_rdy_nbusy, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_por:\t\t%hu%s", dac_data.ee_por, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
			sprintf((char *)resp_buf, "ee_addr_bit:\t%hu%s", dac_data.ee_addr_bit, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to read DAC ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_DAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return state of Synthesiser Lock Detect signals
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetLockDetectsCommand(uint8_t *resp_buf)
{
	bool ld1 = false;
	bool ld2 = false;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (tbg_ReadLockDetects(&lg_sct_tb_gpio, &ld1, &ld2))
	{
		sprintf((char *)resp_buf, "Lock Detect 1: %s%s", (ld1 ? "true" : "false"), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Lock Detect 2: %s%s", (ld2 ? "true" : "false"), SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Board ID! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_LOCK_DETS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the selected synth, 1 or 2
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSelectSynthCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	tbg_SynthRange_t synth;
	int16_t temp = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SYNTH_SEL_CMD_FORMAT, &temp) ==
			SCT_SYNTH_SEL_CMD_FORMAT_NO)
	{
		synth = ((temp > tbg_Synth2) || (temp < tbg_Synth1)) ? tbg_Synth1 : temp;

		if (tbg_SetSynthSelect(&lg_sct_tb_gpio, synth))
		{
			sprintf((char *)resp_buf, "Selected synth: %hd%s",
					(int16_t)synth, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to select Synth %hd ***%s",
					(int16_t)synth, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SYNTH_SEL_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set RF centre frequency in MHz with the specified synth
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRfCentreFreqCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	tbg_SynthRange_t synth;
	int16_t temp = 0U;
	uint32_t freq_mhz = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_SYNTH_FREQ_CMD_FORMAT, &temp, &freq_mhz) ==
			SCT_SET_SYNTH_FREQ_CMD_FORMAT_NO)
	{
		synth = ((temp > tbg_Synth2) || (temp < tbg_Synth1)) ? tbg_Synth1 : temp;

		if (ssd_SetCentreFreqMhz(&lg_sct_synth[synth - 1], freq_mhz))
		{
			sprintf((char *)resp_buf, "Set synth %hd to %lu MHz%s",
					(int16_t)synth, freq_mhz, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set synth frequency %lu ***%s",
					freq_mhz, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_SYNTH_FREQ_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set pre-selector path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetPreselectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t presel = 0U;
	const char **presel_str = iad_GetPreselectorStr();

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_PRESEL_CMD_FORMAT, &presel) ==
			SCT_SET_PRESEL_CMD_FORMAT_NO)
	{
		if (tbg_SetPreselectorPath(&lg_sct_tb_gpio, presel))
		{
			sprintf((char *)resp_buf, "Set pre-selector path to %hu - %s%s",
					presel, presel_str[presel], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set pre-selector path to %hu - %s ***%s",
					presel, presel_str[presel], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_PRESEL_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set RF attenuator to the specified value, units of value is 0.5 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRfAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_RF_ATTEN_CMD_FORMAT, &atten) ==
			SCT_SET_RF_ATTEN_CMD_FORMAT_NO)
	{
		if (tbg_SetRfAtten(&lg_sct_tb_gpio, atten))
		{
			sprintf((char *)resp_buf, "Set RF attenuator to %hu (0.5 dB)%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set RF attenuator to %hu (0.5 dB) ***%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RF_ATTEN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set IF attenuator to the specified value, units of value is 0.5 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetIfAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_IF_ATTEN_CMD_FORMAT, &atten) ==
			SCT_SET_IF_ATTEN_CMD_FORMAT_NO)
	{
		if (tbg_SetIfAtten(&lg_sct_tb_gpio, atten))
		{
			sprintf((char *)resp_buf, "Set IF attenuator to %hu (0.5 dB)%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set IF attenuator to %hu (0.5 dB) ***%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_IF_ATTEN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set LNA Bypass signals, '0' no bypass LNA, non-zero to bypass
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetLnaBypassCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t bypass = 0U;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sscanf((char *)cmd_buf, SCT_SET_LNA_BYPASS_CMD_FORMAT, &bypass) ==
			SCT_SET_LNA_BYPASS_CMD_FORMAT_NO)
	{
		if (tbg_SetLnaBypass(&lg_sct_tb_gpio, (bypass ? true : false)))
		{
			sprintf((char *)resp_buf, "Set LNA bypass to: %s%s",
					(bypass ? "Bypass" : "LNA") , SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set LNA bypass to: %s ***%s",
					(bypass ? "LNA" : "Bypass"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_LNA_BYPASS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return mixer level in centi-dBm
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetMixerLevelCommand(uint8_t *resp_buf)
{
	iad_SpiAdcData_t adc_data = {0};

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	if (sad_ReadAdcData(&lg_sct_spi_dac, &adc_data))
	{
		sprintf((char *)resp_buf, "Mixer Level: %hd centi-dBm%s",
				adc_data.adc_ch_cdbm, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read Mixer Level! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_MXR_LEVEL_RESP, SCT_CRLF);
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
	sprintf((char *)resp_buf, "%s%s%s", SCT_CRLF, SCT_UNKONWN_CMD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}
