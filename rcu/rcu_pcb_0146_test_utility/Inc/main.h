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
#define MAIN_TIM3_PRESCALER 512
#define MAIN_TIM3_500_MS_COUNT 31250
#define BUZZER_ENABLE_Pin GPIO_PIN_14
#define BUZZER_ENABLE_GPIO_Port GPIOC
#define BOARD_LED_Pin GPIO_PIN_15
#define BOARD_LED_GPIO_Port GPIOC
#define XCHANGE_RESET_Pin GPIO_PIN_1
#define XCHANGE_RESET_GPIO_Port GPIOA
#define XCHANGE_UART_TXD_Pin GPIO_PIN_2
#define XCHANGE_UART_TXD_GPIO_Port GPIOA
#define XCHANGE_UART_TXDA3_Pin GPIO_PIN_3
#define XCHANGE_UART_TXDA3_GPIO_Port GPIOA
#define TP9_Pin GPIO_PIN_1
#define TP9_GPIO_Port GPIOB
#define TP10_Pin GPIO_PIN_2
#define TP10_GPIO_Port GPIOB
#define CS_UART_TXD_Pin GPIO_PIN_9
#define CS_UART_TXD_GPIO_Port GPIOA
#define CS_UART_RXD_Pin GPIO_PIN_10
#define CS_UART_RXD_GPIO_Port GPIOA
#define CS_1PPS_IN_Pin GPIO_PIN_11
#define CS_1PPS_IN_GPIO_Port GPIOA
#define CS_1PPS_IN_EXTI_IRQn EXTI4_15_IRQn
#define BTN2_IN_Pin GPIO_PIN_15
#define BTN2_IN_GPIO_Port GPIOA
#define BTN2_IN_EXTI_IRQn EXTI4_15_IRQn
#define I2C_RESET_N_Pin GPIO_PIN_5
#define I2C_RESET_N_GPIO_Port GPIOB
#define BTN1_IN_Pin GPIO_PIN_8
#define BTN1_IN_GPIO_Port GPIOB
#define BTN1_IN_EXTI_IRQn EXTI4_15_IRQn
#define BTN0_IN_Pin GPIO_PIN_9
#define BTN0_IN_GPIO_Port GPIOB
#define BTN0_IN_EXTI_IRQn EXTI4_15_IRQn
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
