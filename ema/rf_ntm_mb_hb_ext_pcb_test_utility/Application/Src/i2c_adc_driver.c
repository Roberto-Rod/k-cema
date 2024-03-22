/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file i2c_adc_driver.c
*
* Driver for LTC12991 I2C ADC, assumptions:
* - internal temperature sensor is enabled, units of Kelvin
* - 8x single-ended voltage inputs
* - ADC configured for continuous sampling
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "i2c_adc_driver.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define IAD_LTC2991_CHANNEL_EN_REG_ADDR		0x01U
#define IAD_LTC2991_V1V2V3V4_CTRL_REG_ADDR	0x06U
#define IAD_LTC2991_V5V6V7V8_CTRL_REG_ADDR	0x07U
#define IAD_LTC2991_CONTROL_REG_ADDR		0x08U
#define IAD_LTC2991_V1_REG_ADDR				0x0AU
#define IAD_LTC2991_V2_REG_ADDR				0x0CU
#define IAD_LTC2991_V3_REG_ADDR				0x0EU
#define IAD_LTC2991_V4_REG_ADDR				0x10U
#define IAD_LTC2991_V5_REG_ADDR				0x12U
#define IAD_LTC2991_V6_REG_ADDR				0x14U
#define IAD_LTC2991_V7_REG_ADDR				0x16U
#define IAD_LTC2991_V8_REG_ADDR				0x18U
#define IAD_LTC2991_INT_TEMP_REG_ADDR		0x1AU
#define IAD_LTC2991_VCC_REG_ADDR			0x1CU

#define IAD_LTC2991_CHANNEL_EN_REG_VAL		0xF8U	/* V1-V8 enabled; internal temperature/VCC enabled */
#define IAD_LTC2991_V1V2V3V4_CTRL_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define IAD_LTC2991_V5V6V7V8_CTR_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define IAD_LTC2991_CONTROL_REG_VAL			0x14U	/* PWM disabled; repeated acquisition; internal voltage filter disabled, Kelvin temp. */

#define IAD_LTC2991_DATA_VALID_BIT			0x8000U
#define IAD_LTC2991_SIGN_BIT				0x4000U
#define IAD_LTC2991_DATA_VALID_MASK			0x7FFFU

#define IAD_RD_REG_LEN			1U
#define IAD_RD_ADC_CH_LEN		2U
#define IAD_WR_REG_ADDR_LEN		1U
#define IAD_WR_REG_LEN			2U

#define IAD_I2C_TIMEOUT_MS		100U

/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
bool iad_ReadRegister(	iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t *p_val);
bool iad_ReadAdcChannel(iad_I2cAdcDriver_t *p_inst,
						uint8_t ch_addr, uint16_t *p_val);
bool iad_WriteRegister (iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


/*****************************************************************************/
/**
* Initialise the I2C ADC driver, this function copies the hw information
* into the driver data structure and calls the iad_InitDevice function to
* initialise the device
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	p_i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address ADC device's I2C bus address
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool iad_InitInstance(	iad_I2cAdcDriver_t  *p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return iad_InitDevice(p_inst);
}


/*****************************************************************************/
/**
* Initialise the I2C ADC device.  Writes pre-defined setting
* strings to the device
*
* @param    p_inst pointer to I2C ADC driver instance data
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool iad_InitDevice(iad_I2cAdcDriver_t  *p_inst)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = iad_WriteRegister(p_inst,
									IAD_LTC2991_V1V2V3V4_CTRL_REG_ADDR,
									IAD_LTC2991_V1V2V3V4_CTRL_REG_VAL);

		if (ret_val)
		{
			ret_val = iad_WriteRegister(p_inst,
										IAD_LTC2991_V5V6V7V8_CTRL_REG_ADDR,
										IAD_LTC2991_V5V6V7V8_CTR_REG_VAL);
		}

		if (ret_val)
		{
			ret_val = iad_WriteRegister(p_inst,
									IAD_LTC2991_CONTROL_REG_ADDR,
									IAD_LTC2991_CONTROL_REG_VAL);
		}

		if (ret_val)
		{
			ret_val = iad_WriteRegister(p_inst,
										IAD_LTC2991_CHANNEL_EN_REG_ADDR,
										IAD_LTC2991_CHANNEL_EN_REG_VAL);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read all the ADC channels from the device and return data to calling
* function, applies scaling factors too so that returned single-ended voltages
* have unit of mVs and temperatures Kelvin
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param 	p_data pointer to data structure to receive ADC data
* @return   true if ADC data read and returned successfully, else false
*
******************************************************************************/
bool iad_ReadAdcData(iad_I2cAdcDriver_t *p_inst, iad_I2cAdcData_t *p_data)
{
	bool ret_val = true;
	int16_t i = 0;
	uint16_t raw_adc_data[IAD_LTC2991_READ_CH_NUM];

	if (p_inst->initialised && (p_data != NULL))
	{
		for (i = 0; i < IAD_LTC2991_READ_CH_NUM; ++i)
		{
			ret_val = iad_ReadAdcChannel(	p_inst,
											IAD_LTC2991_V1_REG_ADDR + (i * 2U),
											&raw_adc_data[i]);
			if (!ret_val)
			{
				break;
			}
		}

		if (ret_val)
		{
			for (i = 0U; i < IAD_LTC2991_READ_CH_NUM; ++i)
			{
				/* All channels are set to single-ended. Small negative readings
				 * can be returned. If the result is negative then return 0.
				 */
				if (raw_adc_data[i] & IAD_LTC2991_SIGN_BIT)
				{
					p_data->adc_ch_mv[i] = 0;
				}
				else
				{
					p_data->adc_ch_mv[i] = (int16_t)((float)raw_adc_data[i] * p_inst->ch_scaling_factors[i]) + p_inst->ch_offsets_mv[i];
				}
			}

			p_data->adc_ch_vcc_mv += IAD_LTC2991_VCC_OFFSET_MV;
		}
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register read from the specified address
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives read register value
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool iad_ReadRegister(	iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[IAD_RD_REG_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->i2c_address,
									buf, IAD_WR_REG_ADDR_LEN, IAD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
									buf, IAD_RD_REG_LEN, IAD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	if (ret_val)
	{
		*p_val = buf[0];
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 16-bit ADC read from the specified address
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	ch_addr address of ADC channel to read
* @param	p_val pointer to variable that receives read data
* @return   true if read successful, else false
*
******************************************************************************/
bool iad_ReadAdcChannel(iad_I2cAdcDriver_t *p_inst,
						uint8_t ch_addr, uint16_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[IAD_RD_ADC_CH_LEN] = {0U};
	volatile uint16_t temp = 0U;

	/* Set the address pointer to the register to be read */
	buf[0] = ch_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, IAD_WR_REG_ADDR_LEN, IAD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
								buf, IAD_RD_ADC_CH_LEN, IAD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	if (ret_val)
	{
		temp = (uint16_t)((uint16_t)(buf[0] << 8) | (uint16_t)buf[1]);
		/* Check validity of read data */
		if (temp & IAD_LTC2991_DATA_VALID_BIT)
		{
			*p_val = (temp & IAD_LTC2991_DATA_VALID_MASK);
		}
		else
		{
			ret_val = false;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register write to the specified address
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
*
******************************************************************************/
bool iad_WriteRegister( iad_I2cAdcDriver_t *p_inst,
						uint8_t reg_addr, uint8_t val)
{
	bool ret_val = true;
	uint8_t buf[IAD_WR_REG_LEN];

	buf[0] = reg_addr;
	buf[1] = val;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, IAD_WR_REG_LEN, IAD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}
