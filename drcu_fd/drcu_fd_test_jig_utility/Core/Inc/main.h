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
#include "stm32l4xx_hal.h"
#include "stm32l4xx_ll_adc.h"
#include "stm32l4xx_ll_dma.h"
#include "stm32l4xx_ll_usart.h"
#include "stm32l4xx_ll_rcc.h"
#include "stm32l4xx_ll_bus.h"
#include "stm32l4xx_ll_cortex.h"
#include "stm32l4xx_ll_system.h"
#include "stm32l4xx_ll_utils.h"
#include "stm32l4xx_ll_pwr.h"
#include "stm32l4xx_ll_gpio.h"

#include "stm32l4xx_ll_exti.h"

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
#define BUZZER_12V_Pin GPIO_PIN_0
#define BUZZER_12V_GPIO_Port GPIOA
#define AUX_SUPPLY_12V_Pin GPIO_PIN_1
#define AUX_SUPPLY_12V_GPIO_Port GPIOA
#define VCP_TX_Pin GPIO_PIN_2
#define VCP_TX_GPIO_Port GPIOA
#define XCHANGE_12V_Pin GPIO_PIN_3
#define XCHANGE_12V_GPIO_Port GPIOA
#define FD_ETH_GND_Pin GPIO_PIN_4
#define FD_ETH_GND_GPIO_Port GPIOA
#define CSM_ETH_GND_Pin GPIO_PIN_5
#define CSM_ETH_GND_GPIO_Port GPIOA
#define CSM_1PPS_DIR_Pin GPIO_PIN_6
#define CSM_1PPS_DIR_GPIO_Port GPIOA
#define POWER_EN_ZER_EN_N_Pin GPIO_PIN_0
#define POWER_EN_ZER_EN_N_GPIO_Port GPIOB
#define CSM_1PPS_Pin GPIO_PIN_1
#define CSM_1PPS_GPIO_Port GPIOB
#define XCHANGE_1PPS_Pin GPIO_PIN_8
#define XCHANGE_1PPS_GPIO_Port GPIOA
#define XCHANGE_1PPS_EXTI_IRQn EXTI9_5_IRQn
#define XCHANGE_RESET_Pin GPIO_PIN_11
#define XCHANGE_RESET_GPIO_Port GPIOA
#define PWR_BTN_N_Pin GPIO_PIN_12
#define PWR_BTN_N_GPIO_Port GPIOA
#define SWDIO_Pin GPIO_PIN_13
#define SWDIO_GPIO_Port GPIOA
#define SWCLK_Pin GPIO_PIN_14
#define SWCLK_GPIO_Port GPIOA
#define VCP_RX_Pin GPIO_PIN_15
#define VCP_RX_GPIO_Port GPIOA
#define LD3_Pin GPIO_PIN_3
#define LD3_GPIO_Port GPIOB
#define SOM_SYS_RST_Pin GPIO_PIN_4
#define SOM_SYS_RST_GPIO_Port GPIOB
#define SOM_SD_BOOT_EN_Pin GPIO_PIN_5
#define SOM_SD_BOOT_EN_GPIO_Port GPIOB
/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
