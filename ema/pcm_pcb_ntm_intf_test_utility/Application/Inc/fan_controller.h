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


/*****************************************************************************
*
*  Local to the C file
*
*****************************************************************************/
#ifdef __FAN_CONTROLLER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define FC_NO_INIT_REGISTERS	63
#define FC_I2C_TIMEOUT			100U

#define FC_EMC2104_RD_CMD_LEN					1
#define FC_EMC2104_WR_CMD_LEN					2
#define FC_EMC2104_INT_WHOLE_TEMP_ADDR			0x00U
#define FC_EMC2104_TEMP1_REG_ADDR				0x0CU
#define FC_EMC2104_TEMP3_REG_ADDR				0x0EU
#define FC_EMC2104_FAN1_TT_HIGH_BYTE_REG_ADDR	0x4DU
#define FC_EMC2104_FAN1_TT_LOW_BYTE_REG_ADDR	0x4CU
#define FC_EMC2104_FAN2_TT_HIGH_BYTE_REG_ADDR	0x8DU
#define FC_EMC2104_FAN2_TT_LOW_BYTE_REG_ADDR	0x8CU
#define FC_EMC2104_FAN1_TACH_HIGH_BYTE_REG_ADDR	0x4EU
#define FC_EMC2104_FAN1_TACH_LOW_BYTE_REG_ADDR	0x4FU
#define FC_EMC2104_FAN2_TACH_HIGH_BYTE_REG_ADDR	0x8EU
#define FC_EMC2104_FAN2_TACH_LOW_BYTE_REG_ADDR	0x8FU
#define FC_EMC2104_FAN1_LUT_CONFIG_ADDR			0x50
#define FC_EMC2104_FAN2_LUT_CONFIG_ADDR			0x90
#define FC_EMC2104_FAN1_DRIVER_SETTING_ADDR		0x40
#define FC_EMC2104_FAN2_DRIVER_SETTING_ADDR		0x80
#define FC_EMC2104_FAN1_CONFIG1_ADDR			0x42
#define FC_EMC2104_FAN1_CONFIG2_ADDR			0x43
#define FC_EMC2104_FAN2_CONFIG1_ADDR			0x82
#define FC_EMC2104_FAN2_CONFIG2_ADDR			0x83
#define FC_EMC2104_MUXED_PIN_CONFIG_ADDR		0xE0
#define FC_EMC2104_FAN_STATUS_REG_ADDR			0x27

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
bool fc_ReadByte(fc_FanCtrlrDriver_t *p_inst, uint8_t addr, uint8_t* p_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
uint8_t lg_fc_init_data[FC_NO_INIT_REGISTERS][2] = { /* Data format {addr, value} */
		{0x20U, 0x00U},				/* Config */
		{0x28U, 0x00U},				/* Irq Enable */
		{0x29U, 0x0FU},				/* Fan Irq Enable - Fan 1 & 2 Fan spin-up and stall fault */
		{0x2AU, 0x00U},				/* PWM Config - PWM1 & PWM2 output polarity*/
		{0x2BU, 0x05U},				/* PWM Base Freq - PWM1 & PWM2 19.53 kHzrange (note, EMC2104 PWM output frequency is very inaccurate +/10 %) */
		{0x41U, 0x01U},				/* Fan 1 Divide - PWM1 divide by 1 */
		{0x42U, 0x3EU},				/* Fan 1 Config 1 - 1200 ms update time; 4-pole fan; 2x TACH count multiplier; Fan Speed Control Algorithm */
		{0x43U, 0x78U},				/* Fan 1 Config 2 - TACH must be present for fan speed; 0 RPM error range; 0x3 basic and step derivative; tacho LPF enabled*/
		{0x45U, 0x2AU},				/* Fan 1 Gain 1 */
		{0x46U, 0x59U},				/* Fan 1 Spin Up Config - 500 ms; final drive 60 %; 100 % fan drive setting; monitor for 32 update periods */
		{0x47U, 0x08U},				/* Fan 1 Step - max fan step size between update times of 8 */
		{0x48U, 0x20U},				/* Fan 1 Min Drive - 32 or 12.5 % */
		{0x49U, 0xC4U},				/* Fan 1 Valid Tach Count, 10,000 RPM */
		{0x4AU, 0x00U},				/* Fan 1 Drive Fail Ban Low Byte */
		{0x4BU, 0x00U},				/* Fan 1 Drive Fail Ban High Byte  */
		{0x81U, 0x01U},				/* Fan 2 Divide - PWM2 divide by 1 */
		{0x82U, 0x3EU},				/* Fan 2 Config 1 - 1200 ms update time; 4-pole fan; 2x TACH count multiplier; Fan Speed Control Algorithm */
		{0x83U, 0x78U},				/* Fan 2 Config 2 - TACH must be present for fan speed; 0 RPM error range; 0x3 basic and step derivative; tacho LPF enabled*/
		{0x85U, 0x2AU},				/* Fan 2 Gain 1 */
		{0x86U, 0x59U},				/* Fan 2 Spin Up Config - 500 ms; final drive 60 %; 100 % fan drive setting; monitor for 32 update periods */
		{0x87U, 0x08U},				/* Fan 2 Step - max fan step size between update times of 8 */
		{0x88U, 0x20U},				/* Fan 2 Min Drive - 32 or 12.5  % */
		{0x89U, 0xC4U},				/* Fan 2 Valid Tach Count, 10,000 RPM */
		{0x8AU, 0x00U},				/* Fan 2 Drive Fail Ban Low Byte */
		{0x8BU, 0x00U},				/* Fan 2 Drive Fail Ban High Byte */
		{0x54U, 0x28U},				/* LUT 1 Temp 3 Setting 1 - 40 deg C */
		{0x94U, 0x28U},				/* LUT 2 Temp 3 Setting 1 - 40 deg C */
		{0x59U, 0x2CU},				/* LUT 1 Temp 3 Setting 2 - 44 deg C */
		{0x99U, 0x2CU},				/* LUT 2 Temp 3 Setting 2 - 44 deg C */
		{0x5EU, 0x31U},				/* LUT 1 Temp 3 Setting 3 - 49 deg C */
		{0x9EU, 0x31U},				/* LUT 2 Temp 3 Setting 3 - 49 deg C */
		{0x63U, 0x35U},				/* LUT 1 Temp 3 Setting 4 - 53 deg C */
		{0xA3U, 0x35U},				/* LUT 2 Temp 3 Setting 4 - 53 deg C */
		{0x68U, 0x39U},				/* LUT 1 Temp 3 Setting 5 - 57 deg C */
		{0xA8U, 0x39U},				/* LUT 2 Temp 3 Setting 5 - 57 deg C */
		{0x6DU, 0x3DU},				/* LUT 1 Temp 3 Setting 6 - 61 deg C */
		{0xADU, 0x3DU},				/* LUT 2 Temp 3 Setting 6 - 61 deg C */
		{0x72U, 0x42U},				/* LUT 1 Temp 3 Setting 7 - 66 deg C */
		{0xB2U, 0x42U},				/* LUT 2 Temp 3 Setting 7 - 66 deg C */
		{0x77U, 0x46U},				/* LUT 1 Temp 3 Setting 8 - 70 deg C */
		{0xB7U, 0x46U},				/* LUT 2 Temp 3 Setting 8 - 70 deg C */
		{0x51U, 0x46U},				/* LUT 1 Drive 1 - 7,022 RPM */
		{0x91U, 0x46U},				/* LUT 2 Drive 1 - 7,022 RPM */
		{0x56U, 0x39U},				/* LUT 1 Drive 2 - 8,263 RPM */
		{0x96U, 0x39U},				/* LUT 2 Drive 2 - 8,263  RPM */
		{0x5BU, 0x30U},				/* LUT 1 Drive 3 - 10,240 RPM */
		{0x9BU, 0x30U},				/* LUT 2 Drive 3 - 10,240 RPM */
		{0x60U, 0x29U},				/* LUT 1 Drive 4 - 11,988 RPM */
		{0xA0U, 0x29U},				/* LUT 2 Drive 4 - 11,988 RPM */
		{0x65U, 0x25U},				/* LUT 1 Drive 5 - 13,284 RPM */
		{0xA5U, 0x25U},				/* LUT 2 Drive 5 - 13,284 RPM */
		{0x6AU, 0x21U},				/* LUT 1 Drive 6 - 14,895 RPM */
		{0xAAU, 0x21U},				/* LUT 2 Drive 6 - 14,895 RPM */
		{0x6FU, 0x1DU},				/* LUT 1 Drive 7 - 16,949 RPM */
		{0xAFU, 0x1DU},				/* LUT 2 Drive 7 - 16,949 RPM */
		{0x74U, 0x1BU},				/* LUT 1 Drive 8 - 18,204 RPM */
		{0xB4U, 0x1BU},				/* LUT 2 Drive 8 - 18,204 RPM */
		{0x79U, 0x02U},				/* LUT 1 Temp Hysteresis - 2 deg C */
		{0xB9U, 0x02U},				/* LUT 2 Temp Hysteresis - 2 deg C */
		{0xE0U, 0x00U},				/* Muxed Pin Config - GPIO1 clk input to FSCA */
		{0xE2U, 0x44U},				/* GPIO Output Config - PWM1 & PWM2 push-pull*/
		{0x50U, 0x2AU},				/* Fan 1 LUT Config - use Pushed Temp 3 & 4 for Temp 3 in LUT; RPM TACH values; Lock the LUT and allow it to be used; 2's comp temp data */
		{0x90U, 0x2AU}				/* Fan 2 LUT Config - use Pushed Temp 3 & 4 for Temp 3 in LUT; RPM TACH values; Lock the LUT and allow it to be used; 2's comp temp data */
};

#endif /* __FAN_CONTROLLER_C */

#endif /* __FAN_CONTROLLER_H */
