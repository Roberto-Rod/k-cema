/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file i2c_gpio_driver.c
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
#define __I2C_GPIO_DRIVER_C

#include "i2c_gpio_driver.h"

/*****************************************************************************/
/**
* Initialise the I2C GPIO driver, set the IO pin directions and default
* state of output pins
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool igd_Init(igd_I2cGpioDriver_t *p_inst)
{
	bool ret_val = false;

	/* De-assert I2C GPIO expander reset signal */
	HAL_GPIO_WritePin(	p_inst->i2c_reset_gpio_port,
						p_inst->i2c_reset_gpio_pin,
						GPIO_PIN_SET);

	/* Set default output state */
	if (igd_WriteRegister(p_inst, IGD_MCP23017_OLAT_REG_ADDR, p_inst->default_op_mask))
	{
		/* Set IO direction register */
		ret_val = 	igd_WriteRegister(p_inst, IGD_MCP23017_IODIR_REG_ADDR, p_inst->io_dir_mask);
	}

	p_inst->initialised = true;

	return ret_val;
}


/*****************************************************************************/
/**
* Set or clear specified pin(s), this function performs a read-modify-write
* operation
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	pin specifies the pin(s) to write can be any combination of
* 			IGD_GPIO_PIN_x where x can be 0..15
* @param	pin_state specifies if the pin(s) is set high or low, one of
* 			igd_PinState enumerated values:
* 				@arg igd_PinReset: pin(s) is set low
* 				@arg igd_PinSet: pin(s) is set high
* @return   true if pin set successfully, else false
* @note     None
*
******************************************************************************/
bool igd_WritePin(igd_I2cGpioDriver_t *p_inst, uint16_t pin, igd_PinState pin_state)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised)
	{
		if (igd_ReadRegister(p_inst, IGD_MCP23017_OLAT_REG_ADDR, &temp))
		{
			if (pin_state == igd_PinReset)
			{
				temp &= (~pin);
			}
			else
			{
				temp |= pin;
			}

			ret_val = igd_WriteRegister(p_inst, IGD_MCP23017_OLAT_REG_ADDR, temp);
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Writes the GPIO register with the specified value, this function overwrites
* rather than performing a read-modify-write operation
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	val 16-bit value to write to GPIO register
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool igd_WritePinsVal(igd_I2cGpioDriver_t *p_inst, uint16_t val)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_WriteRegister(p_inst, IGD_MCP23017_GPIO_REG_ADDR, val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return the state of the specified pin
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	pin specifies the pin(s) to read can be any combination of
* 			IGD_GPIO_PIN_x where x can be 0..15
* @param	p_pin_state pointer to variable that receives the pin state
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool igd_ReadPin(igd_I2cGpioDriver_t *p_inst, uint16_t pin, igd_PinState *p_pin_state)
{
	bool ret_val = false;
	uint16_t temp = 0U;

	if (p_inst->initialised)
	{
		if (igd_ReadRegister(p_inst, IGD_MCP23017_GPIO_REG_ADDR, &temp))
		{
			if ((temp & pin) != 0U)
			{
				*p_pin_state = igd_PinSet;
			}
			else
			{
				*p_pin_state = igd_PinReset;
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
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	p_val pointer to variable that receives 16-bit register value
* 			read from device
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool igd_ReadPinsVal(igd_I2cGpioDriver_t *p_inst, uint16_t *p_val)
{
	bool ret_val = false;

	if (p_inst->initialised)
	{
		ret_val = igd_ReadRegister(p_inst, IGD_MCP23017_GPIO_REG_ADDR, p_val);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Assert the STM32 GPIO pin reset signal to the I2C GPIO expander(s)
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	reset true to assert I2C GPIO expander reset signal, false to
* 			de-assert
* @return   None
* @note     None
*
******************************************************************************/
void igd_SetI2cReset(igd_I2cGpioDriver_t *p_inst, bool reset)
{
	if (p_inst->initialised)
	{
		HAL_GPIO_WritePin(	p_inst->i2c_reset_gpio_port,
							p_inst->i2c_reset_gpio_pin,
							reset ? GPIO_PIN_RESET : GPIO_PIN_SET);
	}
}


/*****************************************************************************/
/**
* Performs a 16-bit register read from the specified address
*
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives 16-bit register value
* 			read from device
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool igd_ReadRegister(	igd_I2cGpioDriver_t *p_inst,
						uint8_t reg_addr, uint16_t *p_val)
{
	bool ret_val = false;
	uint8_t buf[IGD_MCP23017_RD_IO_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, IGD_MCP23017_WR_REG_ADDR_LEN,
								IGD_I2C_TIMEOUT_MS) == HAL_OK)
	{
		/* Read the register */
		if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
									buf, IGD_MCP23017_RD_IO_LEN,
									IGD_I2C_TIMEOUT_MS) == HAL_OK)
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
* @param    p_inst pointer to I2C GPIO driver instance data
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
* @return   true if write successful, else false
* @note     None
*
******************************************************************************/
bool igd_WriteRegister( igd_I2cGpioDriver_t *p_inst,
						uint8_t reg_addr, uint16_t val)
{
	bool ret_val = false;
	uint8_t buf[IGD_MCP23017_WR_IO_LEN];

	buf[0] = reg_addr;
	buf[1] = (uint8_t)(val & 0xFFU);
	buf[2] = (uint8_t)((val >> 8) & 0xFFU);

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, IGD_MCP23017_WR_IO_LEN,
								IGD_I2C_TIMEOUT_MS) == HAL_OK)
	{
		ret_val = true;
	}

	return ret_val;
}
