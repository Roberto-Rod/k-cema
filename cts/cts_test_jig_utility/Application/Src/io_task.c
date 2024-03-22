/*****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
*
* @file io_task.c
*
* Provides analogue and discrete IO task handling.
*
* Project : K-CEMA
*
* Build instructions : Compile using STM32CubeIDE Compiler
*
******************************************************************************/
#include "io_task.h"
#include "mcp23017.h"
#include "spi_synth_driver.h"
#include "i2c_eeprom.h"
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/

/* MCP23017 GPIO expander definitions */
#define IOT_NO_I2C_EXPANDERS	3

#define IOT_RX_ATT_EXP			1
#define IOT_RX_ATT_PINS			(MCP23017_GPIO_PIN_8 | MCP23017_GPIO_PIN_9 | MCP23017_GPIO_PIN_10 | \
								 MCP23017_GPIO_PIN_11 | MCP23017_GPIO_PIN_12 | MCP23017_GPIO_PIN_13)
#define IOT_RX_ATT_LSHIFT		8
#define	IOT_RX_ATT_MIN_VAL		0U
#define	IOT_RX_ATT_MAX_VAL		63U

#define IOT_RX_PATH_SW1_EXP		0
#define IOT_RX_PATH_SW1_PINS	(MCP23017_GPIO_PIN_10 | MCP23017_GPIO_PIN_11 | MCP23017_GPIO_PIN_12)
#define IOT_RX_PATH_SW1_LSHIFT	10

#define IOT_RX_PATH_SW2_EXP		0
#define IOT_RX_PATH_SW2_PINS	(MCP23017_GPIO_PIN_13 | MCP23017_GPIO_PIN_14 | MCP23017_GPIO_PIN_15)
#define IOT_RX_PATH_SW2_LSHIFT	13

#define	IOT_RX_PATH_MIN_VAL		0U
#define	IOT_RX_PATH_MAX_VAL		7U

#define IOT_TX_ATT_EXP			1
#define IOT_TX_ATT_PINS			(MCP23017_GPIO_PIN_0 | MCP23017_GPIO_PIN_1 | MCP23017_GPIO_PIN_2 | \
								 MCP23017_GPIO_PIN_3 | MCP23017_GPIO_PIN_4 | MCP23017_GPIO_PIN_5)
#define IOT_TX_ATT_LSHIFT		0
#define	IOT_TX_ATT_MIN_VAL		0U
#define	IOT_TX_ATT_MAX_VAL		63U

#define IOT_TX_PATH_SW1_EXP		0
#define IOT_TX_PATH_SW1_PINS	(MCP23017_GPIO_PIN_0 | MCP23017_GPIO_PIN_1)
#define IOT_TX_PATH_SW1_LSHIFT	0

#define IOT_TX_PATH_SW2_EXP		0
#define IOT_TX_PATH_SW2_PINS	(MCP23017_GPIO_PIN_2 | MCP23017_GPIO_PIN_3)
#define IOT_TX_PATH_SW2_LSHIFT	2

#define	IOT_TX_PATH_MIN_VAL		0U
#define	IOT_TX_PATH_MAX_VAL		3U

#define IOT_TX_DIV_EXP			0
#define IOT_TX_DIV_PINS			(MCP23017_GPIO_PIN_4 | MCP23017_GPIO_PIN_5 | MCP23017_GPIO_PIN_6)
#define IOT_TX_DIV_LSHIFT		4

#define	IOT_TX_DIV_MIN_VAL		0U
#define	IOT_TX_DIV_MAX_VAL		7U

#define IOT_TB_RF_PATH_EXP		2
#define IOT_TB_RF_PATH_PINS		(MCP23017_GPIO_PIN_8 | MCP23017_GPIO_PIN_9 | MCP23017_GPIO_PIN_10)
#define IOT_TB_RF_PATH_LSHIFT	8

#define	IOT_TB_RF_PATH_MIN_VAL	0U
#define	IOT_TB_RF_PATH_MAX_VAL	2U

/* 1PPS accuracy limits */
#define IOT_1PPS_DELTA_MIN		999U
#define IOT_1PPS_DELTA_MAX		1001U

/* ADC channel definitions */
#define IOT_ADC_ADC_BITS		4096
#define IOT_VDD_CALIB_MV 		((int32_t) (3000))

/* Temperature sensor and voltage reference calibration value addresses */
#define IOT_TEMP130_CAL_ADDR	((uint16_t*) ((uint32_t) 0x1FFF75A8))
#define IOT_TEMP30_CAL_ADDR 	((uint16_t*) ((uint32_t) 0x1FFF75CA))
#define IOT_VREFINT_CAL_ADDR 	((uint16_t*) ((uint32_t) 0x1FFF75AA))

/* DMA interrupt flag bit position calculation */
#define IOT_DMA_IFCR_TC_FLAG(dma_channel) (1UL << ((4 * dma_channel) + 1))
#define IOT_DMA_IFCR_HT_FLAG(dma_channel) (1UL << ((4 * dma_channel) + 2))
#define IOT_DMA_IFCR_TE_FLAG(dma_channel) (1UL << ((4 * dma_channel) + 3))

/* Hardware ID I2C bus addresses */
#define IOT_PCA9500_GPIO_I2C_ADDR		(0x23U << 1)
#define IOT_PCA9500_EEPROM_I2C_ADDR 	(0x53U << 1)

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef struct iot_AdcChannel
{
	iot_AdcChannelId_t	adc_ch;
	int32_t				multiplier;
	int32_t				divider;
	int32_t				raw_value;
	int16_t				scaled_value;
	char				name[IOT_ANALOGUE_READING_NAME_MAX_LEN];
} iot_AdcChannel_t;

