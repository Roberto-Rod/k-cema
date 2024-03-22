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
#include "ltc2991.h"
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/

/* I2C devices bus addresses */
#define IOT_LTC2991_NON_ISO_I2C_BUS_ADDR	0x48U << 1
#define IOT_LTC2991_ISO_I2C_BUS_ADDR		0x49U << 1
#define IOT_MCP23017_I2C_BUS_ADDR			0x20U << 1

/* MCP23017 GPIO expander definitions */
#define IOT_MCP23017_DIR_MASK				0x0C00U
#define IOT_MCP23017_DEFAULT_OP_MASK		0x0000U

/* 1PPS accuracy limits */
#define IOT_1PPS_DELTA_MIN					999U
#define IOT_1PPS_DELTA_MAX					1001U

/* Analogue reading definitions */
#define IOT_ANALOGUE_ENABLED				1

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef struct iot_GpoPins
{
	uint16_t csm_slave_1pps_dir : 1;
	uint16_t select_1pps_s0 : 1;
	uint16_t select_1pps_s1 : 1;
	uint16_t csm_master_cable_det : 1;
	uint16_t tamper_sw : 1;
	uint16_t som_sd_boot_en : 1;
	uint16_t rcu_pwr_btn : 1;
	uint16_t rcu_pwr_en_zer : 1;
	uint16_t keypad_pwr_btn : 1;
	uint16_t keypad_pwr_en_zer : 1;
	uint16_t spare_10 : 1;
	uint16_t spare_11 : 1;
	uint16_t select_uart_s0 : 1;
	uint16_t rcu_1pps_dir : 1;
	uint16_t remote_pwr_on_in : 1;
	uint16_t spare_15 : 1;
} iot_GpoPins_t;

typedef union iot_GpoPinMap
{
	uint16_t reg;
	iot_GpoPins_t pins;
} iot_GpoPinMap_t;

typedef struct iot_GpiPins
{
	uint16_t spare_0 : 1;
	uint16_t spare_1 : 1;
	uint16_t spare_2 : 1;
	uint16_t spare_3 : 1;
	uint16_t spare_4 : 1;
	uint16_t spare_5 : 1;
	uint16_t spare_6 : 1;
	uint16_t spare_7 : 1;
	uint16_t spare_8 : 1;
	uint16_t spare_9 : 1;
	uint16_t csm_master_rack_addr : 1;
	uint16_t csm_slave_rack_addr : 1;
	uint16_t spare_12 : 1;
	uint16_t spare_13 : 11;
	uint16_t spare_14 : 1;
	uint16_t spare_15 : 1;
} iot_GpiPins_t;

typedef union iot_GpiPinMap
{
	uint16_t reg;
	iot_GpiPins_t pins;
} iot_GpiPinMap_t;


typedef enum iot_AdcDevices
{
	iso_adc = 0,
	non_iso_adc
} iot_AdcDevices_t;

typedef struct iot_AnalogueReading
{
	iot_AdcDevices_t	adc_device;
	int16_t				adc_ch_no;
	char				adc_ch_name[IOT_ANALOGUE_READING_NAME_MAX_LEN];
} iot_AnalogueReading_t;


/*****************************************************************************
*
*  Local Functions
*
*****************************************************************************/


/*****************************************************************************
*
*  Local Variables
*
*****************************************************************************/
static iot_Init_t lg_iot_init_data = {0};
static bool lg_iot_initialised = false;

static mcp23017_Driver_t lg_iot_gpio_driver = {0};
static iot_GpoPinMap_t lg_iot_gpo_pin_state = {0};
static iot_GpiPinMap_t lg_iot_gpi_pin_state = {0};

const char *lg_iot_gpi_pin_names[csm_slave_rack_addr + 1] = \
{
	"CSM Master Rack Address",
	"CSM Slave Rack Address"
};

static uint32_t lg_iot_1pps_delta = 0U;
static uint32_t lg_iot_1pps_previous = 0U;

