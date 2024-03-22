/*****************************************************************************/
/**
** Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file spi_adc_driver.c
*
* Driver for ADRV9009 transceiver. Implements a small subset
* of registers for basic hardware testing.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "spi_xcvr_driver.h"
#include "talise_reg_addr_macros.h"

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


/*****************************************************************************/
/**
* Initialise the SPI XCVR driver instance and configures the XCVR ready for
* reading
*
* @param    p_inst pointer to SPI XCVR driver instance data
* @param    spi_device HAL driver handle for the SPI peripheral that the
*           XCVR is connected to
* @param    xcvr_ncs_gpio_port HAL driver GPIO port for XCVR SPI nCS signal
* @param    xcvr_ncs_gpio_pin HAL driver GPIO pin for XCVR SPI nCS signal
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool sxc_InitInstance(  sxc_SpiXcvrDriver_t *p_inst,
                        SPI_HandleTypeDef   *spi_device,
                        GPIO_TypeDef        *xcvr_ncs_gpio_port,
                        uint16_t             xcvr_ncs_gpio_pin)
{
    p_inst->spi_device          = spi_device;
    p_inst->xcvr_ncs_gpio_port  = xcvr_ncs_gpio_port;
    p_inst->xcvr_ncs_gpio_pin   = xcvr_ncs_gpio_pin;
    p_inst->initialised         = true;

    return p_inst->initialised;
}


/*****************************************************************************/
/**
* Initialise the SPI XCVR device
* @param    p_inst pointer to SPI XCVR driver instance data
* @return   true if initialisation successful, else false
* @note     None
*
******************************************************************************/
bool sxc_InitDevice(sxc_SpiXcvrDriver_t *p_inst)
{
    return sxc_WriteRegister(p_inst, TALISE_ADDR_SPI_INTERFACE_CONFIG_A, 0x01);
}

bool sxc_ReadVendorId(sxc_SpiXcvrDriver_t *p_inst, uint16_t *p_id)
{
    bool ret_val = false;
    uint8_t rx_data[2] = {0U};

    if (sxc_ReadRegister(p_inst, TALISE_ADDR_VENDOR_ID_0, &rx_data[0]))
    {
    	if (sxc_ReadRegister(p_inst, TALISE_ADDR_VENDOR_ID_1, &rx_data[1]))
    	{
    		*p_id = ((((uint16_t)(rx_data[1])) << 8) & 0xFF00) |
       		         (((uint16_t)(rx_data[0]))       & 0x00FF);
    		ret_val = true;
    	}
    }

    return ret_val;
}

#if 0
/*****************************************************************************/
/**
* Read the ADC channel, Channel 1 is used to monitor the mixer's RF level,
* read ADC value is returned in units of centi-dBm
*
* @param    p_inst pointer to I2C ADC driver instance data
* @param     p_data pointer to data structure to receive ADC data
* @return   true if ADC data read and returned successfully, else false
* @note     None
*
******************************************************************************/
bool sad_ReadAdcData(sad_SpiAdcDriver_t *p_inst, iad_SpiAdcData_t *p_data)
{
    bool ret_val = false;
    uint8_t tx_buf[SAD_ADC122S101_RDWR_LEN] = {0U};
    uint8_t rx_buf[SAD_ADC122S101_RDWR_LEN] = {0U};
    uint16_t adc_val = 0U;
    float f_val = 0.0f;

    if (p_inst->initialised && (p_data != NULL))
    {
        sad_AssertChipSelect(p_inst, true);

        if (HAL_SPI_TransmitReceive(p_inst->spi_device, tx_buf, rx_buf,
                                    SAD_ADC122S101_RDWR_LEN,
                                    SAD_SPI_TIMEOUT_MS) == HAL_OK)
        {
            /* Using 1650 mV = -20 dBm offset and 4.3 mV / cdBm slope per
             * Mercury code, Vref = 3300 mV, 12-bit ADC, convert ADC reading
             * to units of centi-dBm */
            adc_val = ((uint16_t)rx_buf[0] << 8) | (uint16_t)rx_buf[1];
            f_val = -200.0f + ((((float)adc_val * 3300.0f / 4095.0f) - 1650.0f) / 4.3f);
            p_data->adc_ch_cdbm = (int16_t)f_val;

            ret_val = true;
        }

        sad_AssertChipSelect(p_inst, false);
    }

    return ret_val;
}
#endif

