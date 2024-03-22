/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file spi_synth_driver.c
*
* Driver for ADF5356 frequency synthesiser
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "spi_synth_driver.h"
#include <math.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SSD_SYNTH_REG_LEN_BYTES			4
#define SSD_SYNTH_NUM_REGS				14

#define SSD_SPI_TIMEOUT_MS				100U

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
static int ssd_GreatestCommonDivisor(uint32_t x, uint32_t y);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
uint8_t lg_ssd_synth_init_data[SSD_SYNTH_NUM_REGS][SSD_SYNTH_REG_LEN_BYTES] = {
		{0x00U, 0x00U, 0x00U, 0x0DU}, 		/* Register 13 */
		{0xFFU, 0xFFU, 0xF5U, 0xFCU}, 		/* Register 12... */
		{0x00U, 0x61U, 0x20U, 0x0BU}, \
		{0x00U, 0xC0U, 0x26U, 0xBAU}, \
		{0x27U, 0x19U, 0xFCU, 0xC9U}, \
		{0x15U, 0x59U, 0x65U, 0x68U}, \
		{0x06U, 0x00U, 0x00U, 0x07U}, \
		{0x75U, 0x08U, 0x00U, 0x06U}, \
		{0x00U, 0x80U, 0x00U, 0x25U}, \
		{0x32U, 0x00U, 0xDDU, 0x84U}, \
		{0x00U, 0x00U, 0x00U, 0x03U}, \
		{0x00U, 0x00U, 0x60U, 0x02U}, \
		{0x0EU, 0x40U, 0x00U, 0x01U}, \
		{0x00U, 0x30U, 0x05U, 0x70U}		/* Register 0 */
};

