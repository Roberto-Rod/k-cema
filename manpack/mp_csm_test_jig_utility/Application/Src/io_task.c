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
#include "fan_controller.h"
#include <string.h>

/*****************************************************************************
*
*  Local Definitions
*
*****************************************************************************/

/* I2C devices bus addresses */
#define IOT_LTC2991_NON_ISO1_I2C_BUS_ADDR	(0x48U << 1)
#define IOT_LTC2991_NON_ISO2_I2C_BUS_ADDR   (0x49U << 1)
#define IOT_LTC2991_NON_ISO3_I2C_BUS_ADDR   (0x4AU << 1)
#define IOT_MCP23017_1_I2C_BUS_ADDR			(0x20U << 1)
#define IOT_MCP23017_2_I2C_BUS_ADDR         (0x21U << 1)
#define IOT_EMC2104_I2C_ADDR    			(0x2FU << 1)

/* MCP23017 GPIO expander definitions */
#define IOT_MCP23017_1_DIR_MASK				0x1FDCU		/* '0' = op; '1' = ip */
#define IOT_MCP23017_2_DIR_MASK             0x0440U
#define IOT_MCP23017_1_DEFAULT_OP_MASK		0x0000U
#define IOT_MCP23017_2_DEFAULT_OP_MASK      0x0000U

/* 1PPS accuracy limits */
#define IOT_1PPS_DELTA_MIN					999U
#define IOT_1PPS_DELTA_MAX					1001U

/* Analogue reading definitions */
#define IOT_ANALOGUE_ENABLED				1

/* Hardware ID I2C bus addresses */
#define IOT_PCA9500_GPIO_I2C_ADDR			(0x27U << 1)
#define IOT_PCA9500_EEPROM_I2C_ADDR 		(0x57U << 1)

/*****************************************************************************
*
*  Local Datatypes
*
*****************************************************************************/
typedef struct iot_Gpo1Pins
{
	uint16_t tamper_sw_buzzer : 1;
	uint16_t rcu_pwr_btn : 1;
	uint16_t spare_2 : 1;
	uint16_t spare_3 : 1;
	uint16_t spare_4 : 1;
	uint16_t som_sd_boot_en : 1;
	uint16_t spare_6 : 1;
	uint16_t spare_7 : 1;
	uint16_t spare_8 : 1;
	uint16_t spare_9 : 1;
	uint16_t spare_10 : 1;
	uint16_t spare_11 : 1;
	uint16_t spare_12 : 1;
	uint16_t rcu_pwr_en_zer : 1;
	uint16_t select_i2c_s0 : 1;
	uint16_t select_i2c_s1 : 1;
} iot_Gpo1Pins_t;

typedef struct iot_Gpo2Pins
{
    uint16_t ms_1pps_dir_ctrl : 1;
    uint16_t select_1pps_s0 : 1;
    uint16_t select_1pps_s1 : 1;
    uint16_t select_1pps_s2 : 1;
    uint16_t select_1pps_s3 : 1;
    uint16_t ms_pwr_en : 1;
    uint16_t spare_6 : 1;
    uint16_t ms_master_n : 1;
    uint16_t test_point_1 : 1;
    uint16_t test_point_2 : 1;
    uint16_t spare_10 : 1;
    uint16_t ms_rf_mute_n : 1;
    uint16_t ms_rf_mute_dir : 1;
    uint16_t select_fan_pwm_s0 : 1;
    uint16_t select_fan_pwm_s1 : 1;
    uint16_t select_fan_pwm_s2 : 1;
} iot_Gpo2Pins_t;

typedef union iot_Gpo1PinMap
{
	uint16_t reg;
	iot_Gpo2Pins_t pins;
} iot_Gpo2PinMap_t;

typedef union iot_Gpo2PinMap
{
    uint16_t reg;
    iot_Gpo1Pins_t pins;
} iot_Gpo1PinMap_t;

