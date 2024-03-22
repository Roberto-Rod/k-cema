/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file fan_controller.c
*
* Describe the purpose of the file...
*
* Project   : N/A
*
* Build instructions   : Compile using STM32CubeIDE Compiler
*
* @todo None
*
******************************************************************************/
#define __FAN_CONTROLLER_C

#include "fan_controller.h"

/*****************************************************************************/
/**
* Initialise the fan controller driver, this function copies the hw information
* into the driver data structure
*
* @param    p_inst pointer to fan controller driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
void fc_InitInstance(	fc_FanCtrlrDriver_t	*p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;
}


/*****************************************************************************/
/**
* Initialise the EMC2104 fan controller
*
* @param    p_inst pointer to fan controller driver instance data
* @return   TRUE if initialisation is successful, else FALSE
* @note     None
* @todo		Add in read back to verify registers have been successfully set
*
******************************************************************************/
bool fc_Initialise(fc_FanCtrlrDriver_t *p_inst)
{
	uint8_t buf = 0U;
	uint16_t i = 0U;
	bool return_val = true;

	if (p_inst->initialised)
	{
		for (i = 0U; i < FC_NO_INIT_REGISTERS; ++i)
		{
			if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
										p_inst->i2c_address,
										&lg_fc_init_data[i][0],
										FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
			{
				return_val = false;
				break;
			}
		}

		for (i = 0; i < FC_NO_INIT_REGISTERS; ++i)
		{
			if (fc_ReadByte(p_inst, lg_fc_init_data[i][0], &buf))
			{
				/* Skip Fan Config 1 Registers where EN_ALGO bit is auto set and
				 * Muxed Pin Config register where unused bit returns '1'
				 */
				if ((buf != lg_fc_init_data[i][1]) &&
					(lg_fc_init_data[i][0] != 0x42U) &&
					(lg_fc_init_data[i][0] != 0x82U) &&
					(lg_fc_init_data[i][0] != 0xE0U))
				{
					return_val = false;
				}
			}
			else
			{
				return_val = false;
			}
		}
	}
	else
	{
		return_val = false;
	}

	return return_val;
}


/*****************************************************************************/
/**
* Push Temperature 1 and 3 values to the EMC2104 fan controller
*
* @param    p_inst pointer to fan controller driver instance data
* @param	temperature Temperature in deg C, 2's complement
* @return   TRUE if both temperatures are successfully pushed, else FALSE
* @note     None
*
******************************************************************************/
bool fc_PushTemperature(fc_FanCtrlrDriver_t	*p_inst, int8_t temperature)
{
	uint8_t buf[FC_EMC2104_WR_CMD_LEN];
	bool return_val = true;

	if (p_inst->initialised)
	{
		/* Push Temperature 1 */
		buf[0] = FC_EMC2104_TEMP1_REG_ADDR;
		buf[1] = temperature;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}

		/* Push Temperature 3 */
		buf[0] = FC_EMC2104_TEMP3_REG_ADDR;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}

		/* Read back temperatures to verify they've been set correctly */
		if (fc_ReadByte(p_inst, FC_EMC2104_TEMP1_REG_ADDR, buf))
		{
			if ((int8_t)buf[0] != temperature)
			{
				return_val = false;
			}
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_TEMP3_REG_ADDR, buf))
		{
			if ((int8_t)buf[0] != temperature)
			{
				return_val = false;
			}
		}
		else
		{
			return_val = false;
		}
	}
	else
	{
		return_val = false;
	}

	return return_val;
}


