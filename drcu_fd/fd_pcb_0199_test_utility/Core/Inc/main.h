/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2023 STMicroelectronics.
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
#define POE_PD_AT_DET_N_Pin GPIO_PIN_13
#define POE_PD_AT_DET_N_GPIO_Port GPIOC
#define BOARD_LED_Pin GPIO_PIN_15
#define BOARD_LED_GPIO_Port GPIOC
#define MICRO_I2C_EN_Pin GPIO_PIN_2
#define MICRO_I2C_EN_GPIO_Port GPIOA
#define SOM_I2C_RESET_Pin GPIO_PIN_3
#define SOM_I2C_RESET_GPIO_Port GPIOA
#define PVBAT_Pin GPIO_PIN_6
#define PVBAT_GPIO_Port GPIOA
#define BATT_CHRG_EN_N_Pin GPIO_PIN_0
#define BATT_CHRG_EN_N_GPIO_Port GPIOB
#define BATT_CHRG_STAT_N_Pin GPIO_PIN_1
#define BATT_CHRG_STAT_N_GPIO_Port GPIOB
#define BATT_CHRG_LOW_Pin GPIO_PIN_2
#define BATT_CHRG_LOW_GPIO_Port GPIOB
#define POE_PD_TYP3_DET_N_Pin GPIO_PIN_10
#define POE_PD_TYP3_DET_N_GPIO_Port GPIOB
#define POE_PD_TYP4_DET_N_Pin GPIO_PIN_11
#define POE_PD_TYP4_DET_N_GPIO_Port GPIOB
#define ZER_PWR_HOLD_Pin GPIO_PIN_12
#define ZER_PWR_HOLD_GPIO_Port GPIOB
#define IRQ_TAMPER_N_Pin GPIO_PIN_13
#define IRQ_TAMPER_N_GPIO_Port GPIOB
#define SOM_PWRBTN_N_Pin GPIO_PIN_14
#define SOM_PWRBTN_N_GPIO_Port GPIOB
#define SOM_SYS_RST_PMIC_N_Pin GPIO_PIN_15
#define SOM_SYS_RST_PMIC_N_GPIO_Port GPIOB
#define DISPLAY_CTRL_SEL_Pin GPIO_PIN_8
#define DISPLAY_CTRL_SEL_GPIO_Port GPIOA
#define KP_BTN_IN2_Pin GPIO_PIN_15
#define KP_BTN_IN2_GPIO_Port GPIOA
#define KP_LED_EN_N_Pin GPIO_PIN_5
#define KP_LED_EN_N_GPIO_Port GPIOB
#define KP_BTN_IN1_Pin GPIO_PIN_8
#define KP_BTN_IN1_GPIO_Port GPIOB
#define KP_BTN_IN0_Pin GPIO_PIN_9
#define KP_BTN_IN0_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
