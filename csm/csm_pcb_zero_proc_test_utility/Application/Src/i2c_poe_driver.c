/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file i2c_poe_driver.c
*
* Driver for Skyworks Si3474 PoE PSE Controller.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "i2c_poe_driver.h"

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/

/* Si3474 Register Addresses */
#define IPD_SI3474_PORT1_CLASS_DETECT_STATUS_REG_ADDR	0x0CU
#define IPD_SI3474_PORT2_CLASS_DETECT_STATUS_REG_ADDR	0x0DU
#define IPD_SI3474_PORT3_CLASS_DETECT_STATUS_REG_ADDR	0x0EU
#define IPD_SI3474_PORT4_CLASS_DETECT_STATUS_REG_ADDR	0x0FU
#define IPD_SI3474_POWER_STATUS_REG_ADDR				0x10U
#define IPD_SI3474_PORT_MODE_REG_ADDR					0x12U
#define IPD_SI3474_POWER_ON_FAULT_REG_ADDR				0x24U
#define IPD_SI3474_POWER_ALLOCATION_REG_ADDR			0x29U
#define IPD_SI3474_TEMPERATURE_REG_ADDR					0x2CU
#define IPD_SI3474_VPWR_REG_ADDR						0x2EU
#define IPD_SI3474_PORT1_CURRENT_REG_ADDR				0x30U
#define IPD_SI3474_PORT1_VOLTAGE_REG_ADDR				0x32U
#define IPD_SI3474_PORT2_CURRENT_REG_ADDR				0x34U
#define IPD_SI3474_PORT2_VOLTAGE_REG_ADDR				0x36U
#define IPD_SI3474_PORT3_CURRENT_REG_ADDR				0x38U
#define IPD_SI3474_PORT3_VOLTAGE_REG_ADDR				0x3AU
#define IPD_SI3474_PORT4_CURRENT_REG_ADDR				0x3CU
#define IPD_SI3474_PORT4_VOLTAGE_REG_ADDR				0x3EU

/* Si3474 I2C bus transaction definitions */
#define IPD_SI3474_8BIT_RD_LEN							1U
#define IPD_SI3474_16BIT_RD_LEN							2U
#define IPD_SI3474_8BIT_WR_LEN							2U

#define IPD_SI3474_WR_REG_ADDR_LEN						1U

#define IPD_I2C_TIMEOUT_MS								100U

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
static bool ipd_Read8BitRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint8_t *p_val);
static bool ipd_Read16BitRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint16_t *p_val);
static bool ipd_Write8itRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint8_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


/*****************************************************************************/
/**
* Initialise the I2C PoE driver, this function copies the hw information
* into the driver data, no device initialisation is required.
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param	i2c_device HAL driver handle for the I2C peripheral that the
* 			ADC is connected to
* @param	i2c_address device's I2C bus address
* @return   true if initialisation successful, else false
*
******************************************************************************/
bool ipd_Init(ipd_I2cPoeDriver_t  *p_inst, I2C_HandleTypeDef *p_i2c_device, uint16_t i2c_address)
{
	p_inst->i2c_device	= p_i2c_device;
	p_inst->i2c_address	= i2c_address;
	p_inst->initialised = true;

	return true;
}


