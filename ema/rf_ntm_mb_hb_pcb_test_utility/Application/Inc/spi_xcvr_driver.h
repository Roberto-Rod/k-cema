/****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
**
** @file spi_xcvr_driver.h
**
** Include file for spi_xcvr_driver.c
**
** Project : K-CEMA
**
** Build instructions : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __SPI_XCVR_DRIVER_H
#define __SPI_XCVR_DRIVER_H

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
    SPI_HandleTypeDef  *spi_device;
    GPIO_TypeDef       *xcvr_ncs_gpio_port;
    uint16_t            xcvr_ncs_gpio_pin;
    bool                initialised;
} sxc_SpiXcvrDriver_t;

/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
bool sxc_InitInstance(  sxc_SpiXcvrDriver_t *p_inst,
                        SPI_HandleTypeDef   *spi_device,
                        GPIO_TypeDef        *xcvr_ncs_gpio_port,
                        uint16_t             xcvr_ncs_gpio_pin);
bool sxc_InitDevice(sxc_SpiXcvrDriver_t *p_inst);
bool sxc_ReadVendorId(sxc_SpiXcvrDriver_t *p_inst, uint16_t *p_id);

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
#ifdef __SPI_XCVR_DRIVER_C

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/
#define SXC_XCVR_ADDR_LEN             2
#define SXC_XCVR_DATA_LEN             1
#define SXC_SPI_TIMEOUT_MS            100U

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
void sxc_AssertChipSelect(sxc_SpiXcvrDriver_t *p_inst, bool assert);
bool sxc_WriteRegister(sxc_SpiXcvrDriver_t *p_inst, uint16_t addr, uint8_t data);
bool sxc_ReadRegister(sxc_SpiXcvrDriver_t *p_inst, uint16_t addr, uint8_t *data);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/

#endif /* __SPI_XCVR_DRIVER_C */

#endif /* __SPI_XCVR_DRIVER_H */