typedef struct iot_Gpi1Pins
{
	uint16_t spare_0 : 1;
	uint16_t spare_1 : 1;
	uint16_t ntm1_rf_mute_n : 1;
	uint16_t ntm2_rf_mute_n : 1;
	uint16_t ntm3_rf_mute_n : 1;
	uint16_t spare_5 : 1;
	uint16_t ntm1_pfi_n : 1;
	uint16_t ntm2_pfi_n : 1;
	uint16_t ntm3_pfi_n : 1;
	uint16_t ntm1_fan_alert : 1;
	uint16_t ntm2_fan_alert : 1;
	uint16_t ntm3_fan_alert : 1;
	uint16_t rcu_pwr_en_zer_in : 1;
	uint16_t spare_13 : 11;
	uint16_t spare_14 : 1;
	uint16_t spare_15 : 1;
} iot_Gpi1Pins_t;

typedef struct iot_Gpi2Pins
{
    uint16_t spare_0 : 1;
    uint16_t spare_1 : 1;
    uint16_t spare_2 : 1;
    uint16_t spare_3 : 1;
    uint16_t spare_4 : 1;
    uint16_t spare_5 : 1;
    uint16_t ms_pwr_en_out : 1;
    uint16_t spare_7 : 1;
    uint16_t spare_8 : 1;
    uint16_t spare_9 : 1;
    uint16_t ms_rf_mute_n_in : 1;
    uint16_t spare_11 : 1;
    uint16_t spare_12 : 1;
    uint16_t spare_13 : 11;
    uint16_t spare_14 : 1;
    uint16_t spare_15 : 1;
} iot_Gpi2Pins_t;

typedef union iot_Gpi1PinMap
{
	uint16_t reg;
	iot_Gpi1Pins_t pins;
} iot_Gpi1PinMap_t;

typedef union iot_Gpi2PinMap
{
    uint16_t reg;
    iot_Gpi2Pins_t pins;
} iot_Gpi2PinMap_t;


