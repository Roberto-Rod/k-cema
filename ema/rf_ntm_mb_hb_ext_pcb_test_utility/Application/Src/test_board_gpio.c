/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file test_board_gpio.c
*
* Driver for the KT-000-0202-00 board under test GPIO, GPIO is driven via
* MCP23017 I2C GPIO expanders on the KT-000-0160-00 test interface board
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "test_board_gpio.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define TBG_BOARD_ID_EXP		0
#define TBG_BOARD_ID_PINS		(IGD_GPIO_PIN_12 | IGD_GPIO_PIN_11)
#define TBG_BOARD_ID_SHIFT		11

#define TBG_TX_ATT_DDS_EXP	0
#define TBG_TX_ATT_DDS_PIN	IGD_GPIO_PIN_0

#define TBG_TX_ATT_FINE_EXP		0
#define TBG_TX_ATT_FINE_PINS	(IGD_GPIO_PIN_7 | IGD_GPIO_PIN_6 | IGD_GPIO_PIN_5 | IGD_GPIO_PIN_4 | IGD_GPIO_PIN_3 | IGD_GPIO_PIN_2 | IGD_GPIO_PIN_1)
#define TBG_TX_ATT_FINE_SHIFT	1
#define	TBG_TX_ATT_FINE_MIN_VAL	0U
#define	TBG_TX_ATT_FINE_MAX_VAL	127U

#define TBG_TX_ATT_COARSE_EXP	0
#define TBG_TX_ATT_COARSE_PIN	IGD_GPIO_PIN_9

#define TBG_SYNTH_LD_EXP		2
#define TBG_SYNTH_LD_PIN		IGD_GPIO_PIN_13

#define TBG_SYNTH_CS_N_EXP		2
#define TBG_SYNTH_CS_N_PIN		IGD_GPIO_PIN_14

#define TBG_LNA_BYPASS_EXP		1
#define TBG_LNA_BYPASS_PIN		IGD_GPIO_PIN_0

#define TBG_RX_PATH_LO_EXP		1
#define TBG_RX_PATH_LO_PINS		(IGD_GPIO_PIN_3 | IGD_GPIO_PIN_2 | IGD_GPIO_PIN_1)
#define TBG_RX_PATH_LO_LSHIFT	1
#define TBG_RX_PATH_HI_EXP		2
#define TBG_RX_PATH_HI_PINS		(IGD_GPIO_PIN_12)
#define TBG_RX_PATH_HI_LSHIFT	12
#define TBG_RX_PATH_LO_MASK		0x07U
#define TBG_RX_PATH_HI_MASK		0x08U
#define TBG_RX_PATH_HI_RSHIFT	3
#define	TBG_RX_PATH_MIN_VAL		0U
#define	TBG_RX_PATH_MAX_VAL		15U

#define TBG_TX_PATH_EXP			1
#define TBG_TX_PATH_PINS		(IGD_GPIO_PIN_6 | IGD_GPIO_PIN_5 | IGD_GPIO_PIN_4)
#define TBG_TX_PATH_SHIFT		4
#define	TBG_TX_PATH_MIN_VAL		0U
#define	TBG_TX_PATH_MAX_VAL		7U

#define TBG_RX_EN_EXP			2
#define TBG_RX_EN_PIN			IGD_GPIO_PIN_0

#define TBG_TX_EN_EXP			2
#define TBG_TX_EN_PIN			IGD_GPIO_PIN_1

#define TBG_XCVR_TX_PATH_EXP		1
#define TBG_XCVR_TX_PATH_PINS		(IGD_GPIO_PIN_7)
#define TBG_XCVR_TX_PATH_SHIFT		7
#define	TBG_XCVR_TX_PATH_MIN_VAL	0U
#define	TBG_XCVR_TX_PATH_MAX_VAL	1U

#define TBG_XCVR_RESET_N_EXP	2
#define TBG_XCVR_RESET_N_PIN	IGD_GPIO_PIN_2

#define TBG_GP_INTERRUPT_EXP	2
#define TBG_GP_INTERRUPT_PIN	IGD_GPIO_PIN_3

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
const uint8_t 	lg_tbg_gpio_exp_i2c_addr[TBG_NO_I2C_EXPANDERS] 			= {0x27U << 1, 	0x26U << 1,	0x25U << 1};
const uint16_t  lg_tbg_gpio_exp_io_dir_mask[TBG_NO_I2C_EXPANDERS] 		= {0xF800U, 	0xFF00U, 	0x2FF8U}; /* '1' = ip; '0' = op */
const uint16_t  lg_tbg_gpio_exp_io_pu_mask[TBG_NO_I2C_EXPANDERS]		= {0xFFFFU, 	0xFFFFU, 	0xFFFFU}; /* '1' = en; '0' = dis */
const uint16_t  lg_tbg_gpio_exp_default_op_mask[TBG_NO_I2C_EXPANDERS] 	= {0x0000U, 	0x0000U, 	0x4000U};

