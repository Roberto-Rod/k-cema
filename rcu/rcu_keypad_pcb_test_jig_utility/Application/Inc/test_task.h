/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file test_task.h
**
** Include file for test_task.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __TEST_TASK_H
#define __TEST_TASK_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include <stdbool.h>
#include "cmsis_os.h"
#include "stm32l4xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define TT_KEYPAD_GPI_PIN_NUM 		4
#define TT_RCU_GPI_PIN_NUM			3
#define TT_GPIO_PIN_NAME_MAX_LEN	32

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
	GPIO_TypeDef	*port;
	uint16_t		pin;
	char			name[TT_GPIO_PIN_NAME_MAX_LEN];
} tt_GpioSignal;

typedef struct
{
	osMessageQId 		tx_data_queue;
	osMessageQId 		rx_data_queue;
	UART_HandleTypeDef* xchange_huart;
	TIM_HandleTypeDef 	*rcu_1pps_out_htim;
	uint32_t 			rcu_1pps_out_channel;
	uint16_t			rcu_1pps_in_gpio_pin;
	int16_t				rcu_1pps_in_gpio_irq;
	ADC_HandleTypeDef *	rcu_aop_adc_hadc;
	tt_GpioSignal		keypad_gpi_pins[TT_KEYPAD_GPI_PIN_NUM];
	tt_GpioSignal		rcu_gpi_pins[TT_RCU_GPI_PIN_NUM];
} tt_Init_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void tt_InitTask(tt_Init_t init_data);
void tt_TestTask(void const *argument);

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
#ifdef __TEST_TASK_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define TT_MAX_BUF_SIZE		256

/* Some basic ASCII and ANSI terminal control codes */
#define SCT_CRLF                "\r\n"          /* Carriage return & line feed */
#define SCT_CR                  "\r"            /* Carriage return only */
#define SCT_LF                  "\n"            /* New line only */
#define SCT_TAB                 "\t"            /* Horizontal tab */
#define SCT_CLS                 "[2J"          /* Clear screen */
#define SCT_CL                  "[K"           /* Clear from cursor to end of line */
#define SCT_ERASE_LINE          "[2K"
#define SCT_HOME                "[H"           /* Move cursor to top corner */
#define SCT_LINE_HOME           "[1000D"       /* Assumes the current line isn't longer than 1000 characters! */
#define SCT_RESETSCREEN         "[0;37;40m" CLS HOME
#define SCT_REDTEXT             "[0;1;31m"
#define SCT_YELLOWTEXT          "[0;1;33m"
#define SCT_GREENTEXT           "[0;1;32m"
#define SCT_WHITETEXT           "[0;1;37m"
#define SCT_DEFAULTTEXT         WHITETEXT
#define SCT_FLASHTEXT           "[5m"
#define SCT_UNDERLINETEXT       "[4m"
#define SCT_RESETTEXTATTRIBUTES "[0m"
#define SCT_ENTER               13
#define SCT_ESC                 27
#define SCT_BACKSPACE           8
#define SCT_UP_ARROW            24

/* 1PPS accuracy limits */
#define TT_1PPS_DELTA_MIN		999U
#define TT_1PPS_DELTA_MAX		1001U

/* Xchange UART loopbac test definitions */
#define TT_XC_LB_UART_TEST_LENGTH		10
#define TT_XC_LB_UART_TEST_TIMEOUT_MS	10U

/* ADC channel definitions */
#define TT_AOP_NUM_CHANNELS				3
#define TT_AOP_AVERAGE_LENGTH			5
#define TT_AOP_VREF_MV					3300
#define TT_AOP_VREFINT_MV				1210
#define TT_AOP_ADC_BITS					4096
#define TT_AOP_VREF_INT_CHANNEL_IDX		0
#define TT_AOP_RAIL_3V3_CHANNEL_IDX		1
#define TT_AOP_RAIL_12V_CHANNEL_IDX		2
#define TT_AOP_SCALE_MUL				0
#define TT_AOP_SCALE_DIV				1
#define TT_AOP_ERROR_LOW				0
#define TT_AOP_ERROR_HIGH				1

static const int32_t TT_AOP_SCALE_FACTORS[TT_AOP_NUM_CHANNELS][2] =
{
		{1, TT_AOP_ADC_BITS},			/* Vrefint multiplier and divider */
		{3, TT_AOP_ADC_BITS},	/* +3V3 rail multiplier and divider */
		{11, TT_AOP_ADC_BITS}	/* +12V rail multiplier and divider */
};

static const int32_t TT_AOP_ERROR_LIMTS[TT_AOP_NUM_CHANNELS][2] =
{
		{1180, 1240},	/* Vrefint */
		{3100, 3500},	/* +3V3 */
		{11500, 12500}	/* +12V */
};

#define AOP_ERROR_LIMIT_CHECK(val, ch) ((val >= TT_AOP_ERROR_LIMTS[ch][TT_AOP_ERROR_LOW]) && \
										(val <= TT_AOP_ERROR_LIMTS[ch][TT_AOP_ERROR_HIGH]) ? \
										"PASS" : "FAIL")

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
void tt_PrintHeader(uint8_t *resp_buf);
void tt_PrintKeypadGpoState(uint8_t *resp_buf);
void tt_PrintRcuGpoState(uint8_t *resp_buf);
void tt_PrintRcuAopState(uint8_t *resp_buf);
void tt_PrintRcu1ppsTest(uint8_t *resp_buf);
void tt_PrintRcuXchangeUartTest(uint8_t *resp_buf);
void tt_FlushRespBuf(uint8_t *resp_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
tt_Init_t lg_tt_init_data = {0};
bool lg_tt_initialised = false;
uint8_t lg_sct_cmd_buf[TT_MAX_BUF_SIZE] = {0U};
volatile uint32_t lg_tt_1pps_delta = 0U;
volatile uint32_t lg_tt_1pps_previous = 0U;

#endif /* __SERIAL_CMD_TASK_C */

#endif /* __SERIAL_CMD_TASK_H */
