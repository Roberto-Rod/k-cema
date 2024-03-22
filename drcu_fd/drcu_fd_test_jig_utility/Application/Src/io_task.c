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
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/

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


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/
static void iot_StartAdcConversion(void);

/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static iot_Init_t lg_iot_init_data = {0};
static bool lg_iot_initialised = false;

static iot_AdcChannel_t lg_iot_adc_channels[iot_adc_ch_qty] = {
		{iot_adc_buzzer_12v, 		11, IOT_ADC_ADC_BITS, 0, 0, "Buzzer +12V (mV)"},
		{iot_adc_aux_supply_12v, 	11, IOT_ADC_ADC_BITS, 0, 0, "Aux Supply +12V (mV)"},
		{iot_adc_xchange_12v, 		11, IOT_ADC_ADC_BITS, 0, 0, "Xchange +12V (mV)"},
		{iot_adc_fd_eth_gnd, 		2,  IOT_ADC_ADC_BITS, 0, 0, "FD Ethernet Gnd Test (mV)"},
		{iot_adc_csm_eth_gnd, 		1,  IOT_ADC_ADC_BITS, 0, 0, "DRCU_Eth Gnd Test (mV)"},
		{iot_adc_vref_int, 	    	1,  IOT_ADC_ADC_BITS, 0, 0, "Vref Voltage (mV)"}		/* Vref internal should always be the last channel */
};

static uint16_t lg_iot_adc_buf[iot_adc_ch_qty] = {0};

volatile uint32_t lg_iot_1pps_delta = 0U;
volatile uint32_t lg_iot_1pps_previous = 0U;

iot_GpioPinState_t lg_iot_gpi_pin_states[iot_gpi_qty] = {iot_gpio_reset};
iot_GpioPinState_t lg_iot_gpo_pin_states[iot_gpo_qty] = {iot_gpio_reset, iot_gpio_set, iot_gpio_reset};	/* SOM_SYS_RST asserted */


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

	lg_iot_initialised = true;
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
	const TickType_t task_period_ms = 10;

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
		osDelayUntil(&last_wake_time, task_period_ms);

		/* Read the GPI signals */
		for (iot_GpiPinId_t i = 0; i < iot_gpi_qty; ++i)
		{
			lg_iot_gpi_pin_states[i] = HAL_GPIO_ReadPin(lg_iot_init_data.gpi_signals[i].port,
														lg_iot_init_data.gpi_signals[i].pin) == GPIO_PIN_SET ? iot_gpio_set : iot_gpio_reset;
		}

		/* Set the GPO signals */
		for (iot_GpoPinId_t i = 0; i < iot_gpo_qty; ++i)
		{
			HAL_GPIO_WritePin(lg_iot_init_data.gpo_signals[i].port,
							  lg_iot_init_data.gpo_signals[i].pin,
							  lg_iot_gpo_pin_states[i] == iot_gpio_set ? GPIO_PIN_SET : GPIO_PIN_RESET);
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
* Returns the last read state of the specified GPI pin.
*
* @param    pin_id one of iot_GpiPinId_t enumerated pins
* @param	p_gpi_name receives string associated with the GPI signal, NULL if
* 			the pin_id is invalid.
* @return   iot_GpioPinState_t enumerated pin state:
* 				@arg - iot_gpio_set if pin is high
* 				@arg - iot_gpio_reset if pin is low
*
******************************************************************************/
iot_GpioPinState_t iot_GetGpiPinState(iot_GpiPinId_t pin_id, const char **p_gpi_name)
{
	if ((pin_id >= 0) && (pin_id < iot_gpi_qty) && lg_iot_initialised)
	{
		*p_gpi_name = lg_iot_init_data.gpi_signals[pin_id].name;
		return lg_iot_gpi_pin_states[pin_id];
	}
	else
	{
		*p_gpi_name = NULL;
		return iot_gpio_reset;
	}
}


/*****************************************************************************/
/**
* Sets the state of the specified GPO pin, the output will be set next time
* the task executes.
*
* @param    pin_id one of iot_GpoPinId_t enumerated pins
* @param   	pin_state enumerated pin state:
* 						@arg - iot_gpio_set if pin is high
* 						@arg - iot_gpio_reset if pin is low
* @param	p_gpo_name receives string associated with the GPO signal, NULL if
* 			the pin_id is invalid.
*
******************************************************************************/
void iot_SetGpoPinState(iot_GpoPinId_t pin_id, iot_GpioPinState_t pin_state, const char **p_gpo_name)
{
	if ((pin_id >= 0) && (pin_id < iot_gpo_qty) && lg_iot_initialised)
	{
		lg_iot_gpo_pin_states[pin_id] = pin_state;
		*p_gpo_name = lg_iot_init_data.gpo_signals[pin_id].name;
	}
	else
	{
		*p_gpo_name = NULL;
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

	    if (READ_BIT(adc_device->ISR, IOT_DMA_IFCR_TE_FLAG(adc_dma_channel)) == IOT_DMA_IFCR_TE_FLAG(adc_dma_channel))
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
			/* Ensure that the half-duplex EIA-485 driver is in transmit mode. */
			HAL_GPIO_WritePin(lg_iot_init_data.pps_dir_gpio_port, lg_iot_init_data.pps_dir_gpio_pin, GPIO_PIN_SET);
			HAL_TIMEx_PWMN_Start_IT(lg_iot_init_data.pps_out_htim, lg_iot_init_data.pps_out_channel);
			__HAL_TIM_ENABLE_IT(lg_iot_init_data.pps_out_htim, TIM_IT_UPDATE);
		}
		else
		{
			__HAL_TIM_DISABLE_IT(lg_iot_init_data.pps_out_htim, TIM_IT_UPDATE);
			HAL_TIMEx_PWMN_Stop_IT(lg_iot_init_data.pps_out_htim,  lg_iot_init_data.pps_out_channel);
		}
	}
}


/*****************************************************************************/
/**
* Use the 1PPS GPI input IRQ generated time stamps to determine if a 1PPS
* signal is being received on the Xchange interface.
*
* @param    p_1pps_delta receives the delta between 1PPS pulses in ms if a 1PPS
* 			is detected, else receives 0xFFFFFFFFU
* @return   true if 1PPS detected, else false
*
******************************************************************************/
bool iot_1ppsDetected(uint32_t *p_1pps_delta)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(lg_iot_init_data.xchange_1pps_gpio_irq);
	uint32_t pps_delta = lg_iot_1pps_delta;
	uint32_t pps_previous = lg_iot_1pps_previous;
	HAL_NVIC_EnableIRQ(lg_iot_init_data.xchange_1pps_gpio_irq);
	uint32_t now = osKernelSysTick();

	if (((now - pps_previous) > IOT_1PPS_DELTA_MAX) ||
		(pps_delta > IOT_1PPS_DELTA_MAX) ||
		(pps_delta < IOT_1PPS_DELTA_MIN))
	{
		*p_1pps_delta = (uint32_t)-1;
		return false;
	}
	else
	{
		*p_1pps_delta = pps_delta;
		return true;
	}
}


/*****************************************************************************/
/**
* Handle HAL EXTI GPIO Callback as these are used to monitor presence of 1PPS
* input signal
*
* @param    argument    Not used
* @return   None
* @note     None
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	volatile uint32_t now = osKernelSysTick();

	if (lg_iot_initialised)
	{
		if (GPIO_Pin == lg_iot_init_data.xchange_1pps_gpio_pin)
		{
			lg_iot_1pps_delta = now - lg_iot_1pps_previous;
			lg_iot_1pps_previous = now;
		}
	}
}