const char *lg_tbg_rx_path_str[TBG_RX_PATH_MAX_VAL + 1] = \
{
	"RX0: 400-650 MHz",
	"RX1: 550-1050 MHz",
	"RX2: 950-1450 MHz",
	"RX3: 1350-2250 MHz",
	"RX4: 2150-3050 MHz",
	"RX5: 2950-4650 MHz",
	"RX6: 4550-6000 MHz",
	"RX7: 5700-8000 MHz",
	"OBS0: 400-650 MHz",
	"OBS1: 550-1050 MHz",
	"OBS2: 950-1450 MHz",
	"OBS3: 1350-2250 MHz",
	"OBS4: 2150-3050 MHz",
	"OBS5: 2950-4650 MHz",
	"OBS6: 4550-6000 MHz",
	"OBS7: 5700-8000 MHz"
};

const char *lg_tbg_tx_path_str[TBG_TX_PATH_MAX_VAL + 1] = \
{
	"DDS1: 1400-1880 MHz",
	"DDS2: 1850-2250 MHz",
	"DDS3: 2250-3000 MHz",
	"DDS4: 2400-3400 MHz",
	"DDS5: 3400-4600 MHz",
	"DDS6: 4600-6000 MHz",
	"DDS7: 5700-8000 MHz",
	"DDS0: 400-1500 MHz",
};

const char *lg_tbg_xcvr_tx_path_str[TBG_XCVR_TX_PATH_MAX_VAL + 1] = \
{
	"DDS0: 400-6000 MHz",
	"DDS1: 5700-8000 MHz",
};

/*****************************************************************************/
/**
* Initialise the test board GPIO drivers
*
* @param    p_inst pointer to test board GPIO driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			GPIO expanders are connected to
* @param	i2c_reset_gpio_port HAL driver GPIO port for GPIO expander reset
* @param	i2c_reset_gpio_pin HAL driver GPIO pin for GPIO expander reset
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
* @return   true if attenuator set, else false
*
******************************************************************************/
bool tbg_SetDdsAtten(tbg_TestBoardGpio_t *p_inst, bool atten)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_TX_ATT_DDS_EXP],
								TBG_TX_ATT_DDS_PIN,
								atten ? igd_PinReset : igd_PinSet);
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

			ret_val = igd_WritePinsVal(&p_inst->i2c_gpio_exp[TBG_TX_ATT_FINE_EXP],
									   temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Enable/disable the coarse 20 dB attenuator
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	atten true to enable attenuator, false to disable attenuator
* @return   true if attenuator set, else false
*
******************************************************************************/
bool tbg_SetTxFCoarseAtten(tbg_TestBoardGpio_t *p_inst, bool atten)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(&p_inst->i2c_gpio_exp[TBG_TX_ATT_COARSE_EXP],
							   TBG_TX_ATT_COARSE_PIN,
							   atten ? igd_PinReset : igd_PinSet);
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

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_LNA_BYPASS_EXP],
								TBG_LNA_BYPASS_PIN,
								bypass ? igd_PinSet : igd_PinReset);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the receive path
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	rx_path receiver pre-selector path: TBG_RX_PATH_MIN_VAL to
* 			TBG_RX_PATH_MAX_VAL
* @return   true if setting receiver pre-selector path is successful, else false
*
******************************************************************************/
bool tbg_SetRxPath(tbg_TestBoardGpio_t *p_inst, uint16_t rx_path)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((rx_path >= TBG_RX_PATH_MIN_VAL) && (rx_path <= TBG_RX_PATH_MAX_VAL)))
	{
		/* Set the LO bits */
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_RX_PATH_LO_EXP], &temp))
		{
			temp &= (~TBG_RX_PATH_LO_PINS);
			temp |= (((rx_path & TBG_RX_PATH_LO_MASK) << TBG_RX_PATH_LO_LSHIFT) & TBG_RX_PATH_LO_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_RX_PATH_LO_EXP], temp);
		}

		/* Set the HI bits */
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_RX_PATH_HI_EXP], &temp))
		{
			temp &= (~TBG_RX_PATH_HI_PINS);
			temp |= ((((rx_path & TBG_RX_PATH_HI_MASK) >> TBG_RX_PATH_HI_RSHIFT) << TBG_RX_PATH_HI_LSHIFT) & TBG_RX_PATH_HI_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_RX_PATH_HI_EXP], temp);
		}
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Accessor to constant array of strings describing the receive paths, array
* length is TBG_RX_PATH_MAX_VAL + 1
*
* @return   Pointer to first element of array of strings describing the
* 			receive rx paths
*
******************************************************************************/
const char **tbg_GetRxPathStr(void)
{
	return lg_tbg_rx_path_str;
}


