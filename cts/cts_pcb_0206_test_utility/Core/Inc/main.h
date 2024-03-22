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
#include "stm32f4xx_hal.h"
#include "stm32f4xx_ll_adc.h"
#include "stm32f4xx_ll_dma.h"
#include "stm32f4xx_hal.h"
#include "stm32f4xx_ll_usart.h"
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_cortex.h"
#include "stm32f4xx_ll_system.h"
#include "stm32f4xx_ll_utils.h"
#include "stm32f4xx_ll_pwr.h"
#include "stm32f4xx_ll_gpio.h"

#include "stm32f4xx_ll_exti.h"

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
#define IO_PAIR_9_B_Pin GPIO_PIN_2
#define IO_PAIR_9_B_GPIO_Port GPIOE
#define IO_PAIR_9_A_Pin GPIO_PIN_3
#define IO_PAIR_9_A_GPIO_Port GPIOE
#define IO_PAIR_8_A_Pin GPIO_PIN_4
#define IO_PAIR_8_A_GPIO_Port GPIOE
#define IO_PAIR_10_A_Pin GPIO_PIN_5
#define IO_PAIR_10_A_GPIO_Port GPIOE
#define IO_PAIR_13_B_Pin GPIO_PIN_6
#define IO_PAIR_13_B_GPIO_Port GPIOE
#define PPS_IN_Pin GPIO_PIN_0
#define PPS_IN_GPIO_Port GPIOA
#define PPS_IN_EXTI_IRQn EXTI0_IRQn
#define IO_PAIR_14_A_Pin GPIO_PIN_7
#define IO_PAIR_14_A_GPIO_Port GPIOE
#define IO_PAIR_14_B_Pin GPIO_PIN_8
#define IO_PAIR_14_B_GPIO_Port GPIOE
#define IO_PAIR_15_B_Pin GPIO_PIN_9
#define IO_PAIR_15_B_GPIO_Port GPIOE
#define IO_PAIR_13_A_Pin GPIO_PIN_10
#define IO_PAIR_13_A_GPIO_Port GPIOE
#define IO_PAIR_12_B_Pin GPIO_PIN_11
#define IO_PAIR_12_B_GPIO_Port GPIOE
#define RX_PATH_SW_3_B_Pin GPIO_PIN_12
#define RX_PATH_SW_3_B_GPIO_Port GPIOE
#define RX_PATH_SW_3_A_Pin GPIO_PIN_13
#define RX_PATH_SW_3_A_GPIO_Port GPIOE
#define RX_PATH_SW_4_A_Pin GPIO_PIN_14
#define RX_PATH_SW_4_A_GPIO_Port GPIOE
#define RX_PATH_SW_4_B_Pin GPIO_PIN_15
#define RX_PATH_SW_4_B_GPIO_Port GPIOE
#define ETH_PHY_LED_EN_Pin GPIO_PIN_10
#define ETH_PHY_LED_EN_GPIO_Port GPIOB
#define RX_PATH_3V3_IF_EN_Pin GPIO_PIN_15
#define RX_PATH_3V3_IF_EN_GPIO_Port GPIOB
#define IO_PAIR_11_B_Pin GPIO_PIN_8
#define IO_PAIR_11_B_GPIO_Port GPIOD
#define I2C_SCL_UUT_Pin GPIO_PIN_9
#define I2C_SCL_UUT_GPIO_Port GPIOD
#define TX_PATH_3V3_TX_EN_Pin GPIO_PIN_10
#define TX_PATH_3V3_TX_EN_GPIO_Port GPIOD
#define TX_PATH_5V0_TX_EN_Pin GPIO_PIN_11
#define TX_PATH_5V0_TX_EN_GPIO_Port GPIOD
#define IO_PAIR_2_B_Pin GPIO_PIN_12
#define IO_PAIR_2_B_GPIO_Port GPIOD
#define RX_PATH_DET_EN_Pin GPIO_PIN_13
#define RX_PATH_DET_EN_GPIO_Port GPIOD
#define RX_PATH_SW_5_VC_Pin GPIO_PIN_14
#define RX_PATH_SW_5_VC_GPIO_Port GPIOD
#define RX_PATH_SW_6_VC_Pin GPIO_PIN_15
#define RX_PATH_SW_6_VC_GPIO_Port GPIOD
#define IO_PAIR_8_B_Pin GPIO_PIN_6
#define IO_PAIR_8_B_GPIO_Port GPIOC
#define IO_PAIR_10_B_Pin GPIO_PIN_7
#define IO_PAIR_10_B_GPIO_Port GPIOC
#define IO_PAIR_11_A_Pin GPIO_PIN_8
#define IO_PAIR_11_A_GPIO_Port GPIOC
#define IO_PAIR_1_B_Pin GPIO_PIN_11
#define IO_PAIR_1_B_GPIO_Port GPIOA
#define IO_PAIR_3_B_Pin GPIO_PIN_12
#define IO_PAIR_3_B_GPIO_Port GPIOA
#define IO_PAIR_4_A_Pin GPIO_PIN_15
#define IO_PAIR_4_A_GPIO_Port GPIOA
#define IO_PAIR_1_A_Pin GPIO_PIN_10
#define IO_PAIR_1_A_GPIO_Port GPIOC
#define IO_PAIR_2_A_Pin GPIO_PIN_12
#define IO_PAIR_2_A_GPIO_Port GPIOC
#define IO_PAIR_7_B_Pin GPIO_PIN_0
#define IO_PAIR_7_B_GPIO_Port GPIOD
#define IO_PAIR_5_B_Pin GPIO_PIN_1
#define IO_PAIR_5_B_GPIO_Port GPIOD
#define IO_PAIR_6_A_Pin GPIO_PIN_2
#define IO_PAIR_6_A_GPIO_Port GPIOD
#define IO_PAIR_4_B_Pin GPIO_PIN_3
#define IO_PAIR_4_B_GPIO_Port GPIOD
#define IO_PAIR_5_A_Pin GPIO_PIN_4
#define IO_PAIR_5_A_GPIO_Port GPIOD
#define IO_PAIR_7_A_Pin GPIO_PIN_5
#define IO_PAIR_7_A_GPIO_Port GPIOD
#define IO_PAIR_15_A_Pin GPIO_PIN_6
#define IO_PAIR_15_A_GPIO_Port GPIOD
#define I2C_SDA_UUT_Pin GPIO_PIN_7
#define I2C_SDA_UUT_GPIO_Port GPIOD
#define MCU_LED_Pin GPIO_PIN_5
#define MCU_LED_GPIO_Port GPIOB
#define RX_PATH_PK_DET_DISCHRG_Pin GPIO_PIN_6
#define RX_PATH_PK_DET_DISCHRG_GPIO_Port GPIOB
#define IO_PAIR_3_A_Pin GPIO_PIN_7
#define IO_PAIR_3_A_GPIO_Port GPIOB
#define ETH_PHY_RESET_N_Pin GPIO_PIN_8
#define ETH_PHY_RESET_N_GPIO_Port GPIOB
#define IO_PAIR_6_B_Pin GPIO_PIN_0
#define IO_PAIR_6_B_GPIO_Port GPIOE
#define IO_PAIR_12_A_Pin GPIO_PIN_1
#define IO_PAIR_12_A_GPIO_Port GPIOE
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
