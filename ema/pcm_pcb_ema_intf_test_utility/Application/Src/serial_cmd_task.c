/*****************************************************************************/
/**
** Copyright 2020 Davies Systems Ltd & Kirintec Ltd. All rights reserved.
*
* @file serial_cmd_task.c
*
* Provides serial command task handling.
* <br><br>
* Processes received serial bytes and converts them to commands, performs
* command error handling.
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
	lg_sct_initialised = true;
}


/*****************************************************************************/
/**
* Process bytes received from the EMA UART interface
*
* @param    argument    Not used
* @return   None
* @note     None
*
******************************************************************************/
void sct_SerialCmdEmaTask(void const *argument)
{
	osEvent event;

	for(;;)
	{
		event = osMessageGet(lg_sct_init_data.ema_rx_data_queue, osWaitForever);

		/* Handle echoing of bytes from EMA to PC interface if echo is enabled */
		if (lg_sct_uart_echo_enabled)
		{
			osMessagePut(lg_sct_init_data.pc_tx_data_queue, event.value.v, 1U);
		}
	}
}


/*****************************************************************************/
/**
* Process bytes received from the PC UART interface
*
* @param    argument    Not used
* @return   None
* @note     None
*
******************************************************************************/
void sct_SerialCmdTask(void const *argument)
{
	static uint8_t resp_buf[SCT_MAX_BUF_SIZE] = {0U};
	uint8_t curr_pc_byte = 0U;
	uint8_t last_pc_byte = 0U;
	osEvent event;

	if (!lg_sct_initialised)
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
	sprintf((char *)resp_buf, "'^o'/'^O' - toggle Power Off signal%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
	sprintf((char *)resp_buf, "'^p'/'^P' - toggle 1PPS signal on/off%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
	sprintf((char *)resp_buf, "'^r'/'^R' - toggle RF Mute signal%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);
	sprintf((char *)resp_buf, "'^u'/'^U' - toggle EMA UART echo on/off%s", SCT_CRLF);
	sct_FlushRespBuf(resp_buf);

	for(;;)
	{
		event = osMessageGet(lg_sct_init_data.pc_rx_data_queue, osWaitForever);

		curr_pc_byte = (uint8_t)event.value.v;

		/* If the last character received was a '^' then see if the current character
		 * is a command that needs to be processed... */
		if (last_pc_byte == '^')
		{
			if ((curr_pc_byte == 'o') || (curr_pc_byte== 'O'))
			{
				HAL_GPIO_TogglePin(	lg_sct_init_data.dop_power_off_pin_port,
									lg_sct_init_data.dop_power_off_pin);

				sprintf((char *)resp_buf, "Toggling Power Off pin - %s%s",
						(HAL_GPIO_ReadPin(	lg_sct_init_data.dop_power_off_pin_port,
											lg_sct_init_data.dop_power_off_pin) == GPIO_PIN_RESET ? "ON" : "OFF"),
						SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
			else if ((curr_pc_byte == 'r') || (curr_pc_byte == 'R'))
			{
				HAL_GPIO_TogglePin(	lg_sct_init_data.dop_rf_mute_pin_port,
									lg_sct_init_data.dop_rf_mute_pin);

				sprintf((char *)resp_buf, "Toggling RF Mute pin - %s%s",
						(HAL_GPIO_ReadPin(	lg_sct_init_data.dop_rf_mute_pin_port,
											lg_sct_init_data.dop_rf_mute_pin) == GPIO_PIN_RESET ? "UNMUTE" : "MUTE"),
						SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
			else if ((curr_pc_byte == 'u') || (curr_pc_byte == 'U'))
			{
				lg_sct_uart_echo_enabled = !lg_sct_uart_echo_enabled;

				sprintf((char *)resp_buf, "UART echo %s...%s",
						(lg_sct_uart_echo_enabled ? "Enabled" : "Disabled"), SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
			else if ((curr_pc_byte == 'p') || (curr_pc_byte == 'P'))
			{
				if (lg_sct_1pps_enabled)
				{
					HAL_TIMEx_PWMN_Stop_IT(lg_sct_init_data.htim_1pps, lg_sct_init_data.tim_channel_1pps);
					lg_sct_1pps_enabled = false;
				}
				else
				{
					HAL_TIMEx_PWMN_Start_IT(lg_sct_init_data.htim_1pps, lg_sct_init_data.tim_channel_1pps);
					lg_sct_1pps_enabled = true;
				}

				sprintf((char *)resp_buf, "1PPS Output %s...%s",
						(lg_sct_1pps_enabled ? "Enabled" : "Disabled"), SCT_CRLF);
				sct_FlushRespBuf(resp_buf);
			}
		}

		last_pc_byte = curr_pc_byte;

		/* Handle echoing of bytes from PC to EMA interface if echo is enabled */
		if (lg_sct_uart_echo_enabled)
		{
			osMessagePut(lg_sct_init_data.ema_tx_data_queue, event.value.v, 1U);
		}
	}
}


/*****************************************************************************/
/**
* Flush contents of response buffer to PC UART tx queue
*
* @param    resp_buf data buffer to flush to PC UART tx queue
* @return   None
* @note     None
*
******************************************************************************/
void sct_FlushRespBuf(uint8_t *resp_buf)
{
	int16_t i = 0;

	while ((resp_buf[i] != '\0')  && (i < SCT_MAX_BUF_SIZE))
	{
		osMessagePut(lg_sct_init_data.pc_tx_data_queue, (uint32_t)resp_buf[i], 0U);
		++i;
	}
}
