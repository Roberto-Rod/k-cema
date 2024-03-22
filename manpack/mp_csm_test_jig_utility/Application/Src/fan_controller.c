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
#include "fan_controller.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define FC_NO_INIT_REGISTERS	63
#define FC_I2C_TIMEOUT			100U

#define FC_EMC2104_RD_CMD_LEN					1
#define FC_EMC2104_WR_CMD_LEN					2
#define FC_EMC2104_INT_WHOLE_TEMP_ADDR			0x00U
#define FC_EMC2104_TEMP1_REG_ADDR				0x0CU
#define FC_EMC2104_TEMP3_REG_ADDR				0x0EU
#define FC_EMC2104_FAN1_TT_HIGH_BYTE_REG_ADDR	0x4DU
#define FC_EMC2104_FAN1_TT_LOW_BYTE_REG_ADDR	0x4CU
#define FC_EMC2104_FAN2_TT_HIGH_BYTE_REG_ADDR	0x8DU
#define FC_EMC2104_FAN2_TT_LOW_BYTE_REG_ADDR	0x8CU
#define FC_EMC2104_FAN1_TACH_HIGH_BYTE_REG_ADDR	0x4EU
#define FC_EMC2104_FAN1_TACH_LOW_BYTE_REG_ADDR	0x4FU
#define FC_EMC2104_FAN2_TACH_HIGH_BYTE_REG_ADDR	0x8EU
#define FC_EMC2104_FAN2_TACH_LOW_BYTE_REG_ADDR	0x8FU
#define FC_EMC2104_FAN1_LUT_CONFIG_ADDR			0x50
#define FC_EMC2104_FAN2_LUT_CONFIG_ADDR			0x90
#define FC_EMC2104_FAN1_DRIVER_SETTING_ADDR		0x40
#define FC_EMC2104_FAN2_DRIVER_SETTING_ADDR		0x80
#define FC_EMC2104_FAN1_CONFIG1_ADDR			0x42
#define FC_EMC2104_FAN1_CONFIG2_ADDR			0x43
#define FC_EMC2104_FAN2_CONFIG1_ADDR			0x82
#define FC_EMC2104_FAN2_CONFIG2_ADDR			0x83
#define FC_EMC2104_MUXED_PIN_CONFIG_ADDR		0xE0
#define FC_EMC2104_FAN_STATUS_REG_ADDR			0x27

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
bool fc_ReadByte(fc_FanCtrlrDriver_t *p_inst, uint8_t addr, uint8_t* p_buf);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
uint8_t lg_fc_init_data[FC_NO_INIT_REGISTERS][2] = { /* Data format {addr, value} */
		{0x20U, 0x00U},				/* Config */
		{0x28U, 0x00U},				/* Irq Enable */
		{0x29U, 0x0FU},				/* Fan Irq Enable - Fan 1 & 2 Fan spin-up and stall fault */
		{0x2AU, 0x00U},				/* PWM Config - PWM1 & PWM2 output polarity*/
		{0x2BU, 0x05U},				/* PWM Base Freq - PWM1 & PWM2 19.53 kHzrange (note, EMC2104 PWM output frequency is very inaccurate +/10 %) */
		{0x41U, 0x01U},				/* Fan 1 Divide - PWM1 divide by 1 */
		{0x42U, 0x3EU},				/* Fan 1 Config 1 - 1200 ms update time; 4-pole fan; 2x TACH count multiplier; Fan Speed Control Algorithm */
		{0x43U, 0x78U},				/* Fan 1 Config 2 - TACH must be present for fan speed; 0 RPM error range; 0x3 basic and step derivative; tacho LPF enabled*/
		{0x45U, 0x2AU},				/* Fan 1 Gain 1 */
		{0x46U, 0x59U},				/* Fan 1 Spin Up Config - 500 ms; final drive 60 %; 100 % fan drive setting; monitor for 32 update periods */
		{0x47U, 0x08U},				/* Fan 1 Step - max fan step size between update times of 8 */
		{0x48U, 0x20U},				/* Fan 1 Min Drive - 32 or 12.5 % */
		{0x49U, 0xC4U},				/* Fan 1 Valid Tach Count, 10,000 RPM */
		{0x4AU, 0x00U},				/* Fan 1 Drive Fail Ban Low Byte */
		{0x4BU, 0x00U},				/* Fan 1 Drive Fail Ban High Byte  */
		{0x81U, 0x01U},				/* Fan 2 Divide - PWM2 divide by 1 */
		{0x82U, 0x3EU},				/* Fan 2 Config 1 - 1200 ms update time; 4-pole fan; 2x TACH count multiplier; Fan Speed Control Algorithm */
		{0x83U, 0x78U},				/* Fan 2 Config 2 - TACH must be present for fan speed; 0 RPM error range; 0x3 basic and step derivative; tacho LPF enabled*/
		{0x85U, 0x2AU},				/* Fan 2 Gain 1 */
		{0x86U, 0x59U},				/* Fan 2 Spin Up Config - 500 ms; final drive 60 %; 100 % fan drive setting; monitor for 32 update periods */
		{0x87U, 0x08U},				/* Fan 2 Step - max fan step size between update times of 8 */
		{0x88U, 0x20U},				/* Fan 2 Min Drive - 32 or 12.5  % */
		{0x89U, 0xC4U},				/* Fan 2 Valid Tach Count, 10,000 RPM */
		{0x8AU, 0x00U},				/* Fan 2 Drive Fail Ban Low Byte */
		{0x8BU, 0x00U},				/* Fan 2 Drive Fail Ban High Byte */
		{0x54U, 0x28U},				/* LUT 1 Temp 3 Setting 1 - 40 deg C */
		{0x94U, 0x28U},				/* LUT 2 Temp 3 Setting 1 - 40 deg C */
		{0x59U, 0x2CU},				/* LUT 1 Temp 3 Setting 2 - 44 deg C */
		{0x99U, 0x2CU},				/* LUT 2 Temp 3 Setting 2 - 44 deg C */
		{0x5EU, 0x31U},				/* LUT 1 Temp 3 Setting 3 - 49 deg C */
		{0x9EU, 0x31U},				/* LUT 2 Temp 3 Setting 3 - 49 deg C */
		{0x63U, 0x35U},				/* LUT 1 Temp 3 Setting 4 - 53 deg C */
		{0xA3U, 0x35U},				/* LUT 2 Temp 3 Setting 4 - 53 deg C */
		{0x68U, 0x39U},				/* LUT 1 Temp 3 Setting 5 - 57 deg C */
		{0xA8U, 0x39U},				/* LUT 2 Temp 3 Setting 5 - 57 deg C */
		{0x6DU, 0x3DU},				/* LUT 1 Temp 3 Setting 6 - 61 deg C */
		{0xADU, 0x3DU},				/* LUT 2 Temp 3 Setting 6 - 61 deg C */
		{0x72U, 0x42U},				/* LUT 1 Temp 3 Setting 7 - 66 deg C */
		{0xB2U, 0x42U},				/* LUT 2 Temp 3 Setting 7 - 66 deg C */
		{0x77U, 0x46U},				/* LUT 1 Temp 3 Setting 8 - 70 deg C */
		{0xB7U, 0x46U},				/* LUT 2 Temp 3 Setting 8 - 70 deg C */
		{0x51U, 0x46U},				/* LUT 1 Drive 1 - 7,022 RPM */
		{0x91U, 0x46U},				/* LUT 2 Drive 1 - 7,022 RPM */
		{0x56U, 0x39U},				/* LUT 1 Drive 2 - 8,263 RPM */
		{0x96U, 0x39U},				/* LUT 2 Drive 2 - 8,263  RPM */
		{0x5BU, 0x30U},				/* LUT 1 Drive 3 - 10,240 RPM */
		{0x9BU, 0x30U},				/* LUT 2 Drive 3 - 10,240 RPM */
		{0x60U, 0x29U},				/* LUT 1 Drive 4 - 11,988 RPM */
		{0xA0U, 0x29U},				/* LUT 2 Drive 4 - 11,988 RPM */
		{0x65U, 0x25U},				/* LUT 1 Drive 5 - 13,284 RPM */
		{0xA5U, 0x25U},				/* LUT 2 Drive 5 - 13,284 RPM */
		{0x6AU, 0x21U},				/* LUT 1 Drive 6 - 14,895 RPM */
		{0xAAU, 0x21U},				/* LUT 2 Drive 6 - 14,895 RPM */
		{0x6FU, 0x1DU},				/* LUT 1 Drive 7 - 16,949 RPM */
		{0xAFU, 0x1DU},				/* LUT 2 Drive 7 - 16,949 RPM */
		{0x74U, 0x1BU},				/* LUT 1 Drive 8 - 18,204 RPM */
		{0xB4U, 0x1BU},				/* LUT 2 Drive 8 - 18,204 RPM */
		{0x79U, 0x02U},				/* LUT 1 Temp Hysteresis - 2 deg C */
		{0xB9U, 0x02U},				/* LUT 2 Temp Hysteresis - 2 deg C */
		{0xE0U, 0x00U},				/* Muxed Pin Config - GPIO1 clk input to FSCA */
		{0xE2U, 0x44U},				/* GPIO Output Config - PWM1 & PWM2 push-pull*/
		{0x50U, 0x2AU},				/* Fan 1 LUT Config - use Pushed Temp 3 & 4 for Temp 3 in LUT; RPM TACH values; Lock the LUT and allow it to be used; 2's comp temp data */
		{0x90U, 0x2AU}				/* Fan 2 LUT Config - use Pushed Temp 3 & 4 for Temp 3 in LUT; RPM TACH values; Lock the LUT and allow it to be used; 2's comp temp data */
};

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

#if 1
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
#if 1
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
