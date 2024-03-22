/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file i2c_dac_driver.c
*
* Driver for MCP4728 I2C DAC, assumptions:
* - device is configured for internal reference with gain 2
* - output voltage range 0 to 4.095 V
* - 1 DAC step = 1 mV
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo Add error handling on HAL I2C transfers rather than assuming they work
*
******************************************************************************/
#define __I2C_DAC_DRIVER_C

#include "i2c_dac_driver.h"

/*****************************************************************************/
/**
* Initialise the I2C ADC driver, configure ADC
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			DAC is connected to
* @param	i2c_address device's I2C bus address
* @return   None
* @note     None
*
******************************************************************************/
bool idd_Init(	idd_I2cDacDriver_t 	*p_inst,
				I2C_HandleTypeDef	*p_i2c_device,
				uint16_t			i2c_address)
{

	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return true;
}


/*****************************************************************************/
/**
* Performs a Fast Write to all four DAC channels, the EEPROM contents is not
* updated, allows DAC outputs to be set and/or channels powered up/down
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	dac_data Fast Write DAC data to write to device
* @return   true if DAC is written to successfully, else false
* @note     None
*
******************************************************************************/
bool idd_FastWriteDacs(	idd_I2cDacDriver_t *p_inst,
						idd_I2cDacFwrData_t dac_data)
{
	bool ret_val = false;
	uint8_t buf[IDD_FWR_DAC_LEN];
	int16_t i = 0;

	if (p_inst->initialised)
	{
		/* Build the data words to write to the DAC */
		for (i = 0; i < IDD_MCP4728_CH_NUM; ++i)
		{
			buf[(i*2)+1] = (uint8_t)(dac_data.ch_mv[i] & 0xFFU);
			buf[i*2] = (uint8_t)((dac_data.ch_mv[i] >> 8) & 0xFFU);

			if (dac_data.pwr_dwn[i])
			{
				buf[i*2] |= IDD_MCP4728_FWR_PD_OFF;
			}
			else
			{
				buf[i*2] |= IDD_MCP4728_FWR_PD_ON;
			}
		}

		ret_val = idd_WriteData(p_inst, buf, IDD_FWR_DAC_LEN);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a DAC and EEPROM write to the specified channel
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	ch_mv 12-bit DAC value
* @param	int_vref true for internal reference, false for external reference
* @param	gain_2 true for x2 gain with internal reference, else gain x1
* @param	pwr_dwn_mode 0 = on; 1 = 1k to GND; 2 = 100k to GND; 3 = 500k to GND
* @param	chan DAC channel to read: 0 = A .... 3 = D
* @return   true if DAC is written to successfully, else false
* @note     None
*
******************************************************************************/
bool idd_WriteDacEeprom(	idd_I2cDacDriver_t	*p_inst,
							uint16_t	ch_mv,
							bool		int_vref,
							bool		gain_2,
							uint8_t		pwr_dwn_mode,
							uint16_t 	chan)
{
	bool ret_val = false;
	uint8_t buf[IDD_WR_DAC_LEN] = {0U};

	if (p_inst->initialised && (chan < IDD_MCP4728_CH_NUM))
	{
		buf[2] = (uint8_t)(ch_mv & 0xFFU);
		buf[1] = (uint8_t)((ch_mv >> 8) & 0xFFU);
		buf[1] |= (int_vref ? IDD_MCP4728_VREF_INT : 0U);
		buf[1] |= (gain_2 ? IDD_MCP4728_GAIN_2 : 0U);
		buf[1] |= ((pwr_dwn_mode << IDD_MCP4728_PD_SHIFT) & IDD_MCP4728_PD_BITS);
		buf[0] = IDD_MCP4728_SWR_DAC_EE_CMD | (((uint8_t)chan << IDD_MCP4728_CH_SHIFT) & IDD_MCP4728_CH_BITS);

		ret_val = idd_WriteData(p_inst, buf, IDD_FWR_DAC_LEN);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Reads and returns DAC information associated with the specified channel
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	p_dac_data pointer to data structures that receives read data
* @param	chan DAC channel to read: 0 = A .... 3 = D
* @return   true if DAC is written to successfully, else false
* @note     None
*
******************************************************************************/
bool idd_ReadDac(	idd_I2cDacDriver_t *p_inst,
					idd_I2cDacData_t *p_dac_data,
					uint16_t chan)
{
	bool ret_val = false;
	uint8_t buf[IDD_RD_DAC_LEN] = {0U};

	if (p_inst->initialised  && (chan < IDD_MCP4728_CH_NUM))
	{
		ret_val = idd_ReadData(p_inst, buf, IDD_RD_DAC_LEN);

		if (ret_val)
		{
			p_dac_data->ch_mv = ((uint16_t)(buf[(chan * 6) + 1] & 0x0FU) << 8) | (uint16_t)buf[(chan * 6) + 2];
			p_dac_data->vref = (buf[(chan * 6) + 1] & IDD_MCP4728_GAIN_2) ? 1U : 0U;
			p_dac_data->gain = (buf[(chan * 6) + 1] & IDD_MCP4728_GAIN_2) ? 1U : 0U;
			p_dac_data->pwr_dwn_mode = (buf[(chan * 6) + 1] & IDD_MCP4728_PD_BITS) >> IDD_MCP4728_PD_SHIFT;
			p_dac_data->rdy_nbusy = (buf[(chan * 6) + 0] & IDD_MCP4728_RDY_NBUSY) ? 1U : 0U;
			p_dac_data->por = (buf[(chan * 6) + 0] & IDD_MCP4728_POR) ? 1U : 0U;
			p_dac_data->addr_bit = (buf[(chan * 6) + 0] & IDD_MCP4728_ADDR_BITS) >> IDD_MCP4728_ADDR_SHIFT;
			p_dac_data->ee_ch_mv = ((uint16_t)(buf[(chan * 6) + 4] & 0xFU) << 8) | (uint16_t)buf[(chan * 6) + 5];
			p_dac_data->ee_vref = (buf[(chan * 6) + 4] & IDD_MCP4728_GAIN_2) ? 1U : 0U;
			p_dac_data->ee_gain = (buf[(chan * 6) + 4] & IDD_MCP4728_GAIN_2) ? 1U : 0U;
			p_dac_data->ee_pwr_dwn_mode = (buf[(chan * 6) + 4] & IDD_MCP4728_PD_BITS) >> IDD_MCP4728_PD_SHIFT;
			p_dac_data->ee_rdy_nbusy = (buf[(chan * 6) + 3] & IDD_MCP4728_RDY_NBUSY) ? 1U : 0U;;
			p_dac_data->ee_por = (buf[3] & IDD_MCP4728_POR) ? 1U : 0U;
			p_dac_data->ee_addr_bit = (buf[(chan * 6) + 3] & IDD_MCP4728_ADDR_BITS) >> IDD_MCP4728_ADDR_SHIFT;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register read from the specified address
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	p_data pointer to buffer that receives read data, buffer size
* 			must be >= size
* @param	size number of 8-bit values to read
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool idd_ReadData(idd_I2cDacDriver_t *p_inst, uint8_t *p_data, uint16_t size)
{
	bool ret_val = true;

	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
			p_data, size, IDD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register write to the specified address
*
* @param    p_inst pointer to I2C DAC driver instance data
* @param	p_data pointer to array of 8-bit data to send, array size
* 			must be >= size
* @param	size number of 8-bit values to send
* @return   true if write successful, else false
* @note     None
*
******************************************************************************/
bool idd_WriteData(idd_I2cDacDriver_t *p_inst,	uint8_t *p_data, uint16_t size)
{
	bool ret_val = true;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
			p_data, size, IDD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}