static ltc2991_Driver_t lg_iot_adc_iso_driver = {0};
static ltc2991_Data_t lg_iot_adc_iso_data = {0};
static ltc2991_Driver_t lg_iot_adc_non_iso_driver = {0};
static ltc2991_Data_t lg_iot_adc_non_iso_data = {0};
static iot_AnalogueReading_t lg_analogue_reading_adc_map[IOT_ANALOGUE_READINGS_NUM] =
{	/* adc_device, adc_ch_no, adc_ch_name */
	{non_iso_adc, 0, "(mv) Power Off CS Master"},
	{non_iso_adc, 1, "(mv) Power Off CS Slave"},
	{non_iso_adc, 2, "(mv) RF Mute CSM Master"},
	{non_iso_adc, 3, "(mv) RF Mute CSM Slave"},
	{non_iso_adc, 4, "(mv) Buzzer +12V Supply"},
	{non_iso_adc, 5, "(mA) Test Jig Current"},
	{non_iso_adc, 6, "(mv) Rem Pwr On Out CSM Slave"},
	{iso_adc, 0, "(mv) RCU +12V Out"},
	{iso_adc, 1, "(mv) PoE Supply Out"},
	{iso_adc, 2, "(mv) RCU Eth Gnd"},
	{iso_adc, 3, "(mv) Prog Eth Gnd"},
	{iso_adc, 4, "(mv) CSM Master Eth Gnd"},
	{iso_adc, 5, "(mv) CSM Slave Eth Gnd"}
};

static bool lg_iot_uart_string_found = false;

const char *IOT_UART_EXPECTED_STRING = "The quick brown fox jumped over the lazy fox!";

/*****************************************************************************/
/**
* Initialise the IO task.
*
* @param    init_data initialisation data for the task
* @return   None
*
******************************************************************************/
void iot_InitTask(iot_Init_t init_data)
{
	/* Assume initialisation success */
	lg_iot_initialised = true;

	memcpy((void *)&lg_iot_init_data, (void *)&init_data, sizeof(iot_Init_t));

	/* Initialise the MCP23017 GPIO expander */
	lg_iot_gpio_driver.i2c_device 			= lg_iot_init_data.i2c_device;
	lg_iot_gpio_driver.i2c_address 			= IOT_MCP23017_I2C_BUS_ADDR;
	lg_iot_gpio_driver.io_dir_mask 			= IOT_MCP23017_DIR_MASK;
	lg_iot_gpio_driver.default_op_mask 		= IOT_MCP23017_DEFAULT_OP_MASK;
	lg_iot_gpio_driver.i2c_reset_gpio_port	= lg_iot_init_data.i2c_reset_gpio_port;
	lg_iot_gpio_driver.i2c_reset_gpio_pin 	= lg_iot_init_data.i2c_reset_gpio_pin;

	lg_iot_initialised &= mcp23017_Init(&lg_iot_gpio_driver);
	lg_iot_gpo_pin_state.reg = IOT_MCP23017_DEFAULT_OP_MASK;
#if IOT_ANALOGUE_ENABLED

	lg_iot_adc_non_iso_driver.scaling_factors[0] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_non_iso_driver.scaling_factors[1] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_non_iso_driver.scaling_factors[2] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_non_iso_driver.scaling_factors[3] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_non_iso_driver.scaling_factors[4] = 2.0F;	/* Buzzer +12V channel */
	lg_iot_adc_non_iso_driver.scaling_factors[5] = LTC2991_SE_V_SCALE_FACTOR * 2.273F;	/* Test Jig Current channel */
	lg_iot_adc_non_iso_driver.scaling_factors[6] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_non_iso_driver.scaling_factors[7] = LTC2991_SE_V_SCALE_FACTOR;

	lg_iot_adc_iso_driver.scaling_factors[0] = 2.0F;	/* RCU +12V channel */
	lg_iot_adc_iso_driver.scaling_factors[1] = 8.0F;	/* PoE +Ve Out channel */
	lg_iot_adc_iso_driver.scaling_factors[2] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_iso_driver.scaling_factors[3] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_iso_driver.scaling_factors[4] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_iso_driver.scaling_factors[5] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_iso_driver.scaling_factors[6] = LTC2991_SE_V_SCALE_FACTOR;
	lg_iot_adc_iso_driver.scaling_factors[7] = LTC2991_SE_V_SCALE_FACTOR;

	lg_iot_initialised &= ltc2991_InitInstance(	&lg_iot_adc_non_iso_driver,
												lg_iot_init_data.i2c_device,
												IOT_LTC2991_NON_ISO_I2C_BUS_ADDR);
#if 0
	lg_iot_initialised &= ltc2991_InitInstance(	&lg_iot_adc_iso_driver,
												lg_iot_init_data.i2c_device,
												IOT_LTC2991_ISO_I2C_BUS_ADDR);
#endif
#else
	for (uint16_t i = 0U; i < 6U; ++i)
	{
		lg_iot_adc_iso_data.adc_ch_mv[i] = i * 100U;
		lg_iot_adc_non_iso_data.adc_ch_mv[i] = (i + 1) * 225U;
	}
#endif
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
	TickType_t last_wake_time;
	const TickType_t task_period_ms = 75;

	if (!lg_iot_initialised)
	{
		for(;;);
	}

	for(;;)
	{
		vTaskDelayUntil(&last_wake_time, task_period_ms);

		(void)mcp23017_ReadPinsVal(&lg_iot_gpio_driver, &lg_iot_gpi_pin_state.reg);
		(void)mcp23017_WritePin(&lg_iot_gpio_driver, lg_iot_gpo_pin_state.reg, mcp23017_PinSet);
		(void)mcp23017_WritePin(&lg_iot_gpio_driver, ~lg_iot_gpo_pin_state.reg, mcp23017_PinReset);
#if IOT_ANALOGUE_ENABLED
		if (!ltc2991_ReadAdcData(&lg_iot_adc_non_iso_driver, &lg_iot_adc_non_iso_data))
		{
			memset(&lg_iot_adc_non_iso_data, 0U, sizeof(ltc2991_Data_t));
		}

		if (ltc2991_InitInstance(	&lg_iot_adc_iso_driver,
									lg_iot_init_data.i2c_device,
									IOT_LTC2991_ISO_I2C_BUS_ADDR))
		{
			if (!ltc2991_ReadAdcData(&lg_iot_adc_iso_driver, &lg_iot_adc_iso_data))
			{
				memset(&lg_iot_adc_iso_data, 0U, sizeof(ltc2991_Data_t));
			}
		}
		else
		{
			memset(&lg_iot_adc_iso_data, 0U, sizeof(ltc2991_Data_t));
		}
#endif
	}
}


