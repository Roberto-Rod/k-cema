/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file tamper_driver.c
*
* Driver for ST M41ST87W I2C tamper detection/RTC IC, assumptions:
* - Tamper channels are always configured as connect mode = normally open and
*   polarity mode = connect to GND
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#define __TAMPER_DRIVER_C

#include "tamper_driver.h"

/*****************************************************************************/
/**
* Initialise the tamper detection driver, this function copies the hw
* information into the driver data structure
*
* @param    p_inst pointer to tamper detection driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			tamper detection IC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool td_InitInstance(	td_TamperDriver_t  *p_inst,
						I2C_HandleTypeDef	*p_i2c_device,
						uint16_t			i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return true;
}


/*****************************************************************************/
/**
* Enables/disables anti-tamper channels.  Channels are always configured
* connect mode = normally open and polarity mode = connect to GND (TPMx = 0; TCMx = 1)
*
* @param    p_inst pointer to tamper detection driver instance data
* @param	channel '0' for channel 1; '1' for channel 2
* @param	tpm tamper polarity mode bit, true tamper high, false tamper low
* @param	tcm connect mode bit, true normally open, false normally closed
* @param	enable	true to enable anti-tamper channel, false to disable
* @return   true if tamper device successfully set, else false
* @note     None
*
******************************************************************************/
bool td_TamperEnable(td_TamperDriver_t *p_inst, int16_t channel,
						bool tpm, bool tcm, bool enable)
{
	bool ret_val = true;
	uint8_t buf = 0U;
	uint8_t reg = 0U;

	if (p_inst->initialised &&
		((channel >= td_TamperChannel1) && (channel <= td_TamperChannel2)))
	{
		reg = (channel == td_TamperChannel1) ? TD_TAMPER1_REG : TD_TAMPER2_REG;

		if (enable)
		{
			buf |= (TD_TAMPER_TEB | TD_TAMPER_TIE );
			if (tcm)
			{
				buf |= TD_TAMPER_TCM;
			}
			if (tpm)
			{
				buf |= TD_TAMPER_TPM;
			}
		}
		else
		{
			buf &= (~TD_TAMPER_TEB);
			buf &= (~TD_TAMPER_TIE);
		}

	    /* According to the M41ST87W data sheet the TEBx should be cleared and
	     * then set again whenever the tamper detect condition is modified so
	     * for simplicity start by clearing the value when its a tamper register */
		ret_val = (td_WriteRegister(p_inst, reg, (buf & (~TD_TAMPER_TEB))) && ret_val);
		ret_val = (td_WriteRegister(p_inst, reg, buf) && ret_val);

		/* Set the ABE bit in the Alarm Month register so that a tamper causes
		 * an interrupt in battery backup mode */
		ret_val = (td_WriteRegister(p_inst, TD_ALARM_MONTH_REG,
									(TD_AL_MONTH_ABE | TD_AL_MONTH_AFE)) && ret_val);
	}
	else
	{
		ret_val = false;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Reads the 8-byte TIMEKEEPER registers from the device and returns the time
*
* @param    p_inst pointer to tamper detection driver instance data
* @param	p_time pointer to data structure to receive read time
* @return   true if time read successfully, else false
* @todo		Add processing for all elements of the current time
*
******************************************************************************/
bool td_GetTime(td_TamperDriver_t *p_inst, td_Time *p_time)
{
	bool ret_val = true;
	uint8_t buf[TD_RD_WR_TIME_REG_LEN];

	if (p_inst->initialised)
	{
		/* Write zero to the Alarm Hour register to clear the HT bit and
		 * ensure the user RTC registers are being updated */
		ret_val = td_WriteRegister(p_inst, TD_ALARM_HOUR_REG, 0x00U);

		if (ret_val)
		{
			/* Set the address pointer to the register to be read */
			buf[0] = TD_MS_REG;

			ret_val = ((HAL_I2C_Master_Transmit(p_inst->i2c_device,
												p_inst->i2c_address,
												buf,
												TD_WR_REG_ADDR_LEN,
												TD_I2C_TIMEOUT_MS) == HAL_OK) && ret_val);
		}

		if (ret_val)
		{
			ret_val = ((HAL_I2C_Master_Receive(	p_inst->i2c_device,
												p_inst->i2c_address,
												buf,
												TD_RD_WR_TIME_REG_LEN,
												TD_I2C_TIMEOUT_MS) == HAL_OK) && ret_val);
		}

		if (ret_val)
		{
			p_time->seconds = buf[TD_SECONDS_REG] & 0x0FU;
			p_time->tens_seconds = (buf[TD_SECONDS_REG] & 0x70U) >> 4;
			p_time->minutes = buf[TD_MINUTES_REG] & 0x0FU;
			p_time->tens_minutes = (buf[TD_MINUTES_REG] & 0x70U) >> 4;
			p_time->hours = buf[TD_HOURS_REG] & 0x0FU;
			p_time->tens_hours = (buf[TD_HOURS_REG] & 0x30U) >> 4;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register read from the specified address
*
* @param    p_inst pointer to tamper detection driver instance data
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives read register value
* @return   true if read successful, else false
* @note     None
*
******************************************************************************/
bool td_ReadRegister(	td_TamperDriver_t *p_inst,
						uint8_t reg_addr, uint8_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[TD_RD_REG_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, TD_WR_REG_ADDR_LEN, TD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
								buf, TD_RD_REG_LEN, TD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	if (ret_val)
	{
		*p_val = buf[0];
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register write to the specified address
*
* @param    p_inst pointer to tamper detection driver instance data
* @param	reg_addr device register address to read from
* @param	val 8-bit data value to write to device register
* @return   true if write successful, else false
* @note     None
*
******************************************************************************/
 bool td_WriteRegister(	td_TamperDriver_t *p_inst,
								uint8_t reg_addr, uint8_t val)
{
	bool ret_val = true;
	uint8_t buf[TD_WR_REG_LEN];

	buf[0] = reg_addr;
	buf[1] = val;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
								buf, TD_WR_REG_LEN, TD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}
