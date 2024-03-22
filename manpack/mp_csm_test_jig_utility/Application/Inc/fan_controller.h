/****************************************************************************/
/**
** Copyright 2020  Kirintec Ltd. All rights reserved.
**
** @file fan_controller.h
**
** Include file for fan_controller.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __FAN_CONTROLLER_H
#define __FAN_CONTROLLER_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/


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
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	bool 				initialised;
} fc_FanCtrlrDriver_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void fc_InitInstance(	fc_FanCtrlrDriver_t	*p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address);
bool fc_Initialise(fc_FanCtrlrDriver_t *p_inst);
bool fc_PushTemperature(fc_FanCtrlrDriver_t	*p_inst, int8_t temperature);
bool fc_ReadFanSpeedCounts(	fc_FanCtrlrDriver_t	*p_inst,
							uint16_t* p_fan1_clk_count,
							uint16_t* p_fan3_clk_count,
							uint8_t *p_fan1_pwm,
							uint8_t *p_fan2_pwm);
bool fc_ReadFanTachTargets(	fc_FanCtrlrDriver_t	*p_inst,
							uint16_t* p_fan1_tach_target,
							uint16_t* p_fan2_tach_target);
bool fc_ReadInternalTemp(	fc_FanCtrlrDriver_t	*p_inst,
							int8_t *int_temp_whole);
bool fc_ReadFanStatus(fc_FanCtrlrDriver_t	*p_inst, uint8_t *fan_status_reg);
bool fc_SetDirectSettingMode(fc_FanCtrlrDriver_t *p_inst, uint8_t pwm);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __FAN_CONTROLLER_H */
