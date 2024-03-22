/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file i2c_poe_driver.h
**
** Include file for i2c_poe_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_POE_DRIVER_H
#define __I2C_POE_DRIVER_H

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
#define	IPD_NUM_PORTS	8

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
typedef struct ipd_I2cPoeDriver
{
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	bool 				initialised;
} ipd_I2cPoeDriver_t;

typedef enum ipd_PowerOnFault
{
	ipd_pof_no_event = 0,
	ipd_pof_invalid_detection,
	ipd_pof_classification_error,
	ipd_pof_insufficient_power_allocation
} ipd_PowerOnFault_t;

typedef enum ipd_PortMode
{
	ipd_pm_shutdown = 0,
	ipd_pm_manual,
	ipd_pm_semi_auto,
	ipd_pm_auto
} ipd_PortMode_t;

typedef enum ipd_PortClassStatus
{
	ipd_pcs_unknown = 0,
	ipd_pcs_class1,
	ipd_pcs_class2,
	ipd_pcs_class3,
	ipd_pcs_class5,
	ipd_pcs_invalid1,
	ipd_pcs_class5_4p_ss,
	ipd_pcs_class6_4p_ss,
	ipd_pcs_class7_4p_ss,
	ipd_pcs_class8_4p_ss,
	ipd_pcs_class4_type1_limited,
	ipd_pcs_class5_ds,
	ipd_pcs_invalid2,
	ipd_pcs_class_mismatch
} ipd_PortClassStatus_t;

typedef enum ipd_PortDetectionStatus
{
	ipd_pds_unkown = 0,
	ipd_pds_short_circuit,
	ipd_pds_capacitive,
	ipd_pds_rlow,
	ipd_pds_rgood,
	ipd_pds_rhigh,
	ipd_pds_open_circuit,
	ipd_pds_pse_to_pse,
	ipd_pds_invalid1,
	ipd_pds_invalid2,
	ipd_pds_invalid3,
	ipd_pds_invalid4,
	ipd_pds_invalid5,
	ipd_pds_invalid6,
	ipd_pds_invalid7,
	ipd_pds_mosfet_fault
} ipd_PortDetectionStatus_t;

typedef enum ipd_PowerAllocation
{
	ipd_pa_ss_class3_ds_class2 = 0x88,
	ipd_pa_ss_class4_ds_class3 = 0xBB,
	ipd_pa_ss_class5_ds_class4_class3 = 0xCC,
	ipd_pa_ss_class6_ds_class4 = 0xDD
} ipd_PowerAllocation_t;

typedef struct ipd_PortPowerStatus
{
	bool						power_enable;
	bool						power_good;
	ipd_PowerOnFault_t			power_on_fault;
	ipd_PortMode_t				mode;
	bool						port_2p4p_mode;
	uint8_t						power_allocation;
	ipd_PortClassStatus_t		class_status;
	ipd_PortDetectionStatus_t	detection_status;
	uint32_t					voltage;
	uint32_t					current_ma;
} ipd_PortStatus_t;

typedef struct ipd_DeviceStatus
{

	uint32_t					temperature;
	uint32_t					voltage;
} ipd_DeviceStatus_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool ipd_Init(ipd_I2cPoeDriver_t  *p_inst, I2C_HandleTypeDef *p_i2c_device, uint16_t i2c_address);
bool ipd_GetPortPowerStatus(ipd_I2cPoeDriver_t *p_inst, int16_t port, ipd_PortStatus_t *p_port_status);
bool ipd_GetDeviceStatus(ipd_I2cPoeDriver_t *p_inst, ipd_DeviceStatus_t *p_device_status);
bool ipd_SetPortPowerAllocation(ipd_I2cPoeDriver_t *p_inst, int16_t port, ipd_PowerAllocation_t power_alloc);
bool ipd_IsPortValid(int16_t port);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __I2C_POE_DRIVER_H */