/*****************************************************************************/
/**
* Read fan speed registers and returns clock counts that occur for a single
* revolution of the fan.  High byte is read first, this will load the
* low byte into a shadow register so that when it is read it corresponds with
* the high byte.
*
* @param    p_inst pointer to fan controller driver instance data
* @param	p_fan1_clk_count Receives Fan 1 clock count
* @param	p_fan2_clk_count Receives Fan 2 clock count
* @return   TRUE if both fan speed counts successfully read, else FALSE
* @note     None
*
******************************************************************************/
bool fc_ReadFanSpeedCounts(	fc_FanCtrlrDriver_t	*p_inst,
							uint16_t *p_fan1_clk_count,
							uint16_t *p_fan2_clk_count,
							uint8_t *p_fan1_pwm,
							uint8_t *p_fan2_pwm)
{
	uint8_t buf;
	bool return_val = true;

	if (p_inst->initialised)
	{
		/* Read Fan 1 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_TACH_HIGH_BYTE_REG_ADDR, &buf))
		{
			*p_fan1_clk_count = (uint16_t)buf << 8;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_TACH_LOW_BYTE_REG_ADDR, &buf))
		{
			*p_fan1_clk_count |= (uint16_t)buf;
			*p_fan1_clk_count >>= 3;
		}
		else
		{
			return_val = false;
		}

		/* Read Fan 2 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_TACH_HIGH_BYTE_REG_ADDR, &buf))
		{
			*p_fan2_clk_count = (uint16_t)buf << 8;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_TACH_LOW_BYTE_REG_ADDR, &buf))
		{
			*p_fan2_clk_count |= (uint16_t)buf;
			*p_fan2_clk_count >>= 3;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_DRIVER_SETTING_ADDR, &buf))
		{
			*p_fan1_pwm = buf;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_DRIVER_SETTING_ADDR, &buf))
		{
			*p_fan2_pwm = buf;
		}
		else
		{
			return_val = false;
		}
	}
	else
	{
		return_val = false;
	}

	return return_val;
}


/*****************************************************************************/
/**
* Read fan tach target registers, returns clock counts that occur for a single
* revolution of the fan
*
* @param    p_inst pointer to fan controller driver instance data
* @param	p_fan1_tach_target Receives Fan 1 tach target
* @param	p_fan2_tach_target Receives Fan 2 tach target
* @return   TRUE if both fan tach targets successfully read, else FALSE
* @note     None
*
******************************************************************************/
bool fc_ReadFanTachTargets(	fc_FanCtrlrDriver_t	*p_inst,
							uint16_t *p_fan1_tach_target,
							uint16_t *p_fan2_tach_target)
{
	uint8_t buf;
	bool return_val = true;

	if (p_inst->initialised)
	{
		/* Read Fan 1 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_TT_HIGH_BYTE_REG_ADDR, &buf))
		{
			*p_fan1_tach_target = (uint16_t)buf << 8;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_TT_LOW_BYTE_REG_ADDR, &buf))
		{
			*p_fan1_tach_target |= (uint16_t)buf;
			*p_fan1_tach_target >>= 3;
		}
		else
		{
			return_val = false;
		}

		/* Read Fan 2 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_TT_HIGH_BYTE_REG_ADDR, &buf))
		{
			*p_fan2_tach_target = (uint16_t)buf << 8;
		}
		else
		{
			return_val = false;
		}

		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_TT_LOW_BYTE_REG_ADDR, &buf))
		{
			*p_fan2_tach_target |= (uint16_t)buf;
			*p_fan2_tach_target >>= 3;
		}
		else
		{
			return_val = false;
		}
	}
	else
	{
		return_val = false;
	}

	return return_val;
}


/*****************************************************************************/
/**
* Read the EMC2104 internal temperature diode
*
* @param    p_inst pointer to fan controller driver instance data
* @param	int_temp_whole Receives integer part of temperature
* @return   TRUE if fan temperature read ELSE FALSE
* @note     None
*
******************************************************************************/
bool fc_ReadInternalTemp(fc_FanCtrlrDriver_t *p_inst, int8_t *int_temp_whole)
{
	uint8_t buf = 0U;
	bool return_val = false;

	if (p_inst->initialised)
	{
		/* Read Fan 1 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_INT_WHOLE_TEMP_ADDR, &buf))
		{
			*int_temp_whole = (int8_t)buf;
			return_val = true;
		}
	}

	return return_val;
}


/*****************************************************************************/
/**
* Read the EMC2104 fan status
*
* @param    p_inst pointer to fan controller driver instance data
* @param	fan_status_reg Receives Fan Status Register
* @return   TRUE if fan status read ELSE FALSE
* @note     None
*
******************************************************************************/
bool fc_ReadFanStatus(fc_FanCtrlrDriver_t *p_inst, uint8_t *fan_status_reg)
{
	uint8_t buf = 0U;
	bool return_val = false;

	if (p_inst->initialised)
	{
		/* Read Fan 1 speed count */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN_STATUS_REG_ADDR, &buf))
		{
			*fan_status_reg = buf;
			return_val = true;
		}
	}

	return return_val;
}


/*****************************************************************************/
/**
* Put both fans in to Direct Setting Mode and set Fan Driver Setting registers
* with PWM value
*
* @param    p_inst pointer to fan controller driver instance data
* @param	pwm	PWM value for Fan Driver Setting registers
* @return   TRUE if both fans set to direct mode PWM value correctly
* @note     None
*
******************************************************************************/
bool fc_SetDirectSettingMode(fc_FanCtrlrDriver_t *p_inst, uint8_t pwm)
{
	bool return_val = true;
	uint8_t buf[(FC_EMC2104_WR_CMD_LEN > FC_EMC2104_RD_CMD_LEN ? FC_EMC2104_WR_CMD_LEN : FC_EMC2104_RD_CMD_LEN)];

	if (p_inst->initialised)
	{
		/* Set Muxed Pin Config Register */
		buf[0] = FC_EMC2104_MUXED_PIN_CONFIG_ADDR;
		buf[1] = 0x00U;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}

		/* Read Fan 1 LUT Config Register */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN1_LUT_CONFIG_ADDR, &buf[1]))
		{
			/* Clear Bit 4 - TACH/DRIVE and Bit 5 - LUT_LOCK */
			buf[1] &= 0xCFU;
			buf[0] = FC_EMC2104_FAN1_LUT_CONFIG_ADDR;

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
										p_inst->i2c_address,
										buf,
										FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
			{
				return_val = false;
			}

			/* Set the Fan Driver Setting register */
			buf[1] = pwm;
			buf[0] = FC_EMC2104_FAN1_DRIVER_SETTING_ADDR;

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
										p_inst->i2c_address,
										buf,
										FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
			{
				return_val = false;
			}
		}
		else
		{
			return_val = false;
		}

		/* Set Fan 1 Config Register */
		buf[0] = FC_EMC2104_FAN1_CONFIG1_ADDR;
		buf[1] = 0x3EU;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}
#if 0
		buf[0] = FC_EMC2104_FAN1_CONFIG2_ADDR;
		buf[1] = 0x18U;
		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}
#endif

		/* Read Fan 2 LUT Config Register */
		if (fc_ReadByte(p_inst, FC_EMC2104_FAN2_LUT_CONFIG_ADDR, &buf[1]))
		{
			/* Clear Bit 4 - TACH/DRIVE and Bit 5 - LUT_LOCK */
			buf[1] &= 0xCFU;
			buf[0] = FC_EMC2104_FAN2_LUT_CONFIG_ADDR;

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
										p_inst->i2c_address,
										buf,
										FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
			{
				return_val = false;
			}

			/* Set the Fan Driver Setting register */
			buf[1] = pwm;
			buf[0] = FC_EMC2104_FAN2_DRIVER_SETTING_ADDR;

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
										p_inst->i2c_address,
										buf,
										FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
			{
				return_val = false;
			}
		}
		else
		{
			return_val = false;
		}

		/* Set Fan 2 Config Register */
		buf[0] = FC_EMC2104_FAN2_CONFIG1_ADDR;
		buf[1] = 0x3EU;
		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}
