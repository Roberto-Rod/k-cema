/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
*
* @file spi_synth_driver.c
*
* Driver for ADF4355 frequency synthesiser
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
#define SSD_SYNTH_NUM_REGS				13
#define SSD_SYNTH_NUM_INIT_REGS			SSD_SYNTH_NUM_REGS + 4
#define SSD_INIT_SEQUENCE_LEN			18

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
static double ssd_CalculateRfDivider(double rf_out_freq_mhz);
static int ssd_GreatestCommonDivisor(uint32_t x, uint32_t y);
__STATIC_INLINE void ssd_165usDelay(void);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
uint8_t lg_ssd_synth_init_data[SSD_SYNTH_NUM_INIT_REGS][SSD_SYNTH_REG_LEN_BYTES] = {
		{0xFFU, 0xFFU, 0x04U, 0x1CU},	/* Register 12 */
		{0x00U, 0x61U, 0x30U, 0x0BU}, 	/* Register 11 */
		{0x00U, 0xC0U, 0x3EU, 0xBAU},	/* Register 10 */
		{0x2AU, 0x29U, 0xFCU, 0xC9U},	/* Register 9 */
		{0x10U, 0x2DU, 0x04U, 0x28U},	/* Register 8 */
		{0x12U, 0x00U, 0x00U, 0x67U},	/* Register 7 */
		{0x75U, 0xADU, 0x00U, 0x76U},	/* Register 6 */
		{0x00U, 0x80U, 0x00U, 0x25U},	/* Register 5 */
		{0x36U, 0x00U, 0xDDU, 0x84U},	/* Register 4 - Ref div-by 2 bit set, fPFD halved to 50 MHz*/
		{0x00U, 0x00U, 0x00U, 0x03U},	/* Register 3 */
		{0x00U, 0x50U, 0x03U, 0x22U},	/* Register 2 - Based on fPFD = 50 MHz */
		{0x06U, 0x66U, 0x66U, 0x61U}, 	/* Register 1 - Based on fPFD = 50 MHz */
		{0x00U, 0x20U, 0x06U, 0x60U},	/* Register 0 - Based on fPFD = 50 MHz, Auto Cal enabled */
		{0x34U, 0x00U, 0xDDU, 0x84U},	/* Register 4 - Ref div-by 2 bit cleared, fPFD h= 100 MHz*/
		{0x00U, 0x50U, 0x06U, 0x42U},	/* Register 2 - Based on fPFD = 100 MHz */
		{0x03U, 0x33U, 0x33U, 0x31U}, 	/* Register 1 - Based on fPFD = 100 MHz */
		{0x00U, 0x00U, 0x03U, 0x30U}	/* Register 0 - Based on fPFD = 100 MHz, Auto Cal disabled */
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
bool ssd_InitInstance(	ssd_SpiSynthDriver_t 		*p_inst,
						SPI_HandleTypeDef			*spi_device,
						ssd_AssertSynthCsFuncPtr_t	p_assert_synth_cs_func)
{
	p_inst->spi_device				= spi_device;
	p_inst->p_assert_synth_cs_func 	= p_assert_synth_cs_func;
	p_inst->initialised 			= true;

	return true;
}


/*****************************************************************************/
/**
* Initialise the SPI Synth device, manually controls the nCS signal and
* leaves it in the de-asserted state (HIGH).  Writes pre-defined setting
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
		/* De-assert the nCS signal to ensure it is in a known state */
		p_inst->p_assert_synth_cs_func(false);
		HAL_Delay(1U);

		/* Write to device */
		for (i = 0; i < SSD_SYNTH_NUM_INIT_REGS; ++i)
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
			/* Need a 165 us delay between programming Register 1 and 0 the
			 * first time, for simplicity in the initialisation sequence
			 * delay between each register write. */
			ssd_165usDelay();
		}

		/* Leave the nCS signal de-asserted */
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
* @param	rf_out_freq_mhz required centre frequency in MHz, range