typedef struct iot_GpoPin
{
	uint16_t expander;
	uint16_t mask;
	char name[IOT_MAX_STR_LEN];
} iot_GpoPin_t;

static const iot_GpoPin_t lg_iot_gpo_pin_map[iot_gpo_qty] = {
		{0, MCP23017_GPIO_PIN_7, "uut_rfb_synth_en"},
		{0, MCP23017_GPIO_PIN_8, "uut_rfb_synth_ntx_rx_sel"},
		{0, MCP23017_GPIO_PIN_9, "uut_rfb_rx_path_mixer_en"},
		{2, MCP23017_GPIO_PIN_2, "uut_rfb_p3v3_en"},
		{2, MCP23017_GPIO_PIN_3, "uut_rfb_p5v0_en"},
		{2, MCP23017_GPIO_PIN_4, "uut_rfb_p3v3_tx_en"},
		{2, MCP23017_GPIO_PIN_5, "uut_rfb_p5v0_tx_en"},
		{2, MCP23017_GPIO_PIN_12, "uut_db_cts_pwr_en"},
		{2, MCP23017_GPIO_PIN_0, "uut_db_cts_p12v_en"},
		{2, MCP23017_GPIO_PIN_1, "uut_db_cts_p3v3_en"}
};


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
static void iot_StartAdcConversion(void);
void iot_AssertSynthCs(bool assert);
static bool iot_InitGpioExpanders(void);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static iot_Init_t lg_iot_init_data = {0};
static bool lg_iot_initialised = false;
static const TickType_t lg_iot_task_period_ms = 50;

static mcp23017_Driver_t lg_iot_gpio_driver[IOT_NO_I2C_EXPANDERS] = {0};
static const uint8_t 	lg_iot_gpio_exp_i2c_addr[IOT_NO_I2C_EXPANDERS] 			= {0x25U << 1, 	0x26U << 1,	0x27U << 1};
static const uint16_t  lg_iot_gpio_exp_io_dir_mask[IOT_NO_I2C_EXPANDERS] 		= {0x0000U, 	0xC0C0U, 	0xE880U}; /* '1' = ip; '0' = op */
#if 0
static const uint16_t  lg_iot_gpio_exp_io_pu_mask[IOT_NO_I2C_EXPANDERS]		= {0xFFFFU, 	0xFFFFU, 	0xFFFFU}; /* '1' = en; '0' = dis */
#endif
static const uint16_t  lg_iot_gpio_exp_default_op_mask[IOT_NO_I2C_EXPANDERS] 	= {0x0000U, 	0x0000U, 	0x0000U};

static uint16_t lg_iot_gpo_data[IOT_NO_I2C_EXPANDERS] = {0, 0, 0};
static uint16_t lg_iot_gpi_data[IOT_NO_I2C_EXPANDERS] = {0, 0, 0};

static iot_AdcChannel_t lg_iot_adc_channels[iot_adc_ch_qty] = {
		{iot_adc_psu_p12v_vsns, 11, IOT_ADC_ADC_BITS, 0, 0, "PSU +12V Voltage (mV)"},
		{iot_adc_psu_p5v0_vsns, 3,  IOT_ADC_ADC_BITS, 0, 0, "PSU +5V0 Voltage (mV)"},
		{iot_adc_psu_p3v3_isns, 100,  IOT_ADC_ADC_BITS * 195, 0, 0, "PSU +3V3 Current (mA)"},
		{iot_adc_psu_p3v3_vsns, 3,  IOT_ADC_ADC_BITS, 0, 0, "PSU +3V3 Voltage (mV)"},
		{iot_adc_psu_p5v0_isns, 100,  IOT_ADC_ADC_BITS * 195, 0, 0, "PSU +5V0 Current (mA)"},
		{iot_adc_vref_int, 	    1,  IOT_ADC_ADC_BITS, 0, 0, "Vref Internal Voltage (mV)"}	/* Vref internal should always be the last channel */
};

static uint16_t lg_iot_adc_buf[iot_adc_ch_qty] = {0};

static ssd_SpiSynthDriver_t lg_iot_spi_synth = {0};
static hci_HwConfigInfo_t lg_iot_hci = {0};
static iee_DeviceInfo_t lg_i2c_eeprom = {0};


