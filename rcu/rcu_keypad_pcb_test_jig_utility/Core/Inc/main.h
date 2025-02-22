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
#include "stm32l4xx_hal.h"

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

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define RCU_12V_Pin GPIO_PIN_0
#define RCU_12V_GPIO_Port GPIOA
#define RCU_3V3_Pin GPIO_PIN_1
#define RCU_3V3_GPIO_Port GPIOA
#define VCP_TX_Pin GPIO_PIN_2
#define VCP_TX_GPIO_Port GPIOA
#define RCU_XCHANGE_1PPS_IN_Pin GPIO_PIN_3
#define RCU_XCHANGE_1PPS_IN_GPIO_Port GPIOA
#define RCU_XCHANGE_1PPS_IN_EXTI_IRQn EXTI3_IRQn
#define RCU_XCHANGE_RESET_Pin GPIO_PIN_4
#define RCU_XCHANGE_RESET_GPIO_Port GPIOA
#define KEYPAD_I2C_RESET_N_Pin GPIO_PIN_7
#define KEYPAD_I2C_RESET_N_GPIO_Port GPIOA
#define RCU_POWER_ENABLE_ZEROISE_Pin GPIO_PIN_0
#define RCU_POWER_ENABLE_ZEROISE_GPIO_Port GPIOB
#define RCU_1PPS_OUT_Pin GPIO_PIN_1
#define RCU_1PPS_OUT_GPIO_Port GPIOB
#define KEYPAD_BTN_POWER_Pin GPIO_PIN_8
#define KEYPAD_BTN_POWER_GPIO_Port GPIOA
#define XCHANGE_UART_TX_Pin GPIO_PIN_9
#define XCHANGE_UART_TX_GPIO_Port GPIOA
#define XCHANGE_UART_RX_Pin GPIO_PIN_10
#define XCHANGE_UART_RX_GPIO_Port GPIOA
#define KEYPAD_BTN_IN0_Pin GPIO_PIN_11
#define KEYPAD_BTN_IN0_GPIO_Port GPIOA
#define RCU_BTN_POWER_Pin GPIO_PIN_12
#define RCU_BTN_POWER_GPIO_Port GPIOA
#define SWDIO_Pin GPIO_PIN_13
#define SWDIO_GPIO_Port GPIOA
#define SWCLK_Pin GPIO_PIN_14
#define SWCLK_GPIO_Port GPIOA
#define VCP_RX_Pin GPIO_PIN_15
#define VCP_RX_GPIO_Port GPIOA
#define LD3_Pin GPIO_PIN_3
#define LD3_GPIO_Port GPIOB
#define KEYPAD_BTN_IN1_Pin GPIO_PIN_4
#define KEYPAD_BTN_IN1_GPIO_Port GPIOB
#define KEYPAD_BTN_IN2_Pin GPIO_PIN_5
#define KEYPAD_BTN_IN2_GPIO_Port GPIOB
#define KEYPAD_I2C_SCL_Pin GPIO_PIN_6
#define KEYPAD_I2C_SCL_GPIO_Port GPIOB
#define KEYPAD_I2C_SDA_Pin GPIO_PIN_7
#define KEYPAD_I2C_SDA_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
