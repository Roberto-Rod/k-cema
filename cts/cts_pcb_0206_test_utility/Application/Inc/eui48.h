/****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
**
** @file eui48.h
**
** Include file for eui48.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __EUI48_H__
#define __EUI48_H__

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32f4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define E48_DATA_LEN_BYTES  6

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
/* Structure that defines the state of the EUI48 driver */
typedef struct
{
    I2C_HandleTypeDef	*i2c_device;  				/* Pointer to the I2C master interface used to talk to the 24AA025E48 */
    uint8_t 			i2c_address;               	/* 7-bit I2C address of the 24AA025E48 */
    uint8_t 			buf[E48_DATA_LEN_BYTES];   	/* Data buffer used for sending/receiving data to/from the 24AA025E48 */
    bool 				initialised;
} e48_Eui48Drv_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool e48_Init(e48_Eui48Drv_t *p_inst, I2C_HandleTypeDef *i2c_device, uint8_t i2c_address);
bool e48_GetEui48(e48_Eui48Drv_t *p_inst, uint8_t *p_eui48);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __EUI48_H__ */