/*****************************************************************************/
/**
* Initialise the IO task.
*
* @param    init_data initialisation data for the task
*
******************************************************************************/
void iot_InitTask(iot_Init_t init_data)
{
	/* Assume initialisation success */
	lg_iot_initialised = true;

	memcpy((void *)&lg_iot_init_data, (void *)&init_data, sizeof(iot_Init_t));

	/* Not catching the error here, if they aren't present the task loop will
	 * detect this and attempt to re-initialise them. */
	(void) iot_InitGpioExpanders();

	/* Configure the ADC DMA channel, the ADC channels are configured by the STM32CubeMX auto-generated code in main.c */
	uint32_t dma_reg_addr = LL_ADC_DMA_GetRegAddr(lg_iot_init_data.adc_device, LL_ADC_DMA_REG_REGULAR_DATA);
    LL_DMA_SetPeriphAddress(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel, dma_reg_addr);
    LL_DMA_SetMemoryAddress(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel, (uint32_t)&lg_iot_adc_buf[0]);

    /* Enable DMA Transfer Complete interrupt */
    LL_DMA_EnableIT_TC(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel);

	/* Calibrate the ADC to improve the accuracy of results then enable it */
	LL_ADC_StartCalibration(lg_iot_init_data.adc_device, LL_ADC_SINGLE_ENDED);
	while (LL_ADC_IsCalibrationOnGoing(lg_iot_init_data.adc_device));

	if (!LL_ADC_IsEnabled(lg_iot_init_data.adc_device))
	{
		LL_ADC_Enable(lg_iot_init_data.adc_device);
	}

	/* Set the 1PPS source to internal (STM32) by default */
	HAL_GPIO_WritePin(lg_iot_init_data.pps_ext_en_gpio_port, lg_iot_init_data.pps_ext_en_gpio_pin, GPIO_PIN_RESET);

	/* De-assert the SPI Synth CS signal then initialise the SPI Synth device */
	iot_AssertSynthCs(false);
	lg_iot_initialised &= ssd_InitInstance(&lg_iot_spi_synth, lg_iot_init_data.spi_device, iot_AssertSynthCs);

	hci_Init(&lg_iot_hci, init_data.i2c_device, IOT_PCA9500_GPIO_I2C_ADDR, IOT_PCA9500_EEPROM_I2C_ADDR);
	iee_Init(&lg_i2c_eeprom, lg_iot_init_data.i2c_device, IOT_EEPROM_I2C_ADDR, IOT_EEPROM_ADDR_LEN, IOT_EEPROM_MEM_SIZE_BYTES, IOT_EEPROM_PAGE_SIZE_BYTES, IOT_EEPROM_WRITE_TIME_MS);
}


/*****************************************************************************/
/**
* Resets then re-initialises the MCP23017 GPIO expanders, assumes that the local
* global variable lg_iot_init_data has been populated with relevant information.
*
* @return true if successful, else false
*
******************************************************************************/
static bool iot_InitGpioExpanders(void)
{
	bool ret_val = true;

	/* To prevent the I2C pull-ups back powering the Digital Board the I2C
	 * loop back needs to be enabled to isolate the I2C bus.  The loop back
	 * can be disabled once the Digital Board has been powered up. */
	(void) iot_SetI2cLoobackEnable(true);

	/* Perform a hard-reset of the GPIO expanders */
	HAL_GPIO_WritePin(lg_iot_init_data.i2c_reset_gpio_port, lg_iot_init_data.i2c_reset_gpio_pin, GPIO_PIN_RESET);

	/* Re-initialise the I2C peripheral, this can get locked up otherwise. */
	HAL_I2C_DeInit(lg_iot_init_data.i2c_device);
	HAL_I2C_Init(lg_iot_init_data.i2c_device);
	HAL_I2CEx_ConfigAnalogFilter(lg_iot_init_data.i2c_device, I2C_ANALOGFILTER_ENABLE);
	HAL_I2CEx_ConfigDigitalFilter(lg_iot_init_data.i2c_device, 0);

	HAL_Delay(1U);
	HAL_GPIO_WritePin(lg_iot_init_data.i2c_reset_gpio_port, lg_iot_init_data.i2c_reset_gpio_pin, GPIO_PIN_SET);

	/* Re-configure the GPIO expander registers to their initial states. */
	for (int16_t i = 0; i < IOT_NO_I2C_EXPANDERS; ++i)
	{
		lg_iot_gpio_driver[i].i2c_device 			= lg_iot_init_data.i2c_device;
		lg_iot_gpio_driver[i].i2c_address 			= lg_iot_gpio_exp_i2c_addr[i];
		lg_iot_gpio_driver[i].io_dir_mask 			= lg_iot_gpio_exp_io_dir_mask[i];
		lg_iot_gpio_driver[i].default_op_mask 		= lg_iot_gpio_exp_default_op_mask[i];

		ret_val &= mcp23017_Init(&lg_iot_gpio_driver[i]);
		lg_iot_gpo_data[i] = lg_iot_gpio_exp_default_op_mask[i];
	}

	return ret_val;
}


