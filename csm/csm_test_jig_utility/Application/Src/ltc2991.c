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
#include "ltc2991.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define LTC2991_CHANNEL_EN_REG_ADDR		0x01U
#define LTC2991_V1V2V3V4_CTRL_REG_ADDR	0x06U
#define LTC2991_V5V6V7V8_CTRL_REG_ADDR	0x07U
#define LTC2991_CONTROL_REG_ADDR		0x08U
#define LTC2991_V1_REG_ADDR				0x0AU
#define LTC2991_V2_REG_ADDR				0x0CU
#define LTC2991_V3_REG_ADDR				0x0EU
#define LTC2991_V4_REG_ADDR				0x10U
#define LTC2991_V5_REG_ADDR				0x12U
#define LTC2991_V6_REG_ADDR				0x14U
#define LTC2991_V7_REG_ADDR				0x16U
#define LTC2991_V8_REG_ADDR				0x18U
#define LTC2991_INT_TEMP_REG_ADDR		0x1AU
#define LTC2991_VCC_REG_ADDR			0x1CU

#define LTC2991_CHANNEL_EN_REG_VAL		0xF8U	/* V1-V8 enabled; internal temperature/VCC enabled */
#define LTC2991_V1V2V3V4_CTRL_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define LTC2991_V5V6V7V8_CTR_REG_VAL	0x00U	/* all channels single-ended voltage; filter disabled */
#define LTC2991_CONTROL_REG_VAL			0x14U	/* PWM disabled; repeated acquisition; internal voltage filter disabled, Kelvin temp. */

#define LTC2991_DATA_VALID_BIT			0x8000U
#define LTC2991_DATA_VALID_MASK			0x7FFFU

#define LTC2991_RD_REG_LEN				1U
#define LTC2991_RD_ADC_CH_LEN			2U
#define LTC2991_WR_REG_ADDR_LEN			1U
#define LTC2991_WR_REG_LEN				2U

#define LTC2991_I2C_TIMEOUT_MS			100U

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
static bool ltc2991_ReadRegister(	ltc2991_Driver_t *p_inst,
									uint8_t reg_addr, uint8_t *p_val);
static bool ltc2991_ReadAdcChannel(	ltc2991_Driver_t *p_inst,
									uint8_t ch_addr, uint16_t *p_val);
