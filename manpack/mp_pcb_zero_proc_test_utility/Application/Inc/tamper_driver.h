/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file tamper_driver.h
**
** Include file for tamper_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __TAMPER_DRIVER_H
#define __TAMPER_DRIVER_H

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
/* M41ST81W registers */
#define TD_MS_REG   		0x00U
#define TD_SECONDS_REG   	0x01U
#define TD_MINUTES_REG		0x02U
#define TD_HOURS_REG		0x03U
#define TD_DAY_REG			0x04U
#define TD_CRTL_REG      	0x08U
#define TD_WDOG_REG     	0x09U
#define	TD_ALARM_MONTH_REG	0x0AU
#define	TD_ALARM_HOUR_REG	0x0CU
#define TD_FLAGS_REG     	0x0FU
#define TD_TAMPER1_REG   	0x14U
#define TD_TAMPER2_REG   	0x15U

#define TD_SRAM_START    	0x20U
#define TD_SRAM_LEN			128U

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
} td_TamperDriver_t;

typedef enum
{
	td_TamperChannel1 = 0,
	td_TamperChannel2
} td_TamperChannels;

typedef struct
{
	uint8_t	seconds;
	uint8_t	tens_seconds;
	uint8_t minutes;
	uint8_t	tens_minutes;
	uint8_t hours;
	uint8_t tens_hours;
} td_Time;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool td_InitInstance(	td_TamperDriver_t  *p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address);
bool td_TamperEnable(td_TamperDriver_t *p_inst, int16_t channel,
						bool tpm, bool tcm, bool enable);
bool td_GetTime(td_TamperDriver_t *p_inst, td_Time *p_time);
bool td_ReadRegister(	td_TamperDriver_t *p_inst,
						uint8_t reg_addr, uint8_t *p_val);
bool td_WriteRegister(	td_TamperDriver_t *p_inst,
								uint8_t reg_addr, uint8_t val);

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
#ifdef __TAMPER_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
/* Tamper1/2 register bits */
#define TD_TAMPER_TEB       0x80U 	/* Tamper Enable Bit */
#define TD_TAMPER_TIE       0x40U 	/* Tamper Interrupt Enable */
#define TD_TAMPER_TCM       0x20U 	/* Tamper Connect Mode */
#define TD_TAMPER_TPM       0x10U 	/* Tamper Polarity Mode */
#define TD_TAMPER_TDS       0x08U 	/* Tamper Detect Sampling */
#define TD_TAMPER_TCHILO    0x04U 	/* Tamper Current Hi/Lo */
#define TD_TAMPER_TCLREXT   0x02U 	/* RAM Clear External */
#define TD_TAMPER_TCLR      0x01U 	/* RAM Clear */

/* Flags register bits */
#define TD_FLAG_WDF   		0x80	/* Watchdog (read only) */
#define TD_FLAG_AF    		0x40/	/* Alarm (read only) */
#define TD_FLAG_BL    		0x10	/* Battery Low (read only) */
#define TD_FLAG_OF    		0x04	/* Oscillator Fail */
#define TD_FLAG_TB1   		0x02	/* Tamper Bit 1 (read only) */
#define TD_FLAG_TB2   		0x01	/* Tamper Bit 2 (read only) */

/* Alarm Month register bits */
#define TD_AL_MONTH_AFE		0x80
#define TD_AL_MONTH_SQWE	0x40
#define TD_AL_MONTH_ABE		0x20

#define TD_RD_REG_LEN			1U
#define TD_WR_REG_ADDR_LEN		1U
#define TD_WR_REG_LEN			2U
#define TD_RD_WR_TIME_REG_LEN	8U

#define TD_I2C_TIMEOUT_MS	100U

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


#endif /* __TAMPER_DRIVER_C */

#endif /* __TAMPER_DRIVER_H */