/*****************************************************************************/
/**
* IO task function.
*
* The task period is based on the LTC2991 worst-case cycle time to perform
* conversions on 9x single-ended channels, 1.8 ms/channel and the temperature
* channel, 55 ms/channel.
*
* @param    argument defined by FreeRTOS function prototype, not used
* @return   None
*
******************************************************************************/
void iot_IoTask(void const *argument)
{
	TickType_t last_wake_time = osKernelSysTick();
	bool gpio_expander_success = true;

	if (!lg_iot_initialised)
	{
		for(;;)
		{
			osDelay(1U);
		}
	}

	/* Kick off the first ADC conversion sequence, the results will be collected in the task loop */
	iot_StartAdcConversion();

	for(;;)
	{
		osDelayUntil(&last_wake_time, lg_iot_task_period_ms);

		/* Only update the GPIO expanders if the I2C peripheral is available */
		if (osMutexWait(lg_iot_init_data.i2c_mutex, 0U) == osOK)
		{
			/* If any of the GPIO read/writes failed last time the task ran then re-initialise
			 * the GPIO expanders, the +12V test jig supply may have been removed. */
			if (!gpio_expander_success)
			{
				gpio_expander_success = iot_InitGpioExpanders();
			}

			/* Handle special cases to prevent the GPIO expanders back powering the board under test */
			if ((lg_iot_gpo_data[lg_iot_gpo_pin_map[iot_gpo_uut_rfb_p3v3_en].expander] & lg_iot_gpo_pin_map[iot_gpo_uut_rfb_p3v3_en].mask))
			{
				/* Set the RF Synth nCS signal high */
				iot_AssertSynthCs(false);
			}
			else
			{
				/* Ensure all the GPIO expander outputs to the RF Board are low,
				 * GPIO expanders 0x25 (U5) and 0x26 (U7) */
				lg_iot_gpo_data[0] = 0U;
				lg_iot_gpo_data[1] = 0U;

				/* Set the RF Synth nCS signal low */
				iot_AssertSynthCs(true);
			}

			if ((!(lg_iot_gpo_data[lg_iot_gpo_pin_map[iot_gpo_uut_db_cts_pwr_en].expander] & lg_iot_gpo_pin_map[iot_gpo_uut_db_cts_pwr_en].mask)) ||
				((!(lg_iot_gpo_data[lg_iot_gpo_pin_map[iot_gpo_uut_db_cts_p3v3_en].expander] & lg_iot_gpo_pin_map[iot_gpo_uut_db_cts_p3v3_en].mask))))
			{
				/* To prevent the I2C pull-ups back powering the Digital Board the I2C
				 * loop back needs to be enabled to isolate the I2C bus.  The loop back
				 * can be disabled once the Digital Board has been powered up. */
				(void) iot_SetI2cLoobackEnable(true);
			}

			for (int16_t i = 0; i < IOT_NO_I2C_EXPANDERS; ++i)
			{
				if (gpio_expander_success)
				{
					gpio_expander_success &= mcp23017_ReadPinsVal(&lg_iot_gpio_driver[i], &lg_iot_gpi_data[i]);
				}

				if(gpio_expander_success)
				{
					gpio_expander_success &= mcp23017_WritePin(&lg_iot_gpio_driver[i], lg_iot_gpo_data[i], mcp23017_PinSet);
				}

				if (gpio_expander_success)
				{
					gpio_expander_success &= mcp23017_WritePin(&lg_iot_gpio_driver[i], ~lg_iot_gpo_data[i], mcp23017_PinReset);
				}
			}

			osMutexRelease(lg_iot_init_data.i2c_mutex);
		}

		/* Check if the ADC conversion sequence is complete */
		if (osSemaphoreWait(lg_iot_init_data.adc_semaphore, 0U) == osOK)
		{
			/* Fetch data from the ADC buffer */
			for (int16_t i = 0; i < iot_adc_ch_qty; ++i)
			{
				lg_iot_adc_channels[i].raw_value = (int32_t)lg_iot_adc_buf[i];
			}

			/* Use the Vrefint reading and calibration value to calculate the Vrefext in mV */
			lg_iot_adc_channels[iot_adc_vref_int].scaled_value = (int16_t)((IOT_VDD_CALIB_MV * (int32_t)*IOT_VREFINT_CAL_ADDR) / lg_iot_adc_channels[iot_adc_vref_int].raw_value);

			/* Scale the remaining ADC channels */
			for (int16_t i = 0; i < iot_adc_vref_int; ++i)
			{
				int32_t raw_value = lg_iot_adc_channels[i].raw_value;
				int32_t multiplier = lg_iot_adc_channels[i].multiplier;
				int32_t vref_ext_mv = (int32_t)lg_iot_adc_channels[iot_adc_vref_int].scaled_value;
				int32_t divider = lg_iot_adc_channels[i].divider;
				lg_iot_adc_channels[i].scaled_value = (raw_value * multiplier * vref_ext_mv) / divider;
			}

			iot_StartAdcConversion();
		}
	}
}


/*****************************************************************************/
/**
* Return the scaled value for the specified ADC channel
*
* @param	p_scaled_value receives the scaled value
* @param	p_channel_name receives pointer to constant string describing the
* 			set transmit path
* @return   true if scaled channel reading returned, else false
*
******************************************************************************/
bool iot_GetAdcScaledValue(iot_AdcChannelId_t adc_channel, int16_t *p_scaled_value, const char **p_channel_name)
{
	static const char invalid_channel[] = "Invalid ADC Channel!";

	if (lg_iot_initialised && ((adc_channel >= 0) && (adc_channel < iot_adc_ch_qty)))
	{
		*p_scaled_value = lg_iot_adc_channels[adc_channel].scaled_value;
		*p_channel_name = lg_iot_adc_channels[adc_channel].name;
		return true;
	}
	else
	{
		*p_channel_name = invalid_channel;
		return false;
	}
}


/*****************************************************************************/
/**
* Reconfigures the ADC DMA channel to capture data from the ADC conversion
* sequence then starts the ADC conversion sequence.
*
******************************************************************************/
static void iot_StartAdcConversion(void)
{
	/* Reset the DMA controller for the next ADC conversion sequence, clear irq flags and reset transfer count */
	LL_DMA_DisableChannel(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel);
	WRITE_REG(lg_iot_init_data.adc_dma_device->IFCR, IOT_DMA_IFCR_TC_FLAG(lg_iot_init_data.adc_dma_channel) |
													 IOT_DMA_IFCR_HT_FLAG(lg_iot_init_data.adc_dma_channel) |
													 IOT_DMA_IFCR_TE_FLAG(lg_iot_init_data.adc_dma_channel));
	LL_DMA_SetDataLength(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel, iot_adc_ch_qty);
	LL_DMA_EnableChannel(lg_iot_init_data.adc_dma_device, lg_iot_init_data.adc_dma_channel);

	/* Start the ADC conversion sequence */
	LL_ADC_REG_StartConversion(lg_iot_init_data.adc_device);
}


