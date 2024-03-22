/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file mcp23017.h
**
** Include file for mcp23017.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __MCP23017_H
#define __MCP23017_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
/* Port to other STM32 family micros by changing this include accordingly */
#include "stm32l4xx_hal.h"
#include <stdbool.h>

/*****************************************************************************
*
*  Global Definitions
*
*****************************************************************************/
#define MCP23017_GPIO_PIN_0     ((uint16_t)0x0001)  /* Pin 0 selected    */
#define MCP23017_GPIO_PIN_1     ((uint16_t)0x0002)  /* Pin 1 selected    */
#define MCP23017_GPIO_PIN_2     ((uint16_t)0x0004)  /* Pin 2 selected    */
#define MCP23017_GPIO_PIN_3     ((uint16_t)0x0008)  /* Pin 3 selected    */
#define MCP23017_GPIO_PIN_4     ((uint16_t)0x0010)  /* Pin 4 selected    */
#define MCP23017_GPIO_PIN_5     ((uint16_t)0x0020)  /* Pin 5 selected    */
#define MCP23017_GPIO_PIN_6     ((uint16_t)0x0040)  /* Pin 6 selected    */
#define MCP23017_GPIO_PIN_7     ((uint16_t)0x0080)  /* Pin 7 selected    */
#define MCP23017_GPIO_PIN_8     ((uint16_t)0x0100)  /* Pin 8 selected    */
#define MCP23017_GPIO_PIN_9     ((uint16_t)0x0200)  /* Pin 9 selected    */
#define MCP23017_GPIO_PIN_10    ((uint16_t)0x0400)  /* Pin 10 selected   */
#define MCP23017_GPIO_PIN_11    ((uint16_t)0x0800)  /* Pin 11 selected   */
#define MCP23017_GPIO_PIN_12    ((uint16_t)0x1000)  /* Pin 12 selected   */
#define MCP23017_GPIO_PIN_13    ((uint16_t)0x2000)  /* Pin 13 selected   */
#define MCP23017_GPIO_PIN_14    ((uint16_t)0x4000)  /* Pin 14 selected   */
#define MCP23017_GPIO_PIN_15    ((uint16_t)0x8000)  /* Pin 15 selected   */
#define MCP23017_GPIO_PIN_All   ((uint16_t)0xFFFF)  /* All pins selected */

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
	mcp23017_PinReset = 0,
	mcp23017_PinSet
} mcp23017_PinState_t;

typedef struct mcp23017_I2cGpioDriver
{
	I2C_HandleTypeDef	*i2c_device;
	uint16_t			i2c_address;
	uint16_t			io_dir_mask;		/* '0' = op; '1' = ip */
	uint16_t			default_op_mask;	/* '0' = low; '1' = high */
	GPIO_TypeDef		*i2c_reset_gpio_port;
	uint16_t			i2c_reset_gpio_pin;
	bool 				initialised;
} mcp23017_Driver_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool mcp23017_Init(mcp23017_Driver_t *p_inst);
bool mcp23017_WritePin(mcp23017_Driver_t *p_inst, uint16_t pin, mcp23017_PinState_t pin_state);
bool mcp23017_WritePinsVal(mcp23017_Driver_t *p_inst, uint16_t val);
bool mcp23017_ReadPin(mcp23017_Driver_t *p_inst, uint16_t pin, mcp23017_PinState_t *p_pin_state);
bool mcp23017_ReadPinsVal(mcp23017_Driver_t *p_inst, uint16_t *p_val);
void mcp23017_SetI2cReset(mcp23017_Driver_t *p_inst, bool reset);

/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/


#endif /* __MCP23017_H */
