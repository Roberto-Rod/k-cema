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
#include "led_task.h"
#include "hw_config_info.h"
#include "version.h"
#include "main.h"
#include "stm32l0xx_hal.h"
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
	lg_sct_init_data.tx_data_queue 	= init_data.tx_data_queue;
	lg_sct_init_data.rx_data_queue 	= init_data.rx_data_queue;
	lg_sct_init_data.i2c_device 	= init_data.i2c_device;
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
void sct_SerialCmdTask(void const * argument)
{
	osEvent event;

	if (!lg_sct_initialised)
	{
		for(;;)
		{
		}
	}

  	HAL_Delay(100);
  	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_CLS, SCT_HOME);
	sct_FlushRespBuf();
	sprintf((char *)lg_sct_resp_buf, "%s RCU PCB Test Utility - V%d.%d.%d%s",
			SW_PART_NO, SW_VERSION_MAJOR, SW_VERSION_MINOR, SW_VERSION_BUILD, SCT_CRLF);
	sct_FlushRespBuf();

	for(;;)
	{
		event = osMessageGet(lg_sct_init_data.rx_data_queue, portMAX_DELAY);

		if (event.status == osEventMessage)
		{
			sct_ProcessReceivedByte((uint8_t)event.value.v);
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
void sct_ProcessReceivedByte(uint8_t data)
{
	/* To help with human-entered command strings, backspace key erases last character */
	if ((data == SCT_BACKSPACE) && (lg_sct_cmd_buf_idx > 0U))
	{
		--lg_sct_cmd_buf_idx;
		sprintf((char *)lg_sct_resp_buf, "\b \b");
		sct_FlushRespBuf();
	}
	else
	{
		if (data == SCT_ENTER)
		{
			/* Add null termination to command buffer and process command */
			lg_sct_cmd_buf[lg_sct_cmd_buf_idx] = '\0';
			sct_ProcessCommand();

			/* Reset command buffer ready for next command */
			lg_sct_cmd_buf_idx = 0U;
		}
		else
		{
			/* Add received byte to command buffer */
			lg_sct_cmd_buf[lg_sct_cmd_buf_idx++] = toupper(data);

			if (lg_sct_cmd_buf_idx >= SCT_MAX_BUF_SIZE)
			{
				lg_sct_cmd_buf_idx = 0U;
			}

			/* Echo received data */
			sprintf((char *)lg_sct_resp_buf, "%c", data);
			sct_FlushRespBuf();
		}
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
void sct_FlushRespBuf(void)
{
	int16_t i = 0;

	while ((lg_sct_resp_buf[i] != '\0')  && (i < SCT_MAX_BUF_SIZE))
	{
		osMessagePut(lg_sct_init_data.tx_data_queue, (uint32_t)lg_sct_resp_buf[i], 0U);
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
void sct_ProcessCommand(void)
{
	/* Try and find a match for the command */
	if (!strncmp((char *)lg_sct_cmd_buf, SCT_HW_CONFIG_INFO_CMD, SCT_HW_CONFIG_INFO_CMD_LEN))
	{
		sct_ProcessHwConfigInfoCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_HW_RST_CONFIG_INFO_CMD, SCT_HW_RST_CONFIG_INFO_CMD_LEN))
	{
		sct_ProcessResetHwConfigInfoCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_HW_SET_PARAM_CMD, SCT_HW_SET_PARAM_CMD_LEN))
	{
		sct_ProcessSetHwConfigInfoCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_READ_BTN_CMD, SCT_READ_BTN_CMD_LEN))
	{
		sct_ProcessReadButtonStateCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_SET_BZR_CMD, SCT_SET_BZR_CMD_LEN))
	{
		sct_ProcessSetBuzzerStateCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_SET_XRST_CMD, SCT_SET_XRST_CMD_LEN))
	{
		sct_ProcessSetXchangeResetStateCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_SET_LDC_CMD, SCT_SET_LDC_CMD_LEN))
	{
		sct_ProcessSetLedChangeEventCommand();
	}
	else if (!strncmp((char *)lg_sct_cmd_buf, SCT_SET_LDM_CMD, SCT_SET_LDM_CMD_LEN))
	{
		sct_ProcessSetLedModeCommand();
	}
	else
	{
		sct_ProcessUnkownCommand();
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
void sct_ProcessHwConfigInfoCommand(void)
{
	hci_HwConfigInfo hw_config_info;

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (hci_ReadHwConfigInfo(lg_sct_init_data.i2c_device, &hw_config_info))
	{
		sprintf((char *)lg_sct_resp_buf, "Hardware Configuration Information:\r\n\r\n");
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Hardware Version No: %c%c\r\n",
				((hw_config_info.hw_version > 25U) ? (int16_t)('A') : ((int16_t)hw_config_info.hw_version + (int16_t)('A'))),
				(hw_config_info.hw_version > 25U ? ((int16_t)hw_config_info.hw_version - 26 + (int16_t)('A')) : (int16_t)(' ')));
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Hardware Mod Version No: %u\r\n",
				hw_config_info.hw_mod_version);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Assembly Part No: %s\r\n",
				hw_config_info.assy_part_no);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Assembly Revision No: %s\r\n",
				hw_config_info.assy_rev_no);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Assembly Serial No: %s\r\n",
				hw_config_info.assy_serial_no);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Assembly Build Date or Batch No: %s\r\n",
				hw_config_info.assy_build_date_batch_no);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Hardware Configuration Information CRC: 0x%x\r\n",
				hw_config_info.hci_crc);
		sct_FlushRespBuf();
		sprintf((char *)lg_sct_resp_buf, "Hardware Configuration Information CRC Valid: %s\r\n",
				(hw_config_info.hci_crc_valid != 0U ? "True" : "False"));
		sct_FlushRespBuf();
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "*** Failed to read Hardware Configuration Information! ***\r\n");
		sct_FlushRespBuf();
	}

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_HW_CONFIG_INFO_RESP, SCT_CR);
	sct_FlushRespBuf();
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
void sct_ProcessResetHwConfigInfoCommand(void)
{
	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (hci_ResetHwConfigInfo(lg_sct_init_data.i2c_device))
	{
		sprintf((char *)lg_sct_resp_buf, "Successfully cleared HCI EEPROM%s",
				SCT_CR);
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "*** Failed to clear HCI EEPROM! ***%s",
				SCT_CR);
	}
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_HW_RST_CONFIG_INFO_RESP, SCT_CR);
	sct_FlushRespBuf();
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
void sct_ProcessSetHwConfigInfoCommand(void)
{
	int32_t param_to_set;
	bool param_set = false;
	char param[HCI_STR_PARAM_LEN] = {0};

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (sscanf((char *)lg_sct_cmd_buf, SCT_HW_SET_PARAM_CMD_FORMAT,
			(int *)&param_to_set, param) == SCT_HW_SET_PARAM_CMD_FORMAT_NO)
	{
		/* Ensure last character of string to set is null terminator */
		param[HCI_STR_PARAM_LEN - 1] = 0U;

		if (param_to_set <= sct_BuildBatchNo)
		{
			switch (param_to_set)
			{
			case sct_PartNo:
				param_set = hci_SetAssyPartNo(	lg_sct_init_data.i2c_device,
												(uint8_t *)param);
				break;

			case sct_RevNo:
				param_set = hci_SetAssyRevNo(	lg_sct_init_data.i2c_device,
												(uint8_t *)param);
				break;

			case sct_SerialNo:
				param_set = hci_SetAssySerialNo(lg_sct_init_data.i2c_device,
												(uint8_t *)param);
				break;

			case sct_BuildBatchNo:
				param_set = hci_SetAssyBuildDataBatchNo(
												lg_sct_init_data.i2c_device,
												(uint8_t *)param);
				break;

			default:
				param_set = false;
				break;
			}

			if (param_set)
			{
				sprintf((char *)lg_sct_resp_buf,
						"Successfully set parameter [%s] to [%s]%s",
						sct_SetHciParamStrings[param_to_set], param, SCT_CR);
			}
			else
			{
				sprintf((char *)lg_sct_resp_buf,
						"*** Failed to set parameter [%s] ***%s",
						sct_SetHciParamStrings[param_to_set], SCT_CR);
			}
		}
		else
		{
			sprintf((char *)lg_sct_resp_buf, "*** Unknown Parameter! ***%s",
					SCT_CR);
		}
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "*** Parameter Error! ***%s", SCT_CR);
	}
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_HW_SET_PARAM_RESP, SCT_CR);
	sct_FlushRespBuf();
}


