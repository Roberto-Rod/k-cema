/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file i2c_temp_sensor.c
*
* Driver for AD7415 I2C temperature sensor.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/

#include "i2c_temp_sensor.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define ITS_AD7415_TEMP_VAL_REG_ADDR	0x00U

#define ITS_RD_TEMP_REG_LEN				2U
#define ITS_WR_REG_ADDR_LEN				1U

#define ITS_I2C_TIMEOUT_MS				100U

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
* Initialise the I2C Temp Sensor driver, this function copies the hw information
* into the driver data, no device initialisation is required.
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool its_Init(its_I2cTempSensor_t *p_inst, I2C_HandleTypeDef *p_i2c_device, uint16_t i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return true;
}


/*****************************************************************************/
/**
* Read the temperature and return in units of deg C.
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param 	p_temp pointer to variable that will receive the temperature in deg C
* @return   true if temperature read and returned successfully, else false
*
******************************************************************************/
bool its_ReadTemperature(its_I2cTempSensor_t *p_inst, int16_t *p_temp)
{
	bool ret_val;
	uint8_t buf[ITS_RD_TEMP_REG_LEN];
	uint16_t temp;

	/* Write 0x00U to the Address Pointer Register, 1-byte write */
	buf[0] = 0x00U;

	ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->i2c_address,
										buf, ITS_WR_REG_ADDR_LEN, ITS_I2C_TIMEOUT_MS) == HAL_OK);
	if (ret_val)
	{	/* Read the register */
		ret_val = (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
											buf, ITS_RD_TEMP_REG_LEN, ITS_I2C_TIMEOUT_MS) == HAL_OK);

		if (ret_val)
		{	/* Convert 8-bit buffer to 16-bit value and shift temperature data
			 * bits to the correct position. */
			temp = ((uint16_t)buf[0] << 8) & 0xFF00U;
			temp |= (uint16_t)buf[1] & 0xFFU;
			temp >>= 6;

			/* Handle positive/negative temperatures and scale from 0.25 deg C to 1 deg C */
			if (temp >= 512U)
			{	/* Negative temperature */
				*p_temp = ((int16_t)temp - 1024) / 4;
			}
			else
			{	/* Positive temperature */
				*p_temp = (int16_t)temp / 4;
			}
		}
		else
		{
			*p_temp = 0x8000;
		}
	}

	return ret_val;
}
