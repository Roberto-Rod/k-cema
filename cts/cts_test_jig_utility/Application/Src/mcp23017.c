/*****************************************************************************/
/**
** Copyright 2023 Kirintec Ltd. All rights reserved.
*
* @file mcp23017.c
*
* Driver for MCP23017 GPIO expander, assumes that the reset signal is
* connected to a microntroller GPIO signal.  MCP23017 interrupts are not
* supported
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "mcp23017.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define MCP23017_IODIR_REG_ADDR		0x00U
#define MCP23017_GPIO_REG_ADDR		0x12U
#define MCP23017_OLAT_REG_ADDR		0x14U

#define MCP23017_RD_IO_LEN			2U
#define MCP23017_WR_REG_ADDR_LEN	1U
#define MCP23017_WR_IO_LEN			3U

#define MCP23017_I2C_TIMEOUT_MS		100U

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
static bool mcp23017_ReadRegister(	mcp23017_Driver_t *p_inst,
									uint8_t reg_addr, uint16_t *p_val);
static bool mcp23017_WriteRegister(	mcp23017_Driver_t *p_inst,
									uint8_t reg_addr, uint16_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


/*****************************************************************************/
/**
* Initialise the I2C GPIO driver, set the IO pin directions and default
* state of output pins
*
* @param    p_inst pointer to MCP23017 driver instance data
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool mcp23017_Init(mcp23017_Driver_t *p_inst)
{
	bool ret_val = false;

	/* Set default output state */
	if (mcp23017_WriteRegister(p_inst, MCP23017_OLAT_REG_ADDR, p_inst->default_op_mask))
	{
		/* Set IO direction register */
		ret_val = mcp23017_WriteRegister(p_inst, MCP23017_IODIR_REG_ADDR, p_inst->io_dir_mask);
	}

	p_inst->initialised = true;

	return ret_val;
}


/*****************************************************************************/
/**
* Set or clear specified pin(s), this function performs a read-modify-write
* operation
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	pin specifies the pin(s) to write to, can be any combination of
* 			MCP23017_GPIO_PIN_x where x can be 0..15
* @param	pin_state specifies if the pin(s) is set high or low, one of
* 			mcp23017_PinState_t enumerated values:
* 				@arg mcp23017_PinReset: pin(s) is set low
* 				@arg mcp23017_PinSet: pin(s) is set high
* @return   true if pin set successfully, else false
*
******************************************************************************/
bool mcp23017_WritePin(mcp23017_Driver_t *p_inst, uint16_t pin, mcp23017_PinState_t pin_state)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised)
	{
		if (mcp23017_ReadRegister(p_inst, MCP23017_OLAT_REG_ADDR, &temp))
		{
			if (pin_state == mcp23017_PinReset)
			{
				temp &= (~pin);
			}
			else
			{
				temp |= pin;
			}

			ret_val = mcp23017_WriteRegister(p_inst, MCP23017_OLAT_REG_ADDR, temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Writes the GPIO register with the specified value, this function overwrites
* rather than performing a read-modify-write operation
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	val 16-bit value to write to GPIO register
* @return   true if read successful, else false
*
******************************************************************************/
bool mcp23017_WritePinsVal(mcp23017_Driver_t *p_inst, uint16_t val)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = mcp23017_WriteRegister(p_inst, MCP23017_GPIO_REG_ADDR, val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return the state of the specified pin
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	pin specifies the pin(s) to read can be any combination of
* 			IGD_GPIO_PIN_x where x can be 0..15
* @param	p_pin_state pointer to variable that receives the pin state
* @return   true if read successful, else false
*
******************************************************************************/
bool mcp23017_ReadPin(mcp23017_Driver_t *p_inst, uint16_t pin, mcp23017_PinState_t *p_pin_state)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised)
	{
		if (mcp23017_ReadRegister(p_inst, MCP23017_GPIO_REG_ADDR, &temp))
		{
			if ((temp & pin) != 0U)
			{
				*p_pin_state = mcp23017_PinSet;
			}
			else
			{
				*p_pin_state = mcp23017_PinReset;
			}

			ret_val = true;
		}
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Reads and returns the GPIO register
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	p_val pointer to variable that receives 16-bit register value
* 			read from device
* @return   true if read successful, else false
*
******************************************************************************/
bool mcp23017_ReadPinsVal(mcp23017_Driver_t *p_inst, uint16_t *p_val)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = mcp23017_ReadRegister(p_inst, MCP23017_GPIO_REG_ADDR, p_val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 16-bit register read from the specified address
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives 16-bit register value
* 			read from device
* @return   true if read successful, else false
*
******************************************************************************/
static bool mcp23017_ReadRegister(	mcp23017_Driver_t *p_inst,
									uint8_t reg_addr, uint16_t *p_val)
{
	bool ret_val = false;
	uint8_t buf[MCP23017_RD_IO_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, MCP23017_WR_REG_ADDR_LEN,
								MCP23017_I2C_TIMEOUT_MS) == HAL_OK)
	{
		/* Read the register */
		if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
									buf, MCP23017_RD_IO_LEN,
									MCP23017_I2C_TIMEOUT_MS) == HAL_OK)
		{
			*p_val = (uint16_t)((uint16_t)(buf[1] << 8) | (uint16_t)buf[0]);
			ret_val = true;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 16-bit register write to the specified address
*
* @param    p_inst pointer to MCP23017 driver instance data
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
* @return   true if write successful, else false
*
******************************************************************************/
static bool mcp23017_WriteRegister(	mcp23017_Driver_t *p_inst,
									uint8_t reg_addr, uint16_t val)
{
	bool ret_val = false;
	uint8_t buf[MCP23017_WR_IO_LEN];

	buf[0] = reg_addr;
	buf[1] = (uint8_t)(val & 0xFFU);
	buf[2] = (uint8_t)((val >> 8) & 0xFFU);

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, MCP23017_WR_IO_LEN,
								MCP23017_I2C_TIMEOUT_MS) == HAL_OK)
	{
		ret_val = true;
	}

	return ret_val;
}
