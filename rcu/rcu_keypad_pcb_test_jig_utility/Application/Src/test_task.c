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
#define __TEST_TASK_C

#include "test_task.h"
#include "version.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/*****************************************************************************/
/**
* Initialise the serial command task.
*
* @param    init_data initialisation data for the task
* @return   None
* @note     None
*
******************************************************************************/
void tt_InitTask(tt_Init_t init_data)
{
	memcpy((void *)&lg_tt_init_data, (void *)&init_data, sizeof(tt_Init_t));
	lg_tt_initialised = true;
}

/*****************************************************************************/
/**
* Serial command function.
*
* @param    argument not used
* @return   None
* @note     None
*
******************************************************************************/
void tt_TestTask(void const *argument)
{
	osEvent event;
	static uint8_t resp_buf[TT_MAX_BUF_SIZE] = {0U};

	if (!lg_tt_initialised)
	{
		for(;;)
		{
		}
	}

	HAL_TIMEx_PWMN_Start_IT(lg_tt_init_data.rcu_1pps_out_htim,
							lg_tt_init_data.rcu_1pps_out_channel);
  	HAL_Delay(100);

	for(;;)
	{
		osDelay(200);

		/* Just empty the queue, not doing anything with received data */
		event = osMessageGet(lg_tt_init_data.rx_data_queue, 0U);

		if (event.status == osEventMessage)
		{
		}

		/* Run the tests... */
		tt_PrintHeader(resp_buf);

	  	sprintf((char *)resp_buf, "%s*** KT-000-0147-00 Keypad Test Interface ***%s%s",
	  			SCT_CRLF, SCT_CRLF, SCT_CRLF);
	  	tt_FlushRespBuf(resp_buf);

	  	tt_PrintKeypadGpoState(resp_buf);

	  	sprintf((char *)resp_buf, "%s*** KT-000-0146-00 RCU Board Test Interface ***%s",
	  			SCT_CRLF, SCT_CRLF);
	  	tt_FlushRespBuf(resp_buf);

		tt_PrintRcuGpoState(resp_buf);
		tt_PrintRcuAopState(resp_buf);
		tt_PrintRcu1ppsTest(resp_buf);
		tt_PrintRcuXchangeUartTest(resp_buf);

		(void) osThreadYield();
	}
}