/*****************************************************************************/
/**
* Initialise the SPI Synth driver, this function copies the hw information
* into the driver data structure and calls the ssd_InitDevice function to
* initialise the device
*
* @param    p_inst pointer to SPI Synth driver instance data
* @param	spi_device HAL driver handle for the SPI peripheral that the
* 			synth is connected to
* @param	p_assert_synth_cs_func pointer function used to assert/de-assert
* 			the synth's SPI chip-select signal
* @return   true if initialisation successful, else false
* @note     Assumes that the HAL SPI peripheral is configured as full-duplex
* 			SPI master
*
******************************************************************************/
bool ssd_InitInstance(	ssd_SpiSynthDriver_t 	*p_inst,
						SPI_HandleTypeDef		*spi_device,
						ssd_assert_synth_cs_t	p_assert_synth_cs_func)
{
	p_inst->spi_device				= spi_device;
	p_inst->p_assert_synth_cs_func 	= p_assert_synth_cs_func;
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
*
******************************************************************************/
bool ssd_InitDevice(ssd_SpiSynthDriver_t *p_inst)
{
	bool ret_val = true;
	int16_t i = 0;

	if (p_inst->initialised)
	{
		/* De-assert the nCS signals to ensure they are in a known state */
		p_inst->p_assert_synth_cs_func(false);
		HAL_Delay(1U);

		/* Write to device */
		for (i = 0; i < SSD_SYNTH_NUM_REGS; ++i)
		{
			p_inst->p_assert_synth_cs_func(true);

			if (HAL_SPI_Transmit(	p_inst->spi_device,
									&lg_ssd_synth_init_data[i][0],
									SSD_SYNTH_REG_LEN_BYTES,
									SSD_SPI_TIMEOUT_MS) != HAL_OK)
			{
				ret_val = false;
				break;
			}

			p_inst->p_assert_synth_cs_func(false);
			HAL_Delay(1U);
		}

		/* Leave the nCS signals de-asserted */
		p_inst->p_assert_synth_cs_func(false);
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
* @return   true if successful, else false
* @note     Tidy up the magic numbers!
*
******************************************************************************/
bool ssd_SetCentreFreqMhz(ssd_SpiSynthDriver_t *p_inst, uint32_t centre_freq_mhz)
{
	bool ret_val = false;
	const uint32_t f_pfd_hz = 61440000U;
	const uint32_t f_ch_hz = 1000000U;
	double n = 0.0F;
	double n_frac = 0.0F;
	double f_vco_hz = 0.0F;
	const uint32_t mod1 = 16777216U;
	const uint32_t mod2 = f_pfd_hz / ssd_GreatestCommonDivisor(f_pfd_hz, f_ch_hz);
	uint32_t n_int = 0U;
	uint32_t frac1 = 0U;
	uint32_t frac2 = 0U;
	uint32_t adc_clk_div = 0U;
	uint32_t reg_val = 0U;

	if (p_inst->initialised &&
		((centre_freq_mhz >= SSD_MIN_CENTRE_FREQ_MHZ) &&
		(centre_freq_mhz <= SSD_MAX_CENTRE_FREQ_MHZ)))
	{
		f_vco_hz = ((double)centre_freq_mhz * 1.0E6F) / 2.0F;
		n = f_vco_hz / (double)f_pfd_hz;
		n_int = (uint32_t)floor(n);
		n_frac = n - (double)n_int;
		frac1 = (uint32_t)floor(n_frac * (double)mod1);
		frac2 = (uint32_t)floor((((double)mod1 * n_frac) - (double)frac1) * (double)mod2);
		adc_clk_div = (uint32_t)ceil((((double)f_pfd_hz / 1.0E5F) - 2.0F) / 4.0F);

		/* Set Register 13 */
		reg_val = ((frac2 & 0x0FFFC000U) << 4) | ((mod2 & 0x0FFFC000U) >> 10) | 0xDU;
		ret_val = ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 10 */
		reg_val = ((adc_clk_div & 0xFFU) << 6) | 0x30U | 0xAU;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 2 */
		reg_val = ((frac2 & 0x00003FFFU) << 18) | ((mod2 & 0x00003FFFU) << 4) | 0x00000002U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 1 */
		reg_val = ((frac1 & 0x00FFFFFFU) << 4) | 0x00000001U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Delay for >160 us */
		HAL_Delay(1U);

		/* Set Register 0 */
		reg_val = 0x00300000U | ((n_int & 0x0000FFFFU) << 4) | 0x0U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the ADF5356 synth power-down bit, DB6 in Register 4, all other bits are
* left at initialisation values, synth powered up.
*
* @param    p_inst pointer to SPI Synth driver instance data
* @param	power_down true to power down, false to power up
* @return   true if successful, else false
*
******************************************************************************/
bool ssd_SetSynthPowerDown(ssd_SpiSynthDriver_t *p_inst, bool power_down)
{
	bool ret_val = false;
	uint8_t *reg4_init_vals = &lg_ssd_synth_init_data[SSD_SYNTH_NUM_REGS - 5][0];
	uint32_t reg_val = 0U;

	if (p_inst->initialised)
	{
		/* Build word to send based on Register 4 initialisation values */
		reg_val = (uint32_t)reg4_init_vals[0] << 24;
		reg_val |= (uint32_t)reg4_init_vals[1] << 16;
		reg_val |= (uint32_t)reg4_init_vals[2] << 8;
		reg_val |= (uint32_t)reg4_init_vals[3];

		/* Set or clear the power-down bit, DB6 */
		reg_val |= (power_down ? 0x00000040U : 0U);

		ret_val = ssd_WriteSynthRegister(p_inst, reg_val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Write 32-bit register value to the device via SPI bus, handles the SPI
* chip-select signal.
*
* @param	x positive integer input
* @return   true if the SPI bus transfer is successful, else false
*
******************************************************************************/
bool ssd_WriteSynthRegister(ssd_SpiSynthDriver_t *p_inst, uint32_t reg_val)
{
	bool ret_val = false;
	uint8_t buf[SSD_SYNTH_REG_LEN_BYTES] = {0U};

	if (p_inst->initialised)
	{
		p_inst->p_assert_synth_cs_func(true);

		buf[0] = (uint8_t)((reg_val >> 24) & 0xFFU);
		buf[1] = (uint8_t)((reg_val >> 16) & 0xFFU);
		buf[2] = (uint8_t)((reg_val >> 8) & 0xFFU);
		buf[3] = (uint8_t)(reg_val & 0xFFU);

		ret_val = (HAL_SPI_Transmit(p_inst->spi_device,
									buf,
									SSD_SYNTH_REG_LEN_BYTES,
									SSD_SPI_TIMEOUT_MS) == HAL_OK);

		p_inst->p_assert_synth_cs_func(false);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Calculates the greatest common divisor for two positive integers.
*
* @param	x positive integer input
* @param	x positive integer input
* @return   greatest common divisor for the two positive integers
*
******************************************************************************/
static int ssd_GreatestCommonDivisor(uint32_t x, uint32_t y)
{
    uint32_t r = 0, a, b;
    a = (x > y) ? x : y;	/* a is larger number */
    b = (x < y) ? x : y; 	/* b is smaller number */

    r = b;
    while (a % b != 0)
    {
        r = a % b;
        a = b;
        b = r;
    }
    return r;
}
