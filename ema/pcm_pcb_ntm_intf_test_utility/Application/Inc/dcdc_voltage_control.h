/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file dcdc_voltage_control.h
**
** Include file for dcdc_voltage_control.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __DCDC_VOLTAGE_CONTROL_H
#define __DCDC_VOLTAGE_CONTROL_H

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
} dvc_DcdcVoltCtrlDriver_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void dvc_InitInstance(	dvc_DcdcVoltCtrlDriver_t	*p_inst,
						I2C_HandleTypeDef			*p_i2c_device,
						uint16_t					i2c_address);
bool dvc_SetRdacValue(dvc_DcdcVoltCtrlDriver_t *p_inst, uint16_t rdac_value);
bool dvc_ReadRdacValue(dvc_DcdcVoltCtrlDriver_t *p_inst, uint16_t *p_rdac_value);
bool dvc_StoreWiperTo50TpValue(dvc_DcdcVoltCtrlDriver_t *p_inst);
bool dvc_Read50TpValue(	dvc_DcdcVoltCtrlDriver_t *p_inst,
						uint16_t *p_last_50tp_addr,
						uint16_t *p_50tp_value);
bool dvc_ResetDevice(dvc_DcdcVoltCtrlDriver_t *p_inst);

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
#ifdef __DCDC_VOLTAGE_CONTROL_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define DVC_AD5272_RDAC_MIN       	0x0U
#define DVC_AD5272_RDAC_MAX       	0x3FFU
/* I2C command definitions */
#define DVC_AD5272_WR_RDAC_CMD    			0x01U
#define DVC_AD5272_RD_RDAC_CMD    			0x02U
#define DVC_AD5272_WR_50TP_CMD				0x03U
#define DVC_AD5272_RESET_CMD				0x04U
#define DVC_AD5272_RD_50TP_CMD				0x05U
#define DVC_AD5272_RD_LAST_50TP_ADDR_CMD	0x06U
#define DVC_AD5272_WR_CTRL_CMD    			0x07U
#define DVC_AD5272_RD_CTRL_CMD    			0x08U
#define DVC_AD52752_CMD_DATA_LEN			2
#define DVC_AD52752_RD_DATA_LEN				2
/* Control Register Bits */
#define DVC_AD7252_50TP_WR_EN 				0x001U
#define DVC_AD7252_RDAC_WR_EN 				0x002U
#define DVC_AD7252_RES_PERFORMANCE_EN		0x004U
#define DVC_AD7252_50TP_PROG_SUCCESS		0x008U

#define DVC_AD5272_MEM_PROG_TIME_MS			350U
#define DVC_I2C_TIMEOUT						100U

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


#endif /* __DCDC_VOLTAGE_CONTROL_C */

#endif /* __DCDC_VOLTAGE_CONTROL_H */