static bool ltc2991_WriteRegister(	ltc2991_Driver_t *p_inst,
									uint8_t reg_addr, uint8_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static const float lg_ltc2991_adc_ch_scaling_factors[LTC2991_READ_CH_NUM] = \
{
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR,
	LTC2991_TEMP_SCALE_FACTOR,
	LTC2991_SE_V_SCALE_FACTOR
};


/*****************************************************************************/
/**
* Initialise the I2C ADC driver, this function copies the hw information
* into the driver data structure and calls the ltc2991_InitDevice function to
* initialise the device
*
* @param    p_inst pointer to LTC2991 driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool ltc2991_InitInstance(	ltc2991_Driver_t  *p_inst,
							I2C_HandleTypeDef	*p_i2c_device,
							uint16_t			i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return ltc2991_InitDevice(p_inst);
}


/*****************************************************************************/
/**
* Initialise the LTC2991 device.  Writes pre-defined settings values to the
* device:
* 	- internal temperature sensor is enabled, units of Kelvin
* 	- 8x single-ended voltage inputs
* 	- ADC configured for continuous sampling
*
* @param    p_inst pointer to LTC2991 driver instance data
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool ltc2991_InitDevice(ltc2991_Driver_t  *p_inst)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = ltc2991_WriteRegister(p_inst,
										LTC2991_V1V2V3V4_CTRL_REG_ADDR,
										LTC2991_V1V2V3V4_CTRL_REG_VAL);

		if (ret_val)
		{
			ret_val = ltc2991_WriteRegister(p_inst,
											LTC2991_V5V6V7V8_CTRL_REG_ADDR,
											LTC2991_V5V6V7V8_CTR_REG_VAL);
		}

		if (ret_val)
		{
			ret_val = ltc2991_WriteRegister(p_inst,
											LTC2991_CONTROL_REG_ADDR,
											LTC2991_CONTROL_REG_VAL);
		}

		if (ret_val)
		{
			ret_val = ltc2991_WriteRegister(p_inst,
											LTC2991_CHANNEL_EN_REG_ADDR,
											LTC2991_CHANNEL_EN_REG_VAL);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read all the ADC channels from the device and return data to calling
* function, applies scaling factors to so that returned single-ended voltages
* have unit of mVs and temperatures Kelvin
*
* @param    p_inst pointer to LTC2991 driver instance data
* @param 	p_data pointer to data structure to receive ADC data
* @return   true if ADC data read and returned successfully, else false
*
******************************************************************************/
bool ltc2991_ReadAdcData(ltc2991_Driver_t *p_inst, ltc2991_Data_t *p_data)
{
	bool ret_val = true;
	uint16_t i = 0U;
	uint16_t adc_data[LTC2991_READ_CH_NUM] = {0U};

	if (p_inst->initialised && (p_data != NULL))
	{
		for (i = 0U; i < LTC2991_READ_CH_NUM; ++i)
		{
			ret_val = ltc2991_ReadAdcChannel(	p_inst,
												LTC2991_V1_REG_ADDR + (i * 2U),
												&adc_data[i]);
			if (!ret_val)
			{
				break;
			}
		}

		if (ret_val)
		{
			for (i = 0U; i < LTC2991_READ_CH_NUM; ++i)
			{
				if (i < LTC2991_SE_CH_NUM)
				{
					p_data->adc_ch_mv[i] = (uint16_t)((float)adc_data[i] * p_inst->scaling_factors[i]);
				}
				else if ((int32_t)i == LTC2991_INT_TEMP_RD_IDX)
				{
					p_data->adc_ch_int_temp_k = (uint16_t)((float)adc_data[i] * lg_ltc2991_adc_ch_scaling_factors[i]);
				}
				else if ((int32_t)i == LTC2991_VCC_RD_IDX)
				{
					p_data->adc_ch_vcc_mv = (uint16_t)((float)adc_data[i] * lg_ltc2991_adc_ch_scaling_factors[i]);
				}
				else
				{
				}
			}

			p_data->adc_ch_vcc_mv += LTC2991_VCC_OFFSET_MV;
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
* @param    p_inst pointer to LTC2991 driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives read register value
* @return   true if read successful, else false
*
******************************************************************************/
static bool ltc2991_ReadRegister(	ltc2991_Driver_t *p_inst,
									uint8_t reg_addr, uint8_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[LTC2991_RD_REG_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(	p_inst->i2c_device, p_inst->i2c_address,
									buf, LTC2991_WR_REG_ADDR_LEN, LTC2991_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
								buf, LTC2991_RD_REG_LEN, LTC2991_I2C_TIMEOUT_MS) != HAL_OK)
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
* @param    p_inst pointer to LTC2991 driver instance data
* @param	ch_addr address of ADC channel to read
* @param	p_val pointer to variable that receives read data
* @return   true if read successful, else false
*
******************************************************************************/
static bool ltc2991_ReadAdcChannel(	ltc2991_Driver_t *p_inst,
									uint8_t ch_addr, uint16_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[LTC2991_RD_ADC_CH_LEN] = {0U};
	volatile uint16_t temp = 0U;

	/* Set the address pointer to the register to be read */
	buf[0] = ch_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, LTC2991_WR_REG_ADDR_LEN, LTC2991_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
								buf, LTC2991_RD_ADC_CH_LEN, LTC2991_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	if (ret_val)
	{
		temp = (uint16_t)((uint16_t)(buf[0] << 8) | (uint16_t)buf[1]);
		/* Check validity of read data */
		if (temp & LTC2991_DATA_VALID_BIT)
		{
			*p_val = (temp & LTC2991_DATA_VALID_MASK);
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
* @param    p_inst pointer to LTC2991 driver instance data
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
* @return   true if write successful, else false
*
******************************************************************************/
static bool ltc2991_WriteRegister( 	ltc2991_Driver_t *p_inst,
									uint8_t reg_addr, uint8_t val)
{
	bool ret_val = true;
	uint8_t buf[LTC2991_WR_REG_LEN];

	buf[0] = reg_addr;
	buf[1] = val;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, LTC2991_WR_REG_LEN, LTC2991_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}
