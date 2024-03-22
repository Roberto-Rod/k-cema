/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include "serial_buffer_task.h"
#include "serial_echo_task.h"
#include "serial_cmd_task.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc;

I2C_HandleTypeDef hi2c1;
I2C_HandleTypeDef hi2c2;

TIM_HandleTypeDef htim7;

UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;

osThreadId defaultTaskHandle;
osThreadId serialBufferTaskHandle;
osThreadId serialCmdTaskHandle;
osThreadId serialEchoTaskHandle;
osMessageQId serialRxEventHandle;
osMessageQId serialCmdTaskRxDataHandle;
osMessageQId serialCmdTaskTxDataHandle;
osMessageQId serialEchoTaskRxDataHandle;
osMessageQId serialEchoTaskTxDataHandle;
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC_Init(void);
static void MX_I2C1_Init(void);
static void MX_I2C2_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_TIM7_Init(void);
void StartDefaultTask(void const * argument);
extern void sbt_SerialBufferTask(void const * argument);
extern void sct_SerialCmdTask(void const * argument);
extern void set_SerialEchoTask(void const * argument);

/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  sct_Init_t sct_init_data;
  set_Init_t set_init_data;
  sbt_Init_t sbt_init_data;
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_ADC_Init();
  MX_I2C1_Init();
  MX_I2C2_Init();
  MX_USART1_UART_Init();
  MX_USART2_UART_Init();
  MX_TIM7_Init();
  /* USER CODE BEGIN 2 */
  /* If either the anti-tamper or cable disconnect irqs are low
   * set ZER_PWR_HOLD to keep the +3V0_ZER_MICRO supply enabled */
  if ((HAL_GPIO_ReadPin(IRQ_TAMPER_N_GPIO_Port, IRQ_TAMPER_N_Pin) == GPIO_PIN_RESET) ||
	  (HAL_GPIO_ReadPin(IRQ_CABLE_UNPLUG_N_GPIO_Port, IRQ_CABLE_UNPLUG_N_Pin) == GPIO_PIN_RESET))
  {
	  HAL_GPIO_WritePin(ZER_PWR_HOLD_GPIO_Port, ZER_PWR_HOLD_Pin, GPIO_PIN_SET);
  }
  /* USER CODE END 2 */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* definition and creation of serialRxEvent */
  osMessageQDef(serialRxEvent, 128, uint32_t);
  serialRxEventHandle = osMessageCreate(osMessageQ(serialRxEvent), NULL);

  /* definition and creation of serialCmdTaskRxData */
  osMessageQDef(serialCmdTaskRxData, 128, uint32_t);
  serialCmdTaskRxDataHandle = osMessageCreate(osMessageQ(serialCmdTaskRxData), NULL);

  /* definition and creation of serialCmdTaskTxData */
  osMessageQDef(serialCmdTaskTxData, 1024, uint32_t);
  serialCmdTaskTxDataHandle = osMessageCreate(osMessageQ(serialCmdTaskTxData), NULL);

  /* definition and creation of serialEchoTaskRxData */
  osMessageQDef(serialEchoTaskRxData, 32, uint32_t);
  serialEchoTaskRxDataHandle = osMessageCreate(osMessageQ(serialEchoTaskRxData), NULL);

  /* definition and creation of serialEchoTaskTxData */
  osMessageQDef(serialEchoTaskTxData, 32, uint32_t);
  serialEchoTaskTxDataHandle = osMessageCreate(osMessageQ(serialEchoTaskTxData), NULL);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* definition and creation of defaultTask */
  osThreadDef(defaultTask, StartDefaultTask, osPriorityLow, 0, 128);
  defaultTaskHandle = osThreadCreate(osThread(defaultTask), NULL);

  /* definition and creation of serialBufferTask */
  osThreadDef(serialBufferTask, sbt_SerialBufferTask, osPriorityNormal, 0, 256);
  serialBufferTaskHandle = osThreadCreate(osThread(serialBufferTask), NULL);

  /* definition and creation of serialCmdTask */
  osThreadDef(serialCmdTask, sct_SerialCmdTask, osPriorityBelowNormal, 0, 512);
  serialCmdTaskHandle = osThreadCreate(osThread(serialCmdTask), NULL);

  /* definition and creation of serialEchoTask */
  osThreadDef(serialEchoTask, set_SerialEchoTask, osPriorityBelowNormal, 0, 256);
  serialEchoTaskHandle = osThreadCreate(osThread(serialEchoTask), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  sbt_init_data.rx_event_queue				= serialRxEventHandle;
  sbt_init_data.no_uarts					= 2;
  sbt_init_data.uarts[0].huart 				= &huart2;
  sbt_init_data.uarts[0].uart_rx_data_queue	= serialEchoTaskRxDataHandle;
  sbt_init_data.uarts[0].uart_tx_data_queue = serialEchoTaskTxDataHandle;
  sbt_init_data.uarts[1].huart 				= &huart1;
  sbt_init_data.uarts[1].uart_rx_data_queue	= serialCmdTaskRxDataHandle;
  sbt_init_data.uarts[1].uart_tx_data_queue	= serialCmdTaskTxDataHandle;
  sbt_InitTask(sbt_init_data);

  set_init_data.tx_data_queue 		= serialEchoTaskTxDataHandle;
  set_init_data.rx_data_queue 		= serialEchoTaskRxDataHandle;
  set_InitTask(set_init_data);

  sct_init_data.tx_data_queue 		= serialCmdTaskTxDataHandle;
  sct_init_data.rx_data_queue 		= serialCmdTaskRxDataHandle;
  sct_init_data.i2c_device0			= &hi2c1;
  sct_init_data.i2c_device1			= &hi2c2;
  sct_init_data.buzzer_gpio_port	= BUZZER_EN_GPIO_Port;
  sct_init_data.buzzer_gpio_pin		= BUZZER_EN_Pin;
  sct_init_data.gpi_pins[0].port	= IRQ_TAMPER_N_GPIO_Port;
  sct_init_data.gpi_pins[0].pin		= IRQ_TAMPER_N_Pin;
  sct_init_data.i2c_reset_gpio_port = KEYPAD_I2C_RESET_N_GPIO_Port;
  sct_init_data.i2c_reset_gpio_pin	= KEYPAD_I2C_RESET_N_Pin;
  sct_init_data.pps_gpio_pin		= PPS_Pin;
  sct_init_data.pps_gpio_irq		= EXTI4_15_IRQn;
  sct_init_data.pwr_btn_timer       = &htim7;
  strncpy(sct_init_data.gpi_pins[0].name, "IRQ_TAMPER_N", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[1].port	= BATT_CHRG_STAT_N_GPIO_Port;
  sct_init_data.gpi_pins[1].pin		= BATT_CHRG_STAT_N_Pin;
  strncpy(sct_init_data.gpi_pins[1].name, "BATT_CHRG_STAT_N", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[2].port	= IRQ_CABLE_UNPLUG_N_GPIO_Port;
  sct_init_data.gpi_pins[2].pin		= IRQ_CABLE_UNPLUG_N_Pin;
  strncpy(sct_init_data.gpi_pins[2].name, "IRQ_CABLE_UNPLUG_N", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[3].port	= PGOOD_3V3_SUP_GPIO_Port;
  sct_init_data.gpi_pins[3].pin		= PGOOD_3V3_SUP_Pin;
  strncpy(sct_init_data.gpi_pins[3].name, "PGOOD_3V3_SUP", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[4].port	= KEYPAD_BTN_IN0_GPIO_Port;
  sct_init_data.gpi_pins[4].pin		= KEYPAD_BTN_IN0_Pin;
  strncpy(sct_init_data.gpi_pins[4].name, "KEYPAD_BTN_IN0", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[5].port	= KEYPAD_BTN_IN1_GPIO_Port;
  sct_init_data.gpi_pins[5].pin		= KEYPAD_BTN_IN1_Pin;
  strncpy(sct_init_data.gpi_pins[5].name, "KEYPAD_BTN_IN1", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpi_pins[6].port	= KEYPAD_BTN_IN2_GPIO_Port;
  sct_init_data.gpi_pins[6].pin		= KEYPAD_BTN_IN2_Pin;
  strncpy(sct_init_data.gpi_pins[6].name, "KEYPAD_BTN_IN2", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[0].port	= ZER_PWR_HOLD_GPIO_Port;
  sct_init_data.gpo_pins[0].pin		= ZER_PWR_HOLD_Pin;
  strncpy(sct_init_data.gpo_pins[0].name, "ZER_PWR_HOLD", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[1].port	= ZER_FPGA_PWR_EN_GPIO_Port;
  sct_init_data.gpo_pins[1].pin		= ZER_FPGA_PWR_EN_Pin;
  strncpy(sct_init_data.gpo_pins[1].name, "ZER_FPGA_PWR_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[2].port	= ZER_I2C_SOM_EN_GPIO_Port;
  sct_init_data.gpo_pins[2].pin		= ZER_I2C_SOM_EN_Pin;
  strncpy(sct_init_data.gpo_pins[2].name, "ZER_I2C_SOM_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[3].port	= ZER_I2C_FPGA_EN_GPIO_Port;
  sct_init_data.gpo_pins[3].pin		= ZER_I2C_FPGA_EN_Pin;
  strncpy(sct_init_data.gpo_pins[3].name, "ZER_I2C_FPGA_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[4].port	= ZER_FPGA_RST_GPIO_Port;
  sct_init_data.gpo_pins[4].pin		= ZER_FPGA_RST_Pin;
  strncpy(sct_init_data.gpo_pins[4].name, "ZER_FPGA_RST", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[5].port	= RCU_MICRO_TX_EN_GPIO_Port;
  sct_init_data.gpo_pins[5].pin		= RCU_MICRO_TX_EN_Pin;
  strncpy(sct_init_data.gpo_pins[5].name, "RCU_MICRO_TX_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[6].port	= BATT_CHRG_LOW_GPIO_Port;
  sct_init_data.gpo_pins[6].pin		= BATT_CHRG_LOW_Pin;
  strncpy(sct_init_data.gpo_pins[6].name, "BATT_CHRG_LOW", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[7].port	= BATT_CHRG_EN_N_GPIO_Port;
  sct_init_data.gpo_pins[7].pin		= BATT_CHRG_EN_N_Pin;
  strncpy(sct_init_data.gpo_pins[7].name, "BATT_CHRG_EN_N", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[8].port	= SOM_2V5_PWR_EN_GPIO_Port;
  sct_init_data.gpo_pins[8].pin		= SOM_2V5_PWR_EN_Pin;
  strncpy(sct_init_data.gpo_pins[8].name, "SOM_2V5_PWR_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_InitTask(sct_init_data);
  /* USER CODE END RTOS_THREADS */

  /* Start scheduler */
  osKernelStart();

  /* We should never get here as control is now taken by the scheduler */
  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_BYPASS;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLLMUL_8;
  RCC_OscInitStruct.PLL.PLLDIV = RCC_PLLDIV_2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USART1|RCC_PERIPHCLK_USART2
                              |RCC_PERIPHCLK_I2C1;
  PeriphClkInit.Usart1ClockSelection = RCC_USART1CLKSOURCE_PCLK2;
  PeriphClkInit.Usart2ClockSelection = RCC_USART2CLKSOURCE_PCLK1;
  PeriphClkInit.I2c1ClockSelection = RCC_I2C1CLKSOURCE_PCLK1;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC_Init(void)
{

  /* USER CODE BEGIN ADC_Init 0 */

  /* USER CODE END ADC_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC_Init 1 */

  /* USER CODE END ADC_Init 1 */
  /** Configure the global features of the ADC (Clock, Resolution, Data Alignment and number of conversion)
  */
  hadc.Instance = ADC1;
  hadc.Init.OversamplingMode = DISABLE;
  hadc.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
  hadc.Init.Resolution = ADC_RESOLUTION_12B;
  hadc.Init.SamplingTime = ADC_SAMPLETIME_1CYCLE_5;
  hadc.Init.ScanConvMode = ADC_SCAN_DIRECTION_FORWARD;
  hadc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc.Init.ContinuousConvMode = DISABLE;
  hadc.Init.DiscontinuousConvMode = DISABLE;
  hadc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc.Init.DMAContinuousRequests = DISABLE;
  hadc.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  hadc.Init.Overrun = ADC_OVR_DATA_PRESERVED;
  hadc.Init.LowPowerAutoWait = DISABLE;
  hadc.Init.LowPowerFrequencyMode = DISABLE;
  hadc.Init.LowPowerAutoPowerOff = DISABLE;
  if (HAL_ADC_Init(&hadc) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure for the selected ADC regular channel to be converted.
  */
  sConfig.Channel = ADC_CHANNEL_TEMPSENSOR;
  sConfig.Rank = ADC_RANK_CHANNEL_NUMBER;
  if (HAL_ADC_ConfigChannel(&hadc, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure for the selected ADC regular channel to be converted.
  */
  sConfig.Channel = ADC_CHANNEL_VREFINT;
  if (HAL_ADC_ConfigChannel(&hadc, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC_Init 2 */

  /* USER CODE END ADC_Init 2 */

}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.Timing = 0x00707CBB;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Analogue filter
  */
  if (HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Digital filter
  */
  if (HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief I2C2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C2_Init(void)
{

  /* USER CODE BEGIN I2C2_Init 0 */

  /* USER CODE END I2C2_Init 0 */

  /* USER CODE BEGIN I2C2_Init 1 */

  /* USER CODE END I2C2_Init 1 */
  hi2c2.Instance = I2C2;
  hi2c2.Init.Timing = 0x00707CBB;
  hi2c2.Init.OwnAddress1 = 0;
  hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c2.Init.OwnAddress2 = 0;
  hi2c2.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
  hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c2) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Analogue filter
  */
  if (HAL_I2CEx_ConfigAnalogFilter(&hi2c2, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Digital filter
  */
  if (HAL_I2CEx_ConfigDigitalFilter(&hi2c2, 0) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C2_Init 2 */

  /* USER CODE END I2C2_Init 2 */

}

/**
  * @brief TIM7 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM7_Init(void)
{

  /* USER CODE BEGIN TIM7_Init 0 */

  /* USER CODE END TIM7_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM7_Init 1 */

  /* USER CODE END TIM7_Init 1 */
  htim7.Instance = TIM7;
  htim7.Init.Prescaler = 32000;
  htim7.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim7.Init.Period = 1000;
  htim7.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim7) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_OnePulse_Init(&htim7, TIM_OPMODE_SINGLE) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim7, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM7_Init 2 */

  /* USER CODE END TIM7_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, BUZZER_EN_Pin|MICRO_LED_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, BATT_CHRG_LOW_Pin|ZER_FPGA_PWR_EN_Pin|ZER_I2C_SOM_EN_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, ZER_PWR_HOLD_Pin|ZER_I2C_FPGA_EN_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, RCU_MICRO_TX_EN_Pin|SOM_2V5_PWR_EN_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, BATT_CHRG_EN_N_Pin|ZER_FPGA_RST_Pin|KEYPAD_I2C_RESET_N_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : PGOOD_3V3_SUP_Pin */
  GPIO_InitStruct.Pin = PGOOD_3V3_SUP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(PGOOD_3V3_SUP_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : BUZZER_EN_Pin MICRO_LED_Pin */
  GPIO_InitStruct.Pin = BUZZER_EN_Pin|MICRO_LED_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : IRQ_TAMPER_N_Pin BATT_CHRG_STAT_N_Pin IRQ_CABLE_UNPLUG_N_Pin KEYPAD_BTN_IN2_Pin */
  GPIO_InitStruct.Pin = IRQ_TAMPER_N_Pin|BATT_CHRG_STAT_N_Pin|IRQ_CABLE_UNPLUG_N_Pin|KEYPAD_BTN_IN2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : BATT_CHRG_LOW_Pin ZER_PWR_HOLD_Pin ZER_FPGA_PWR_EN_Pin ZER_I2C_SOM_EN_Pin
                           ZER_I2C_FPGA_EN_Pin */
  GPIO_InitStruct.Pin = BATT_CHRG_LOW_Pin|ZER_PWR_HOLD_Pin|ZER_FPGA_PWR_EN_Pin|ZER_I2C_SOM_EN_Pin
                          |ZER_I2C_FPGA_EN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : RCU_MICRO_TX_EN_Pin BATT_CHRG_EN_N_Pin ZER_FPGA_RST_Pin SOM_2V5_PWR_EN_Pin
                           KEYPAD_I2C_RESET_N_Pin */
  GPIO_InitStruct.Pin = RCU_MICRO_TX_EN_Pin|BATT_CHRG_EN_N_Pin|ZER_FPGA_RST_Pin|SOM_2V5_PWR_EN_Pin
                          |KEYPAD_I2C_RESET_N_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : PPS_Pin */
  GPIO_InitStruct.Pin = PPS_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(PPS_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : KEYPAD_BTN_IN1_Pin KEYPAD_BTN_IN0_Pin */
  GPIO_InitStruct.Pin = KEYPAD_BTN_IN1_Pin|KEYPAD_BTN_IN0_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI4_15_IRQn, 3, 0);
  HAL_NVIC_EnableIRQ(EXTI4_15_IRQn);

}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used 
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void const * argument)
{
  /* USER CODE BEGIN 5 */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1000);
    HAL_GPIO_TogglePin(MICRO_LED_GPIO_Port, MICRO_LED_Pin);
  }
  /* USER CODE END 5 */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM21 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM21) {
    HAL_IncTick();
  }
  /* USER CODE BEGIN Callback 1 */

  /* USER CODE END Callback 1 */
}

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */

  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     tex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