/*****************************************************************************/
/**
* Read and return status information for the specified port.
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param	port port to query, valid range 1..8
* @param 	p_port_status pointer to data structure that will receive the
* 			status information.
* @return   true if status information read and returned successfully, else false
*
******************************************************************************/
bool ipd_GetPortPowerStatus(ipd_I2cPoeDriver_t *p_inst, int16_t port, ipd_PortStatus_t *p_port_status)
{
	bool ret_val = false;
	uint8_t port_i2c_address;
	uint16_t u16_temp;
	uint8_t u8_temp;
	uint8_t mask;
	int16_t shift;
	uint8_t reg_addr;

	if ((port >= 1) && (port <= IPD_NUM_PORTS))
	{
		/* Determine which quad to access */
		port_i2c_address = (port > (IPD_NUM_PORTS / 2)) ? p_inst->i2c_address + 2U : p_inst->i2c_address;

		ret_val = ipd_Read8BitRegister(	p_inst,
										port_i2c_address,
										IPD_SI3474_POWER_STATUS_REG_ADDR,
										&u8_temp);
		if (ret_val)
		{
			p_port_status->power_enable = u8_temp & (1 << (port % (IPD_NUM_PORTS / 2)));
			p_port_status->power_good = u8_temp & (1 << ((port % (IPD_NUM_PORTS / 2)) + 4));
		}

		/* Read the Power On Fault Register */
		ret_val = ret_val && ipd_Read8BitRegister(	p_inst,
													port_i2c_address,
													IPD_SI3474_POWER_ON_FAULT_REG_ADDR,
													&u8_temp);
		if (ret_val)
		{
			p_port_status->power_on_fault = \
					(ipd_PowerOnFault_t)(u8_temp >> (((port % (IPD_NUM_PORTS / 2)) - 1) * 2)) & 0x03U;
		}

		/* Read the Port Mode Register */
		ret_val = ret_val && ipd_Read8BitRegister(	p_inst,
													port_i2c_address,
													IPD_SI3474_PORT_MODE_REG_ADDR,
													&u8_temp);
		if (ret_val)
		{
			p_port_status->mode = \
					(ipd_PortMode_t)(u8_temp >> (((port % (IPD_NUM_PORTS / 2)) - 1) * 2)) & 0x03U;
		}

		/* Read the Power Allocation Register */
		ret_val = ret_val && ipd_Read8BitRegister(	p_inst,
													port_i2c_address,
													IPD_SI3474_POWER_ALLOCATION_REG_ADDR,
													&u8_temp);

		mask = (port > (IPD_NUM_PORTS / 2)) ?
				((port - 6) >= 0 ? 0x80U : 0x08U) :
				((port - 2) >= 0 ? 0x80U : 0x08U);

		p_port_status->port_2p4p_mode = u8_temp & mask;

		shift = (port > (IPD_NUM_PORTS / 2)) ? ((port - 6) >= 0 ? 4 : 0) : ((port - 2) >= 0 ? 4 : 0);
		p_port_status->power_allocation = (u8_temp >> shift) & 0x07U;


		/* Read the Port x Class Status Register */
		reg_addr = IPD_SI3474_PORT1_CLASS_DETECT_STATUS_REG_ADDR + (port % (IPD_NUM_PORTS / 2)) - 1;
		ret_val = ret_val && ipd_Read8BitRegister(	p_inst,
													port_i2c_address,
													reg_addr,
													&u8_temp);
		if (ret_val)
		{
			p_port_status->detection_status = (ipd_PortDetectionStatus_t)(u8_temp & 0x0FU);
			p_port_status->class_status = (ipd_PortClassStatus_t)((u8_temp >> 4) & 0x0FU);
		}

		/* Read the Port x Current */
		reg_addr = IPD_SI3474_PORT1_CURRENT_REG_ADDR + (((port % (IPD_NUM_PORTS / 2)) - 1) * 4);
		ret_val = ret_val && ipd_Read16BitRegister(	p_inst,
													port_i2c_address,
													reg_addr,
													&u16_temp);
		if (ret_val)
		{
			p_port_status->current_ma = \
					((uint32_t)1000U * (uint32_t)u16_temp) / (uint32_t)16384U;
		}

		/* Read the Port x Voltage */
		reg_addr = IPD_SI3474_PORT1_CURRENT_REG_ADDR + (((port % (IPD_NUM_PORTS / 2)) - 1) * 4) + 2;
		ret_val = ret_val && ipd_Read16BitRegister(	p_inst,
													port_i2c_address,
													reg_addr,
													&u16_temp);
		if (ret_val)
		{
			p_port_status->voltage = \
					((uint32_t)60000U * (uint32_t)u16_temp) / (uint32_t)16384U;
		}
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read and return device status information.
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param 	p_device_status pointer to data structure that will receive the
* 			status information.
* @return   true if status information read and returned successfully, else false
*
******************************************************************************/
bool ipd_GetDeviceStatus(ipd_I2cPoeDriver_t *p_inst, ipd_DeviceStatus_t *p_device_status)
{
	bool ret_val;
	uint16_t u16_temp;
	uint8_t u8_temp;

	/* Read the Temperature Register */
	ret_val = ipd_Read8BitRegister(	p_inst,
									p_inst->i2c_address,
									IPD_SI3474_TEMPERATURE_REG_ADDR,
									&u8_temp);
	if (ret_val)
	{
		p_device_status->temperature = \
				(((uint32_t)u8_temp * (uint32_t)100U) / (uint32_t)15U) - (uint32_t)200U;
	}

	/* Read the Power Supply Voltage */
	ret_val = ret_val && ipd_Read16BitRegister(	p_inst,
												p_inst->i2c_address,
												IPD_SI3474_VPWR_REG_ADDR,
												&u16_temp);
	if (ret_val)
	{
		p_device_status->voltage = \
				((uint32_t)60000U * (uint32_t)u16_temp) / (uint32_t)16384U;
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the Power Allocation register to the requested mode.  All ports in the
* specified ports quad will be set to the same mode.  This works on the
* KT-000-0140-00 board as there is only one connected port per quad.
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param	port port to set, valid range 1..8
* @param 	power_alloc required power allocation class
* @return   true if power allocation set, else false
*
******************************************************************************/
bool ipd_SetPortPowerAllocation(ipd_I2cPoeDriver_t *p_inst, int16_t port, ipd_PowerAllocation_t power_alloc)
{
	bool ret_val = false;
	uint8_t port_i2c_address;

	/* Determine which quad to access */
	port_i2c_address = (port > (IPD_NUM_PORTS / 2)) ? p_inst->i2c_address + 2U : p_inst->i2c_address;

	ret_val = ipd_Write8itRegister(	p_inst,
									port_i2c_address,
									IPD_SI3474_POWER_ALLOCATION_REG_ADDR,
									(uint8_t)power_alloc);

	return ret_val;
}


/*****************************************************************************/
/**
* Utility function to check that a port number is valid.
*
* @param	port port number to check
* @return   true if port number is valid, else false
*
******************************************************************************/
bool ipd_IsPortValid(int16_t port)
{
	return ((port >= 1) && (port <= IPD_NUM_PORTS));
}


/*****************************************************************************/
/**
* Performs a 8-bit register read from the specified address
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param 	i2c_address I2C bus address to read from
* @param	reg_addr device register address to read from
* @param	p_val pointer to variable that receives read register value
* @return   true if read successful, else false
*
******************************************************************************/
static bool ipd_Read8BitRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint8_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[IPD_SI3474_8BIT_RD_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(	p_inst->i2c_device, i2c_address,
									buf, IPD_SI3474_WR_REG_ADDR_LEN, IPD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, i2c_address,
								buf, IPD_SI3474_8BIT_RD_LEN, IPD_I2C_TIMEOUT_MS) != HAL_OK)
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
* Performs a 16-bit, 2x consecutive 8-bit register read from the specified address
*
* @param    p_inst pointer to I2C PoE driver instance data
* @param 	i2c_address I2C bus address to read from
* @param	ch_addr address of ADC channel to read
* @param	p_val pointer to variable that receives read data
* @return   true if read successful, else false
*
******************************************************************************/
static bool ipd_Read16BitRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint16_t *p_val)
{
	bool ret_val = true;
	uint8_t buf[IPD_SI3474_16BIT_RD_LEN] = {0U};

	/* Set the address pointer to the register to be read */
	buf[0] = reg_addr;

	if (HAL_I2C_Master_Transmit(	p_inst->i2c_device, i2c_address,
									buf, IPD_SI3474_WR_REG_ADDR_LEN, IPD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	/* Read the register */
	if (HAL_I2C_Master_Receive(	p_inst->i2c_device, i2c_address,
								buf, IPD_SI3474_16BIT_RD_LEN, IPD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	if (ret_val)
	{
		*p_val = (uint16_t)buf[0] | (((uint16_t)buf[1] << 8) & 0xFF00U);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Performs a 8-bit register write to the specified address
*
* @param    p_inst pointer to I2C ADC driver instance data
* * @param 	i2c_address I2C bus address to read from
* @param	reg_addr device register address to read from
* @param	val 16-bit data value to write to device register
* @return   true if write successful, else false
* @note     None
*
******************************************************************************/
static bool ipd_Write8itRegister(	ipd_I2cPoeDriver_t *p_inst, uint8_t i2c_address,
									uint8_t reg_addr, uint8_t val)
{
	bool ret_val = true;
	uint8_t buf[IPD_SI3474_8BIT_WR_LEN];

	buf[0] = reg_addr;
	buf[1] = val;

	if (HAL_I2C_Master_Transmit(p_inst->i2c_device, i2c_address,
								buf, IPD_SI3474_8BIT_WR_LEN, IPD_I2C_TIMEOUT_MS) != HAL_OK)
	{
		ret_val = false;
	}

	return ret_val;
}