/*****************************************************************************/
/**
* Returns the last read state of the specified GPI pin.
*
* @param    pin_id one of iot_GpiPinId_t enumerated pins
* @return   iot_GpioPinState_t enumerated pin state:
* 				@arg - set if pin is high
* 				@arg - reset if pin is low
*
******************************************************************************/
iot_GpioPinState_t iot_GetGpiPinState(iot_GpiPinId_t pin_id, const char **p_chanel_name)
{
	uint16_t pin_state;

	switch(pin_id)
	{
	case csm_master_rack_addr:
		pin_state = lg_iot_gpi_pin_state.pins.csm_master_rack_addr;
		break;

	case csm_slave_rack_addr:
		pin_state = lg_iot_gpi_pin_state.pins.csm_slave_rack_addr;
		break;

	default:
		pin_state = 0U;
		break;
	}

	*p_chanel_name = lg_iot_gpi_pin_names[pin_id];

	return pin_state ? set : reset;
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
* @return	None
*
******************************************************************************/
void iot_SetGpoPinState(iot_GpoPinId_t pin_id, iot_GpioPinState_t pin_state)
{
	uint16_t pin_val = pin_state == set ? 1U : 0U;

	switch(pin_id)
	{
	case csm_slave_1pps_dir:
		lg_iot_gpo_pin_state.pins.csm_slave_1pps_dir = pin_val;
		break;

	case select_1pps_s0:
		lg_iot_gpo_pin_state.pins.select_1pps_s0 = pin_val;
		break;

	case select_1pps_s1:
		lg_iot_gpo_pin_state.pins.select_1pps_s1 = pin_val;
		break;

	case csm_master_cable_det:
		lg_iot_gpo_pin_state.pins.csm_master_cable_det = pin_val;
		break;

	case tamper_sw:
		lg_iot_gpo_pin_state.pins.tamper_sw = pin_val;
		break;

	case som_sd_boot_en:
		lg_iot_gpo_pin_state.pins.som_sd_boot_en = pin_val;
		break;

	case rcu_pwr_btn:
		lg_iot_gpo_pin_state.pins.rcu_pwr_btn = pin_val;
		break;

	case rcu_pwr_en_zer:
		lg_iot_gpo_pin_state.pins.rcu_pwr_en_zer = pin_val;
		break;

	case keypad_pwr_btn:
		lg_iot_gpo_pin_state.pins.keypad_pwr_btn = pin_val;
		break;

	case keypad_pwr_en_zer:
		lg_iot_gpo_pin_state.pins.keypad_pwr_en_zer = pin_val;
		break;

	case select_uart_s0:
		lg_iot_gpo_pin_state.pins.select_uart_s0 = pin_val;
		break;

	case rcu_1pps_dir:
		lg_iot_gpo_pin_state.pins.rcu_1pps_dir = pin_val;
		break;

	case remote_pwr_on_in:
		lg_iot_gpo_pin_state.pins.remote_pwr_on_in = pin_val;
		break;

	default:
		break;
	}
}


/*****************************************************************************/
/**
* Enable/disable the 1PPS output by starting or stopping the timer in irq
* driver in PWM mode.
*
* @param    enable true to enable 1PPS output, false to disable 1PPS output
* @return   None
*
******************************************************************************/
void iot_GetAnalogueReading(int16_t analogue_reading_no,
							uint16_t *p_analgoue_reading,
							const char **p_analogue_reading_name)
{
	int16_t ar = analogue_reading_no >= IOT_ANALOGUE_READINGS_NUM ?
										IOT_ANALOGUE_READINGS_NUM - 1 :
										(analogue_reading_no < 0 ? 0 : analogue_reading_no);

	if  (lg_analogue_reading_adc_map[ar].adc_device == iso_adc)
	{
		*p_analgoue_reading = lg_iot_adc_iso_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
	}
	else
	{
		*p_analgoue_reading = lg_iot_adc_non_iso_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
	}

	*p_analogue_reading_name = lg_analogue_reading_adc_map[ar].adc_ch_name;
}


/*****************************************************************************/
/**
* Enable/disable the 1PPS output by starting or stopping the timer in irq
* driver in PWM mode.
*
* @param    enable true to enable 1PPS output, false to disable 1PPS output
* @return   None
*
******************************************************************************/
void iot_Enable1PpsOp(bool enable)
{
	if (lg_iot_initialised)
	{
		if (enable)
		{
			HAL_TIMEx_PWMN_Start_IT(lg_iot_init_data.csm_1pps_out_htim,
									lg_iot_init_data.csm_1pps_out_channel);
		}
		else
		{
			HAL_TIMEx_PWMN_Stop_IT(lg_iot_init_data.csm_1pps_out_htim,
									lg_iot_init_data.csm_1pps_out_channel);
		}
	}
}


/*****************************************************************************/
/**
* Use the 1PPS GPI input IRQ generated time stamps to determine if a 1PPS
* signal is being received.
*
* @param    p_pps_delta receives the delta between 1PPS pulses in ms if a 1PPS
* 			is detected, else receives 0xFFFFFFFFU
* @return   true if 1PPS is detected, else false
*
******************************************************************************/
bool iot_PpsDetected(uint32_t *p_pps_delta)
{
	/* Disable the EXTI interrupt to ensure the next two lines are atomic */
	HAL_NVIC_DisableIRQ(lg_iot_init_data.csm_1pps_in_gpio_irq);
	uint32_t pps_delta = lg_iot_1pps_delta;
	uint32_t pps_previous = lg_iot_1pps_previous;
	HAL_NVIC_EnableIRQ(lg_iot_init_data.csm_1pps_in_gpio_irq);

	uint32_t now = osKernelSysTick();

	if (((now - pps_previous) > IOT_1PPS_DELTA_MAX) ||
		(pps_delta > IOT_1PPS_DELTA_MAX) ||
		(pps_delta < IOT_1PPS_DELTA_MIN))
	{
		*p_pps_delta = (uint32_t)-1;
		return false;
	}
	else
	{
		*p_pps_delta = pps_delta;
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
*
******************************************************************************/
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
	volatile uint32_t now = osKernelSysTick();

	if (lg_iot_initialised)
	{
		if (GPIO_Pin == lg_iot_init_data.csm_1pps_in_gpio_pin)
		{
			lg_iot_1pps_delta = now - lg_iot_1pps_previous;
			lg_iot_1pps_previous = now;
		}
	}
}


/*****************************************************************************/
/**
* UART detect task function.
*
* @param    argument defined by FreeRTOS function prototype, not used
* @return   None
*
******************************************************************************/
void iot_UartDetectTask(void const *argument)
{
	extern const char *IOT_UART_EXPECTED_STRING;
	static int32_t rx_idx = 0;
	osMessageQId rx_data_queue = (osMessageQId)argument;
	osEvent event;

	for(;;)
	{
		event = osMessageGet(rx_data_queue, portMAX_DELAY);

		if (event.status == osEventMessage)
		{	/* Check if this is the character we're looking for */
			if ((uint8_t)event.value.v == IOT_UART_EXPECTED_STRING[rx_idx])
			{
				if ((char)event.value.v == '!')
				{	/* Found the string so stop searching */
					lg_iot_uart_string_found = true;
				}
				else if (!lg_iot_uart_string_found)
				{	/* Look for the next character in the string */
					rx_idx++;
				}
				else
				{
				}
			}
			else
			{
				rx_idx = 0;
			}
		}
	}

}


/*****************************************************************************/
/**
* If the expected string has been previously found call this function to
* restart the search process.
*
* @param    None
* @return   None
*
******************************************************************************/
void iot_UartStartStringSearch(void)
{
	lg_iot_uart_string_found = false;
}


/*****************************************************************************/
/**
* Query if the expected string has been found.
*
* @param    None
* @return   true if the string has been found, else false.
*
******************************************************************************/
bool iot_UartIsStringFound(void)
{
	return lg_iot_uart_string_found;
}
