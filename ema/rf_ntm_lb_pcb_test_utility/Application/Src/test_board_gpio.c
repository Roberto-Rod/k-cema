/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file test_board_gpio.c
*
* Driver for the KT-000-0136-00 board under test GPIO, GPIO is driven via
* MCP23017 I2C GPIO expanders on the KT-000-0155-00 test interface board
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#define __TEST_BOARD_GPIO_C

#include "test_board_gpio.h"

/*****************************************************************************/
/**
* Initialise the test board GPIO drivers
*
* @param    p_inst pointer to test board GPIO driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			GPIO expanders are connected to
* @param	i2c_reset_gpio_port HAL driver GPIO port for GPIO expander reset
* @param	i2c_reset_gpio_pin HAL driver GPIO pin for GPIO expander reset
* @return   None
* @note     None
*
******************************************************************************/
void tbg_Init(	tbg_TestBoardGpio_t	*p_inst,
				I2C_HandleTypeDef	*i2c_device,
				GPIO_TypeDef		*i2c_reset_gpio_port,
				uint16_t 			i2c_reset_gpio_pin)
{
	int16_t i;

	/* Set up the I2C GPIO driver instances for the test board, copy data... */
	for (i = 0; i < TBG_NO_I2C_EXPANDERS; ++i)
	{
		p_inst->i2c_gpio_exp[i].i2c_device 			= i2c_device;
		p_inst->i2c_gpio_exp[i].i2c_address 		= lg_tbg_gpio_exp_i2c_addr[i];
		p_inst->i2c_gpio_exp[i].io_dir_mask 		= lg_tbg_gpio_exp_io_dir_mask[i];
		p_inst->i2c_gpio_exp[i].default_op_mask 	= lg_tbg_gpio_exp_default_op_mask[i];
		p_inst->i2c_gpio_exp[i].i2c_reset_gpio_port	= i2c_reset_gpio_port;
		p_inst->i2c_gpio_exp[i].i2c_reset_gpio_pin 	= i2c_reset_gpio_pin;
	}

	/* Initialise IO signals... */
	for (i = 0; i < TBG_NO_I2C_EXPANDERS; ++i)
	{
		(void) igd_Init(&p_inst->i2c_gpio_exp[i]);
	}

	p_inst->initialised = true;
}


/*****************************************************************************/
/**
* Set the receiver power enable signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	enable true to enable rx power, false to disable rx power
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_RxPowerEnable(tbg_TestBoardGpio_t *p_inst, bool enable)
{
	bool ret_val = false;
	igd_PinState pin_state = igd_PinReset;

	if (p_inst->initialised)
	{
		if (enable)
		{
			pin_state = igd_PinSet;
		}
		else
		{
			pin_state = igd_PinReset;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_RX_PWR_EN_EXP],
								TBG_RX_PWR_EN_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return the Board ID signals
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_board_id pointer to variable that receives the Board ID value
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool tbg_ReadBoardId(tbg_TestBoardGpio_t *p_inst, uint16_t *p_board_id)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised)
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_BOARD_ID_EXP], &temp))
		{
			*p_board_id = (temp & TBG_BOARD_ID_PINS) >> TBG_BOARD_ID_SHIFT;
			ret_val = true;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return state of Synthesiser Lock Detect signals
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_ld1 pointer to variable that receives Synthesiser Lock Detect 1
* @param	p_ld1 pointer to variable that receives Synthesiser Lock Detect 2
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool tbg_ReadLockDetects(tbg_TestBoardGpio_t *p_inst, bool *p_ld1, bool *p_ld2)
{
	bool ret_val = false;
	igd_PinState temp = igd_PinReset;

	if (p_inst->initialised)
	{
		ret_val = igd_ReadPin(	&p_inst->i2c_gpio_exp[TBG_SYNTH_LD1_EXP],
								TBG_SYNTH_LD1_PIN, &temp);
		if (ret_val)
		{
			if (temp == igd_PinSet)
			{
				*p_ld1 = true;
			}
			else
			{
				*p_ld1 = false;
			}

			ret_val = igd_ReadPin(	&p_inst->i2c_gpio_exp[TBG_SYNTH_LD2_EXP],
									TBG_SYNTH_LD2_PIN, &temp);
			if (ret_val)
			{
				if (temp == igd_PinSet)
				{
					*p_ld2 = true;
				}
				else
				{
					*p_ld2 = false;
				}
			}
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set GPOs to select either synth 1 or 2
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	synth synth to enable one of tbg_SynthRange_t enumerated values
* @return   true if synth selection is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetSynthSelect(tbg_TestBoardGpio_t *p_inst, tbg_SynthRange_t synth)
{
	bool ret_val = false;
	igd_PinState pin_state;

	if (p_inst->initialised)
	{
		if (synth == tbg_Synth1)
		{
			pin_state = igd_PinReset;
		}
		else
		{
			pin_state = igd_PinSet;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_SYNTH_SEL_EXP],
								TBG_SYNTH_SEL_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the pre-selector path
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	presel pre-selector path: TBG_PRESEL_MIN_VAL to TBG_PRESEL_MAX_VAL
* @return   true if setting pre-selector path is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetPreselectorPath(tbg_TestBoardGpio_t *p_inst, uint16_t presel)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((presel >= TBG_PRESEL_MIN_VAL) && (presel <= TBG_PRESEL_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_PRESEL_EXP], &temp))
		{
			temp &= (~TBG_PRESEL_PINS);
			temp |= ((presel << TBG_PRESEL_SHIFT) & TBG_PRESEL_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_PRESEL_EXP],
										temp);
		}
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Accessor to constant array of strings describing the pres-selector paths,
* array length is TBG_PRESEL_MAX_VAL + 1
*
* @return   Pointer to first element of array of strings describing the
* 			pre-selector
* @note     None
*
******************************************************************************/
const char **iad_GetPreselectorStr(void)
{
	return lg_tbg_presel_str;
}


