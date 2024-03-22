/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file i2c_dac_driver.h
**
** Include file for i2c_dac_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_DAC_DRIVER_H
#define __I2C_DAC_DRIVER_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include "stm32l4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define IDD_MCP4728_CH_NUM		4U

/*****************************************************************************
*
*  Global Macros
*
*****************************************************************************/


/*****************************************************************************
*
*  Global Datatypes
*
*****************************************************************************/
typedef struct
{
	I2C_HandleTypeDef* 	i2c_device;
	uint16_t			i2c_address;
	bool 				initialised;
} idd_I2cDacDriver_t;

typedef struct
{
	uint16_t	ch_mv[IDD_MCP4728_CH_NUM];		/* DAC output value in mV 0 to 4095 */
	bool		pwr_dwn[IDD_MCP4728_CH_NUM];	/* true to power down channel */
} idd_I2cDacFwrData_t;

typedef struct
{
	uint16_t	ch_mv;
	uint8_t		vref;
	uint8_t		gain;
	uint8_t		pwr_dwn_mode;
	uint8_t		rdy_nbusy;
	uint8_t		por;
	uint8_t		addr_bit;
	uint16_t	ee_ch_mv;
	uint8_t		ee_vref;
	uint8_t		ee_gain;
	uint8_t		ee_pwr_dwn_mode;
	uint8_t		ee_rdy_nbusy;
	uint8_t		ee_por;
	uint8_t		ee_addr_bit;
} idd_I2cDacData_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool idd_Init(	idd_I2cDacDriver_t	*p_inst,
				I2C_HandleTypeDef	*p_i2c_device,
				uint16_t			i2c_address);
bool idd_FastWriteDacs(	idd_I2cDacDriver_t 	*p_inst,
						idd_I2cDacFwrData_t dac_data);
bool idd_WriteDacEeprom(	idd_I2cDacDriver_t	*p_inst,
							uint16_t	ch_mv,
							bool		int_vref,
							bool		gain_2,
							uint8_t		pwr_dwn_mode,
							uint16_t 	chan);
bool idd_ReadDac(	idd_I2cDacDriver_t	*p_inst,
					idd_I2cDacData_t 	*p_dac_data,
					uint16_t 			chan);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


/*****************************************************************************
*
*  Local to the C file
*
*****************************************************************************/
#ifdef __I2C_DAC_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define IDD_MCP4728_FWR_DAC_CMD		0x00U
#define IDD_MCP4728_SWR_DAC_EE_CMD	0x58U

#define IDD_MCP4728_CS_A			0x00U
#define IDD_MCP4728_CS_B			0x02U
#define IDD_MCP4728_CS_C			0x04U
#define IDD_MCP4728_CS_D			0x06U

#define IDD_MCP4728_RDY_NBUSY		0x80U
#define IDD_MCP4728_POR				0x40U
#define IDD_MCP4728_ADDR_BITS		0x07U
#define IDD_MCP4728_ADDR_SHIFT		0
#define IDD_MCP4728_VREF_INT		0x80U
#define IDD_MCP4728_PD_BITS			0x60U
#define IDD_MCP4728_PD_SHIFT		5
#define IDD_MCP4728_GAIN_2			0x10U
#define IDD_MCP4728_CH_BITS			0x06U
#define IDD_MCP4728_CH_SHIFT		1

#define IDD_MCP4728_FWR_PD_ON		0x00U
#define IDD_MCP4728_FWR_PD_OFF		0x30U

#define IDD_RD_DAC_LEN			24U
#define IDD_WR_REG_ADDR_LEN		1U
#define IDD_FWR_DAC_LEN			8U
#define IDD_WR_DAC_LEN			3U

#define IDD_MCP2748_WR_TIME_MS	50U
#define IDD_I2C_TIMEOUT_MS		100U

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
bool idd_ReadData(idd_I2cDacDriver_t *p_inst, uint8_t *p_data, uint16_t size);
bool idd_WriteData(idd_I2cDacDriver_t *p_inst, uint8_t *p_data, uint16_t size);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


#endif /* __I2C_DAC_DRIVER_C */

#endif /* __I2C_DAC_DRIVER_H */
