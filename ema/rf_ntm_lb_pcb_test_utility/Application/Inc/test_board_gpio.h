/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
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
bool tbg_RxPowerEnable(tbg_TestBoardGpio_t* p_inst, bool enable);
bool tbg_ReadBoardId(tbg_TestBoardGpio_t *p_inst, uint16_t *p_board_id);
bool tbg_ReadLockDetects(tbg_TestBoardGpio_t *p_inst, bool *p_ld1, bool *p_ld2);
bool tbg_SetSynthSelect(tbg_TestBoardGpio_t *p_inst, tbg_SynthRange_t synth);
bool tbg_SetPreselectorPath(tbg_TestBoardGpio_t *p_inst, uint16_t presel);
bool tbg_SetRfAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten);
bool tbg_SetIfAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten);
bool tbg_SetLnaBypass(tbg_TestBoardGpio_t *p_inst, bool bypass);
const char **iad_GetPreselectorStr(void);


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
#ifdef __TEST_BOARD_GPIO_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define TBG_RX_PWR_EN_EXP		0
#define TBG_RX_PWR_EN_PIN		IGD_GPIO_PIN_9
#define TBG_BOARD_ID_EXP		0
#define TBG_BOARD_ID_PINS		(IGD_GPIO_PIN_15 | IGD_GPIO_PIN_14 | IGD_GPIO_PIN_13 | IGD_GPIO_PIN_12 | IGD_GPIO_PIN_11)
#define TBG_BOARD_ID_SHIFT		11
#define TBG_SYNTH_LD1_EXP		0
#define TBG_SYNTH_LD1_PIN		IGD_GPIO_PIN_6
#define TBG_SYNTH_LD2_EXP		0
#define TBG_SYNTH_LD2_PIN		IGD_GPIO_PIN_7
#define TBG_SYNTH_SEL_EXP		1
#define TBG_SYNTH_SEL_PIN		IGD_GPIO_PIN_4
#define TBG_PRESEL_EXP			1
#define TBG_PRESEL_PINS			(IGD_GPIO_PIN_15 | IGD_GPIO_PIN_14 | IGD_GPIO_PIN_13)
#define TBG_PRESEL_SHIFT		13
#define	TBG_PRESEL_MIN_VAL		0U
#define	TBG_PRESEL_MAX_VAL		7U
#define TBG_RF_ATTEN_EXP		1
#define TBG_RF_ATTEN_PINS		(IGD_GPIO_PIN_10 | IGD_GPIO_PIN_9 | IGD_GPIO_PIN_8 | IGD_GPIO_PIN_7 | IGD_GPIO_PIN_6 | IGD_GPIO_PIN_5)
#define TBG_RF_ATTEN_SHIFT		5
#define	TBG_RF_ATTEN_MIN_VAL	0U
#define	TBG_RF_ATTEN_MAX_VAL	63U
#define TBG_IF_ATTEN_EXP		0
#define TBG_IF_ATTEN_PINS		(IGD_GPIO_PIN_5 | IGD_GPIO_PIN_4 | IGD_GPIO_PIN_3 | IGD_GPIO_PIN_2 | IGD_GPIO_PIN_1 | IGD_GPIO_PIN_0)
#define TBG_IF_ATTEN_SHIFT		0
#define	TBG_IF_ATTEN_MIN_VAL	0U
#define	TBG_IF_ATTEN_MAX_VAL	63U
#define TBG_LNA_BYPASS_EXP		1
#define TBG_LNA_BYPASS_PIN		IGD_GPIO_PIN_12


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


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
const uint8_t 	lg_tbg_gpio_exp_i2c_addr[TBG_NO_I2C_EXPANDERS] 			= {0x27U << 1, 	0x26U << 1,	0x25U << 1};
const uint16_t  lg_tbg_gpio_exp_io_dir_mask[TBG_NO_I2C_EXPANDERS] 		= {0xF5C0U, 	0x080FU, 	0x0000U};
const uint16_t  lg_tbg_gpio_exp_default_op_mask[TBG_NO_I2C_EXPANDERS] 	= {0x0000U, 	0x0000U, 	0x0000U};

const char *lg_tbg_presel_str[TBG_PRESEL_MAX_VAL + 1] = \
{
	"20-80 MHz",
	"80-130 MHz",
	"130-180 MHz",
	"180-280 MHz",
	"280-420 MHz",
	"400-470 MHz",
	"470-520 MHz",
	"Isolation"
};

#endif /* __TEST_BOARD_GPIO_C*/

#endif /* __TEST_BOARD_GPIO_H */
