/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file led_task.c
*
* Provides LED indication handling.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo None
*
******************************************************************************/
#define __LED_TASK_C

#include "led_task.h"
#include "led_driver.h"
#include "main.h"

/*****************************************************************************/
/**
* Initialise the LED task.
*
* @param    init_data    Initialisation data for the task
* @return   None
* @note     None
*
******************************************************************************/
void led_InitTask(led_Init_t init_data)
{
	lg_led_init_data.led_event_queue	= init_data.led_event_queue;
	lg_led_init_data.i2c_device 		= init_data.i2c_device;
	lg_led_init_data.timer_device		= init_data.timer_device;
	lg_led_initialised 					= true;
}

/*****************************************************************************/
/**
* LED task function.
*
* @param    argument not used
* @return   None
* @note     None
*
******************************************************************************/
void led_Task(void const * argument)
{
#if LED_0165_BUILD_OPTION
	led_Task0165TestBoard(argument);
#else
	led_TaskPrototpyeTestBoard(argument);
#endif
}

void led_Task0165TestBoard(void const * argument)
{
	int16_t current_led = 0;
	int16_t led_index[3] = {LD_0165_RED_LED_IDX, LD_0165_YELLOW_LED_IDX, LD_0165_GREEN_LED_IDX};
	osEvent event;

	ld_Init0165(lg_led_init_data.i2c_device);

	/* Infinite loop */
	for(;;)
	{
		event = osMessageGet(lg_led_init_data.led_event_queue, portMAX_DELAY);

		if (event.status == osEventMessage)
		{
			switch (lg_led_current_mode)
			{
			case led_single:
				{
					ld_SetLed0165(lg_led_init_data.i2c_device, led_index[current_led]);

					if (++current_led == LD_NO_0165_LEDS)
					{
						current_led = 0;
					}
				}
				break;

			case led_all_off:
			case led_all:
			case led_mix:
			case led_typical:
			default:
				break;
			}
		}
	}
}

void led_TaskPrototpyeTestBoard(void const * argument)
{
	int16_t strobe_colour = ld_Yellow;
	int16_t mix_start_colour = ld_Green;
	int16_t current_led = 0;
	osEvent event;

	ld_Init(lg_led_init_data.i2c_device);

	/* Infinite loop */
	for(;;)
	{
		event = osMessageGet(lg_led_init_data.led_event_queue, portMAX_DELAY);

		/* Just in case the device has been reset by a read of the PCA9500
		 * HCI device */
		ld_Init(lg_led_init_data.i2c_device);

		if (event.status == osEventMessage)
		{
			switch (lg_led_current_mode)
			{
			case led_all_off:
				{
					ld_SetAllLeds(lg_led_init_data.i2c_device, led_Off);
				}
				break;

			case led_single:
				{
					ld_SetLed(lg_led_init_data.i2c_device, current_led);

					if (++current_led == LD_NO_LEDS)
					{
						current_led = 0;
					}
				}
				break;

			case led_all:
				{
					switch (strobe_colour)
					{
					case led_Off:
						ld_SetAllLeds(lg_led_init_data.i2c_device, led_Off);
						strobe_colour = ld_Green;
						break;

					case ld_Green:
						ld_SetAllLeds(lg_led_init_data.i2c_device, ld_Green);
						strobe_colour = ld_Red;
						break;

					case ld_Red:
						ld_SetAllLeds(lg_led_init_data.i2c_device, ld_Red);
						strobe_colour = ld_Yellow;
						break;

					case ld_Yellow:
						ld_SetAllLeds(lg_led_init_data.i2c_device, ld_Yellow);
						strobe_colour = led_Off;
						break;

					default:
						strobe_colour = ld_Yellow;
						break;
					}
				}
				break;

			default:
			case led_mix:
				{
					ld_SetMixLeds(lg_led_init_data.i2c_device, mix_start_colour);

					if (++mix_start_colour > led_Yellow)
					{
						mix_start_colour = ld_Green;
					}
				}
				break;

			case led_typical:
				{
					ld_SetTypicalLeds(lg_led_init_data.i2c_device);
				}
				break;
			}
		}
	}
}

/*****************************************************************************/
/**
* Handle HAL EXTI GPIO Callback for push-buttons as these are used to change
* LED state
*
* @param    GPIO_Pin the GPIO pin that caused the interrupt
* @return   None
* @note     None
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	switch (GPIO_Pin)
	{
	case CS_1PPS_IN_Pin:
		if (lg_led_current_change_on == led_1pps)
		{
			osMessagePut(lg_led_init_data.led_event_queue, 0U, 0U);
		}
		break;

	case BTN0_IN_Pin:
		if (lg_led_current_change_on == led_btn0)
		{
			osMessagePut(lg_led_init_data.led_event_queue, 0U, 0U);
		}
		break;

	case BTN1_IN_Pin:
		if (lg_led_current_change_on == led_btn1)
		{
			osMessagePut(lg_led_init_data.led_event_queue, 0U, 0U);
		}
		break;

	case BTN2_IN_Pin:
		if (lg_led_current_change_on == led_btn2)
		{
			osMessagePut(lg_led_init_data.led_event_queue, 0U, 0U);
		}
		break;

	default:
		break;
	}
}


/*****************************************************************************/
/**
* Used by external tasks and interrupts to post an update event to the
* led_event_queue
*
* @param    None
* @return   None
* @note     None
*
******************************************************************************/
void led_PostUpdateEvent(void)
{
	osMessagePut(lg_led_init_data.led_event_queue, 0U, 0U);
}


/*****************************************************************************/
/**
* Used by external tasks and interrupts to set the LED flash mode
*
* @param    mode one of led_Mode_t enumerated values
* @return   mode after function call
* @note     None
*
******************************************************************************/
led_Mode_t led_SetMode(led_Mode_t mode)
{
	if ((mode >= led_all_off) && (mode <= led_typical))
	{
		lg_led_current_mode = mode;
	}

	return lg_led_current_mode;
}


/*****************************************************************************/
/**
* Used by external tasks and interrupts to set the LED flash mode
*
* @param    mode one of led_Mode_t enumerated values
* @return   mode after function call
* @note     None
*
******************************************************************************/
led_ChangeOn_t led_SetChangeEvent(led_ChangeOn_t change_event)
{
	if ((change_event >= led_1pps) &&
		(change_event <= led_timer))
	{
		lg_led_current_change_on = change_event;

		/* Only attempt to start/stop the time if the task is initialised */
		if (lg_led_initialised)
		{
			if (lg_led_current_change_on == led_timer)
			{
				HAL_TIM_Base_Start_IT(lg_led_init_data.timer_device);
			}
			else
			{
				HAL_TIM_Base_Stop_IT(lg_led_init_data.timer_device);
			}
		}
	}

	return lg_led_current_change_on;
}
