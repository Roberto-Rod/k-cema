/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file spi_synth_driver.c
*
* Driver for ADF4351 frequency synthesiser
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
* @todo Add error handling on HAL I2C transfers rather than assuming they work
*
******************************************************************************/
#define __SPI_SYNTH_DRIVER_C

#include "spi_synth_driver.h"

/*****************************************************************************/
/**
* Initialise the SPI Synth driver, this function copies the hw information
* into the driver data structure and calls the ssd_InitDevice function to
* initialise the device
*
* @param    p_inst pointer to SPI Synth driver instance data
* @param	spi_device HAL driver handle for the SPI peripheral that the
* 			synth is connected to
* @param	synth_ncs_gpio_port HAL driver GPIO port for synth SPI nCS signal
* @param	synth_ncs_gpio_pin HAL driver GPIO pin for synth SPI nCS signal
* @return   true if initialisation successful, else false
* @note     Assumes that the HAL SPI peripheral is configured as full-duplex
* 			SPI master
*
******************************************************************************/
bool ssd_InitInstance(	ssd_SpiSynthDriver_t 	*p_inst,
						SPI_HandleTypeDef		*spi_device,
						GPIO_TypeDef			*synth_ncs_gpio_port,
						uint16_t				synth_ncs_gpio_pin)
{
	p_inst->spi_device				= spi_device;
	p_inst->synth_ncs_gpio_port		= synth_ncs_gpio_port;
	p_inst->synth_ncs_gpio_pin		= synth_ncs_gpio_pin;
	p_inst->initialised 			= true;

	return ssd_InitDevice(p_inst);
}


/*****************************************************************************/
/**
* Initialise the SPI Synth device, manually controls the nCS signals and
* leaves them in the de-asserted state (HIGH).  Writes pre-defined setting
* strings to the device
*
* @param    p_inst pointer to SPI Synth driver instance data
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool ssd_InitDevice(ssd_SpiSynthDriver_t *p_inst)
{
	bool ret_val = true;
	int16_t i = 0;

	if (p_inst->initialised)
	{
		/* De-assert the nCS signals to ensure they are in a known state */
		ssd_AssertChipSelect(p_inst, false);
		HAL_Delay(1U);

		/* Write to device */
		for (i = 0; i < SSD_SYNTH_NUM_REGS; ++i)
		{
			ssd_AssertChipSelect(p_inst, true);

			if (HAL_SPI_Transmit(	p_inst->spi_device,
									&lg_ssd_synth_init_data[i][0],
									SSD_SYNTH_REG_LEN_BYTES,
									SSD_SPI_TIMEOUT_MS) != HAL_OK)
			{
				ret_val = false;
				break;
			}

			ssd_AssertChipSelect(p_inst, false);
			HAL_Delay(1U);
		}

		/* Leave the nCS signals de-asserted */
		ssd_AssertChipSelect(p_inst, false);
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the SPI Synth centre frequency to value specified in MHz
*
* @param    p_inst pointer to SPI Synth driver instance data
* @param	centre_freq_mhz required centre frequency in MHz, range
* @return   true if initialisation successful, else false
* @note     Make sense of the Mercury magic numbers!
*
******************************************************************************/
bool ssd_SetCentreFreqMhz(ssd_SpiSynthDriver_t *p_inst, uint32_t centre_freq_mhz)
{
	bool ret_val = false;
	uint32_t int_val = 0U;
	uint32_t reg_val = 0U;
	uint8_t buf[SSD_SYNTH_REG_LEN_BYTES] = {0U};

	if (p_inst->initialised &&
		((centre_freq_mhz >= SSD_MIN_CENTRE_FREQ_MHZ) &&
		(centre_freq_mhz <= SSD_MAX_CENTRE_FREQ_MHZ)))
	{
		int_val = (centre_freq_mhz / 5U) + 113U;
		reg_val = 0x00000E78 | ((int_val << 15) & 0x7FFF8000U);
		buf[0] = (uint8_t)((reg_val >> 24) & 0xFFU);
		buf[1] = (uint8_t)((reg_val >> 16) & 0xFFU);
		buf[2] = (uint8_t)((reg_val >> 8) & 0xFFU);
		buf[3] = (uint8_t)(reg_val & 0xFFU);

		ssd_AssertChipSelect(p_inst, true);

		if (HAL_SPI_Transmit(	p_inst->spi_device, buf,
								SSD_SYNTH_REG_LEN_BYTES,
								SSD_SPI_TIMEOUT_MS) == HAL_OK)
		{
			ret_val = true;
		}

		ssd_AssertChipSelect(p_inst, false);
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Asserts/de-asserst the nCS signals
*
* @param    p_inst pointer to SPI Synth driver instance data
* @param	assert true to assert active-low chip select signals, else false
* 			to de-assert
* @return   None
* @note     Not checking the driver instance is initialised as this local function
* 			is only called from functions which have already checked this
*
******************************************************************************/
void ssd_AssertChipSelect(ssd_SpiSynthDriver_t *p_inst, bool assert)
{
	if (assert)
	{
		HAL_GPIO_WritePin(	p_inst->synth_ncs_gpio_port,
							p_inst->synth_ncs_gpio_pin,
							GPIO_PIN_RESET);
	}
	else
	{
		HAL_GPIO_WritePin(	p_inst->synth_ncs_gpio_port,
							p_inst->synth_ncs_gpio_pin,
							GPIO_PIN_SET);
	}
}
