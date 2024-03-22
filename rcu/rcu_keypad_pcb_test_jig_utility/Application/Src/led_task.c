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
#include "led_driver_pwm.h"
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
	lg_led_init_data.i2c_device 		= init_data.i2c_device;
	lg_led_init_data.i2c_reset_pin_port	= init_data.i2c_reset_pin_port;
	lg_led_init_data.i2c_reset_pin		= init_data.i2c_reset_pin;
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
	int16_t strobe_colour = ld_Yellow;
	uint32_t previous_wake_time;
	ld_SetAllLeds_t p_set_all_leds_func = NULL;

	previous_wake_time = osKernelSysTick();

	/* Infinite loop */
	for(;;)
	{
		(void) osDelayUntil(&previous_wake_time, LED_CHANGE_COLOUR_DELAY_MS);

		/* Try to initialise LED GPIO driver using MCP23017 for Rev D.x and older boards,
		 * if this fails try initialising LED PWM driver using PCA9685 for Rev E.x and
		 * newer boards.
		 * Use the set all LEDs function for the drier that initialises successfully. */
		if (ld_Init(lg_led_init_data.i2c_device,
					lg_led_init_data.i2c_reset_pin_port,
					lg_led_init_data.i2c_reset_pin))
		{
			p_set_all_leds_func = ld_SetAllLeds;
		}
		else if(ldp_Init(lg_led_init_data.i2c_device,
						 lg_led_init_data.i2c_reset_pin_port,
						 lg_led_init_data.i2c_reset_pin))
		{
			p_set_all_leds_func = ldp_SetAllLeds;
		}
		else
		{
			p_set_all_leds_func = NULL;
		}

		if (p_set_all_leds_func != NULL)
		{
			switch (strobe_colour)
			{
			case led_Off:
				p_set_all_leds_func(lg_led_init_data.i2c_device, led_Off);
				strobe_colour = ld_Green;
				break;

			case ld_Green:
				p_set_all_leds_func(lg_led_init_data.i2c_device, ld_Green);
				strobe_colour = ld_Red;
				break;

			case ld_Red:
				p_set_all_leds_func(lg_led_init_data.i2c_device, ld_Red);
				strobe_colour = ld_Yellow;
				break;

			case ld_Yellow:
				p_set_all_leds_func(lg_led_init_data.i2c_device, ld_Yellow);
				strobe_colour = led_Off;
				break;

			default:
				strobe_colour = ld_Yellow;
				break;
			}
		}
	}
}