/*****************************************************************************/
/**
* Reads and returns the state of the keypad push-buttons
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessReadButtonStateCommand(void)
{
	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "Button 0 (Start Jamming):\t%u\r\n",
			HAL_GPIO_ReadPin(BTN0_IN_GPIO_Port, BTN0_IN_Pin));
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "Button 1 (Alarm Mute):\t\t%u\r\n",
			HAL_GPIO_ReadPin(BTN1_IN_GPIO_Port, BTN1_IN_Pin));
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "Button 2 (Mission Select):\t%u\r\n",
			HAL_GPIO_ReadPin(BTN2_IN_GPIO_Port, BTN2_IN_Pin));
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_READ_BTN_RESP, SCT_CR);
	sct_FlushRespBuf();
}


/*****************************************************************************/
/**
* Sets the buzzer enable signal state, disable if serial command parameter is
* zero, else enable
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetBuzzerStateCommand(void)
{
	uint16_t set_state = 0U;
	GPIO_PinState pin_state = GPIO_PIN_RESET;

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (sscanf((char *)lg_sct_cmd_buf, SCT_SET_BZR_CMD_FORMAT, &set_state) ==
			SCT_SET_BZR_CMD_FORMAT_NO)
	{
		if (set_state == 0U)
		{
			pin_state = GPIO_PIN_RESET;
			sprintf((char *)lg_sct_resp_buf, "Buzzer disabled\r\n");
		}
		else
		{
			pin_state = GPIO_PIN_SET;
			sprintf((char *)lg_sct_resp_buf, "Buzzer enabled\r\n");
		}
		HAL_GPIO_WritePin(BUZZER_ENABLE_GPIO_Port, BUZZER_ENABLE_Pin, pin_state);
		sct_FlushRespBuf();
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "*** Parameter Error! ***%s", SCT_CR);
		sct_FlushRespBuf();
	}

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_SET_BZR_RESP, SCT_CR);
	sct_FlushRespBuf();
}


/*****************************************************************************/
/**
* Sets the XCHANGE reset signal state, disable if serial command parameter is
* zero, else enable
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetXchangeResetStateCommand(void)
{
	uint16_t set_state = 0U;
	GPIO_PinState pin_state = GPIO_PIN_RESET;

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (sscanf((char *)lg_sct_cmd_buf, SCT_SET_XRST_CMD_FORMAT, &set_state) ==
			SCT_SET_XRST_CMD_FORMAT_NO)
	{
		if (set_state == 0U)
		{
			pin_state = GPIO_PIN_RESET;
			sprintf((char *)lg_sct_resp_buf, "XCHANGE reset de-asserted\r\n");
		}
		else
		{
			pin_state = GPIO_PIN_SET;
			sprintf((char *)lg_sct_resp_buf, "XCHANGE reset asserted\r\n");
		}
		HAL_GPIO_WritePin(XCHANGE_RESET_GPIO_Port, XCHANGE_RESET_Pin, pin_state);
		sct_FlushRespBuf();
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "***Parameter Error! ***%s", SCT_CR);
		sct_FlushRespBuf();
	}

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_SET_XRST_RESP, SCT_CR);
	sct_FlushRespBuf();
}


/*****************************************************************************/
/**
* Sets the event that causes the LED indications to change state, must be one
* of led_ChangeOn_t enumerated values
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetLedChangeEventCommand(void)
{
	led_ChangeOn_t set_event;
	int16_t ip_event = 0;
	extern const char* led_ChangeOnStrings[];

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (sscanf((char *)lg_sct_cmd_buf, SCT_SET_LDC_CMD_FORMAT, &ip_event) ==
			SCT_SET_LDC_CMD_FORMAT_NO)
	{
		set_event = led_SetChangeEvent((led_ChangeOn_t)ip_event);

		sprintf((char *)lg_sct_resp_buf, "Set LED change event to: [%s]%s",
				led_ChangeOnStrings[set_event], SCT_CR);
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "***Parameter Error! ***%s", SCT_CR);
	}
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_SET_LDC_RESP, SCT_CR);
	sct_FlushRespBuf();
}


/*****************************************************************************/
/**
* Sets the LED indication mode, must be one of led_Mode_t enumerated values
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void sct_ProcessSetLedModeCommand(void)
{
	led_Mode_t set_mode;
	int16_t ip_mode = 0;
	extern const char* led_ModeStrings[];

	sprintf((char *)lg_sct_resp_buf, "%s", SCT_CR);
	sct_FlushRespBuf();

	if (sscanf((char *)lg_sct_cmd_buf, SCT_SET_LDM_CMD_FORMAT, &ip_mode) ==
			SCT_SET_LDC_CMD_FORMAT_NO)
	{
		set_mode = led_SetMode((led_Mode_t)ip_mode);

		sprintf((char *)lg_sct_resp_buf, "Set LED mode to: [%s]%s",
				led_ModeStrings[set_mode], SCT_CR);
	}
	else
	{
		sprintf((char *)lg_sct_resp_buf, "***Parameter Error! ***%s", SCT_CR);
	}
	sct_FlushRespBuf();

	sprintf((char *)lg_sct_resp_buf, "%s%s", SCT_SET_LDM_RESP, SCT_CR);
	sct_FlushRespBuf();
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
void sct_ProcessUnkownCommand(void)
{
	sprintf((char *)lg_sct_resp_buf, "%s%s%s", SCT_CR, SCT_UNKONWN_CMD_RESP, SCT_CR);
	sct_FlushRespBuf();
}
