/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
*
* @file keypad_test_board.c
*
* Driver for the KT-000-0203-00 Keypad Test Interface board, sets the four
* keypad button state using Microchip MCP23017 I2C GPIO expander.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
*
******************************************************************************/
#include "keypad_test_board.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define KTB_MCP23017_IODIR_REG_ADDR		0x00U
#define KTB_MCP23017_GPIO_REG_ADDR		0x12U

#define KTB_MCP23017_WR_LEN				3U
#define KTB_MCP23017_WR_REG_ADDR_LEN	1U
#define KTB_MCP23017_RD_LEN				2U

#define KTB_I2C_TIMEOUT_MS				100U

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
static bool ktb_ReadRegister(   ktb_KeypadTestBoard_t *p_inst,
								uint8_t reg_addr, uint16_t *p_val);
static bool ktb_WriteRegister(	ktb_KeypadTestBoard_t *p_inst,
								uint8_t reg_addr, uint16_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
const char *lg_ktb_button_names[KTB_NO_BUTTONS] =
{
	"Power Button",
	"Button 0",
	"Button 1",
	"Button 2"
};

/*****************************************************************************/
/**
* Initialises the MCP23017 GPIO expander on the KT-000-0197-00 Keypad
* loopback test board.
*
* Sets all GPIO as outputs and buttons not-asserted
*
* @param    p_inst pointer to keypad test board driver instance data
* @param    i2c_device HAL driver handle for the I2C peripheral that the
* 			MCP23017 device is connected to
* @param	i2c_address MCP23017 device I2C bus address
* @param	i2c_reset_gpio_port HAL driver GPIO port for GPIO expander reset
* @param	i2c_reset_gpio_pin HAL driver GPIO pin for GPIO expander reset
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool ktb_InitInstance(	ktb_KeypadTestBoard_t *p_inst,
						I2C_HandleTypeDef *i2c_device,
						uint16_t i2c_address,
						GPIO_TypeDef *i2c_reset_gpio_port,
						uint16_t i2c_reset_gpio_pin)
{
	p_inst->i2c_device			= i2c_device;
	p_inst->i2c_address			= i2c_address;
	p_inst->i2c_reset_gpio_port	= i2c_reset_gpio_port;
	p_inst->i2c_reset_gpio_pin	= i2c_reset_gpio_pin;
	p_inst->initialised			= true;

	return true;
}


/*****************************************************************************/
/**
* Initialise the MCP23017 device, brings GPIO expanders out of reset and
* sets all the LEDs to the OFF state
*
* @param    p_inst pointer to keypad test board driver instance data
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool ktb_InitDevice(ktb_KeypadTestBoard_t *p_inst)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		HAL_GPIO_WritePin(	p_inst->i2c_reset_gpio_port,
							p_inst->i2c_reset_gpio_pin,
							GPIO_PIN_SET);

		/* Set initial state of buttons, de-asserted */
		ret_val = ktb_SetAllButtons(p_inst, false);

		/* Set all the GPIO pins as outputs */
		ret_val &= ktb_WriteRegister(p_inst, KTB_MCP23017_IODIR_REG_ADDR, 0x0000U);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Disable the MCP23017 device by asserting the reset signal>
*
* @param    p_inst pointer to keypad test board driver instance data
* @return   true if initialisation successful, else false
*
******************************************************************************/
void ktb_DisableDevice(ktb_KeypadTestBoard_t *p_inst)
{
	if (p_inst->initialised)
	{
		HAL_GPIO_WritePin(	p_inst->i2c_reset_gpio_port,
							p_inst->i2c_reset_gpio_pin,
							GPIO_PIN_RESET);
	}
}


/*****************************************************************************/
/**
* Sets all the buttons to the specified state, asserted/de-asserted
*
* @param    p_inst pointer to keypad test board driver instance data
* @param 	assert true to assert buttons, false to de-assert buttons
* @return   true buttons set successfully, else false
* @note     None
*
******************************************************************************/
bool ktb_SetAllButtons(ktb_KeypadTestBoard_t *p_inst, bool assert)
{
	uint16_t 	gpo;
	bool 		ret_val = false;

	if (p_inst->initialised)
	{
		gpo = assert ? 0x0004U : 0x0000U;
		ret_val = ktb_WriteRegister(p_inst, KTB_MCP23017_GPIO_REG_ADDR, gpo);
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Assert/de-assert and individual button.
*
* @param    p_inst pointer to keypad test board driver instance data
* @param 	btn button to set
* @param 	assert true to assert button, false to de-assert button
* @return   true if button set, else false
*
******************************************************************************/
bool ktb_SetButton(ktb_KeypadTestBoard_t *p_inst, ktb_Buttons_t btn, bool assert)
{
	uint16_t gpo = 0U;
	bool ret_val = true;

	if (p_inst->initialised && (btn < ktb_no_buttons))
	{
		ret_val &= ktb_ReadRegister(p_inst, KTB_MCP23017_GPIO_REG_ADDR, &gpo);

		if (assert)
		{
			gpo |= (1 << btn);
		}
		else
		{
			gpo &= (~(1 << btn));
		}

		ret_val &= ktb_WriteRegister(p_inst, KTB_MCP23017_GPIO_REG_ADDR, gpo);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Accessor to array of strings describing the buttons, array length is
* KTB_NO_BUTTONS.
*
* @return   Pointer to first element of array of strings describing the button
* 			names
*
******************************************************************************/
const char **ktb_GetButtonNames(void)
{
	return lg_ktb_button_names;
}


/*****************************************************************************/
/**
* Performs a 16-bit register read from the specified MCP23017 address
*
* @param    p_inst pointer to keypad test board driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives 16-bit register value
* 			read from device
* @return   true if read successful, else false
*
******************************************************************************/
static bool ktb_ReadRegister(   ktb_KeypadTestBoard_t *p_inst,
								uint8_t reg_addr, uint16_t *p_val)
{
	bool ret_val = false;
	uint8_t buf[KTB_MCP23017_RD_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, KTB_MCP23017_WR_REG_ADDR_LEN,
								KTB_I2C_TIMEOUT_MS) == HAL_OK)
	{
		/* Read the register */
		if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
									buf, KTB_MCP23017_RD_LEN,
									KTB_I2C_TIMEOUT_MS) == HAL_OK)
		{
			*p_val = (uint16_t)((uint16_t)(buf[1] << 8) | (uint16_t)buf[0]);
			ret_val = true;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 16-bit register write to the specified MCP23017 address
*
* @param    p_inst pointer to keypad test board driver instance data
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
* @return   true if write successful, else false
*
******************************************************************************/
static bool ktb_WriteRegister(	ktb_KeypadTestBoard_t *p_inst,
								uint8_t reg_addr, uint16_t val)
{
	bool ret_val;
	uint8_t buf[KTB_MCP23017_WR_LEN];

	buf[0] = reg_addr;
	buf[1] = (uint8_t)(val & 0xFFU);
	buf[2] = (uint8_t)((val >> 8) & 0xFFU);

	ret_val = (HAL_I2C_Master_Transmit(	p_inst->i2c_device,
										p_inst->i2c_address,
										buf,
										KTB_MCP23017_WR_LEN,
										KTB_I2C_TIMEOUT_MS) == HAL_OK);
	return ret_val;
}