typedef enum iot_AdcDevices
{
    non_iso1_adc = 0,
	non_iso2_adc,
	non_iso3_adc,
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
const TickType_t lg_iot_task_period_ms = 75;

static mcp23017_Driver_t lg_iot_gpio1_driver = {0};
static mcp23017_Driver_t lg_iot_gpio2_driver = {0};
static iot_Gpo1PinMap_t lg_iot_gpo1_pin_state = {0};
static iot_Gpo2PinMap_t lg_iot_gpo2_pin_state = {0};
static iot_Gpi1PinMap_t lg_iot_gpi1_pin_state = {0};
static iot_Gpi2PinMap_t lg_iot_gpi2_pin_state = {0};

const char *lg_iot_gpi_pin_names[ntm3_pfi_n + 1] = \
{
	"NTM 1 Fan Alert",
	"NTM 2 Fan Alert",
	"NTM 3 Fan Alert",
	"NTM 1 RF Mute",
	"NTM 2 RF Mute",
	"NTM 3 RF Mute",
	"RCU Zeroise Power Enable",
	"Control Port Power Enable",
	"Control Port RF Mute",
	"NTM 1 PFI (active-low)",
	"NTM 2 PFI (active-low)",
	"NTM 3 PFI (active-low)"
};

static uint32_t lg_iot_1pps_delta = 0U;
static uint32_t lg_iot_1pps_previous = 0U;

static ltc2991_Driver_t lg_iot_adc_non_iso1_driver = {0};
static ltc2991_Driver_t lg_iot_adc_non_iso2_driver = {0};
static ltc2991_Driver_t lg_iot_adc_non_iso3_driver = {0};
static ltc2991_Data_t lg_iot_adc_non_iso1_data = {0};
static ltc2991_Data_t lg_iot_adc_non_iso2_data = {0};
static ltc2991_Data_t lg_iot_adc_non_iso3_data = {0};
static iot_AnalogueReading_t lg_analogue_reading_adc_map[IOT_ANALOGUE_READINGS_NUM] =
{	/* adc_device, adc_ch_no, adc_ch_name */
	{non_iso1_adc, 0, "(mv) NTM 1 DC Out"},
	{non_iso1_adc, 1, "(mv) NTM 2 DC Out"},
	{non_iso1_adc, 2, "(mv) NTM 3 DC Out"},
	{non_iso1_adc, 3, "(mv) NTM 1 +3V4 STBY"},
	{non_iso1_adc, 4, "(mv) NTM 2 +3V4 STBY"},
	{non_iso1_adc, 5, "(mv) NTM 3 +3V4 STBY"},
	{non_iso1_adc, 6, "(mv) NTM 1 +3V3 Out"},
	{non_iso1_adc, 7, "(mv) NTM 2 +3V3 Out"},
	{non_iso2_adc, 0, "(mv) NTM 3 +3V3 Out"},
	{non_iso2_adc, 1, "(mv) RCU +12V Out"},
	{non_iso2_adc, 2, "(mv) VSUP STBY"},
	{non_iso2_adc, 3, "(mv) Buzzer +12V Supply"},
	{non_iso2_adc, 4, "(mv) Prog. Eth Gnd"},
	{non_iso2_adc, 5, "(mv) RCU Eth Gnd"},
	{non_iso3_adc, 0, "(mv) IPAM 1 DC Out"},
    {non_iso3_adc, 1, "(mv) IPAM 2 DC Out"},
    {non_iso3_adc, 2, "(mv) IPAM 3 DC Out"},
    {non_iso3_adc, 3, "(mv) Fan 1.1 +12V"},
    {non_iso3_adc, 4, "(mv) Fan 2.1 +12V"},
    {non_iso3_adc, 5, "(mv) Fan 2.2 +12V"},
    {non_iso3_adc, 6, "(mv) Fan 3.1 +12V"},
};

static hci_HwConfigInfo_t lg_iot_hci = {0};
static fc_FanCtrlrDriver_t lg_sct_fan_ctrlr = {0};


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

	/* Initialise the MCP23017 GPIO expanders */
	lg_iot_gpio1_driver.i2c_device 			= lg_iot_init_data.i2c_device;
	lg_iot_gpio1_driver.i2c_address 		= IOT_MCP23017_1_I2C_BUS_ADDR;
	lg_iot_gpio1_driver.io_dir_mask 		= IOT_MCP23017_1_DIR_MASK;
	lg_iot_gpio1_driver.default_op_mask 	= IOT_MCP23017_1_DEFAULT_OP_MASK;
	lg_iot_gpio1_driver.i2c_reset_gpio_port	= lg_iot_init_data.i2c_reset_gpio_port;
	lg_iot_gpio1_driver.i2c_reset_gpio_pin 	= lg_iot_init_data.i2c_reset_gpio_pin;

	lg_iot_gpio2_driver.i2c_device          = lg_iot_init_data.i2c_device;
    lg_iot_gpio2_driver.i2c_address         = IOT_MCP23017_2_I2C_BUS_ADDR;
    lg_iot_gpio2_driver.io_dir_mask         = IOT_MCP23017_2_DIR_MASK;
    lg_iot_gpio2_driver.default_op_mask     = IOT_MCP23017_2_DEFAULT_OP_MASK;
    lg_iot_gpio2_driver.i2c_reset_gpio_port = lg_iot_init_data.i2c_reset_gpio_port;
    lg_iot_gpio2_driver.i2c_reset_gpio_pin  = lg_iot_init_data.i2c_reset_gpio_pin;

	lg_iot_initialised &= mcp23017_Init(&lg_iot_gpio1_driver);
	lg_iot_initialised &= mcp23017_Init(&lg_iot_gpio2_driver);
	lg_iot_gpo1_pin_state.reg = IOT_MCP23017_1_DEFAULT_OP_MASK;
	lg_iot_gpo2_pin_state.reg = IOT_MCP23017_2_DEFAULT_OP_MASK;

	lg_iot_adc_non_iso1_driver.scaling_factors[0] = 7.0F;                      /* NTM 1 DC Out */
	lg_iot_adc_non_iso1_driver.scaling_factors[1] = 7.0F;                      /* NTM 2 DC Out */
	lg_iot_adc_non_iso1_driver.scaling_factors[2] = 7.0F;                      /* NTM 3 DC Out */
	lg_iot_adc_non_iso1_driver.scaling_factors[3] = 1.0F;                      /* NTM 1 +3V4 STBY */
	lg_iot_adc_non_iso1_driver.scaling_factors[4] = 1.0F;                      /* NTM 2 +3V4 STBY */
	lg_iot_adc_non_iso1_driver.scaling_factors[5] = 1.0F;                      /* NTM 3 +3V4 STBY */
	lg_iot_adc_non_iso1_driver.scaling_factors[6] = 1.0F;                      /* NTM 1 +3V3 Out */
	lg_iot_adc_non_iso1_driver.scaling_factors[7] = 1.0F;                      /* NTM 2 +3V3 Out */

    lg_iot_adc_non_iso2_driver.scaling_factors[0] = 1.0F;                      /* NTM 3 +3V3 Out */
    lg_iot_adc_non_iso2_driver.scaling_factors[1] = 2.0F;                      /* RCU +12V Out */
    lg_iot_adc_non_iso2_driver.scaling_factors[2] = 1.0F;                      /* Control/Master VSUP_SDBY */
    lg_iot_adc_non_iso2_driver.scaling_factors[3] = 2.0F;                      /* Buzzer +12V*/
    lg_iot_adc_non_iso2_driver.scaling_factors[4] = 1.0F;                      /* Prog. Eth GND */
    lg_iot_adc_non_iso2_driver.scaling_factors[5] = 1.0F;                      /* RCU Eth GND */
    lg_iot_adc_non_iso2_driver.scaling_factors[6] = LTC2991_SE_V_SCALE_FACTOR;
    lg_iot_adc_non_iso2_driver.scaling_factors[7] = LTC2991_SE_V_SCALE_FACTOR;

    lg_iot_adc_non_iso3_driver.scaling_factors[0] = 7.0F;                      /* IPAM 1 DC Out */
    lg_iot_adc_non_iso3_driver.scaling_factors[1] = 7.0F;                      /* IPAM 2 DC Out */
    lg_iot_adc_non_iso3_driver.scaling_factors[2] = 7.0F;                      /* IPAM 3 DC Out */
    lg_iot_adc_non_iso3_driver.scaling_factors[3] = 3.08F;                     /* Fan Interface 1, Fan 1 */
    lg_iot_adc_non_iso3_driver.scaling_factors[4] = 3.08F;                     /* Fan Interface 2, Fan 1 */
    lg_iot_adc_non_iso3_driver.scaling_factors[5] = 3.08F;                     /* Fan Interface 2, Fan 2 */
    lg_iot_adc_non_iso3_driver.scaling_factors[6] = 3.08F;                     /* Fan Interface 3, Fan 1 */
    lg_iot_adc_non_iso3_driver.scaling_factors[7] = LTC2991_SE_V_SCALE_FACTOR;

	lg_iot_initialised &= ltc2991_InitInstance(	&lg_iot_adc_non_iso1_driver,
												lg_iot_init_data.i2c_device,
												IOT_LTC2991_NON_ISO1_I2C_BUS_ADDR);
	lg_iot_initialised &= ltc2991_InitInstance( &lg_iot_adc_non_iso2_driver,
	                                            lg_iot_init_data.i2c_device,
	                                            IOT_LTC2991_NON_ISO2_I2C_BUS_ADDR);
    lg_iot_initialised &= ltc2991_InitInstance( &lg_iot_adc_non_iso3_driver,
                                                lg_iot_init_data.i2c_device,
                                                IOT_LTC2991_NON_ISO3_I2C_BUS_ADDR);

    hci_Init(&lg_iot_hci, init_data.i2c_device, IOT_PCA9500_GPIO_I2C_ADDR, IOT_PCA9500_EEPROM_I2C_ADDR);

	fc_InitInstance(&lg_sct_fan_ctrlr, init_data.i2c_device, IOT_EMC2104_I2C_ADDR);
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

	if (!lg_iot_initialised)
	{
		for(;;)
		{
			osDelay(1000U);
		}
	}

	/* Start generating the Fan Tacho Output. */
	HAL_TIM_PWM_Start(lg_iot_init_data.fan_tacho_out_htim,
		    		  lg_iot_init_data.fan_tacho_out_channel);

	for(;;)
	{
		osDelayUntil(&last_wake_time, lg_iot_task_period_ms);

		/* Only update the GPIO expanders and ADC data if the I2C peripheral is available */
		if (osMutexWait(lg_iot_init_data.i2c_mutex, 0U) == osOK)
		{
			if (!ltc2991_ReadAdcData(&lg_iot_adc_non_iso1_driver, &lg_iot_adc_non_iso1_data))
			{
				memset(&lg_iot_adc_non_iso1_data, 0U, sizeof(ltc2991_Data_t));
			}

			if (!ltc2991_ReadAdcData(&lg_iot_adc_non_iso2_driver, &lg_iot_adc_non_iso2_data))
			{
				memset(&lg_iot_adc_non_iso2_data, 0U, sizeof(ltc2991_Data_t));
			}

			if (!ltc2991_ReadAdcData(&lg_iot_adc_non_iso3_driver, &lg_iot_adc_non_iso3_data))
			{
				memset(&lg_iot_adc_non_iso3_data, 0U, sizeof(ltc2991_Data_t));
			}

			(void)mcp23017_ReadPinsVal(&lg_iot_gpio1_driver, &lg_iot_gpi1_pin_state.reg);
			(void)mcp23017_ReadPinsVal(&lg_iot_gpio2_driver, &lg_iot_gpi2_pin_state.reg);
			(void)mcp23017_WritePin(&lg_iot_gpio2_driver, lg_iot_gpo2_pin_state.reg, mcp23017_PinSet);
			(void)mcp23017_WritePin(&lg_iot_gpio2_driver, ~lg_iot_gpo2_pin_state.reg, mcp23017_PinReset);
			(void)mcp23017_WritePin(&lg_iot_gpio1_driver, lg_iot_gpo1_pin_state.reg, mcp23017_PinSet);
			(void)mcp23017_WritePin(&lg_iot_gpio1_driver, ~lg_iot_gpo1_pin_state.reg, mcp23017_PinReset);

			osMutexRelease(lg_iot_init_data.i2c_mutex);
		}
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
    case ntm1_fan_alert:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm1_fan_alert;
        break;

    case ntm2_fan_alert:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm2_fan_alert;
        break;

    case ntm3_fan_alert:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm3_fan_alert;
        break;

    case ntm1_rf_mute_n:
    	pin_state = lg_iot_gpi1_pin_state.pins.ntm1_rf_mute_n;
        break;

    case ntm2_rf_mute_n:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm2_rf_mute_n;
        break;

    case ntm3_rf_mute_n:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm3_rf_mute_n;
        break;

    case rcu_pwr_en_zer_in:
        pin_state = lg_iot_gpi1_pin_state.pins.rcu_pwr_en_zer_in;
        break;

    case ms_pwr_en_out:
        pin_state = lg_iot_gpi2_pin_state.pins.ms_pwr_en_out;
        break;

    case ms_rf_mute_n_in:
        pin_state = lg_iot_gpi2_pin_state.pins.ms_rf_mute_n_in;
        break;

    case ntm1_pfi_n:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm1_pfi_n;
        break;

    case ntm2_pfi_n:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm1_pfi_n;
        break;

    case ntm3_pfi_n:
        pin_state = lg_iot_gpi1_pin_state.pins.ntm3_pfi_n;
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
	case tamper_sw_buzzer:
	    lg_iot_gpo1_pin_state.pins.tamper_sw_buzzer = pin_val;
	    break;

    case rcu_pwr_btn:
        lg_iot_gpo1_pin_state.pins.rcu_pwr_btn = pin_val;
        break;

    case som_sd_boot_en:
        lg_iot_gpo1_pin_state.pins.som_sd_boot_en = pin_val;
        break;

    case rcu_pwr_en_zer_out:
        lg_iot_gpo1_pin_state.pins.rcu_pwr_en_zer = pin_val;
        break;

    case select_i2c_s0:
        lg_iot_gpo1_pin_state.pins.select_i2c_s0 = pin_val;
        break;

    case select_i2c_s1:
        lg_iot_gpo1_pin_state.pins.select_i2c_s1 = pin_val;
        break;

    case ms_1pps_dir_ctrl:
        lg_iot_gpo2_pin_state.pins.ms_1pps_dir_ctrl = pin_val;
        break;

	case select_1pps_s0:
		lg_iot_gpo2_pin_state.pins.select_1pps_s0 = pin_val;
		break;

	case select_1pps_s1:
		lg_iot_gpo2_pin_state.pins.select_1pps_s1 = pin_val;
		break;

    case select_1pps_s2:
        lg_iot_gpo2_pin_state.pins.select_1pps_s2 = pin_val;
        break;

    case select_1pps_s3:
        lg_iot_gpo2_pin_state.pins.select_1pps_s3 = pin_val;
        break;

    case ms_pwr_en_in:
        lg_iot_gpo2_pin_state.pins.ms_pwr_en = pin_val;
        break;

    case ms_master_n:
        lg_iot_gpo2_pin_state.pins.ms_master_n = pin_val;
        break;

    case test_point_1:
        lg_iot_gpo2_pin_state.pins.test_point_1 = pin_val;
        break;

    case test_point_2:
        lg_iot_gpo2_pin_state.pins.test_point_2 = pin_val;
        break;

    case ms_rf_mute_n_out:
        lg_iot_gpo2_pin_state.pins.ms_rf_mute_n = pin_val;
        break;

    case ms_rf_mute_dir:
        lg_iot_gpo2_pin_state.pins.ms_rf_mute_dir = pin_val;
        break;

    case select_fan_pwm_s0:
        lg_iot_gpo2_pin_state.pins.select_fan_pwm_s0 = pin_val;
        break;

    case select_fan_pwm_s1:
        lg_iot_gpo2_pin_state.pins.select_fan_pwm_s1 = pin_val;
        break;

    case select_fan_pwm_s2:
        lg_iot_gpo2_pin_state.pins.select_fan_pwm_s2 = pin_val;
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

#if 0
	if  (lg_analogue_reading_adc_map[ar].adc_device == iso_adc)
	{
		*p_analgoue_reading = lg_iot_adc_iso_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
	}
	else
	{
		*p_analgoue_reading = lg_iot_adc_non_iso_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
	}
#else
    if  (lg_analogue_reading_adc_map[ar].adc_device == non_iso1_adc)
    {
        *p_analgoue_reading = lg_iot_adc_non_iso1_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
    }
    else if  (lg_analogue_reading_adc_map[ar].adc_device == non_iso2_adc)
    {
        *p_analgoue_reading = lg_iot_adc_non_iso2_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
    }
    else if  (lg_analogue_reading_adc_map[ar].adc_device == non_iso3_adc)
    {
        *p_analgoue_reading = lg_iot_adc_non_iso3_data.adc_ch_mv[lg_analogue_reading_adc_map[ar].adc_ch_no];
    }
#endif
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

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = hci_SetAssyBuildDataBatchNo(&lg_iot_hci, assy_build_date_batch_no);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets the NTM I2C bus switched into the NUCLEO board's I2C bus.
*
* @param	source required I2C bus source
*
******************************************************************************/
void iot_SetI2cBus(iot_I2cBusSource_t source)
{
	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 4U) == osOK))
	{
		switch (source)
		{
		case i2c_bus_ntm1:
			iot_SetGpoPinState(select_i2c_s0, reset);
			iot_SetGpoPinState(select_i2c_s1, set);
			break;

		case i2c_bus_ntm2:
			iot_SetGpoPinState(select_i2c_s0, set);
			iot_SetGpoPinState(select_i2c_s1, reset);
			break;

		case i2c_bus_ntm3:
			iot_SetGpoPinState(select_i2c_s0, set);
			iot_SetGpoPinState(select_i2c_s1, set);
			break;

		case i2c_bus_none:
		default:
			iot_SetGpoPinState(select_i2c_s0, reset);
			iot_SetGpoPinState(select_i2c_s1, reset);
			break;
		}
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}
}


