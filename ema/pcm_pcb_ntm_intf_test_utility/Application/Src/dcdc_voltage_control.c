/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file dcdc_voltage_control.c
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
#define __DCDC_VOLTAGE_CONTROL_C

#include "dcdc_voltage_control.h"

/*****************************************************************************/
/**
* Initialise the DC-DC voltage control driver, this function copies the hw information
* into the driver data structure
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
void dvc_InitInstance(	dvc_DcdcVoltCtrlDriver_t	*p_inst,
						I2C_HandleTypeDef			*p_i2c_device,
						uint16_t					i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;
}


/*****************************************************************************/
/**
* Set the RDAC value of the AD5272 wiper.  The RDAC write protect bit must be
* set to '1' to allow the RDAC to be programmed
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @param	rdac_value	10-bit RDAC value to be set
* @return   TRUE if RDAC value is set, else FALSE
* @note     None
*
******************************************************************************/
bool dvc_SetRdacValue(dvc_DcdcVoltCtrlDriver_t *p_inst, uint16_t rdac_value)
{
	uint8_t buf[DVC_AD52752_CMD_DATA_LEN];
	bool return_val = false;

	if (p_inst->initialised)
	{
		if (rdac_value <= DVC_AD5272_RDAC_MAX)
		{
			/* The RDAC register write protect Control Register bit must be set to
			 * '1' to allow the RDAC value to be updated via the digital interface */
			buf[0] = (uint8_t)(DVC_AD5272_WR_CTRL_CMD << 2) |
						(uint8_t)((DVC_AD7252_RDAC_WR_EN >> 8) & 0xFFU);
			buf[1] = (uint8_t)(DVC_AD7252_RDAC_WR_EN & 0xFFU);

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
										buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
					== HAL_OK)
			{
				/* Assemble the command string to set the RDAC value */
				buf[0] = (uint8_t)(DVC_AD5272_WR_RDAC_CMD << 2) |
							(uint8_t)((rdac_value >> 8) & 0xFFU);
				buf[1] = (uint8_t)(rdac_value & 0xFFU);

				if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
											buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
						== HAL_OK)
				{
					return_val = true;
				}
			}
		}
	}

	return return_val;
}

/*****************************************************************************/
/**
* Read the current AD5272 RDAC wiper value.
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @param	p_rdac_value	Pointer to variable that will receive the 10-bit
* 							RDAC value
* @return   TRUE if RDAC value is read from the device, else FALSE
* @note     None
*
******************************************************************************/
bool dvc_ReadRdacValue(dvc_DcdcVoltCtrlDriver_t	*p_inst, uint16_t *p_rdac_value)
{
	uint8_t buf[DVC_AD52752_RD_DATA_LEN >= DVC_AD52752_CMD_DATA_LEN ? DVC_AD52752_RD_DATA_LEN : DVC_AD52752_CMD_DATA_LEN];
	bool return_val = false;

	if (p_inst->initialised)
	{
		/* Send readback command for the RDAC register */
		buf[0] = (uint8_t)(DVC_AD5272_RD_RDAC_CMD << 2);
		buf[1] = 0U;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
									buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
				== HAL_OK)
		{
			if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
										buf, DVC_AD52752_RD_DATA_LEN, DVC_I2C_TIMEOUT)
					== HAL_OK)
			{
				*p_rdac_value = (uint16_t)(((buf[0] & 0x3U) << 8) | buf[1]);
				return_val = true;
			}
		}
	}

	return return_val;
}

/*****************************************************************************/
/**
* Store the current wiper value to 50-TP memory, The 50-TP program enable bit
* must be set to '1' to allow the RDAC to be programmed
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @return   TRUE if device is value is stored, else FALSE
* @note     None
*
******************************************************************************/
bool dvc_StoreWiperTo50TpValue(dvc_DcdcVoltCtrlDriver_t	*p_inst)
{
	uint8_t buf[DVC_AD52752_RD_DATA_LEN >= DVC_AD52752_CMD_DATA_LEN ? DVC_AD52752_RD_DATA_LEN : DVC_AD52752_CMD_DATA_LEN];
	bool return_val = false;

	if (p_inst->initialised)
	{
		/* The 50-TP program enable protect Control Register bit must be set to
		 * '1' to allow the 50-TP memory to be programmed via the digital interface */
		buf[0] = (uint8_t)(DVC_AD5272_WR_CTRL_CMD << 2) | (uint8_t)((DVC_AD7252_50TP_WR_EN >> 8) & 0xFFU);
		buf[1] = (uint8_t)(DVC_AD7252_50TP_WR_EN & 0xFFU);

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
									buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
				== HAL_OK)
		{
			/* Send store wiper to 50-TP memory command to the AD5272 */
			buf[0] = (uint8_t)(DVC_AD5272_WR_50TP_CMD << 2);
			buf[1] = 0U;

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
										buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
					== HAL_OK)
			{
				HAL_Delay(DVC_AD5272_MEM_PROG_TIME_MS);

				/* Read AD5272 Control Register to determine success of 50-TP programming operation */
				buf[0] = (uint8_t)(DVC_AD5272_RD_CTRL_CMD << 2);
				buf[1] = 0U;

				if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
											buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
						== HAL_OK)
				{
					if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
												buf, DVC_AD52752_RD_DATA_LEN, DVC_I2C_TIMEOUT)
							== HAL_OK)
					{
						if (buf[1] & DVC_AD7252_50TP_PROG_SUCCESS)
						{
							return_val = true;
						}
					}
				}
			}
		}
	}

	return return_val;
}