/*****************************************************************************/
/**
* Handler for the ADC DMA interrupts.
*
* @param	adc_device ADC device associated with this DMA interrupt.
*
******************************************************************************/
void iot_AdcDMAIrqHandler(ADC_TypeDef *adc_device)
{
	if (adc_device == lg_iot_init_data.adc_device)
	{
		uint32_t adc_dma_channel = lg_iot_init_data.adc_dma_channel;
		DMA_TypeDef	*adc_dma_device = lg_iot_init_data.adc_dma_device;

	    if (READ_BIT(adc_dma_device->ISR, IOT_DMA_IFCR_TE_FLAG(adc_dma_channel)) == IOT_DMA_IFCR_TE_FLAG(adc_dma_channel))
	    {
	        /* Clear transfer error flag */
	        WRITE_REG(adc_dma_device->IFCR, IOT_DMA_IFCR_TE_FLAG(adc_dma_channel));
	        /* Clear the data in the ADC buffer */
	        memset(lg_iot_adc_buf, 0, sizeof(lg_iot_adc_buf));
	        /* Conversion complete, signal the task */
	        (void) osSemaphoreRelease(lg_iot_init_data.adc_semaphore);
	    }
	    else if (LL_DMA_IsEnabledIT_TC(adc_dma_device, adc_dma_channel) &&
	    			(READ_BIT(adc_dma_device->ISR, IOT_DMA_IFCR_TC_FLAG(adc_dma_channel)) == IOT_DMA_IFCR_TC_FLAG(adc_dma_channel)))
	    {
	       /* Clear transfer complete flag */
	       WRITE_REG(adc_dma_device->IFCR, IOT_DMA_IFCR_TC_FLAG(adc_dma_channel));
	       /* Conversion complete, signal the task */
	       (void) osSemaphoreRelease(lg_iot_init_data.adc_semaphore);
	    }
	}
}


/*****************************************************************************/
/**
* Enable/disable the 1PPS output by starting or stopping the timer in irq
* driver in PWM mode.
*
* @param    enable true to enable 1PPS output, false to disable 1PPS output
*
******************************************************************************/
void iot_Enable1PpsOp(bool enable)
{
	if (lg_iot_initialised)
	{
		if (enable)
		{
			HAL_TIMEx_PWMN_Start_IT(lg_iot_init_data.pps_out_htim, lg_iot_init_data.pps_out_channel);
		}
		else
		{
			HAL_TIMEx_PWMN_Stop_IT(lg_iot_init_data.pps_out_htim,  lg_iot_init_data.pps_out_channel);
		}
	}
}


/*****************************************************************************/
/**
* Set the 1PPS source.
*
* @param    external true to set external 1PPS source (test board J9),
* 			false to set internal 1PPS source (STM32)
*
******************************************************************************/
void iot_Set1PpsSource(bool external)
{
	if (lg_iot_initialised)
	{
		HAL_GPIO_WritePin(lg_iot_init_data.pps_ext_en_gpio_port,
						  lg_iot_init_data.pps_ext_en_gpio_pin,
						  external ? GPIO_PIN_SET : GPIO_PIN_RESET);

	}
}