* @return   true if successful, else false
* @note     Tidy up the magic numbers!
*
******************************************************************************/
bool ssd_SetCentreFreqMhz(ssd_SpiSynthDriver_t *p_inst, uint32_t rf_out_freq_mhz)
{
	const uint32_t f_pfd_hz = 100000000U;	/* 100 MHz */
	const uint32_t f_ch_hz = 1000000U;
	const uint32_t adc_clk_div = (uint32_t)ceil((((double)f_pfd_hz / 1.0E5F) - 2.0F) / 4.0F);
	const uint32_t mod1 = 16777216U;

	bool ret_val = false;
	double n = 0.0F;
	double n_frac = 0.0F;
	double f_vco_hz = 0.0F;
	double rf_div = ssd_CalculateRfDivider((double)rf_out_freq_mhz);
	uint32_t rf_div_bits = log2(rf_div);
	uint32_t mod2 = 0U;
	uint32_t n_int = 0U;
	uint32_t frac1 = 0U;
	uint32_t frac2 = 0U;
	uint32_t reg_val = 0U;

	if (p_inst->initialised &&
		((rf_out_freq_mhz >= SSD_MIN_CENTRE_FREQ_MHZ) &&
		(rf_out_freq_mhz <= SSD_MAX_CENTRE_FREQ_MHZ)))
	{
		/* Set Register 10 */
		reg_val = ((adc_clk_div & 0xFFU) << 6) | (0x300U << 14) | 0x30U | 0xAU;
		ret_val = ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 6 - Update RF Divider Setting */
		reg_val = 0x750D0076U | (rf_div_bits << 21);
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 4 - Counter Reset Enabled */
		reg_val = 0x3400DD94U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Calculate Register 2, 1 and 0 values based on fPFD = 50 MHz */
		f_vco_hz = ((double)rf_out_freq_mhz * 1.0E6F) * rf_div;
		n = f_vco_hz / (double)(f_pfd_hz / 2U);
		n_int = (uint32_t)floor(n);
		n_frac = n - (double)n_int;
		frac1 = (uint32_t)floor(n_frac * (double)mod1);
		mod2 = (f_pfd_hz / 2U) / ssd_GreatestCommonDivisor((f_pfd_hz / 2U), f_ch_hz);
		frac2 = (uint32_t)floor((((double)mod1 * n_frac) - (double)frac1) * (double)mod2);

		/* Set Register 2 */
		reg_val = ((frac2 & 0x00003FFFU) << 18) | ((mod2 & 0x00003FFFU) << 4) | 0x00000002U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 1 */
		reg_val = ((frac1 & 0x00FFFFFFU) << 4) | 0x00000001U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 0 - Auto Cal disabled, Bit 21 set to '0'  */
		reg_val = ((n_int < 75 ? 0x0U : (0x1U << 20))) | ((n_int & 0x0000FFFFU) << 4) | 0x0U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 4 - Counter Reset Disabled, Ref div-by 2 bit set, fPFD halved to 50 MHz */
		reg_val = 0x3600DD84U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		ssd_165usDelay();

		/* Set Register 0 - Auto Cal enabled, Bit 21 set to '1'  */
		reg_val = (0x1U << 21) | ((n_int < 75 ? 0x0U : (0x1U << 20))) | ((n_int & 0x0000FFFFU) << 4) | 0x0U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 4 - Ref div-by 2 bit cleared, fPFD = 100 MHz */
		reg_val = 0x3400DD84U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Calculate Register 2, 1 and 0 values based on fPFD = 100 MHz */
		f_vco_hz = ((double)rf_out_freq_mhz * 1.0E6F) * rf_div;
		n = f_vco_hz / (double)(f_pfd_hz);
		n_int = (uint32_t)floor(n);
		n_frac = n - (double)n_int;
		frac1 = (uint32_t)floor(n_frac * (double)mod1);
		mod2 = (f_pfd_hz) / ssd_GreatestCommonDivisor((f_pfd_hz), f_ch_hz);
		frac2 = (uint32_t)floor((((double)mod1 * n_frac) - (double)frac1) * (double)mod2);

		/* Set Register 2 */
		reg_val = ((frac2 & 0x00003FFFU) << 18) | ((mod2 & 0x00003FFFU) << 4) | 0x00000002U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 1 */
		reg_val = ((frac1 & 0x00FFFFFFU) << 4) | 0x00000001U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);

		/* Set Register 0 - Auto Cal disabled,, Bit 21 set to '0'  */
		reg_val = ((n_int < 75 ? 0x0U : (0x1U << 20))) | ((n_int & 0x0000FFFFU) << 4) | 0x0U;
		ret_val &= ssd_WriteSynthRegister(p_inst, reg_val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the ADF4355 synth power-down bit, DB6 in Register 4, all other bits are
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
	uint8_t *reg4_init_vals = &lg_ssd_synth_init_data[SSD_SYNTH_NUM_INIT_REGS - 4][0];
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
* @param	reg_val register value
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
* Calculates the required RF divider value based on the required RFOUTB
* frequency.
*
* @param	rf_out_hz required output frequency in MHz
* @return   required RF divider value as double, -1.0F if the requested
* 			frequency is out of range.
*
******************************************************************************/
static double ssd_CalculateRfDivider(double rf_out_freq_mhz)
{
	if ((rf_out_freq_mhz >= 3400.0F) && (rf_out_freq_mhz <= 6800.0F))
	{
		return 1.0F;
	}
	else if ((rf_out_freq_mhz >= 1700.0F) && (rf_out_freq_mhz < 3400.0F))
	{
		return 2.0F;
	}
	else if ((rf_out_freq_mhz >= 850.0F) && (rf_out_freq_mhz < 1700.0F))
	{
		return 4.0F;
	}
	else if ((rf_out_freq_mhz >= 425.0F) && (rf_out_freq_mhz < 800.0F))
	{
		return 8.0F;
	}
	else if ((rf_out_freq_mhz >= 212.5F) && (rf_out_freq_mhz < 425.0F))
	{
		return 16.0F;
	}
	else if ((rf_out_freq_mhz >= 106.25F) && (rf_out_freq_mhz < 212.5F))
	{
		return 32.0F;
	}
	else if ((rf_out_freq_mhz >= 53.125F) && (rf_out_freq_mhz < 106.25F))
	{
		return 64.0F;
	}
	else
	{
		return -1.0F;
	}
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


/*****************************************************************************/
/**
* 165 us delay required between Register 1 and Register 0 writes for synth
* frequency tuning.  The actual delay will depend on compiler optimisation,
* the factor of '3' attempts to compensate for loop overhead.
*
******************************************************************************/
__STATIC_INLINE void ssd_165usDelay(void)
{
	volatile uint32_t wait_loop_index = (165U * (SystemCoreClock / (100000U * 3U))) / 10U;
	while(wait_loop_index-- != 0);
}