/*****************************************************************************/
/**
* Read the current AD5272 last programmed 50-TP wiper value.
* This process requires 2x steps, first read back the last 50-TP address written
* to then read back the wiper value from this address in 50-TP memory
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @param	p_last_50tp_addr Pointer to variable that will receive the last
* 							50-TP address written to
* @param	p_50tp_value	Pointer to variable that will receive the 10-bit
* 							50-TP wiper value
* @return   TRUE if last 50-TP value is read from the device, else FALSE
* @note     None
*
******************************************************************************/
bool dvc_Read50TpValue(	dvc_DcdcVoltCtrlDriver_t *p_inst,
						uint16_t *p_last_50tp_addr,
						uint16_t *p_50tp_value)
{
	uint8_t buf[DVC_AD52752_RD_DATA_LEN >= DVC_AD52752_CMD_DATA_LEN ? DVC_AD52752_RD_DATA_LEN : DVC_AD52752_CMD_DATA_LEN];
	bool return_val1 = false;
	bool return_val2 = false;

	if (p_inst->initialised)
	{
		/* Read back the last 50-TP address written to */
		buf[0] = (uint8_t)(DVC_AD5272_RD_LAST_50TP_ADDR_CMD << 2);
		buf[1] = 0U;
		*p_last_50tp_addr = 0U;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
									buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
				== HAL_OK)
		{
			if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
										buf, DVC_AD52752_RD_DATA_LEN, DVC_I2C_TIMEOUT)
					== HAL_OK)
			{
				*p_last_50tp_addr = (uint16_t)(((buf[0] & 0x3U) << 8) | buf[1]);
				return_val1 = true;
			}
		}

		if (*p_last_50tp_addr != 0U)
		{
			/* Read back the last stored 50-TP value */
			buf[0] = (uint8_t)(DVC_AD5272_RD_50TP_CMD << 2) |
						(uint8_t)((*p_last_50tp_addr >> 8) & 0xFFU);
			buf[1] = (uint8_t)(*p_last_50tp_addr  & 0xFFU);

			if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
										buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
					== HAL_OK)
			{
				if (HAL_I2C_Master_Receive(	p_inst->i2c_device, p_inst->i2c_address,
											buf, DVC_AD52752_RD_DATA_LEN, DVC_I2C_TIMEOUT)
						== HAL_OK)
				{
					*p_50tp_value = (uint16_t)(((buf[0] & 0x3U) << 8) | buf[1]);
					return_val2 = true;
				}
			}
		}
	}

	return return_val1 & return_val2;
}

/*****************************************************************************/
/**
* Perform an AD5272 software reset.
*
* @param    p_inst pointer to DC-DC voltage control driver instance data
* @return   TRUE if device is reset, else FALSE
* @note     None
*
******************************************************************************/
bool dvc_ResetDevice(dvc_DcdcVoltCtrlDriver_t *p_inst)
{
	uint8_t buf[DVC_AD52752_CMD_DATA_LEN];
	bool return_val = false;

	if (p_inst->initialised)
	{
		/* Send reset command to the AD5272 */
		buf[0] = (uint8_t)(DVC_AD5272_RESET_CMD << 2);
		buf[1] = 0U;

		if (HAL_I2C_Master_Transmit(p_inst->i2c_device, p_inst->i2c_address,
									buf, DVC_AD52752_CMD_DATA_LEN, DVC_I2C_TIMEOUT)
				== HAL_OK)
		{
			return_val = true;
		}
	}

	return return_val;
}