/*****************************************************************************/
/**
* Set the rx attenuation to specified value, attenuator works by winding out
* attenuation, 0 = max attenuation so value must be converted to set pins
*
* @param	atten required attenuation in 0.5 dB steps, e.g. 5 = 2.5 dB
* @return   true if setting attenuation is successful, else false
*
******************************************************************************/
bool iot_SetRxAtten(uint16_t atten)
{
	if (lg_iot_initialised && ((atten >= IOT_RX_ATT_MIN_VAL) && (atten <= IOT_RX_ATT_MAX_VAL)))
	{
		atten = IOT_RX_ATT_MAX_VAL - atten;
		lg_iot_gpo_data[IOT_RX_ATT_EXP] &= ~IOT_RX_ATT_PINS;
		lg_iot_gpo_data[IOT_RX_ATT_EXP] |= (atten <<  IOT_RX_ATT_LSHIFT) & IOT_RX_ATT_PINS;

		return true;
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Set the receive path to the requested value.
*
* @param	rx_path receive path: IOT_RX_PATH_MIN_VAL to IOT_RX_PATH_MAX_VAL
* @param	p_rx_path_name receives pointer to constant string describing the
* 			set receive path
* @return   true if setting receive path is successful, else false
*
******************************************************************************/
bool iot_SetRxPath(uint16_t rx_path, const char **p_rx_path_name)
{
	typedef struct rx_path
	{
		uint16_t sw1;
		uint16_t sw2;
		char name[IOT_MAX_STR_LEN];
	} rx_path_t;

	static const rx_path_t rx_path_map[IOT_RX_PATH_MAX_VAL + 1] = {
			{0x4U, 0x5U, "RX0: 20-500 MHz"},
			{0x5U, 0x0U, "RX1: 500-800 MHz"},
			{0x1U, 0x4U, "RX2: 800-2000 MHz"},
			{0x6U, 0x2U, "RX3: 2000-2600 MHz"},
			{0x6U, 0x6U, "RX4: 2600-4400 MHz"},
			{0x2U, 0x1U, "RX5: 4400-6000 MHz"},
			{0x3U, 0x3U, "Isolation"},
			{0x0U, 0x3U, "TX"}
	};

	static const char invalid_path_name[] = "Invalid Tx Path!";

	if (lg_iot_initialised && ((rx_path >= IOT_RX_PATH_MIN_VAL) && (rx_path <= IOT_RX_PATH_MAX_VAL)))
	{
		/* Set SW1 pin state */
		lg_iot_gpo_data[IOT_RX_PATH_SW1_EXP] &= ~IOT_RX_PATH_SW1_PINS;
		lg_iot_gpo_data[IOT_RX_PATH_SW1_EXP] |= (rx_path_map[rx_path].sw1 <<  IOT_RX_PATH_SW1_LSHIFT) & IOT_RX_PATH_SW1_PINS;

		/* Set SW2 pin state */
		lg_iot_gpo_data[IOT_RX_PATH_SW2_EXP] &= ~IOT_RX_PATH_SW2_PINS;
		lg_iot_gpo_data[IOT_RX_PATH_SW2_EXP] |= (rx_path_map[rx_path].sw2 <<  IOT_RX_PATH_SW2_LSHIFT) & IOT_RX_PATH_SW2_PINS;

		*p_rx_path_name = rx_path_map[rx_path].name;

		return true;
	}
	else
	{
		*p_rx_path_name = invalid_path_name;
		return false;
	}
}


/*****************************************************************************/
/**
* Set the tx attenuation to specified value, attenuator works by winding out
* attenuation, 0 = max attenuation so value must be converted to set pins
*
* @param	atten required attenuation in 0.5 dB steps, e.g. 5 = 2.5 dB
* @return   true if setting attenuation is successful, else false
*
******************************************************************************/
bool iot_SetTxAtten(uint16_t atten)
{
	if (lg_iot_initialised && ((atten >= IOT_TX_ATT_MIN_VAL) && (atten <= IOT_TX_ATT_MAX_VAL)))
	{
		atten = IOT_TX_ATT_MAX_VAL - atten;
		lg_iot_gpo_data[IOT_TX_ATT_EXP] &= ~IOT_TX_ATT_PINS;
		lg_iot_gpo_data[IOT_TX_ATT_EXP] |= (atten <<  IOT_TX_ATT_LSHIFT) & IOT_TX_ATT_PINS;

		return true;
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Set the transmit path to the requested value.
*
* @param	tx_path transmit path: IOT_TX_PATH_MIN_VAL to IOT_TX_PATH_MAX_VAL
* @param	p_tx_path_name receives pointer to constant string describing the
* 			set transmit path
* @return   true if setting transmit path is successful, else false
*
******************************************************************************/
bool iot_SetTxPath(uint16_t tx_path, const char **p_tx_path_name)
{
	typedef struct tx_path
	{
		uint16_t sw1;
		uint16_t sw2;
		char name[IOT_MAX_STR_LEN];
	} tx_path_t;

	static const tx_path_t tx_path_map[IOT_TX_PATH_MAX_VAL + 1] = {
			{0x0U, 0x3U, "TX0: 20-800 MHz"},
			{0x3U, 0x0U, "TX1: 700-1500 MHz"},
			{0x1U, 0x2U, "TX2: 1200-2700 MHz"},
			{0x2U, 0x1U, "TX3: 2400-6000 MHz"}
	};

	static const char invalid_path_name[] = "Invalid Tx Path!";

	if (lg_iot_initialised && ((tx_path >= IOT_RX_PATH_MIN_VAL) && (tx_path <= IOT_TX_PATH_MAX_VAL)))
	{
		/* Set SW1 pin state */
		lg_iot_gpo_data[IOT_TX_PATH_SW1_EXP] &= ~IOT_TX_PATH_SW1_PINS;
		lg_iot_gpo_data[IOT_TX_PATH_SW1_EXP] |= (tx_path_map[tx_path].sw1 <<  IOT_TX_PATH_SW1_LSHIFT) & IOT_TX_PATH_SW1_PINS;

		/* Set SW2 pin state */
		lg_iot_gpo_data[IOT_RX_PATH_SW2_EXP] &= ~IOT_TX_PATH_SW2_PINS;
		lg_iot_gpo_data[IOT_RX_PATH_SW2_EXP] |= (tx_path_map[tx_path].sw2 <<  IOT_TX_PATH_SW2_LSHIFT) & IOT_TX_PATH_SW2_PINS;

		*p_tx_path_name = tx_path_map[tx_path].name;

		return true;
	}
	else
	{
		*p_tx_path_name = invalid_path_name;
		return false;
	}
}


/*****************************************************************************/
/**
* Set the transmit divider to the requested value.
*
* @param	tx_div receiver divider: IOT_TX_DIV_MIN_VAL to IOT_TX_DIV_MAX_VAL
* @param	p_tx_div_name receives pointer to constant string describing the
* 			set divide ratio
* @return   true if setting transmit divider is successful, else false
*
******************************************************************************/
bool iot_SetTxDivider(uint16_t tx_div, const char **p_tx_div_name)
{
	typedef struct tx_div
	{
		uint16_t pins;
		char name[IOT_MAX_STR_LEN];
	} tx_div_t;

	static const tx_div_t tx_div_map[IOT_TX_DIV_MAX_VAL + 1] = {
			{0x0U, "0 - Divide Ratio 1"},
			{0x1U, "1 - Divide Ratio 2"},
			{0x10U, "2 - Invalid Tx Divider Value!"},
			{0x3U, "3 - Divide Ratio 4"},
			{0x10U, "4 - Invalid Tx Divider Value!"},
			{0x10U, "5 - Invalid Tx Divider Value!"},
			{0x10U, "6 - Invalid Tx Divider Value!"},
			{0x7U, "7 - Divide Ratio 8"}
	};

	static const char invalid_divider_value_name[] = "Invalid Tx Divider Value!";

	if (lg_iot_initialised && ((tx_div >= IOT_TX_DIV_MIN_VAL) && (tx_div <= IOT_TX_DIV_MAX_VAL)))
	{
		if (tx_div_map[tx_div].pins != 0x10U)
		{
			/* Set pin state */
			lg_iot_gpo_data[IOT_TX_DIV_EXP] &= ~IOT_TX_DIV_PINS;
			lg_iot_gpo_data[IOT_TX_DIV_EXP] |= (tx_div_map[tx_div].pins <<  IOT_TX_DIV_LSHIFT) & IOT_TX_DIV_PINS;
		}

		*p_tx_div_name = tx_div_map[tx_div].name;

		return true;
	}
	else
	{
		*p_tx_div_name = invalid_divider_value_name;
		return false;
	}
}


/*****************************************************************************/
/**
* Sets the state of the specified GPO pin, the output will be set next time
* the task executes.
*
* @param    pin_id one of iot_GpoPinId_t enumerated pins
* @param   	pin_state enumerated pin state:
* 						@arg - set if pin is high
* 						@arg - reset if pin is low
* @param	p_pin_name receives pointer to constant string describing the
* 			GPO pin.
* @return	None
*
******************************************************************************/
bool iot_SetGpoPinState(iot_GpoPins_t pin_id, iot_GpioPinState_t pin_state, const char **p_pin_name)
{
	static const char invalid_pin_id_name[] = "Invalid Pin ID!";

	if (lg_iot_initialised && ((pin_id >= 0) && (pin_id < iot_gpo_qty)))
	{
		/* Set pin state */
		if (pin_state == iot_gpo_high)
		{
			lg_iot_gpo_data[lg_iot_gpo_pin_map[pin_id].expander] |= lg_iot_gpo_pin_map[pin_id].mask;
		}
		else
		{
			lg_iot_gpo_data[lg_iot_gpo_pin_map[pin_id].expander] &= ~lg_iot_gpo_pin_map[pin_id].mask;
		}

		*p_pin_name = lg_iot_gpo_pin_map[pin_id].name;

		return true;
	}
	else
	{
		*p_pin_name = invalid_pin_id_name;
		return false;
	}
}


/*****************************************************************************/
/**
* Set the test board RF path to the requested value.
*
* @param	path receiver path: IOT_TB_RF_PATH_MIN_VAL to IOT_TB_RF_PATH_MAX_VAL
* @param	p_path_name receives pointer to constant string describing the
* 			set test board RF path
* @return   true if setting test board RF path is successful, else false
*
******************************************************************************/
bool iot_SetTestBoardRfPath(uint16_t path, const char **p_path_name)
{
	typedef struct tb_rf_path
	{
		uint16_t val;
		char name[IOT_MAX_STR_LEN];
	} tb_rf_path_t;

	static const tb_rf_path_t tb_rf_path_map[IOT_TX_PATH_MAX_VAL + 1] = {
			{0x1U, "Digital Board Test Rx Mode"},
			{0x0U, "RF Board Test Rx Mode"},
			{0x6U, "RF Board Test Tx Mode"}
	};

	static const char invalid_path_name[] = "Invalid Test Board RF Path!";

	if (lg_iot_initialised && ((path >= IOT_TB_RF_PATH_MIN_VAL) && (path <= IOT_TB_RF_PATH_MAX_VAL)))
	{
		/* Set SW1 pin state */
		lg_iot_gpo_data[IOT_TB_RF_PATH_EXP] &= ~IOT_TB_RF_PATH_PINS;
		lg_iot_gpo_data[IOT_TB_RF_PATH_EXP] |= (tb_rf_path_map[path].val <<  IOT_TB_RF_PATH_LSHIFT) & IOT_TB_RF_PATH_PINS;

		*p_path_name = tb_rf_path_map[path].name;

		return true;
	}
	else
	{
		*p_path_name = invalid_path_name;
		return false;
	}
}


/*****************************************************************************/
/**
* Utility function to assert/de-assert the SPI synth chip-select signal.
* Matches ssd_AssertSynthCsFuncPtr_t type so it can be used with the SPI Synth
* driver.
*
* @param	assert true to assert active-low CS signal, false to de-assert
*
******************************************************************************/
void iot_AssertSynthCs(bool assert)
{
	HAL_GPIO_WritePin(lg_iot_init_data.spi_ncs_gpio_port,
			          lg_iot_init_data.spi_ncs_gpio_pin,
					  assert ? GPIO_PIN_RESET : GPIO_PIN_SET);
}


/*****************************************************************************/
/**
* Return the state of the synth lock detect signal
*
* @return true if synth lock detect asserted high, else false
*
******************************************************************************/
bool iot_GetSynthLockDetect(void)
{
	if (lg_iot_initialised)
	{
		return HAL_GPIO_ReadPin(lg_iot_init_data.synth_ld_gpio_port, lg_iot_init_data.synth_ld_gpio_pin) == GPIO_PIN_SET ? true : false;
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Set the Synth centre frequency to value specified in MHz
*
* @param	rf_out_freq_mhz required centre frequency in MHz, range

* @return   true if successful, else false
*
******************************************************************************/
bool iot_SetSynthFreqMhz(uint32_t rf_out_freq_mhz)
{
	if (lg_iot_initialised)
	{
		return ssd_SetCentreFreqMhz(&lg_iot_spi_synth, rf_out_freq_mhz);
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Set the synth power-down bit
*
* @param	power_down true to power down, false to power up

* @return   true if successful, else false
*
******************************************************************************/
bool iot_SetSynthPowerDown(bool power_down)
{
	if (lg_iot_initialised)
	{
		return ssd_SetSynthPowerDown(&lg_iot_spi_synth, power_down);
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Write 32-bit register value to the synth
*
* @param	reg_val register value
* @return   true if successful, else false
*
******************************************************************************/
bool iot_WriteSynthRegister(uint32_t reg_val)
{
	if (lg_iot_initialised)
	{
		return ssd_WriteSynthRegister(&lg_iot_spi_synth, reg_val);
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Initialise the synth
*
* @return   true if successful, else false
*
******************************************************************************/
bool iot_InitSynth(void)
{
	if (lg_iot_initialised)
	{
		return ssd_InitDevice(&lg_iot_spi_synth);
	}
	else
	{
		return false;
	}
}


/*****************************************************************************/
/**
* Reads hardware configuration information from the PCA9500 I2C device.
*
* @param	p_hw_config_info pointer to data structure to receive read info.
* @return   true if data read from device, else false
*
******************************************************************************/
bool iot_ReadHwConfigInfo(hci_HwConfigInfoData_t *p_hw_config_info)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_ReadHwConfigInfo(&lg_iot_hci, p_hw_config_info);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Clears all the hardware config information to blank, sets version
* parameter to 1 and creates CRC
*
* @return   true if data reset, else false
*
******************************************************************************/
bool iot_ResetHwConfigInfo(void)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_ResetHwConfigInfo(&lg_iot_hci);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly part number in PCA9500 EEPROM, see hw_config_info driver for
* more details.
*
* @param	assy_part_no pointer to null terminated string defining the assembly
* 			part number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
*
******************************************************************************/
bool iot_SetAssyPartNo(uint8_t *assy_part_no)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_SetAssyPartNo(&lg_iot_hci, assy_part_no);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly revision number in PCA9500 EEPROM, see hw_config_info driver for
* more details.
*
* @param	assy_rev_no pointer to null terminated string defining the assembly
* 			revision number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
*
******************************************************************************/
bool iot_SetAssyRevNo(uint8_t *assy_rev_no)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_SetAssyRevNo(&lg_iot_hci, assy_rev_no);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly serial number in PCA9500 EEPROM, see hw_config_info driver for
* more details.
*
* @param	assy_serial_no pointer to null terminated string defining the assembly
* 			serial number, max string length is HCI_STR_PARAM_LEN including null
* 			terminator
* @return   true if data written to device, else false
*
******************************************************************************/
bool iot_SetAssySerialNo(uint8_t *assy_serial_no)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_SetAssySerialNo(&lg_iot_hci, assy_serial_no);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets assembly build batch number in PCA9500 EEPROM, see hw_config_info driver
* for more details.
*
* @param	assy_build_date_batch_no pointer to null terminated string defining
* 			the assembly build date/batch number, max string length is
* 			HCI_STR_PARAM_LEN including null terminator
* @return   true if data written to device, else false
*
******************************************************************************/
bool iot_SetAssyBuildDataBatchNo(uint8_t *assy_build_date_batch_no)
{
	bool ret_val = false;

	if (lg_iot_initialised&& (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_SetAssyBuildDataBatchNo(&lg_iot_hci, assy_build_date_batch_no);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}

/*****************************************************************************/
/**
* Set the I2C Loop Back Enable pin.
*
* To prevent the I2C pull-ups back powering the Digital Board the I2C loop back
* should be enabled (default state) to isolate the I2C bus when the Digital
* Board is NOT powered up.  The loop back can be disabled once the Digital
* Board has been powered up.
*
* @param val true to set high, false to set low
* @return true if signal set, else false
*
******************************************************************************/
bool iot_SetI2cLoobackEnable(bool val)
{
	if (lg_iot_initialised)
	{
		HAL_GPIO_WritePin(lg_iot_init_data.i2c_lb_en_gpio_port, lg_iot_init_data.i2c_lb_en_gpio_pin, val ? GPIO_PIN_SET : GPIO_PIN_RESET);
		return true;
	}
	else
	{
		return false;
	}
}



/*****************************************************************************/
/**
* Write a byte to the EEPROM device, this function is blocking and will return
* once the I2C bus transaction is complete.
*
* @param    p_inst pointer to I2C EEPROM driver instance data
* @param	address memory address to write to
* @param 	data value to write to the I2C EEPROM
*
******************************************************************************/
bool iot_I2cEepromWriteByte(uint16_t address, uint8_t data)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = iee_WriteByte(&lg_i2c_eeprom, address, data);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read a byte from the EEPROM device, this function is blocking and will return
* once the I2C bus transaction is complete.
*
* @param	address memory address to read from
* @param 	p_data variable to receive value read from the I2C EEPROM
*
******************************************************************************/
bool iot_I2cEepromReadByte(uint16_t address, uint8_t *p_data)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = iee_ReadByte(&lg_i2c_eeprom, address, p_data);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read a page of data from the EEPROM device, this function is blocking and
* will return once the I2C bus transaction is complete.
*
* @param	page_address start memory address of page to read
* @param 	p_data buffer to receive page data read from the I2C EEPROM, must be
* 			the greater than or equal to the size of a page.
*
******************************************************************************/
bool iot_I2cEepromReadPage(uint16_t page_address, uint8_t *p_data)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = iee_ReadPage(&lg_i2c_eeprom, page_address, p_data);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}