/*****************************************************************************/
/**
* Initialises the Microchip EMC2104 fan controller, see fan_controller driver
* for more details.
*
* @return   true if data written to device, else false
*
******************************************************************************/
bool iot_InitialiseFanController(void)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = fc_Initialise(&lg_sct_fan_ctrlr);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Read the Microchip EMC2104 fan controller fan speed counters, see fan_controller
* driver for more details.
*
* @param p_fan1_clk_count receives the fan 1 speed count
* @param p_fan2_clk_count receivse the fan 2 speed count
*
* @return   true if fan counts read from device, else false
*
******************************************************************************/
bool iot_ReadFanSpeedCounts(uint16_t *p_fan1_clk_count,
							uint16_t *p_fan2_clk_count)
{
	bool ret_val = false;
	uint8_t fan1_pwm, fan2_pwm;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		ret_val = fc_ReadFanSpeedCounts(&lg_sct_fan_ctrlr,
									    p_fan1_clk_count, p_fan2_clk_count,
									    &fan1_pwm, &fan2_pwm);
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Set the Microchip EMC2104 fan controller PWM duty cycle, see fan_controller
* driver for more details.
*
* @param p_fan1_clk_count receives the fan 1 speed count
* @param p_fan2_clk_count receivse the fan 2 speed count
*
* @return   true if fan counts read from device, else false
*
******************************************************************************/
bool iot_SetFanSpeedDuty(uint16_t pwm)
{
	bool ret_val = false;

	if (lg_iot_initialised && (osMutexWait(lg_iot_init_data.i2c_mutex,
			(uint32_t)lg_iot_task_period_ms * 2U) == osOK))
	{
		if ((pwm >= 0U) && (pwm <= 100U))
		{
			ret_val = fc_SetDirectSettingMode(&lg_sct_fan_ctrlr, (uint8_t)((pwm * 255U) / 100U));
		}
		osMutexRelease(lg_iot_init_data.i2c_mutex);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Measure the Microchip EMC2104 fan controller output signal PWM duty cycle.
* Assuming that TIM2 is configured for PWM measurement on Channel 2 in the
* STM32Cube project.
*
* @return   PWM duty as percentage
*
******************************************************************************/
uint32_t iot_MeasureFanPwmDuty(void)
{
	uint32_t ret_val = 0xFFFFFFFFU;

	if (lg_iot_initialised)
	{
		/* Clear the counters. */
		lg_iot_init_data.fan_pwm_htim->Instance->CNT = 0U;
		lg_iot_init_data.fan_pwm_htim->Instance->CCR1 = 0U;
		lg_iot_init_data.fan_pwm_htim->Instance->CCR2 = 0U;

		/* Enable the input capture. */
		lg_iot_init_data.fan_pwm_htim->Instance->CR1 |= TIM_CR1_CEN;
		lg_iot_init_data.fan_pwm_htim->Instance->CCER |= (TIM_CCER_CC1E | TIM_CCER_CC2E);
		osDelay(1U);

		uint32_t period_count = lg_iot_init_data.fan_pwm_htim->Instance->CCR2;
		uint32_t duty_count = lg_iot_init_data.fan_pwm_htim->Instance->CCR1;

		ret_val = period_count == 0U ? 0U : ((duty_count * 100) / period_count);

		/* Disable the input capture. */
		lg_iot_init_data.fan_pwm_htim->Instance->CR1 &= ~TIM_CR1_CEN;
		lg_iot_init_data.fan_pwm_htim->Instance->CCER &= ~(TIM_CCER_CC1E | TIM_CCER_CC2E);
	}

	return ret_val;
}


/*****************************************************************************/
/**
* Sets the Fan PWM source switched into the NUCLEO board's TIM1 PWM input.
*
* @param	source required I2C bus source
*
******************************************************************************/
void iot_SetFanPwmSource(iot_FanPwmSource_t source)
{
	if (lg_iot_initialised)
	{
		switch (source)
		{
		case fan_pwm_2_1:
			iot_SetGpoPinState(select_fan_pwm_s0, set);
			iot_SetGpoPinState(select_fan_pwm_s2, reset);
			break;

		case fan_pwm_2_2:
			iot_SetGpoPinState(select_fan_pwm_s1, reset);
			iot_SetGpoPinState(select_fan_pwm_s2, set);
			break;

		case fan_pwm_3_1:
			iot_SetGpoPinState(select_fan_pwm_s1, set);
			iot_SetGpoPinState(select_fan_pwm_s2, set);
			break;

		case fan_pwm_1_1:
		default:
			iot_SetGpoPinState(select_fan_pwm_s0, reset);
			iot_SetGpoPinState(select_fan_pwm_s2, reset);
			break;
		}
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