/*****************************************************************************/
/**
* Clear terminal, send the cursor home and print header block
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintHeader(uint8_t *resp_buf)
{
  	sprintf((char *)resp_buf, "%s%s", SCT_CLS, SCT_HOME);
  	tt_FlushRespBuf(resp_buf);
	sprintf((char *)resp_buf, "%s RCU and Keypad PCB Test Utility - V%d.%d.%d%s%s",
			SW_PART_NO, SW_VERSION_MAJOR, SW_VERSION_MINOR, SW_VERSION_BUILD,
			SCT_CRLF, SCT_CRLF);
	tt_FlushRespBuf(resp_buf);

  	sprintf((char *)resp_buf, "Run-time: %lu seconds%s%s", osKernelSysTick() / 1000U,
  			SCT_CRLF, SCT_CRLF);
  	tt_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Read and report Keypad Button Status
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintKeypadGpoState(uint8_t *resp_buf)
{
	int16_t i;

	for (i = 0; i < TT_KEYPAD_GPI_PIN_NUM; ++i)
	{
		sprintf((char *)resp_buf, "%s: %d%s",
				lg_tt_init_data.keypad_gpi_pins[i].name,
				(int) HAL_GPIO_ReadPin(	lg_tt_init_data.keypad_gpi_pins[i].port,
										lg_tt_init_data.keypad_gpi_pins[i].pin),
				SCT_CRLF);
		tt_FlushRespBuf(resp_buf);
	}
}


/*****************************************************************************/
/**
* Read and report RCU Discrete Output Status
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintRcuGpoState(uint8_t *resp_buf)
{
	int16_t i;

	sprintf((char *)resp_buf, "%s", SCT_CRLF);
	tt_FlushRespBuf(resp_buf);

	for (i = 0; i < TT_RCU_GPI_PIN_NUM; ++i)
	{
		sprintf((char *)resp_buf, "%s: %d%s",
				lg_tt_init_data.rcu_gpi_pins[i].name,
				(int) HAL_GPIO_ReadPin(	lg_tt_init_data.rcu_gpi_pins[i].port,
										lg_tt_init_data.rcu_gpi_pins[i].pin),
				SCT_CRLF);
		tt_FlushRespBuf(resp_buf);
	}
}


/*****************************************************************************/
/**
* Read and report RCU Analogue Output Status, performs averaging to filter
* the test data
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintRcuAopState(uint8_t *resp_buf)
{
	static int32_t adc_reading[TT_AOP_NUM_CHANNELS][TT_AOP_AVERAGE_LENGTH] = {0};
	static int16_t adc_reading_av_idx = 0;
	int32_t adc_reading_av[TT_AOP_NUM_CHANNELS] = {0};
	int32_t vref_ext = 0;
	int16_t i;
	int16_t j;

	/* Start the ADC sampling and perform calibration to improve result accuracy */
	HAL_ADCEx_Calibration_Start(lg_tt_init_data.rcu_aop_adc_hadc, ADC_SINGLE_ENDED);
	HAL_ADC_Start(lg_tt_init_data.rcu_aop_adc_hadc);

	/* Get a sample for each ADC channel and add it to the averaging buffer */
	for (i = 0; i < TT_AOP_NUM_CHANNELS; ++i)
	{
		HAL_ADC_PollForConversion(lg_tt_init_data.rcu_aop_adc_hadc, 10U);
		adc_reading[i][adc_reading_av_idx] = (int32_t)HAL_ADC_GetValue(
														lg_tt_init_data.rcu_aop_adc_hadc);
	}

	adc_reading_av_idx++;
	if (adc_reading_av_idx >= TT_AOP_AVERAGE_LENGTH)
	{
		adc_reading_av_idx = 0;
	}

	HAL_ADC_Stop(lg_tt_init_data.rcu_aop_adc_hadc);

	/* Calculate average values */
	for (i = 0; i < TT_AOP_NUM_CHANNELS; ++i)
	{
		for (j = 0; j < TT_AOP_AVERAGE_LENGTH; ++j)
		{
			adc_reading_av[i] += adc_reading[i][j];
		}

		adc_reading_av[i] /= TT_AOP_AVERAGE_LENGTH;
	}

	/* Use the Vrefint reading to calculate the Vrefext in mV */
	vref_ext = (TT_AOP_VREFINT_MV * (TT_AOP_ADC_BITS - 1)) /
				adc_reading_av[TT_AOP_VREF_INT_CHANNEL_IDX];

	/* Calculate scaled values */
	for (i = 0; i < TT_AOP_NUM_CHANNELS; ++i)
	{
		adc_reading_av[i] = (adc_reading_av[i] *
									TT_AOP_SCALE_FACTORS[i][TT_AOP_SCALE_MUL] * vref_ext) /
									TT_AOP_SCALE_FACTORS[i][TT_AOP_SCALE_DIV];
	}

	/* Perform error limit checking and output results */
	sprintf((char *)resp_buf, "RCU +3V3:\t%lu mV\t\t- %s%s",
			adc_reading_av[TT_AOP_RAIL_3V3_CHANNEL_IDX],
			AOP_ERROR_LIMIT_CHECK(	adc_reading_av[TT_AOP_RAIL_3V3_CHANNEL_IDX],
									TT_AOP_RAIL_3V3_CHANNEL_IDX),
			SCT_CRLF);
	tt_FlushRespBuf(resp_buf);

	sprintf((char *)resp_buf, "RCU +12V:\t%lu mV\t- %s%s",
			adc_reading_av[TT_AOP_RAIL_12V_CHANNEL_IDX],
			AOP_ERROR_LIMIT_CHECK(	adc_reading_av[TT_AOP_RAIL_12V_CHANNEL_IDX],
									TT_AOP_RAIL_12V_CHANNEL_IDX),
									SCT_CRLF);
	tt_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Check if the RCU Xchange 1PPS output is being detected
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintRcu1ppsTest(uint8_t *resp_buf)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(lg_tt_init_data.rcu_1pps_in_gpio_irq);
	uint32_t pps_delta = lg_tt_1pps_delta;
	uint32_t pps_previous = lg_tt_1pps_previous;
	HAL_NVIC_EnableIRQ(lg_tt_init_data.rcu_1pps_in_gpio_irq);
	uint32_t now = osKernelSysTick();

	if ((now - pps_previous) > TT_1PPS_DELTA_MAX)
	{
		sprintf((char *)resp_buf, "%sRCU Xchange 1PPS NOT detected\t- FAIL%s",
				SCT_CRLF, SCT_CRLF);
		tt_FlushRespBuf(resp_buf);
	}
	else
	{
		sprintf((char *)resp_buf, "%sRCU Xchange 1PPS delta: %lu ms\t- PASS%s",
				SCT_CRLF, pps_delta, SCT_CRLF);
		tt_FlushRespBuf(resp_buf);
	}
}


