/****************************************************************************/
/**
** Copyright 2022 Kirintec Ltd. All rights reserved.
**
** @file io_task.h
**
** Include file for io_task.c
**
** Project   : K-CEMA
**
** Build instructions   : None, include file only
**
****************************************************************************/

/* Define to prevent recursive inclusion */
#ifndef __IO_TASK_H
#define __IO_TASK_H

/*****************************************************************************
*
*  Include
*
*****************************************************************************/
#include <stdbool.h>
#include "hw_config_info.h"
#include "cmsis_os.h"
#include "stm32l4xx_hal.h"
#include "stm32l4xx_ll_dma.h"
#include "stm32l4xx_ll_adc.h"

/*****************************************************************************
*
*  Global Definitions
******************************************************************************/

#define IOT_MAX_STR_LEN						32
#define IOT_ANALOGUE_READINGS_NUM			13
#define IOT_ANALOGUE_READING_NAME_MAX_LEN	IOT_MAX_STR_LEN

/* I2C EEPROM definitions */
#define IOT_EEPROM_I2C_ADDR 			(0x50U << 1)
#define IOT_EEPROM_ADDR_LEN				2U
#define IOT_EEPROM_MEM_SIZE_BYTES		128U
#define IOT_EEPROM_PAGE_SIZE_BYTES		(IOT_EEPROM_MEM_SIZE_BYTES)
#define IOT_EEPROM_WRITE_TIME_MS		5U

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
typedef enum iot_GpoPins
{
	iot_gpo_uut_rfb_synth_en = 0,
	iot_gpo_uut_rfb_synth_ntx_rx_sel,
	iot_gpo_uut_rfb_rx_path_mixer_en,
	iot_gpo_uut_rfb_p3v3_en,
	iot_gpo_uut_rfb_p5v0_en,
	iot_gpo_uut_rfb_p3v3_tx_en,
	iot_gpo_uut_rfb_p5v0_tx_en,
	iot_gpo_uut_db_cts_pwr_en,
	iot_gpo_uut_db_cts_p12v_en,
	iot_gpo_uut_db_cts_p3v3_en,
	iot_gpo_qty
} iot_GpoPins_t;

typedef enum iot_GpioPinState
{
	iot_gpo_low = 0,
	iot_gpo_high
} iot_GpioPinState_t;


typedef struct iot_Init
{
	I2C_HandleTypeDef	*i2c_device;
	osMutexId			i2c_mutex;
	GPIO_TypeDef		*i2c_reset_gpio_port;
	uint16_t 			i2c_reset_gpio_pin;
	TIM_HandleTypeDef 	*pps_out_htim;
	uint32_t 			pps_out_channel;
	GPIO_TypeDef		*pps_ext_en_gpio_port;
	uint16_t 			pps_ext_en_gpio_pin;
	ADC_TypeDef			*adc_device;
	DMA_TypeDef			*adc_dma_device;
	uint32_t			adc_dma_channel;
	osSemaphoreId		adc_semaphore;
	SPI_HandleTypeDef	*spi_device;
	GPIO_TypeDef		*spi_ncs_gpio_port;
	uint16_t 			spi_ncs_gpio_pin;
	GPIO_TypeDef		*synth_ld_gpio_port;
	uint16_t 			synth_ld_gpio_pin;
	GPIO_TypeDef		*i2c_lb_en_gpio_port;
	uint16_t 			i2c_lb_en_gpio_pin;
} iot_Init_t;

typedef enum iot_AdcChannelId
{
	iot_adc_psu_p12v_vsns = 0,
	iot_adc_psu_p5v0_vsns,
	iot_adc_psu_p3v3_isns,
	iot_adc_psu_p3v3_vsns,
	iot_adc_psu_p5v0_isns,
	iot_adc_vref_int,		/* This should always be the last entry in lg_iot_adc_channels */
	iot_adc_ch_qty
} iot_AdcChannelId_t;


/*****************************************************************************
*
*  Global Functions
*
*****************************************************************************/
void iot_InitTask(iot_Init_t init_data);
void iot_IoTask(void const *argument);
bool iot_GetAdcScaledValue(iot_AdcChannelId_t adc_channel, int16_t *p_scaled_value, const char **p_channel_name);
void iot_AdcDMAIrqHandler(ADC_TypeDef *adc_device);
void iot_Enable1PpsOp(bool enable);
void iot_Set1PpsSource(bool external);
bool iot_SetRxAtten(uint16_t atten);
bool iot_SetRxPath(uint16_t rx_path, const char **p_rx_path_name);
bool iot_SetTxAtten(uint16_t atten);
bool iot_SetTxPath(uint16_t tx_path, const char **p_tx_path_name);
bool iot_SetTxDivider(uint16_t tx_div, const char **p_tx_div_name);
bool iot_SetGpoPinState(iot_GpoPins_t pin_id, iot_GpioPinState_t pin_state, const char **p_pin_name);
bool iot_SetTestBoardRfPath(uint16_t path, const char **p_path_name);
bool iot_GetSynthLockDetect(void);
bool iot_SetSynthFreqMhz(uint32_t rf_out_freq_mhz);
bool iot_SetSynthPowerDown(bool power_down);
bool iot_WriteSynthRegister(uint32_t reg_val);
bool iot_InitSynth(void);
bool iot_ReadHwConfigInfo(hci_HwConfigInfoData_t *p_hw_config_info);
bool iot_ResetHwConfigInfo(void);
bool iot_SetAssyPartNo(uint8_t *assy_part_no);
bool iot_SetAssyRevNo(uint8_t *assy_rev_no);
bool iot_SetAssySerialNo(uint8_t *assy_serial_no);
bool iot_SetAssyBuildDataBatchNo(uint8_t *assy_build_date_batch_no);
bool iot_SetI2cLoobackEnable(bool val);
bool iot_I2cEepromWriteByte(uint16_t address, uint8_t data);
bool iot_I2cEepromReadByte(uint16_t address, uint8_t *p_data);
bool iot_I2cEepromReadPage(uint16_t page_address, uint8_t *p_data);



/*****************************************************************************
*
*  External Variables
*
*****************************************************************************/

extern const char *IOT_UART_EXPECTED_STRING;

#endif /* __IO_TASK_H */