/*****************************************************************************/
/**
* Set the RF attenuation to specified value, attenuator works by winding out
* attenuation, 0 = max attenuation so value must be converted to set pins
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten required attenuation in 0.5 dB steps
* @return   true if setting attenuation is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetRfAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten)
{
	bool ret_val = false;
	uint16_t temp = 0U;
	uint16_t bit_4 = 0U;
	uint16_t bit_5 = 0U;

	if (p_inst->initialised &&
		((atten >= TBG_RF_ATTEN_MIN_VAL) && (atten <= TBG_RF_ATTEN_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_RF_ATTEN_EXP], &temp))
		{
			atten = (TBG_RF_ATTEN_MAX_VAL - atten);
			temp &= (~TBG_RF_ATTEN_PINS);
			temp |= ((atten << TBG_RF_ATTEN_SHIFT) & TBG_RF_ATTEN_PINS);

			/* Pins 4 and 5 are swapped so manipulate the value to compensate */
			if (temp & IGD_GPIO_PIN_9)
			{
				bit_4 = IGD_GPIO_PIN_10;
			}

			if (temp & IGD_GPIO_PIN_10)
			{
				bit_5 = IGD_GPIO_PIN_9;
			}

			temp &= (~(IGD_GPIO_PIN_10 | IGD_GPIO_PIN_9));
			temp |= (bit_4 | bit_5);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_RF_ATTEN_EXP],
										temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the IF attenuation to specified value, attenuator works by winding out
* attenuation, 0 = maxs attenuation so value must be converted to set pins
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten required attenuation in 0.5 dB steps
* @return   true if setting attenuation is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetIfAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((atten >= TBG_IF_ATTEN_MIN_VAL) && (atten <= TBG_IF_ATTEN_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_IF_ATTEN_EXP], &temp))
		{
			atten = (TBG_IF_ATTEN_MAX_VAL - atten);
			temp &= (~TBG_IF_ATTEN_PINS);
			temp |= ((atten << TBG_IF_ATTEN_SHIFT) & TBG_IF_ATTEN_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_IF_ATTEN_EXP],
										temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the LNA bypass signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	enable true to enable bypass, false for no bypass
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_SetLnaBypass(tbg_TestBoardGpio_t *p_inst, bool bypass)
{
	bool ret_val = false;
	igd_PinState pin_state = igd_PinReset;

	if (p_inst->initialised)
	{
		if (bypass)
		{
			pin_state = igd_PinReset;
		}
		else
		{
			pin_state = igd_PinSet;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_LNA_BYPASS_EXP],
								TBG_LNA_BYPASS_PIN, pin_state);
	}

	return ret_val;
}
