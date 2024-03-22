/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
**
** @file keypad_test_board.h
**
** Include file for keypad_test_board.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __KEYPAD_TEST_BOARD_H
#define __KEYPAD_TEST_BOARD_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l0xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define KTB_NO_BUTTONS	4

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
typedef struct ktb_KeypadTestBoard
{
	I2C_HandleTypeDef	*i2c_device;
	uint16_t			i2c_address;
	GPIO_TypeDef 		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	bool 				initialised;
} ktb_KeypadTestBoard_t;

typedef enum
{
	ktb_btn_power = 0,
	ktb_btn_0,
	ktb_btn_1,
	ktb_btn_2,
	ktb_no_buttons
} ktb_Buttons_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ktb_InitInstance(	ktb_KeypadTestBoard_t *p_inst,
						I2C_HandleTypeDef *i2c_device,
						uint16_t i2c_address,
						GPIO_TypeDef *i2c_reset_gpio_port,
						uint16_t i2c_reset_gpio_pin);
bool ktb_InitDevice(ktb_KeypadTestBoard_t *p_inst);
void ktb_DisableDevice(ktb_KeypadTestBoard_t *p_inst);
bool ktb_SetAllButtons(ktb_KeypadTestBoard_t *p_inst, bool assert);
bool ktb_SetButton(ktb_KeypadTestBoard_t *p_inst, ktb_Buttons_t btn, bool assert);
const char **ktb_GetButtonNames(void);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __KEYPAD_TEST_BOARD_H */