#if 0
		buf[0] = FC_EMC2104_FAN2_CONFIG2_ADDR;
		buf[1] = 0x18U;
		if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
									p_inst->i2c_address,
									buf,
									FC_EMC2104_WR_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
		{
			return_val = false;
		}
#endif
	}
	else
	{
		return_val = false;
	}

	return return_val;
}


/*****************************************************************************/
/**
* Read a byte from the EMC2104 fan controller, sets device's internal address
* pointer to required address, reads and returns byte
*
* @param    p_inst pointer to fan controller driver instance data
* @param	addr 8-bit register address to read
* @param	p_buf Receives the read byte
* @return   TRUE if both fan speed counts successfully read, else FALSE
* @note     None
*
******************************************************************************/
bool fc_ReadByte(fc_FanCtrlrDriver_t *p_inst, uint8_t addr, uint8_t *p_buf)
{
	bool return_val = true;
	uint8_t buf[FC_EMC2104_WR_CMD_LEN > FC_EMC2104_RD_CMD_LEN ? FC_EMC2104_WR_CMD_LEN : FC_EMC2104_RD_CMD_LEN];

	/* Set the EMC2104 internal address pointer to the required address */
	buf[0] = addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device,
								p_inst->i2c_address,
								buf,
								FC_EMC2104_RD_CMD_LEN, FC_I2C_TIMEOUT) != HAL_OK)
	{
		return_val = false;
	}

	if (HAL_I2C_Master_Receive(	p_inst->i2c_device,
								p_inst->i2c_address,
								buf,
								FC_EMC2104_RD_CMD_LEN, FC_I2C_TIMEOUT) == HAL_OK)
	{
		*p_buf = buf[0];
	}
	else
	{
		return_val = false;
	}

	return return_val;
}
