/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file test_board_gpio.h
**
** Include file for test_board_gpio.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __TEST_BOARD_GPIO_H
#define __TEST_BOARD_GPIO_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>
#include "i2c_gpio_driver.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define TBG_NO_I2C_EXPANDERS	3

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
typedef struct
{
	igd_I2cGpioDriver_t i2c_gpio_exp[TBG_NO_I2C_EXPANDERS];
	bool 				initialised;
} tbg_TestBoardGpio_t;

typedef enum
{
	tbg_Synth1 = 1,
	tbg_Synth2
} tbg_SynthRange_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void tbg_Init(	tbg_TestBoardGpio_t	*p_inst,
				I2C_HandleTypeDef	*i2c_device,
				GPIO_TypeDef		*i2c_reset_gpio_port,
				uint16_t 			i2c_reset_gpio_pin);
bool tbg_ReadBoardId(tbg_TestBoardGpio_t *p_inst, uint16_t *p_board_id);
bool tbg_SetDdsAtten(tbg_TestBoardGpio_t *p_inst, bool atten);
bool tbg_SetTxFineAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten);
bool tbg_SetTxFCoarseAtten(tbg_TestBoardGpio_t *p_inst, bool atten);
bool tbg_SetRxLnaBypass(tbg_TestBoardGpio_t *p_inst, bool bypass);
bool tbg_SetRxPath(tbg_TestBoardGpio_t *p_inst, uint16_t rx_presel);
const char **tbg_GetRxPathStr(void);
bool tbg_SetTxPath(tbg_TestBoardGpio_t *p_inst, uint16_t tx_path);
const char **tbg_GetTxPathStr(void);
bool tbg_RxEnable(tbg_TestBoardGpio_t* p_inst, bool enable);
bool tbg_TxEnable(tbg_TestBoardGpio_t* p_inst, bool enable);
bool tbg_SetXcvrTxPath(tbg_TestBoardGpio_t *p_inst, uint16_t tx_path);
const char **tbg_GetXcvrTxPathStr(void);
bool tbg_XcvrReset(tbg_TestBoardGpio_t* p_inst, bool reset);
bool tbg_XcvrReadGpInterrupt(tbg_TestBoardGpio_t *p_inst, bool *p_gp_interrupt);
bool tbg_AssertSynthChipSelect(tbg_TestBoardGpio_t *p_inst, bool assert);
bool tbg_ReadSynthLockDetect(tbg_TestBoardGpio_t *p_inst, bool *p_lock_detect);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __TEST_BOARD_GPIO_H */
