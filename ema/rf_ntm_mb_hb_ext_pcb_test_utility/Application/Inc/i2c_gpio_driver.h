/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file i2c_gpio_driver.h
**
** Include file for i2c_gpio_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __I2C_GPIO_DRIVER_H
#define __I2C_GPIO_DRIVER_H

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
#define IGD_GPIO_PIN_0     ((uint16_t)0x0001)  /* Pin 0 selected    */
#define IGD_GPIO_PIN_1     ((uint16_t)0x0002)  /* Pin 1 selected    */
#define IGD_GPIO_PIN_2     ((uint16_t)0x0004)  /* Pin 2 selected    */
#define IGD_GPIO_PIN_3     ((uint16_t)0x0008)  /* Pin 3 selected    */
#define IGD_GPIO_PIN_4     ((uint16_t)0x0010)  /* Pin 4 selected    */
#define IGD_GPIO_PIN_5     ((uint16_t)0x0020)  /* Pin 5 selected    */
#define IGD_GPIO_PIN_6     ((uint16_t)0x0040)  /* Pin 6 selected    */
#define IGD_GPIO_PIN_7     ((uint16_t)0x0080)  /* Pin 7 selected    */
#define IGD_GPIO_PIN_8     ((uint16_t)0x0100)  /* Pin 8 selected    */
#define IGD_GPIO_PIN_9     ((uint16_t)0x0200)  /* Pin 9 selected    */
#define IGD_GPIO_PIN_10    ((uint16_t)0x0400)  /* Pin 10 selected   */
#define IGD_GPIO_PIN_11    ((uint16_t)0x0800)  /* Pin 11 selected   */
#define IGD_GPIO_PIN_12    ((uint16_t)0x1000)  /* Pin 12 selected   */
#define IGD_GPIO_PIN_13    ((uint16_t)0x2000)  /* Pin 13 selected   */
#define IGD_GPIO_PIN_14    ((uint16_t)0x4000)  /* Pin 14 selected   */
#define IGD_GPIO_PIN_15    ((uint16_t)0x8000)  /* Pin 15 selected   */
#define IGD_GPIO_PIN_All   ((uint16_t)0xFFFF)  /* All pins selected */

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
typedef enum
{
	igd_PinReset = 0,
	igd_PinSet
} igd_PinState;

typedef struct
{
	I2C_HandleTypeDef	*i2c_device;
	uint16_t			i2c_address;
	uint16_t			io_dir_mask;		/* '0' = op; '1' = ip */
	uint16_t			io_pu_mask;			/* '0' = disabled; '1' = enabled */
	uint16_t			default_op_mask;	/* '0' = low; '1' = high */
	GPIO_TypeDef		*i2c_reset_gpio_port;
	uint16_t			i2c_reset_gpio_pin;
	bool 				initialised;
} igd_I2cGpioDriver_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool igd_Init(igd_I2cGpioDriver_t *p_inst);
bool igd_WritePin(igd_I2cGpioDriver_t *p_inst, uint16_t pin, igd_PinState pin_state);
bool igd_WritePinsVal(igd_I2cGpioDriver_t *p_inst, uint16_t val);
bool igd_ReadPin(igd_I2cGpioDriver_t *p_inst, uint16_t pin, igd_PinState *p_pin_state);
bool igd_ReadPinsVal(igd_I2cGpioDriver_t *p_inst, uint16_t *p_val);
void igd_SetI2cReset(igd_I2cGpioDriver_t *p_inst, bool reset);

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
#ifdef __I2C_GPIO_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define IGD_MCP23017_IODIR_REG_ADDR		0x00U
#define IGD_MCP23017_GPIO_REG_ADDR		0x12U
#define IGD_MCP23017_OLAT_REG_ADDR		0x14U
#define IGD_MCP23017_GPPU_REG_ADDR		0x0CU
#define IGD_MCP23017_RD_IO_LEN			2U
#define IGD_MCP23017_WR_REG_ADDR_LEN	1U
#define IGD_MCP23017_WR_IO_LEN			3U

#define IGD_I2C_TIMEOUT_MS				100U

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
bool igd_ReadRegister(	igd_I2cGpioDriver_t *p_inst,
						uint8_t reg_addr, uint16_t *p_val);
bool igd_WriteRegister(	igd_I2cGpioDriver_t *p_inst,
						uint8_t reg_addr, uint16_t val);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/


#endif /* __I2C_GPIO_DRIVER_C */

#endif /* __I2C_GPIO_DRIVER_H */
