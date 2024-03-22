/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file led_task.h
**
** Include file for led_task.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __LED_TASK_H
#define __LED_TASK_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include <stdbool.h>
#include "cmsis_os.h"
#include "stm32l0xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
/* Set to 0 to build for original prototype test jig */
#define LED_0165_BUILD_OPTION	1

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
	osMessageQId		led_event_queue;
	I2C_HandleTypeDef* 	i2c_device;
	TIM_HandleTypeDef*	timer_device;
} led_Init_t;

typedef enum
{
	led_1pps = 0,
	led_btn0,
	led_btn1,
	led_btn2,
	led_timer
} led_ChangeOn_t;

typedef enum
{
	led_all_off = 0,
	led_all,
	led_single,
	led_mix,
	led_typical
} led_Mode_t;

typedef enum led_Colours
{
	led_Off = 0,
	led_Green,
	led_Red,
	led_Yellow
} led_Colours_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void led_InitTask(led_Init_t init_data);
void led_Task(void const * argument);
void led_PostUpdateEvent(void);
led_Mode_t led_SetMode(led_Mode_t mode);
led_ChangeOn_t led_SetChangeEvent(led_ChangeOn_t change_event);

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
#ifdef __LED_TASK_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define LED_STROBE_DELAY_MS			500U

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
void led_Task0165TestBoard(void const * argument);
void led_TaskPrototpyeTestBoard(void const * argument);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
led_Init_t lg_led_init_data = {0};
bool lg_led_initialised = false;

#if LED_0165_BUILD_OPTION
led_Mode_t lg_led_current_mode = led_single;
#else
led_Mode_t lg_led_current_mode = led_mix;
#endif

int lg_led_current_change_on = led_1pps;

const char* led_ModeStrings[] = {
	"led_all_off",
	"led_all",
	"led_single",
	"led_mix",
	"led_typical"
};

const char* led_ChangeOnStrings[] = {
	"led_1pps",
	"led_btn0",
	"led_btn1",
	"led_btn2",
	"led_timer"
};

#endif /* __LED_TASK_C */

#endif /* __LED_TASK_H */
