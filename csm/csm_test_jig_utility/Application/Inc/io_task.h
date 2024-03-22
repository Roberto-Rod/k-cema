/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file io_task.h
**
** Include file for io_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __IO_TASK_H
#define __IO_TASK_H

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
#define IOT_ANALOGUE_READINGS_NUM			13
#define IOT_ANALOGUE_READING_NAME_MAX_LEN	32

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
typedef struct iot_Init
{
	I2C_HandleTypeDef	*i2c_device;
	GPIO_TypeDef		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	TIM_HandleTypeDef 	*csm_1pps_out_htim;
	uint32_t 			csm_1pps_out_channel;
	uint16_t			csm_1pps_in_gpio_pin;
	int16_t				csm_1pps_in_gpio_irq;
} iot_Init_t;

typedef enum iot_GpoPinId
{
	csm_slave_1pps_dir = 0,
	select_1pps_s0,
	select_1pps_s1,
	csm_master_cable_det,
	tamper_sw,
	som_sd_boot_en,
	rcu_pwr_btn,
	rcu_pwr_en_zer,
	keypad_pwr_btn,
	keypad_pwr_en_zer,
	select_uart_s0,
	rcu_1pps_dir,
	remote_pwr_on_in
} iot_GpoPinId_t;

typedef enum ot_GpiPinId
{
	csm_master_rack_addr = 0,
	csm_slave_rack_addr
} iot_GpiPinId_t;

typedef enum iot_GpioPinState
{
	reset = 0,
	set
} iot_GpioPinState_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void iot_InitTask(iot_Init_t init_data);
void iot_IoTask(void const *argument);
iot_GpioPinState_t iot_GetGpiPinState(iot_GpiPinId_t pin_id, const char **p_chanel_name);
void iot_SetGpoPinState(iot_GpoPinId_t pin_id, iot_GpioPinState_t pin_state);
void iot_Enable1PpsOp(bool enable);
bool iot_PpsDetected(uint32_t *p_pps_delta);
void iot_UartStartStringSearch(void);
bool iot_UartIsStringFound(void);
void iot_GetAnalogueReading(int16_t analogue_reading_no,
							uint16_t *p_analgoue_reading,
							const char **p_analogue_reading_name);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/

extern const char *IOT_UART_EXPECTED_STRING;

#endif /* __IO_TASK_H */
