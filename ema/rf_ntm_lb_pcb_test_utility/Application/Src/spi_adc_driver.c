/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file spi_adc_driver.c
*
* Driver for ADC122S101 SPI ADC, assumptions:
* - only channel 1 is used
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#define __SPI_ADC_DRIVER_C

#include "spi_adc_driver.h"

/*****************************************************************************/
/**
* Initialise the SPI ADC driver instance and configures the ADC ready for
* reading
*
* @param    p_inst pointer to SPI ADC driver instance data
* @param	spi_device HAL driver handle for the SPI peripheral that the
* 			ADC is connected to
* @param	adc_ncs_gpio_port HAL driver GPIO port for ADC SPI nCS signal
* @param	adc_ncs_gpio_pin HAL driver GPIO pin for ADC SPI nCS signal
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool sad_InitInstance(	sad_SpiAdcDriver_t  *p_inst,
						SPI_HandleTypeDef	*spi_device,
						GPIO_TypeDef		*adc_ncs_gpio_port,
						uint16_t			adc_ncs_gpio_pin)
{
	p_inst->spi_device			= spi_device;
	p_inst->adc_ncs_gpio_port	= adc_ncs_gpio_port;
	p_inst->adc_ncs_gpio_pin	= adc_ncs_gpio_pin;
	p_inst->initialised 		= true;

	return sad_InitDevice(p_inst);
}


/*****************************************************************************/
/**
* Initialise the SPI ADC device.  Only ever need to read Channel 1 so
* initialise by setting the channel to read as 1, control word 0x0
* @param    p_inst pointer to SPI ADC driver instance data
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool sad_InitDevice(sad_SpiAdcDriver_t *p_inst)
{
	bool ret_val = false;
	uint8_t tx_buf[SAD_ADC122S101_RDWR_LEN] = {0U};

	if (p_inst->initialised)
	{
		/* De-assert the nCS signals to ensure they are in a known state */
		sad_AssertChipSelect(p_inst, false);
		HAL_Delay(1U);

		/* Write to device */
		sad_AssertChipSelect(p_inst, true);

		if (HAL_SPI_Transmit(	p_inst->spi_device, tx_buf,
								SAD_ADC122S101_RDWR_LEN,
								SAD_SPI_TIMEOUT_MS) == HAL_OK)
		{
			ret_val = true;
		}

		/* Leave the nCS signals de-asserted */
		sad_AssertChipSelect(p_inst, false);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read the ADC channel, Channel 1 is used to monitor the mixer's RF level,
* read ADC value is returned in units of centi-dBm
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param 	p_data pointer to data structure to receive ADC data
* @return   true if ADC data read and returned successfully, else false
* @note     None
*
******************************************************************************/
bool sad_ReadAdcData(sad_SpiAdcDriver_t *p_inst, iad_SpiAdcData_t *p_data)
{
	bool ret_val = false;
	uint8_t tx_buf[SAD_ADC122S101_RDWR_LEN] = {0U};
	uint8_t rx_buf[SAD_ADC122S101_RDWR_LEN] = {0U};
	uint16_t adc_val = 0U;
	float f_val = 0.0f;

	if (p_inst->initialised && (p_data != NULL))
	{
		sad_AssertChipSelect(p_inst, true);

		if (HAL_SPI_TransmitReceive(p_inst->spi_device, tx_buf, rx_buf,
									SAD_ADC122S101_RDWR_LEN,
									SAD_SPI_TIMEOUT_MS) == HAL_OK)
		{
			/* Using 1650 mV = -20 dBm offset and 4.3 mV / cdBm slope per
			 * Mercury code, Vref = 3300 mV, 12-bit ADC, convert ADC reading
			 * to units of centi-dBm */
			adc_val = ((uint16_t)rx_buf[0] << 8) | (uint16_t)rx_buf[1];
			f_val = -200.0f + ((((float)adc_val * 3300.0f / 4095.0f) - 1650.0f) / 4.3f);
			p_data->adc_ch_cdbm = (int16_t)f_val;

			ret_val = true;
		}

		sad_AssertChipSelect(p_inst, false);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Accessor to array of string describing the ADC channel
*
* @return   Pointer to string describing the ADC channel
* @note     None
*
******************************************************************************/
const char *sad_GetChannelName(void)
{
	return lg_sad_ch_name;
}


/*****************************************************************************/
/**
* Asserts/de-asserst the nCS signals
*
* @param    p_inst pointer to SPI ADC driver instance data
* @param	assert true to assert active-low chip select signal, else false
* 			to de-assert
* @return   None
* @note     Not checking the driver instance is initialised as this local function
* 			is only called from functions which have already checked this
*
******************************************************************************/
void sad_AssertChipSelect(sad_SpiAdcDriver_t *p_inst, bool assert)
{
	if (assert)
	{
		HAL_GPIO_WritePin(	p_inst->adc_ncs_gpio_port,
							p_inst->adc_ncs_gpio_pin,
							GPIO_PIN_RESET);
	}
	else
	{
		HAL_GPIO_WritePin(	p_inst->adc_ncs_gpio_port,
							p_inst->adc_ncs_gpio_pin,
							GPIO_PIN_SET);
	}
}
