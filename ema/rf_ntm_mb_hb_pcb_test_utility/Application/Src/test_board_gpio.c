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
		p_inst->i2c_gpio_exp[i].io_pu_mask			= lg_tbg_gpio_exp_io_pu_mask[i];
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
* Enable/disable the DDS 20 dB attenuator
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten true to enable attenuator, false to disable attenuator
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_SetDdsAtten(tbg_TestBoardGpio_t *p_inst, bool atten)
{
	bool ret_val = false;
	igd_PinState pin_state = igd_PinReset;

	if (p_inst->initialised)
	{
		if (atten)
		{
			pin_state = igd_PinReset;
		}
		else
		{
			pin_state = igd_PinSet;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_TX_ATT_DDS_EXP],
								TBG_TX_ATT_DDS_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the fine attenuation to specified value, attenuator works by winding out
* attenuation, 0 = max attenuation so value must be converted to set pins
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten required attenuation in 0.25 dB steps, e.g. 5 = 1.25 dB
* @return   true if setting attenuation is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetTxFineAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((atten >= TBG_TX_ATT_FINE_MIN_VAL) && (atten <= TBG_TX_ATT_FINE_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_TX_ATT_FINE_EXP], &temp))
		{
			atten = (TBG_TX_ATT_FINE_MAX_VAL - atten);
			temp &= (~TBG_TX_ATT_FINE_PINS);
			temp |= ((atten << TBG_TX_ATT_FINE_SHIFT) & TBG_TX_ATT_FINE_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_TX_ATT_FINE_EXP],
										temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the coarse attenuation to specified value, attenuator works by winding out
* attenuation, 0 = max attenuation so value must be converted to set pins
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten required attenuation in 3 dB steps, e.g. 5 = 15 dB
* @return   true if setting attenuation is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetTxFCoarseAtten(tbg_TestBoardGpio_t *p_inst, uint16_t atten)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((atten >= TBG_TX_ATT_COARSE_MIN_VAL) && (atten <= TBG_TX_ATT_COARSE_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_TX_ATT_COARSE_EXP], &temp))
		{
			atten = (TBG_TX_ATT_COARSE_MAX_VAL - atten);
			temp &= (~(TBG_TX_ATT_COARSE_PINS_LO | TBG_TX_ATT_COARSE_PINS_HI));
			temp |= ((atten << TBG_TX_ATT_COARSE_SHIFT_LO) & TBG_TX_ATT_COARSE_PINS_LO);
			temp |= ((atten << TBG_TX_ATT_COARSE_SHIFT_HI) & TBG_TX_ATT_COARSE_PINS_HI);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_TX_ATT_COARSE_EXP],
										temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the Rx LNA bypass signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	enable true to enable bypass, false for no bypass
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_SetRxLnaBypass(tbg_TestBoardGpio_t *p_inst, bool bypass)
{
	bool ret_val = false;
	igd_PinState pin_state = igd_PinReset;

	if (p_inst->initialised)
	{
		if (bypass)
		{
			pin_state = igd_PinSet;
		}
		else
		{
			pin_state = igd_PinReset;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_LNA_BYPASS_EXP],
								TBG_LNA_BYPASS_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the receive pre-selector path
*
* @param    p_inst pointer to I2C GPIO driver instainnce data
* @param	rx_presel receiver pre-selector path: TBG_RX_PATH_MIN_VAL to
* 			TBG_RX_PATH_MAX_VAL
* @return   true if setting receiver pre-selector path is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetRxPreselectorPath(tbg_TestBoardGpio_t *p_inst, uint16_t rx_presel)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((rx_presel >= TBG_RX_PATH_MIN_VAL) && (rx_presel <= TBG_RX_PATH_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_RX_PATH_EXP], &temp))
		{
			temp &= (~TBG_RX_PATH_PINS);
			temp |= ((rx_presel << TBG_RX_PATH_SHIFT) & TBG_RX_PATH_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_RX_PATH_EXP],
										temp);
		}
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Accessor to constant array of strings describing the receive pre-selector
* paths, array length is TBG_RX_PATH_MAX_VAL + 1
*
* @return   Pointer to first element of array of strings describing the
* 			receive pre-selector paths
* @note     None
*
******************************************************************************/
const char **tbg_GetRxPreselectorPathStr(void)
{
	return lg_tbg_rx_presel_str;
}


/*****************************************************************************/
/**
* Set the transmit path
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	tx_path transmitter path: TBG_TX_PATH_MIN_VAL to TBG_TX_PATH_MAX_VAL
* @return   true if setting transmit path is successful, else false
* @note     None
*
******************************************************************************/
bool tbg_SetTxPath(tbg_TestBoardGpio_t *p_inst, uint16_t tx_path)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((tx_path >= TBG_TX_PATH_MIN_VAL) && (tx_path <= TBG_TX_PATH_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_TX_PATH_EXP], &temp))
		{
			temp &= (~TBG_TX_PATH_PINS);
			temp |= ((tx_path << TBG_TX_PATH_SHIFT) & TBG_TX_PATH_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_TX_PATH_EXP],
										temp);
		}
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Accessor to constant array of strings describing the transmit paths,
* array length is TBG_TX_PATH_MAX_VAL + 1
*
* @return   Pointer to first element of array of strings describing the
* 			transmit paths
* @note     None
*
******************************************************************************/
const char **tbg_GetTxPathStr(void)
{
	return lg_tbg_tx_path_str;
}


/*****************************************************************************/
/**
* Set the receiver enable signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	enable true to enable rx, false to disable rx
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_RxEnable(tbg_TestBoardGpio_t *p_inst, bool enable)
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

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_RX_EN_EXP],
								TBG_RX_EN_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the transmitter enable signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	enable true to enable tx, false to disable tx
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_TxEnable(tbg_TestBoardGpio_t *p_inst, bool enable)
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

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_TX_EN_EXP],
								TBG_TX_EN_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the transceiver reset signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	reset true to assert reset, false to de-assert reset
* @return   true if pin set, else false
* @note     None
*
******************************************************************************/
bool tbg_XcvrReset(tbg_TestBoardGpio_t *p_inst, bool reset)
{
	bool ret_val = false;
	igd_PinState pin_state = igd_PinReset;

	if (p_inst->initialised)
	{
		if (reset)
		{
			pin_state = igd_PinReset;
		}
		else
		{
			pin_state = igd_PinSet;
		}

		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_XCVR_RESET_N_EXP],
								TBG_XCVR_RESET_N_PIN, pin_state);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return state of Synthesiser Lock Detect signals
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_gp_interrupt to variable that receives GP interrupt signal,
* 			true if interrupt asserted, else false
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool tbg_ReadGpInterrupt(tbg_TestBoardGpio_t *p_inst, bool *p_gp_interrupt)
{
	bool ret_val = false;
	igd_PinState temp = igd_PinReset;

	if (p_inst->initialised)
	{
		ret_val = igd_ReadPin(	&p_inst->i2c_gpio_exp[TBG_GP_INTERRUPT_EXP],
								TBG_GP_INTERRUPT_PIN, &temp);
		if (ret_val)
		{
			if (temp == igd_PinSet)
			{
				*p_gp_interrupt = true;
			}
			else
			{
				*p_gp_interrupt = false;
			}
		}
	}

	return ret_val;
}