/*****************************************************************************/
/**
* Set the transmit path
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	tx_path transmitter path: TBG_TX_PATH_MIN_VAL to TBG_TX_PATH_MAX_VAL
* @return   true if setting transmit path is successful, else false
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

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_RX_EN_EXP],
								TBG_RX_EN_PIN,
								enable ? igd_PinSet : igd_PinReset);
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
*
******************************************************************************/
bool tbg_TxEnable(tbg_TestBoardGpio_t *p_inst, bool enable)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_TX_EN_EXP],
								TBG_TX_EN_PIN,
								enable ? igd_PinSet : igd_PinReset);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the transceiver transmit path
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	tx_path transmitter path: TBG_XCVR_TX_PATH_MIN_VAL to
* 			TBG_XCVR_TX_PATH_MAX_VAL
* @return   true if setting transceiver transmit path is successful, else false
*
******************************************************************************/
bool tbg_SetXcvrTxPath(tbg_TestBoardGpio_t *p_inst, uint16_t tx_path)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised &&
		((tx_path >= TBG_XCVR_TX_PATH_MIN_VAL) && (tx_path <= TBG_XCVR_TX_PATH_MAX_VAL)))
	{
		if (igd_ReadPinsVal(&p_inst->i2c_gpio_exp[TBG_XCVR_TX_PATH_EXP], &temp))
		{
			temp &= (~TBG_XCVR_TX_PATH_PINS);
			temp |= ((tx_path << TBG_XCVR_TX_PATH_SHIFT) & TBG_XCVR_TX_PATH_PINS);

			ret_val = igd_WritePinsVal(	&p_inst->i2c_gpio_exp[TBG_XCVR_TX_PATH_EXP], temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Accessor to constant array of strings describing the transceiver transmit paths,
* array length is TBG_TX_PATH_MAX_VAL + 1
*
* @return   Pointer to first element of array of strings describing the
* 			transmit paths
* @note     None
*
******************************************************************************/
const char **tbg_GetXcvrTxPathStr(void)
{
	return lg_tbg_xcvr_tx_path_str;
}


/*****************************************************************************/
/**
* Set the transceiver reset signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	reset true to assert reset, false to de-assert reset
* @return   true if pin set, else false
*
******************************************************************************/
bool tbg_XcvrReset(tbg_TestBoardGpio_t *p_inst, bool reset)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_XCVR_RESET_N_EXP],
								TBG_XCVR_RESET_N_PIN,
								reset ? igd_PinReset : igd_PinSet);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return state of transceiver interrupt signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_gp_interrupt to variable that receives GP interrupt signal,
* 			true if interrupt asserted, else false
* @return   true if read successful, else false
*
******************************************************************************/
bool tbg_XcvrReadGpInterrupt(tbg_TestBoardGpio_t *p_inst, bool *p_gp_interrupt)
{
	bool ret_val = false;
	igd_PinState temp = igd_PinReset;

	if (p_inst->initialised)
	{
		ret_val = igd_ReadPin(	&p_inst->i2c_gpio_exp[TBG_GP_INTERRUPT_EXP],
								TBG_GP_INTERRUPT_PIN, &temp);
		if (ret_val)
		{
			*p_gp_interrupt = (temp == igd_PinSet) ? true : false;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Asserts/de-asserts the Synth nCS signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	assert true to assert active-low chip select signals, else false
* 			to de-assert
*
******************************************************************************/
bool tbg_AssertSynthChipSelect(tbg_TestBoardGpio_t *p_inst, bool assert)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WritePin(	&p_inst->i2c_gpio_exp[TBG_SYNTH_CS_N_EXP],
								TBG_SYNTH_CS_N_PIN,
								assert ? igd_PinReset : igd_PinSet);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return state of synthesiser Lock Detect signal
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_lock_detect to variable that receives synth lock detect signal,
* 			true if locked, else false
* @return   true if read successful, else false
*
******************************************************************************/
bool tbg_ReadSynthLockDetect(tbg_TestBoardGpio_t *p_inst, bool *p_lock_detect)
{
	bool ret_val = false;
	igd_PinState temp = igd_PinReset;

	if (p_inst->initialised)
	{
		ret_val = igd_ReadPin(	&p_inst->i2c_gpio_exp[TBG_SYNTH_LD_EXP],
								TBG_SYNTH_LD_PIN, &temp);
		if (ret_val)
		{
			*p_lock_detect = (temp == igd_PinSet) ? true : false;
		}
	}

	return ret_val;
}