/*****************************************************************************/
/**
* Perform loopback test on the Xchange UART, test passes if
* TT_XC_LB_UART_TEST_LENGTH last echoes were received correctly
*
* @param    resp_buf data buffer for sending tx data to UART
* @return   None
* @note     None
*
******************************************************************************/
void tt_PrintRcuXchangeUartTest(uint8_t *resp_buf)
{
	static bool test_history[TT_XC_LB_UART_TEST_LENGTH];
	static int16_t test_history_idx = 0;
	uint8_t tx_val = (uint8_t)(rand() & 0xFFU);
	uint8_t rx_val = tx_val + 0xA5;	/* Ensure the rx_val isn't equal to tx_val */
	uint32_t later = osKernelSysTick() + TT_XC_LB_UART_TEST_TIMEOUT_MS;
	int16_t i;
	bool overall_result = true;

	if (HAL_UART_Transmit(lg_tt_init_data.xchange_huart, &tx_val, 1U, 1U) == HAL_OK)
	{
		while (osKernelSysTick() < later)
		{
			if (HAL_UART_Receive(lg_tt_init_data.xchange_huart, &rx_val, 1U, 1U) == HAL_OK)
			{
				if (rx_val == tx_val)
				{
					break;
				}
			}
		}
	}

	if (rx_val == tx_val)
	{
      test_history[test_history_idx++] = true;
	}
	else
	{
		test_history[test_history_idx++] = false;
	}

	if (test_history_idx >= TT_XC_LB_UART_TEST_LENGTH)
	{
		test_history_idx = 0;
	}

	for (i = 0; i < TT_XC_LB_UART_TEST_LENGTH; ++i)
	{
		overall_result &= test_history[i];
	}

	sprintf((char *)resp_buf, "%sRCU Xchange UART loopback test\t- %s%s",
			SCT_CRLF, (overall_result ? "PASS" : "FAIL"), SCT_CRLF);
	tt_FlushRespBuf(resp_buf);
}


/*****************************************************************************/
/**
* Flush contents of response buffer to tx queue.
*
* @param    resp_buf data buffer to flush to tx queue
* @return   None
* @note     None
*
******************************************************************************/
void tt_FlushRespBuf(uint8_t *resp_buf)
{
	int16_t i = 0;

	while ((resp_buf[i] != '\0')  && (i < TT_MAX_BUF_SIZE))
	{
		osMessagePut(lg_tt_init_data.tx_data_queue, (uint32_t)resp_buf[i], 0U);
		++i;
	}
}


/*****************************************************************************/
/**
* Handle HAL EXTI GPIO Callback as these are used to monitor presence of 1PPS
* input signal
*
* @param    argument    Not used
* @return   None
* @note     None
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	volatile uint32_t now = osKernelSysTick();

	if (lg_tt_initialised)
	{
		if (GPIO_Pin == lg_tt_init_data.rcu_1pps_in_gpio_pin)
		{
			lg_tt_1pps_delta = now - lg_tt_1pps_previous;
			lg_tt_1pps_previous = now;
		}
	}
}
