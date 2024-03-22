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
	lg_sct_init_data.spi_device 			= init_data.spi_device;
	lg_sct_init_data.i2c_reset_gpio_port 	= init_data.i2c_reset_gpio_port;
	lg_sct_init_data.i2c_reset_gpio_pin 	= init_data.i2c_reset_gpio_pin;
	lg_sct_init_data.xcvr_ncs_gpio_port     = init_data.xcvr_ncs_gpio_port;
	lg_sct_init_data.xcvr_ncs_gpio_pin      = init_data.xcvr_ncs_gpio_pin;

	tbg_Init(	&lg_sct_tb_gpio,
				init_data.i2c_device,
				init_data.i2c_reset_gpio_port,
				init_data.i2c_reset_gpio_pin);

	hci_Init(	&lg_sct_hci, init_data.i2c_device,
				SCT_PCA9500_GPIO_I2C_ADDR,
				SCT_PCA9500_EEPROM_I2C_ADDR);

	(void) iad_InitInstance(&lg_sct_i2c_adc, lg_sct_init_data.i2c_device, SCT_LTC2991_ADC_I2C_ADDR);

	(void) sxc_InitInstance(&lg_sct_spi_xcvr,
							lg_sct_init_data.spi_device,
			                lg_sct_init_data.xcvr_ncs_gpio_port,
							lg_sct_init_data.xcvr_ncs_gpio_pin);

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
	else if (!strncmp((char *)cmd_buf, SCT_GET_ADC_DATA_CMD, SCT_GET_ADC_DATA_CMD_LEN))
	{
		sct_ProcesssGetAdcDataCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_BOARD_ID_CMD, SCT_GET_BOARD_ID_CMD_LEN))
	{
		sct_ProcessGetBoardIdCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_DDS_ATT_CMD, SCT_SET_DDS_ATT_CMD_LEN))
	{
		sct_ProcessSetDdsAttenCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_TX_ATT_FINE_CMD, SCT_SET_TX_ATT_FINE_CMD_LEN))
	{
		sct_ProcessSetTxFineAttenCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_TX_ATT_COARSE_CMD, SCT_SET_TX_ATT_COARSE_CMD_LEN))
	{
		sct_ProcessSetTxCoarseAttenCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RX_LNA_BYPASS_CMD, SCT_SET_RX_LNA_BYPASS_CMD_LEN))
	{
		sct_ProcessSetRxLnaBypassCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RX_PRESEL_CMD, SCT_SET_RX_PRESEL_CMD_LEN))
	{
		sct_ProcessSetRxPreselectorCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_TX_PATH_CMD, SCT_SET_TX_PATH_CMD_LEN))
	{
		sct_ProcessSetTxPathCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RX_EN_CMD, SCT_SET_RX_EN_CMD_LEN))
	{
		sct_ProcessSetRxEnableCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_TX_EN_CMD, SCT_SET_TX_EN_CMD_LEN))
	{
		sct_ProcessSetTxEnableCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_XCVR_RESET_CMD, SCT_SET_XCVR_RESET_CMD_LEN))
	{
		sct_ProcessSetXcvrResetCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_XCVR_VID_CMD, SCT_GET_XCVR_VID_CMD_LEN))
	{
		sct_ProcessGetXcvrVendorIdCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_GET_GP_INTERRUPT_CMD, SCT_GET_GP_INTERRUPT_CMD_LEN))
	{
		sct_ProcessGetGpInterruptCommand(resp_buf);
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
* Read and return the ADC data
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
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
* Set DDS 20dB attenuator command, '0' disable attenuator, non-zero to enable
* attenuator
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetDdsAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_DDS_ATT_CMD_FORMAT, &atten) ==
			SCT_SET_DDS_ATT_CMD_FORMAT_NO)
	{
		if (tbg_SetDdsAtten(&lg_sct_tb_gpio, (atten ? true : false)))
		{
			sprintf((char *)resp_buf, "Set DDS 20 dB attenuator to: %s%s",
					(atten ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set DDS 20 dB attenuator to: %s ***%s",
					(atten ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_DDS_ATT_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set TX fine attenuator to the specified value, units of value is 0.25 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetTxFineAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_ATT_FINE_CMD_FORMAT, &atten) ==
			SCT_SET_TX_ATT_FINE_CMD_FORMAT_NO)
	{
		if (tbg_SetTxFineAtten(&lg_sct_tb_gpio, atten))
		{
			sprintf((char *)resp_buf, "Set tx fine attenuator to %hu (x0.25 dB)%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx fine attenuator to %hu (x0.25 dB) ***%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_ATT_FINE_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set TX coarse attenuator to the specified value, units of value is 3 dB
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetTxCoarseAttenCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t atten = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_ATT_COARSE_CMD_FORMAT, &atten) ==
			SCT_SET_TX_ATT_COARSE_CMD_FORMAT_NO)
	{
		if (tbg_SetTxFCoarseAtten(&lg_sct_tb_gpio, atten))
		{
			sprintf((char *)resp_buf, "Set tx coarse attenuator to %hu (x3 dB)%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx coarse attenuator to %hu (x3 dB) ***%s",
					atten, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_ATT_COARSE_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set RX LNA Bypass signals, '0' no bypass LNA, non-zero to bypass
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRxLnaBypassCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t bypass = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_RX_LNA_BYPASS_CMD_FORMAT, &bypass) ==
			SCT_SET_RX_LNA_BYPASS_CMD_FORMAT_NO)
	{
		if (tbg_SetRxLnaBypass(&lg_sct_tb_gpio, (bypass ? true : false)))
		{
			sprintf((char *)resp_buf, "Set rx LNA bypass to: %s%s",
					(bypass ? "Bypass" : "LNA") , SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set rx LNA bypass to: %s ***%s",
					(bypass ? "Bypass" : "LNA"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_LNA_BYPASS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set RX pre-selector path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRxPreselectorCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t presel = 0U;
	const char **presel_str = tbg_GetRxPreselectorPathStr();

	if (sscanf((char *)cmd_buf, SCT_SET_RX_PRESEL_CMD_FORMAT, &presel) ==
			SCT_SET_RX_PRESEL_CMD_FORMAT_NO)
	{
		if (tbg_SetRxPreselectorPath(&lg_sct_tb_gpio, presel))
		{
			sprintf((char *)resp_buf, "Set rx pre-selector path to %hu - %s%s",
					presel, presel_str[presel], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set rx pre-selector path to %hu ***%s",
					presel, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_PRESEL_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set TX path to the specified value
*
* @param    resp_buf buffer for transmitting command response
* @param	cmd_buf command buffer to extract parameters from
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetTxPathCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t path = 0U;
	const char **tx_path_str = tbg_GetTxPathStr();

	if (sscanf((char *)cmd_buf, SCT_SET_TX_PATH_CMD_FORMAT, &path) ==
			SCT_SET_TX_PATH_CMD_FORMAT_NO)
	{
		if (tbg_SetTxPath(&lg_sct_tb_gpio, path))
		{
			sprintf((char *)resp_buf, "Set tx path to %hu - %s%s",
					path, tx_path_str[path], SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx path to %hu ***%s",
					path, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_PATH_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set RX enable command, '0' disable , non-zero to enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRxEnableCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t enable = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_RX_EN_CMD_FORMAT, &enable) ==
			SCT_SET_RX_EN_CMD_FORMAT_NO)
	{
		if (tbg_RxEnable(&lg_sct_tb_gpio, (enable ? true : false)))
		{
			sprintf((char *)resp_buf, "Set rx enable to: %s%s",
					(enable ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set rx enable to: %s ***%s",
					(enable ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RX_EN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set TX enable command, '0' disable , non-zero to enable
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetTxEnableCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t enable = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_TX_EN_CMD_FORMAT, &enable) ==
			SCT_SET_TX_EN_CMD_FORMAT_NO)
	{
		if (tbg_TxEnable(&lg_sct_tb_gpio, (enable ? true : false)))
		{
			sprintf((char *)resp_buf, "Set tx enable to: %s%s",
					(enable ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set tx enable to: %s ***%s",
					(enable ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_TX_EN_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set transceiver reset command, '0' de-assert reset , non-zero to assert reset
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetXcvrResetCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t reset = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_XCVR_RESET_CMD_FORMAT, &reset) ==
			SCT_SET_XCVR_RESET_CMD_FORMAT_NO)
	{
		if (tbg_XcvrReset(&lg_sct_tb_gpio, (reset ? true : false)))
		{
			sprintf((char *)resp_buf, "Set transceiver reset to: %s%s",
					(reset ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);

			if (!reset)
			{
				bool initOk = sxc_InitDevice(&lg_sct_spi_xcvr);

				sprintf((char *)resp_buf, "Transceiver SPI initialisation %s%s",
					    (initOk ? "OK" : "FAILED"), SCT_CRLF);
                sct_FlushRespBuf(resp_buf);
			}
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set transceiver reset to: %s ***%s",
					(reset ? "Enabled" : "Disabled"), SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_XCVR_RESET_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Get transceiver vendor ID
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetXcvrVendorIdCommand(uint8_t *resp_buf)
{
	uint16_t id = 0;
	if (sxc_ReadVendorId(&lg_sct_spi_xcvr, &id))
	{
		sprintf((char *)resp_buf, "Vendor ID: 0x%04X%s", id, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read transceiver Vendor ID! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_XCVR_VID_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read GP interrupt signal
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetGpInterruptCommand(uint8_t *resp_buf)
{
	bool gp_interrupt = false;

	if (tbg_ReadGpInterrupt(&lg_sct_tb_gpio, &gp_interrupt))
	{
		sprintf((char *)resp_buf, "GP Interrupt: %hd%s", (int16_t)gp_interrupt, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read GP Interrupt! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_GET_GP_INTERRUPT_RESP, SCT_CRLF);
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