/*****************************************************************************/
/**
* Asserts/de-asserts the nCS signals
*
* @param    p_inst pointer to SPI XCVR driver instance data
* @param    assert true to assert active-low chip select signal, else false
*             to de-assert
* @return   None
* @note     Not checking the driver instance is initialised as this local function
*             is only called from functions which have already checked this
*
******************************************************************************/
void sxc_AssertChipSelect(sxc_SpiXcvrDriver_t *p_inst, bool assert)
{
    if (assert)
    {
        HAL_GPIO_WritePin(  p_inst->xcvr_ncs_gpio_port,
                            p_inst->xcvr_ncs_gpio_pin,
                            GPIO_PIN_RESET);
    }
    else
    {
        HAL_GPIO_WritePin(  p_inst->xcvr_ncs_gpio_port,
                            p_inst->xcvr_ncs_gpio_pin,
                            GPIO_PIN_SET);
    }
}

bool sxc_WriteRegister(sxc_SpiXcvrDriver_t *p_inst, uint16_t addr, uint8_t data)
{
	bool ret_val = false;

    if (p_inst->initialised)
    {
        uint8_t tx_buf[SXC_XCVR_ADDR_LEN + SXC_XCVR_DATA_LEN];
        tx_buf[0] = (uint8_t)((addr >> 8) & 0xFF);
        tx_buf[1] = (uint8_t)(addr & 0xFF);
        tx_buf[2] = data;

        /* De-assert the nCS signal to ensure it is in a known state */
        sxc_AssertChipSelect(p_inst, false);
        HAL_Delay(1U);

        /* Assert the nCS signal */
        sxc_AssertChipSelect(p_inst, true);

        if (HAL_SPI_Transmit( p_inst->spi_device, tx_buf,
        		              (SXC_XCVR_ADDR_LEN + SXC_XCVR_DATA_LEN),
                              SXC_SPI_TIMEOUT_MS) == HAL_OK)
        {
            ret_val = true;
        }

        /* Leave the nCS signals de-asserted */
        sxc_AssertChipSelect(p_inst, false);
    }

	return ret_val;
}

bool sxc_ReadRegister(sxc_SpiXcvrDriver_t *p_inst, uint16_t addr, uint8_t *data)
{
	bool ret_val = false;

    if (p_inst->initialised)
    {
    	int tries = 3;
    	do
    	{
			uint8_t tx_buf[SXC_XCVR_ADDR_LEN];
			uint8_t rx_buf[SXC_XCVR_DATA_LEN];
			tx_buf[0] = ((uint8_t)((addr >> 8) & 0xFF)) | 0x80;
			tx_buf[1] = (uint8_t)(addr & 0xFF);

			/* De-assert the nCS signal to ensure it is in a known state */
			sxc_AssertChipSelect(p_inst, false);
			HAL_Delay(1U);

			/* Assert the nCS signal */
			sxc_AssertChipSelect(p_inst, true);

			if (HAL_SPI_Transmit(p_inst->spi_device, tx_buf, SXC_XCVR_ADDR_LEN, SXC_SPI_TIMEOUT_MS) == HAL_OK)
			{
				if (HAL_SPI_Receive(p_inst->spi_device, rx_buf, SXC_XCVR_DATA_LEN, SXC_SPI_TIMEOUT_MS) == HAL_OK)
				{
					*data = rx_buf[0];
					ret_val = true;
				}
			}

			/* Leave the nCS signals de-asserted */
			sxc_AssertChipSelect(p_inst, false);
    	} while (--tries > 0);
    }

	return ret_val;
}

