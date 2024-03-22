/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file #include "eui48.c
*
* Implements a driver to read EUI48 (MAC address) from a Microchip 24AA025E48
* device.
*
* Project   : N/A
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "eui48.h"

#include <stdio.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define E48_I2C_TIMEOUT     100U
#define E48_MEMORY_OFFSET   0xFAU

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


/*****************************************************************************/
/**
* Initialises the EUI48 info driver
*
* @param    p_inst pointer to eui48 instance data
* @param    p_i2cm_inst pointer to I2C master driver instance
* @param    i2c_addr 7-bit I2C address of 24AA025E48
* @return   true if initialisation successful, else false
* @note    None
*
******************************************************************************/
bool e48_Init(  e48_E48Info_t		*p_inst,
				I2C_HandleTypeDef* 	i2c_device,
				uint16_t			i2c_address)
{
    bool ret_val = false;

    if (p_inst != NULL)
    {
        /* Initialise the EUI48 instance structure */
        p_inst->i2c_device  = i2c_device;
        p_inst->i2c_address = i2c_address;
        p_inst->initialised = true;

        ret_val = true;
    }

    return ret_val;
}


/*****************************************************************************/
/**
* Reads the MAC address information from the 24AA025E48.
*
* The function blocks until the I2C read transaction is complete, the read
* EUI48 is then returned.
*
* @param    p_inst pointer to EUI48 instance data
* @param    p_eui48 pointer t buffer to receive EUI48, buffer must have length
*           >=E48_DATA_LEN_BYTES
* @return   true if read successful, else false
* @todo     This function needs a timeout to prevent infinite loops
*
******************************************************************************/
bool e48_GetEui48(e48_E48Info_t *p_inst, uint8_t *p_eui48)
{
    bool ret_val = false;

    if ((p_inst != NULL) && (p_eui48 != NULL) && p_inst->initialised)
    {

		if (HAL_I2C_Mem_Read(	p_inst->i2c_device, p_inst->i2c_address,
								E48_MEMORY_OFFSET, 1U, p_eui48, E48_DATA_LEN_BYTES,
								E48_I2C_TIMEOUT) == HAL_OK)
    	{
			ret_val = true;
    	}
    }

    return ret_val;
}

