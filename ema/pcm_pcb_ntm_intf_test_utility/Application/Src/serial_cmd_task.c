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
	lg_sct_init_data.fan_alert_n_gpio_port	= init_data.fan_alert_n_gpio_port;
	lg_sct_init_data.fan_alert_n_gpio_pin	= init_data.fan_alert_n_gpio_pin;
	lg_sct_init_data.rf_mute_n_gpio_port	= init_data.rf_mute_n_gpio_port;
	lg_sct_init_data.rf_mute_n_gpio_pin		= init_data.rf_mute_n_gpio_pin;
	lg_sct_init_data.pfi_n_gpio_port		= init_data.pfi_n_gpio_port;
	lg_sct_init_data.pfi_n_gpio_pin			= init_data.pfi_n_gpio_pin;
	lg_sct_init_data.pps_gpio_pin			= init_data.pps_gpio_pin;
	lg_sct_init_data.aop_adc_hadc			= init_data.aop_adc_hadc;

	hci_Init(	&lg_sct_hci, init_data.i2c_device,
				SCT_PCA9500_GPIO_I2C_ADDR,
				SCT_PCA9500_EEPROM_I2C_ADDR);

	fc_InitInstance(&lg_sct_fan_ctrlr,
					init_data.i2c_device,
					SCT_EMC2104_I2C_ADDR);

	dvc_InitInstance(	&lg_sct_dcdc_volt_ctrl,
						init_data.i2c_device,
						SCT_AD5272_I2C_ADDR);

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

	if (lg_sct_initialised == false)
	{
		for(;;)
		{
		}
	}

  	HAL_Delay(100U);
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
	static uint8_t 	cmd_buf[SCT_MAX_BUF_SIZE] = {0U};
	static uint16_t	cmd_buf_idx = 0U;

	/* To help with human-entered command strings, backspace key erases last character */
	if (data == SCT_BACKSPACE)
	{
		if (cmd_buf_idx > 0U)
		{
			--cmd_buf_idx;
		}

		sprintf((char *)resp_buf, "\b \b");
		sct_FlushRespBuf(resp_buf);
	}
	else if (data == SCT_ENTER)
	{
		/* Add null termination to command buffer and process command */
		cmd_buf[cmd_buf_idx] = '\0';
		sct_ProcessCommand(cmd_buf, resp_buf);

		/* Reset command buffer ready for next command */
		cmd_buf_idx = 0U;
	}
	else
	{
		/* Add received byte to command buffer */
		cmd_buf[cmd_buf_idx++] = toupper(data);

		/* Not expecting to see this situation as all commands have
		 * length < SCT_MAX_BUF_SIZE */
		if (cmd_buf_idx >= SCT_MAX_BUF_SIZE)
		{
			cmd_buf_idx = 0U;
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
		sct_ProcessHwConfigInfoCommand(cmd_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_HW_RST_CONFIG_INFO_CMD, SCT_HW_RST_CONFIG_INFO_CMD_LEN))
	{
		sct_ProcessResetHwConfigInfoCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_HW_SET_PARAM_CMD, SCT_HW_SET_PARAM_CMD_LEN))
	{
		sct_ProcessSetHwConfigInfoCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_RDAC_CMD, SCT_READ_RDAC_CMD_LEN))
	{
		sct_ProcessReadRdacCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_RDAC_CMD, SCT_SET_RDAC_CMD_LEN))
	{
		sct_ProcessSetRdacCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_RESET_RDAC_CMD, SCT_RESET_RDAC_CMD_LEN))
	{
		sct_ProcessResetRdacCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_50TP_CMD, SCT_READ_50TP_CMD_LEN))
	{
		sct_ProcessRead50TpCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_SET_50TP_CMD, SCT_SET_50TP_CMD_LEN))
	{
		sct_ProcessSet50TpCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_INIT_FAN_CTRLR, SCT_INIT_FAN_CTRLR_LEN))
	{
		sct_ProcessInitFanControllerCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_PUSH_TEMP, SCT_FAN_PUSH_TEMP_LEN))
	{
		sct_ProcessPushFanTempCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_SET_DIRECT, SCT_FAN_SET_DIRECT_LEN))
	{
		sct_ProcessSetFanDirectCommand(cmd_buf, resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_GET_SPEED_CMD, SCT_FAN_GET_SPEED_CMD_LEN))
	{
		sct_ProcessGetFanSpeedCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_GET_TACH_TRGT_CMD, SCT_FAN_GET_TACH_TRGT_CMD_LEN))
	{
		sct_ProcessGetFanTachTargetCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_GET_TEMP_CMD, SCT_FAN_GET_TEMP_CMD_LEN))
	{
		sct_ProcessGetFanTempCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_FAN_STATUS_CMD, SCT_FAN_STATUS_CMD_LEN))
	{
		sct_ProcessGetFanStatusCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_DOP_CMD, SCT_READ_DOP_CMD_LEN))
	{
		sct_ProcessReadDigitalOutputsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_PPS_CMD, SCT_READ_PPS_CMD_LEN))
	{
		sct_ProcessReadPpsCommand(resp_buf);
	}
	else if (!strncmp((char *)cmd_buf, SCT_READ_AOP_CMD, SCT_READ_AOP_CMD_LEN))
	{
		sct_ProcessReadAnalogOutputsCommand(resp_buf);
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
* Read the current RDAC value from the AD7252
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReadRdacCommand(uint8_t *resp_buf)
{
	uint16_t rdac_val = 0U;

	if (dvc_ReadRdacValue(&lg_sct_dcdc_volt_ctrl, &rdac_val))
	{
		sprintf((char *)resp_buf, "AD5272 RDAC value: %hu%s", rdac_val, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read RDAC value! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_RDAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the AD7252 RDAC value to the specified value
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetRdacCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t rdac_val = 0U;

	if (sscanf((char *)cmd_buf, SCT_SET_RDAC_CMD_FORMAT, &rdac_val) ==
			SCT_SET_RDAC_CMD_FORMAT_NO)
	{
		if (dvc_SetRdacValue(&lg_sct_dcdc_volt_ctrl, rdac_val))
		{
			sprintf((char *)resp_buf, "RDAC value set: %hu%s", rdac_val, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set RDAC value! ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_RDAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Reset the AD7252 RDAC value to the power-on-reset value
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessResetRdacCommand(uint8_t *resp_buf)
{
	if (dvc_ResetDevice(&lg_sct_dcdc_volt_ctrl))
	{
		sprintf((char *)resp_buf, "Reset AD5272 RDAC to POR value%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to reset AD5272! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_RESET_RDAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read the current 50TP value from the AD7252
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessRead50TpCommand(uint8_t *resp_buf)
{
	uint16_t last_50tp_addr = 0U, value_50tp = 0U;

	if (dvc_Read50TpValue(&lg_sct_dcdc_volt_ctrl, &last_50tp_addr, &value_50tp))
	{
		sprintf((char *)resp_buf, "Last 50-TP address written to: %hu%s",
				last_50tp_addr, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
		sprintf((char *)resp_buf, "Last 50-TP value stored: %hu%s",
				value_50tp, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read 50TP value! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_READ_RDAC_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Program the current AD7252 RDAC value into 50TP memory
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSet50TpCommand(uint8_t *resp_buf)
{
	if (dvc_StoreWiperTo50TpValue(&lg_sct_dcdc_volt_ctrl))
	{
		sprintf((char *)resp_buf, "AD5272 50TP value successfully programmed%s",
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to program AD5272 50TP value! ***%s",
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_SET_50TP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Initialise the fan controller IC
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessInitFanControllerCommand(uint8_t *resp_buf)
{
	if (fc_Initialise(&lg_sct_fan_ctrlr))
	{
		sprintf((char *)resp_buf, "EMC2104 fan controller successfully initialised%s",
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to initialise EMC2104 fan controller! ***%s",
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_INIT_FAN_CTRLR_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Push the specified temperature to the fan controller
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessPushFanTempCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	int16_t temp = 0;

	if (sscanf((char *)cmd_buf, SCT_FAN_PUSH_TEMP_FORMAT, &temp) ==
			SCT_FAN_PUSH_TEMP_FORMAT_NO)
	{
		if (fc_PushTemperature(&lg_sct_fan_ctrlr, (int8_t)temp))
		{
			sprintf((char *)resp_buf, "Pushed temperature to fan controller: %hd%s",
					temp, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to push temperature! ***%s", SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_PUSH_TEMP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Set the fan speed to direct mode using specified PWM value
*
* @param	cmd_buf command buffer to extract parameters from
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetFanDirectCommand(uint8_t *cmd_buf, uint8_t *resp_buf)
{
	uint16_t pwm = 0;

	if (sscanf((char *)cmd_buf, SCT_FAN_SET_DIRECT_FORMAT, &pwm) ==
			SCT_FAN_SET_DIRECT_FORMAT_NO)
	{
		if (fc_SetDirectSettingMode(&lg_sct_fan_ctrlr, (uint8_t)pwm))
		{
			sprintf((char *)resp_buf, "Set direct fan drive setting: %hu%s",
					pwm, SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
		else
		{
			sprintf((char *)resp_buf, "*** Failed to set direct fan drive setting! ***%s",
					SCT_CRLF);
			sct_FlushRespBuf(resp_buf);
		}
	}
	else
	{
		sprintf((char *)resp_buf, "*** Parameter Error! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_SET_DIRECT_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read the fan speeds from the fan controller
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetFanSpeedCommand(uint8_t *resp_buf)
{
	uint16_t fan1_clk_count = 0U, fan2_clk_count = 0U;
	uint8_t fan1_pwm = 0U, fan2_pwm = 0U;

	if (fc_ReadFanSpeedCounts(	&lg_sct_fan_ctrlr,
								&fan1_clk_count, &fan2_clk_count,
								&fan1_pwm, &fan2_pwm))
	{
		sprintf((char *)resp_buf, "Fan 1 Speed Count: %u%sFan 2 Speed Count: %u%s",
				fan1_clk_count, SCT_CRLF, fan2_clk_count, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Fan 1 Speed RPM: %u%sFan 2 Speed RPM: %u%s",
				15734640U / fan1_clk_count, SCT_CRLF, 15734640U / fan2_clk_count, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);

		sprintf((char *)resp_buf, "Fan 1 PWM Drive: %u%sFan 2 PWM Drive: %u%s",
				fan1_pwm, SCT_CRLF, fan2_pwm, SCT_CRLF);
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
* Read the fan speed tacho target registers from the fan controller
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetFanTachTargetCommand(uint8_t *resp_buf)
{
	uint16_t fan1_tach_target = 0U, fan2_tach_target = 0U;

	if (fc_ReadFanTachTargets(	&lg_sct_fan_ctrlr,
								&fan1_tach_target, &fan2_tach_target))
	{
		sprintf((char *)resp_buf, "Fan 1 Tach Target: %u%sFan 2 Tach Target: %u%s",
				fan1_tach_target, SCT_CRLF, fan2_tach_target, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read tach targets! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_GET_TACH_TRGT_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read the internal temperature of the fan controller
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetFanTempCommand(uint8_t *resp_buf)
{
	int8_t int_temp = 0;

	if (fc_ReadInternalTemp(&lg_sct_fan_ctrlr, &int_temp))
	{
		sprintf((char *)resp_buf, "EMC2104 Internal Temperature: %d%s",
				int_temp, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read temperature! ***%s", SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_GET_TEMP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return fan controller status register
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessGetFanStatusCommand(uint8_t *resp_buf)
{
	uint8_t fan_status_reg = 0U;

	if (fc_ReadFanStatus(&lg_sct_fan_ctrlr, &fan_status_reg))
	{
		sprintf((char *)resp_buf, "EMC2104 Fan Status: %x%s",
				fan_status_reg, SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "*** Failed to read fan status! ***%s",
				SCT_CRLF);
		sct_FlushRespBuf(resp_buf);
	}

	sprintf((char *)resp_buf, "%s%s", SCT_FAN_STATUS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and return digital outputs from the KT-000-0143-00 board
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReadDigitalOutputsCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "FAN_ALERT_N:\t%s%s",
			(HAL_GPIO_ReadPin(	lg_sct_init_data.fan_alert_n_gpio_port,
								lg_sct_init_data.fan_alert_n_gpio_pin)
									== GPIO_PIN_RESET ? "0" : "1"), SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "RF_MUTE_N:\t%s%s",
			(HAL_GPIO_ReadPin(	lg_sct_init_data.rf_mute_n_gpio_port,
								lg_sct_init_data.rf_mute_n_gpio_pin)
									== GPIO_PIN_RESET ? "0" : "1"), SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "PFI_N:\t\t%s%s",
			(HAL_GPIO_ReadPin(	lg_sct_init_data.pfi_n_gpio_port,
								lg_sct_init_data.pfi_n_gpio_pin)
									== GPIO_PIN_RESET ? "0" : "1"), SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_READ_DOP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Check if the 1PPS output from the KT-000-0143-00 board is present
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReadPpsCommand(uint8_t *resp_buf)
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

	sprintf((char *)resp_buf, "%s%s", SCT_READ_PPS_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}

/*****************************************************************************/
/**
* Read and return digital outputs from the KT-000-0143-00 board
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReadAnalogOutputsCommand(uint8_t *resp_buf)
{
	int32_t adc_reading[SCT_AOP_NUM_CHANNELS] = {0};
	int32_t adc_reading_scaled[SCT_AOP_NUM_CHANNELS] = {0};
	int32_t vref_ext = 0;
	int16_t i = 0;

	/* Start the ADC sampling and perform calibration to improve result accuracy */
	HAL_ADCEx_Calibration_Start(lg_sct_init_data.aop_adc_hadc, ADC_SINGLE_ENDED);
	HAL_ADC_Start(lg_sct_init_data.aop_adc_hadc);

	/* Get a sample for each ADC channel and add it to the averaging buffer */
	for (i = 0; i < SCT_AOP_NUM_CHANNELS; ++i)
	{
		HAL_ADC_PollForConversion(lg_sct_init_data.aop_adc_hadc, 10U);
		adc_reading[i] = (int32_t)HAL_ADC_GetValue(lg_sct_init_data.aop_adc_hadc);
	}

	HAL_ADC_Stop(lg_sct_init_data.aop_adc_hadc);

	/* Use the Vrefint reading to calculate the Vrefext in mV */
	vref_ext = (SCT_AOP_VREFINT_MV * (SCT_AOP_ADC_BITS - 1)) /
				adc_reading[SCT_AOP_VREF_INT_CHANNEL_IDX];

	/* Calculate scaled values */
	for (i = 0; i < SCT_AOP_NUM_CHANNELS; ++i)
	{
		adc_reading_scaled[i] = (adc_reading[i] *
									SCT_AOP_SCALE_FACTORS[i][SCT_AOP_SCALE_MUL] * vref_ext) /
									SCT_AOP_SCALE_FACTORS[i][SCT_AOP_SCALE_DIV];
	}

	/* Output results */
	sprintf((char *)resp_buf, "+3V4_STBY:\t%lu mV%s",
			adc_reading_scaled[SCT_AOP_RAIL_3V4_CHANNEL_IDX], SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "+28V:\t\t%lu mV%s",
			adc_reading_scaled[SCT_AOP_RAIL_28V_CHANNEL_IDX], SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "%s%s", SCT_READ_AOP_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Send response associated with receiving an unknown command
*
* @param    resp_buf buffer for transmitting command response
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessUnkownCommand(uint8_t *resp_buf)
{
	sprintf((char *)resp_buf, "%s%s", SCT_UNKONWN_CMD_RESP, SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
}


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
