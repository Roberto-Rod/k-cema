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
bool tbg_ReadBoardId(tbg_TestBoardGpio_t *p_inst, uint16_t *p_board_id);
bool tbg_SetDdsAtten(tbg_TestBoardGpio_t *p_inst, bool atten);
bool tbg_SetTxFineAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten);
bool tbg_SetTxFCoarseAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten);
bool tbg_SetRxLnaBypass(tbg_TestBoardGpio_t *p_inst, bool bypass);
bool tbg_SetRxPreselectorPath(tbg_TestBoardGpio_t *p_inst, uint16_t rx_presel);
const char **tbg_GetRxPreselectorPathStr(void);
bool tbg_SetTxPath(tbg_TestBoardGpio_t *p_inst, uint16_t tx_path);
const char **tbg_GetTxPathStr(void);
bool tbg_RxEnable(tbg_TestBoardGpio_t* p_inst, bool enable);
bool tbg_TxEnable(tbg_TestBoardGpio_t* p_inst, bool enable);
bool tbg_XcvrReset(tbg_TestBoardGpio_t* p_inst, bool reset);
bool tbg_ReadGpInterrupt(tbg_TestBoardGpio_t *p_inst, bool *p_gp_interrupt);

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
#define TBG_BOARD_ID_EXP		0
#define TBG_BOARD_ID_PINS		(IGD_GPIO_PIN_15 | IGD_GPIO_PIN_14 | IGD_GPIO_PIN_13 | IGD_GPIO_PIN_12 | IGD_GPIO_PIN_11)
#define TBG_BOARD_ID_SHIFT		11

#define TBG_TX_ATT_DDS_EXP	0
#define TBG_TX_ATT_DDS_PIN	IGD_GPIO_PIN_0

#define TBG_TX_ATT_FINE_EXP		0
#define TBG_TX_ATT_FINE_PINS	(IGD_GPIO_PIN_5 | IGD_GPIO_PIN_4 | IGD_GPIO_PIN_3 | IGD_GPIO_PIN_2 | IGD_GPIO_PIN_1)
#define TBG_TX_ATT_FINE_SHIFT	1
#define	TBG_TX_ATT_FINE_MIN_VAL	0U
#define	TBG_TX_ATT_FINE_MAX_VAL	31U

#define TBG_TX_ATT_COARSE_EXP		0
#define TBG_TX_ATT_COARSE_PINS_LO	(IGD_GPIO_PIN_7 | IGD_GPIO_PIN_6)
#define TBG_TX_ATT_COARSE_SHIFT_LO	6
#define TBG_TX_ATT_COARSE_PINS_HI	(IGD_GPIO_PIN_10 | IGD_GPIO_PIN_9)
#define TBG_TX_ATT_COARSE_SHIFT_HI	7
#define	TBG_TX_ATT_COARSE_MIN_VAL	0U
#define	TBG_TX_ATT_COARSE_MAX_VAL	15U

#define TBG_LNA_BYPASS_EXP		1
#define TBG_LNA_BYPASS_PIN		IGD_GPIO_PIN_0

#define TBG_RX_PATH_EXP			1
#define TBG_RX_PATH_PINS		(IGD_GPIO_PIN_3 | IGD_GPIO_PIN_2 | IGD_GPIO_PIN_1)
#define TBG_RX_PATH_SHIFT		1
#define	TBG_RX_PATH_MIN_VAL		0U
#define	TBG_RX_PATH_MAX_VAL		7U

#define TBG_TX_PATH_EXP			1
#define TBG_TX_PATH_PINS		(IGD_GPIO_PIN_7 | IGD_GPIO_PIN_6 | IGD_GPIO_PIN_5 | IGD_GPIO_PIN_4)
#define TBG_TX_PATH_SHIFT		4
#define	TBG_TX_PATH_MIN_VAL		0U
#define	TBG_TX_PATH_MAX_VAL		15U

#define TBG_RX_EN_EXP			2
#define TBG_RX_EN_PIN			IGD_GPIO_PIN_0

#define TBG_TX_EN_EXP			2
#define TBG_TX_EN_PIN			IGD_GPIO_PIN_1

#define TBG_XCVR_RESET_N_EXP	2
#define TBG_XCVR_RESET_N_PIN	IGD_GPIO_PIN_2

#define TBG_GP_INTERRUPT_EXP	2
#define TBG_GP_INTERRUPT_PIN	IGD_GPIO_PIN_3

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
const uint16_t  lg_tbg_gpio_exp_io_dir_mask[TBG_NO_I2C_EXPANDERS] 		= {0xF800U, 	0xFF00U, 	0xFFF8U}; /* '1' = ip; '0' = op */
const uint16_t  lg_tbg_gpio_exp_io_pu_mask[TBG_NO_I2C_EXPANDERS]		= {0xFFFFU, 	0xFFFFU, 	0xFFFFU}; /* '1' = en; '0' = dis */
const uint16_t  lg_tbg_gpio_exp_default_op_mask[TBG_NO_I2C_EXPANDERS] 	= {0x0000U, 	0x0000U, 	0x0000U};

const char *lg_tbg_rx_presel_str[TBG_RX_PATH_MAX_VAL + 1] = \
{
	"400-600 MHz",
	"600-1000 MHz",
	"1000-1400 MHz",
	"1400-2200 MHz",
	"2200-3000 MHz",
	"3000-4600 MHz",
	"4600-6000 MHz",
	"Isolation"
};

const char *lg_tbg_tx_path_str[TBG_TX_PATH_MAX_VAL + 1] = \
{
	"MB: 400-1500 MHz",
	"MB: 1400-1880 MHz",
	"MB: 1850-2250 MHz",
	"MB: 2250-2500 MHz",
	"MB: 2500-2700 MHz",
	"MB: 2700-3000 MHz",
	"Invalid Band 0",
	"Invalid Band 1",
	"HB: 2400-3400 MHz",
	"HB: 3400-4600 MHz",
	"HB: 4600-6000 MHz",
	"Invalid Band 2",
	"Invalid Band 3",
	"Invalid Band 4",
	"Invalid Band 5",
	"Invalid Band 6"
};

#endif /* __TEST_BOARD_GPIO_C*/

#endif /* __TEST_BOARD_GPIO_H */
