/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file hw_config_info.h.h
**
** Include file for hw_config_info.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __HW_CONFIG_INFO_H
#define __HW_CONFIG_INFO_H

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
#define PCA9500_MEM_SIZE_BYTES	256U
#define PCA9500_PAGE_SIZE_BYES	4U
#define PCAA9500_WRITE_TIME_MS	10U
#define I2C_TIMEOUT				100U
#define HCI_STR_PARAM_LEN		16

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
	uint16_t			i2c_gpio_address;
	uint16_t			i2c_mem_address;
	bool 				initialised;
} hci_HwConfigInfo_t;

typedef struct
{
	uint8_t 	assy_part_no[HCI_STR_PARAM_LEN];
	uint8_t 	assy_rev_no[HCI_STR_PARAM_LEN];
	uint8_t		assy_serial_no[HCI_STR_PARAM_LEN];
	uint8_t 	assy_build_date_batch_no[HCI_STR_PARAM_LEN];
	uint8_t 	hci_version_no;
	uint16_t	hci_crc;
	bool		hci_crc_valid;
	uint8_t		hw_version;
	uint8_t 	hw_mod_version;
} hci_HwConfigInfoData_t;

typedef struct
{
	uint8_t 	assy_part_no[HCI_STR_PARAM_LEN];
	uint8_t 	assy_rev_no[HCI_STR_PARAM_LEN];
	uint8_t		assy_serial_no[HCI_STR_PARAM_LEN];
	uint8_t 	assy_build_date_batch_no[HCI_STR_PARAM_LEN];
	uint8_t		spare[189];	/* Pad data structure to 256-bytes */
	uint8_t 	hci_version_no;
	uint16_t	hci_crc;
} hci_HwConfigEepromData_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void hci_Init(	hci_HwConfigInfo_t	*p_inst,
				I2C_HandleTypeDef* 	i2c_device,
				uint16_t			i2c_gpio_address,
				uint16_t			i2c_mem_address);
bool hci_ReadHwConfigInfo(	hci_HwConfigInfo_t		*p_inst,
							hci_HwConfigInfoData_t	*p_hw_config_info);
bool hci_ResetHwConfigInfo(hci_HwConfigInfo_t *p_inst);
bool hci_SetAssyPartNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_part_no);
bool hci_SetAssyRevNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_rev_no);
bool hci_SetAssySerialNo(hci_HwConfigInfo_t *p_inst, uint8_t *assy_serial_no);
bool hci_SetAssyBuildDataBatchNo(	hci_HwConfigInfo_t *p_inst,
									uint8_t *assy_build_date_batch_no);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __HW_CONFIG_INFO_H */
