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
#include "hw_config_info.h"
#include "cmsis_os.h"
#include "stm32l4xx_hal.h"

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define IOT_ANALOGUE_READINGS_NUM			21
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
	osMutexId			i2c_mutex;
	GPIO_TypeDef		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	TIM_HandleTypeDef 	*csm_1pps_out_htim;
	uint32_t 			csm_1pps_out_channel;
	TIM_HandleTypeDef 	*fan_tacho_out_htim;
	uint32_t 			fan_tacho_out_channel;
	TIM_HandleTypeDef   *fan_pwm_htim;
	uint16_t			csm_1pps_in_gpio_pin;
	int16_t				csm_1pps_in_gpio_irq;
} iot_Init_t;

typedef enum
{
	tamper_sw_buzzer = 0,
	rcu_pwr_btn,
	som_sd_boot_en,
	rcu_pwr_en_zer_out,
	select_i2c_s0,
	select_i2c_s1,
    ms_1pps_dir_ctrl,
    select_1pps_s0,
    select_1pps_s1,
    select_1pps_s2,
    select_1pps_s3,
    ms_pwr_en_in,
    ms_master_n,
    test_point_1,
    test_point_2,
    ms_rf_mute_n_out,
    ms_rf_mute_dir,
    select_fan_pwm_s0,
    select_fan_pwm_s1,
    select_fan_pwm_s2,
	gpo_pin_qty
} iot_GpoPinId_t;

typedef enum
{
    ntm1_fan_alert,
    ntm2_fan_alert,
    ntm3_fan_alert,
    ntm1_rf_mute_n,
    ntm2_rf_mute_n,
    ntm3_rf_mute_n,
    rcu_pwr_en_zer_in,
    ms_pwr_en_out,
    ms_rf_mute_n_in,
    ntm1_pfi_n,
    ntm2_pfi_n,
    ntm3_pfi_n
} iot_GpiPinId_t;

typedef enum
{
	reset = 0,
	set
} iot_GpioPinState_t;

typedef enum
{
	i2c_bus_none = 0,
	i2c_bus_ntm1,
	i2c_bus_ntm2,
	i2c_bus_ntm3
} iot_I2cBusSource_t;

typedef enum
{
	fan_pwm_1_1 = 0,
	fan_pwm_2_1,
	fan_pwm_2_2,
	fan_pwm_3_1
} iot_FanPwmSource_t;

typedef enum
{
	rfm_input = 0,
	rfm_output
} iot_RfMuteDir_t;


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
bool iot_ReadHwConfigInfo(hci_HwConfigInfoData_t *p_hw_config_info);
bool iot_ResetHwConfigInfo(void);
bool iot_SetAssyPartNo(uint8_t *assy_part_no);
bool iot_SetAssyRevNo(uint8_t *assy_rev_no);
bool iot_SetAssySerialNo(uint8_t *assy_serial_no);
bool iot_SetAssyBuildDataBatchNo(uint8_t *assy_build_date_batch_no);
void iot_SetI2cBus(iot_I2cBusSource_t source);
bool iot_InitialiseFanController(void);
bool iot_ReadFanSpeedCounts(uint16_t *p_fan1_clk_count,
							uint16_t *p_fan2_clk_count);
bool iot_SetFanSpeedDuty(uint16_t pwm);
void iot_SetFanPwmSource(iot_FanPwmSource_t source);
uint32_t iot_MeasureFanPwmDuty(void);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/

extern const char *IOT_UART_EXPECTED_STRING;

#endif /* __IO_TASK_H */
