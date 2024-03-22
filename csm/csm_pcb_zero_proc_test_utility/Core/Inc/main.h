/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2020 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32l0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define PGOOD_3V3_SUP_Pin GPIO_PIN_13
#define PGOOD_3V3_SUP_GPIO_Port GPIOC
#define BUZZER_EN_Pin GPIO_PIN_14
#define BUZZER_EN_GPIO_Port GPIOC
#define MICRO_LED_Pin GPIO_PIN_15
#define MICRO_LED_GPIO_Port GPIOC
#define IRQ_TAMPER_N_Pin GPIO_PIN_0
#define IRQ_TAMPER_N_GPIO_Port GPIOA
#define BATT_CHRG_STAT_N_Pin GPIO_PIN_1
#define BATT_CHRG_STAT_N_GPIO_Port GPIOA
#define SOM_ZER_TXD_BUF_Pin GPIO_PIN_2
#define SOM_ZER_TXD_BUF_GPIO_Port GPIOA
#define SOM_ZER_RXD_BUF_Pin GPIO_PIN_3
#define SOM_ZER_RXD_BUF_GPIO_Port GPIOA
#define BATT_CHRG_LOW_Pin GPIO_PIN_4
#define BATT_CHRG_LOW_GPIO_Port GPIOA
#define ZER_PWR_HOLD_Pin GPIO_PIN_5
#define ZER_PWR_HOLD_GPIO_Port GPIOA
#define ZER_FPGA_PWR_EN_Pin GPIO_PIN_6
#define ZER_FPGA_PWR_EN_GPIO_Port GPIOA
#define IRQ_CABLE_UNPLUG_N_Pin GPIO_PIN_7
#define IRQ_CABLE_UNPLUG_N_GPIO_Port GPIOA
#define RCU_MICRO_TX_EN_Pin GPIO_PIN_0
#define RCU_MICRO_TX_EN_GPIO_Port GPIOB
#define BATT_CHRG_EN_N_Pin GPIO_PIN_1
#define BATT_CHRG_EN_N_GPIO_Port GPIOB
#define ZER_FPGA_RST_Pin GPIO_PIN_2
#define ZER_FPGA_RST_GPIO_Port GPIOB
#define I2C1_ZER_SCL_Pin GPIO_PIN_10
#define I2C1_ZER_SCL_GPIO_Port GPIOB
#define I2C1_ZER_SDA_Pin GPIO_PIN_11
#define I2C1_ZER_SDA_GPIO_Port GPIOB
#define SOM_2V5_PWR_EN_Pin GPIO_PIN_12
#define SOM_2V5_PWR_EN_GPIO_Port GPIOB
#define ZER_I2C_POE_EN_Pin GPIO_PIN_13
#define ZER_I2C_POE_EN_GPIO_Port GPIOB
#define ZER_FPGA_CORE_EN_N_Pin GPIO_PIN_14
#define ZER_FPGA_CORE_EN_N_GPIO_Port GPIOB
#define ZER_I2C_SOM_EN_Pin GPIO_PIN_8
#define ZER_I2C_SOM_EN_GPIO_Port GPIOA
#define RCU_MICRO_TXD_Pin GPIO_PIN_9
#define RCU_MICRO_TXD_GPIO_Port GPIOA
#define RCU_MICRO_RXD_Pin GPIO_PIN_10
#define RCU_MICRO_RXD_GPIO_Port GPIOA
#define PPS_Pin GPIO_PIN_11
#define PPS_GPIO_Port GPIOA
#define PPS_EXTI_IRQn EXTI4_15_IRQn
#define ZER_I2C_FPGA_EN_Pin GPIO_PIN_12
#define ZER_I2C_FPGA_EN_GPIO_Port GPIOA
#define KEYPAD_BTN_IN2_Pin GPIO_PIN_15
#define KEYPAD_BTN_IN2_GPIO_Port GPIOA
#define POE_PSE_RST_N_Pin GPIO_PIN_3
#define POE_PSE_RST_N_GPIO_Port GPIOB
#define POE_PSE_INT_N_Pin GPIO_PIN_4
#define POE_PSE_INT_N_GPIO_Port GPIOB
#define KEYPAD_I2C_RESET_N_Pin GPIO_PIN_5
#define KEYPAD_I2C_RESET_N_GPIO_Port GPIOB
#define I2C0_ZER_SCL_Pin GPIO_PIN_6
#define I2C0_ZER_SCL_GPIO_Port GPIOB
#define I2C0_ZER_SDA_Pin GPIO_PIN_7
#define I2C0_ZER_SDA_GPIO_Port GPIOB
#define KEYPAD_BTN_IN1_Pin GPIO_PIN_8
#define KEYPAD_BTN_IN1_GPIO_Port GPIOB
#define KEYPAD_BTN_IN0_Pin GPIO_PIN_9
#define KEYPAD_BTN_IN0_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
