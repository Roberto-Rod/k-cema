/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include "io_task.h"
#include "serial_buffer_task.h"
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

TIM_HandleTypeDef htim1;

UART_HandleTypeDef huart1;
DMA_HandleTypeDef hdma_usart1_rx;
DMA_HandleTypeDef hdma_usart1_tx;

osThreadId defaultTaskHandle;
uint32_t defaultTaskBuffer[ 128 ];
osStaticThreadDef_t defaultTaskControlBlock;
osThreadId serialBufferTaskHandle;
uint32_t serialBufferTaskBuffer[ 256 ];
osStaticThreadDef_t serialBufferTaskControlBlock;
osThreadId ioTaskHandle;
uint32_t ioTaskBuffer[ 256 ];
osStaticThreadDef_t ioTaskControlBlock;
osThreadId serialCmdTaskHandle;
uint32_t serialCmdTaskBuffer[ 512 ];
osStaticThreadDef_t serialCmdTaskControlBlock;
osMessageQId serialCmdRxDataHandle;
uint8_t serialCmdRxDataBuffer[ 128 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialCmdRxDataControlBlock;
osMessageQId serialCmdTxDataHandle;
uint8_t serialCmdTxDataBuffer[ 1024 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialCmdTxDataControlBlock;
osMessageQId serialEchoRxDataHandle;
uint8_t serialEchoRxDataBuffer[ 128 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialEchoRxDataControlBlock;
osMessageQId serialEchoTxDataHandle;
uint8_t serialEchoTxDataBuffer[ 128 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialEchoTxDataControlBlock;
osSemaphoreId uart1TxSemaphoreHandle;
osStaticSemaphoreDef_t uart1TxSemaphoreControlBlock;
osSemaphoreId uart2TxSemaphoreHandle;
osStaticSemaphoreDef_t uart2TxSemaphoreControlBlock;
osSemaphoreId iotAdcSemaphoreHandle;
osStaticSemaphoreDef_t iotAdcSemaphoreControlBlock;
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_ADC1_Init(void);
static void MX_TIM1_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART1_UART_Init(void);
void StartDefaultTask(void const * argument);
extern void sbt_SerialBufferTask(void const * argument);
extern void iot_IoTask(void const * argument);
extern void sct_SerialCmdTask(void const * argument);

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
  iot_Init_t iot_init_data = {0};
  sbt_Init_t sbt_init_data = {0};
  sct_Init_t sct_init_data = {0};
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
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_TIM1_Init();
  MX_USART2_UART_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* Create the semaphores(s) */
  /* definition and creation of uart1TxSemaphore */
  osSemaphoreStaticDef(uart1TxSemaphore, &uart1TxSemaphoreControlBlock);
  uart1TxSemaphoreHandle = osSemaphoreCreate(osSemaphore(uart1TxSemaphore), 1);

  /* definition and creation of uart2TxSemaphore */
  osSemaphoreStaticDef(uart2TxSemaphore, &uart2TxSemaphoreControlBlock);
  uart2TxSemaphoreHandle = osSemaphoreCreate(osSemaphore(uart2TxSemaphore), 1);

  /* definition and creation of iotAdcSemaphore */
  osSemaphoreStaticDef(iotAdcSemaphore, &iotAdcSemaphoreControlBlock);
  iotAdcSemaphoreHandle = osSemaphoreCreate(osSemaphore(iotAdcSemaphore), 1);

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* definition and creation of serialCmdRxData */
  osMessageQStaticDef(serialCmdRxData, 128, uint8_t, serialCmdRxDataBuffer, &serialCmdRxDataControlBlock);
  serialCmdRxDataHandle = osMessageCreate(osMessageQ(serialCmdRxData), NULL);

  /* definition and creation of serialCmdTxData */
  osMessageQStaticDef(serialCmdTxData, 1024, uint8_t, serialCmdTxDataBuffer, &serialCmdTxDataControlBlock);
  serialCmdTxDataHandle = osMessageCreate(osMessageQ(serialCmdTxData), NULL);

  /* definition and creation of serialEchoRxData */
  osMessageQStaticDef(serialEchoRxData, 128, uint8_t, serialEchoRxDataBuffer, &serialEchoRxDataControlBlock);
  serialEchoRxDataHandle = osMessageCreate(osMessageQ(serialEchoRxData), NULL);

  /* definition and creation of serialEchoTxData */
  osMessageQStaticDef(serialEchoTxData, 128, uint8_t, serialEchoTxDataBuffer, &serialEchoTxDataControlBlock);
  serialEchoTxDataHandle = osMessageCreate(osMessageQ(serialEchoTxData), NULL);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* definition and creation of defaultTask */
  osThreadStaticDef(defaultTask, StartDefaultTask, osPriorityNormal, 0, 128, defaultTaskBuffer, &defaultTaskControlBlock);
  defaultTaskHandle = osThreadCreate(osThread(defaultTask), NULL);

  /* definition and creation of serialBufferTask */
  osThreadStaticDef(serialBufferTask, sbt_SerialBufferTask, osPriorityNormal, 0, 256, serialBufferTaskBuffer, &serialBufferTaskControlBlock);
  serialBufferTaskHandle = osThreadCreate(osThread(serialBufferTask), NULL);

  /* definition and creation of ioTask */
  osThreadStaticDef(ioTask, iot_IoTask, osPriorityLow, 0, 256, ioTaskBuffer, &ioTaskControlBlock);
  ioTaskHandle = osThreadCreate(osThread(ioTask), NULL);

  /* definition and creation of serialCmdTask */
  osThreadStaticDef(serialCmdTask, sct_SerialCmdTask, osPriorityNormal, 0, 512, serialCmdTaskBuffer, &serialCmdTaskControlBlock);
  serialCmdTaskHandle = osThreadCreate(osThread(serialCmdTask), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  iot_init_data.pps_out_htim = &htim1;
  iot_init_data.pps_out_channel = TIM_CHANNEL_3;
  iot_init_data.pps_dir_gpio_port = CSM_1PPS_DIR_GPIO_Port;
  iot_init_data.pps_dir_gpio_pin = CSM_1PPS_DIR_Pin;
  iot_init_data.xchange_1pps_gpio_pin = XCHANGE_1PPS_Pin;
  iot_init_data.xchange_1pps_gpio_irq = XCHANGE_1PPS_EXTI_IRQn;
  iot_init_data.adc_device = ADC1;
  iot_init_data.adc_dma_device = DMA2;
  iot_init_data.adc_dma_channel = LL_DMA_CHANNEL_3;
  iot_init_data.adc_semaphore = iotAdcSemaphoreHandle;
  iot_init_data.gpi_signals[iot_gpi_pwr_btn_n].port = PWR_BTN_N_GPIO_Port;
  iot_init_data.gpi_signals[iot_gpi_pwr_btn_n].pin = PWR_BTN_N_Pin;
  strncpy(iot_init_data.gpi_signals[iot_gpi_pwr_btn_n].name , "POWER_BUTTON_N", IOT_MAX_STR_LEN - 1);
  iot_init_data.gpi_signals[iot_gpi_pwr_en_zer_n].port = POWER_EN_ZER_EN_N_GPIO_Port;
  iot_init_data.gpi_signals[iot_gpi_pwr_en_zer_n].pin = POWER_EN_ZER_EN_N_Pin;
  strncpy(iot_init_data.gpi_signals[iot_gpi_pwr_en_zer_n].name, "POWER_ENABLE_ZEROISE_N", IOT_MAX_STR_LEN - 1);
  iot_init_data.gpi_signals[iot_gpi_xchange_reset].port = XCHANGE_RESET_GPIO_Port;
  iot_init_data.gpi_signals[iot_gpi_xchange_reset].pin = XCHANGE_RESET_Pin;
  strncpy(iot_init_data.gpi_signals[iot_gpi_xchange_reset].name, "XCHANGE_RESET", IOT_MAX_STR_LEN - 1);
  iot_init_data.gpo_signals[iot_gpo_csm_1pps_dir].port = CSM_1PPS_DIR_GPIO_Port;
  iot_init_data.gpo_signals[iot_gpo_csm_1pps_dir].pin = CSM_1PPS_DIR_Pin;
  strncpy(iot_init_data.gpo_signals[iot_gpo_csm_1pps_dir].name, "CSM_1PPS_DIRECTION", IOT_MAX_STR_LEN - 1);
  iot_init_data.gpo_signals[iot_gpo_som_sys_rst].port = SOM_SYS_RST_GPIO_Port;
  iot_init_data.gpo_signals[iot_gpo_som_sys_rst].pin = SOM_SYS_RST_Pin;
  strncpy(iot_init_data.gpo_signals[iot_gpo_som_sys_rst].name, "SOM_RESET", IOT_MAX_STR_LEN - 1);
  iot_init_data.gpo_signals[iot_gpo_som_sd_boot_en].port = SOM_SD_BOOT_EN_GPIO_Port;
  iot_init_data.gpo_signals[iot_gpo_som_sd_boot_en].pin = SOM_SD_BOOT_EN_Pin;
  strncpy(iot_init_data.gpo_signals[iot_gpo_som_sd_boot_en].name, "SOM_SD_BOOT_ENABLE", IOT_MAX_STR_LEN - 1);
  iot_InitTask(iot_init_data);

  sbt_init_data.no_uarts					= 1;
  sbt_init_data.uarts[0].huart 				= USART2;
  sbt_init_data.uarts[0].dma_device 		= DMA1;
  sbt_init_data.uarts[0].rx_dma_channel 	= LL_DMA_CHANNEL_6;
  sbt_init_data.uarts[0].rx_data_queue	 	= serialCmdRxDataHandle;
  sbt_init_data.uarts[0].tx_dma_channel 	= LL_DMA_CHANNEL_7;
  sbt_init_data.uarts[0].tx_semaphore 		= uart2TxSemaphoreHandle;
  sbt_init_data.uarts[0].tx_data_queue 		= serialCmdTxDataHandle;
  sbt_InitTask(sbt_init_data);

  sct_init_data.tx_data_queue	= serialCmdTxDataHandle;
  sct_init_data.rx_data_queue	= serialCmdRxDataHandle;
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

  /** Configure LSE Drive Capability
  */
  HAL_PWR_EnableBkUpAccess();
  __HAL_RCC_LSEDRIVE_CONFIG(RCC_LSEDRIVE_LOW);
  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_LSE|RCC_OSCILLATORTYPE_MSI;
  RCC_OscInitStruct.LSEState = RCC_LSE_ON;
  RCC_OscInitStruct.MSIState = RCC_MSI_ON;
  RCC_OscInitStruct.MSICalibrationValue = 0;
  RCC_OscInitStruct.MSIClockRange = RCC_MSIRANGE_7;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_MSI;
  RCC_OscInitStruct.PLL.PLLM = 1;
  RCC_OscInitStruct.PLL.PLLN = 20;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV7;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
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

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USART1|RCC_PERIPHCLK_USART2
                              |RCC_PERIPHCLK_ADC;
  PeriphClkInit.Usart1ClockSelection = RCC_USART1CLKSOURCE_PCLK2;
  PeriphClkInit.Usart2ClockSelection = RCC_USART2CLKSOURCE_PCLK1;
  PeriphClkInit.AdcClockSelection = RCC_ADCCLKSOURCE_PLLSAI1;
  PeriphClkInit.PLLSAI1.PLLSAI1Source = RCC_PLLSOURCE_MSI;
  PeriphClkInit.PLLSAI1.PLLSAI1M = 1;
  PeriphClkInit.PLLSAI1.PLLSAI1N = 8;
  PeriphClkInit.PLLSAI1.PLLSAI1P = RCC_PLLP_DIV7;
  PeriphClkInit.PLLSAI1.PLLSAI1Q = RCC_PLLQ_DIV2;
  PeriphClkInit.PLLSAI1.PLLSAI1R = RCC_PLLR_DIV2;
  PeriphClkInit.PLLSAI1.PLLSAI1ClockOut = RCC_PLLSAI1_ADC1CLK;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure the main internal regulator output voltage
  */
  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
  {
    Error_Handler();
  }
  /** Enable MSI Auto calibration
  */
  HAL_RCCEx_EnableMSIPLLMode();
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  LL_ADC_InitTypeDef ADC_InitStruct = {0};
  LL_ADC_REG_InitTypeDef ADC_REG_InitStruct = {0};
  LL_ADC_CommonInitTypeDef ADC_CommonInitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_AHB2_GRP1_EnableClock(LL_AHB2_GRP1_PERIPH_ADC);

  LL_AHB2_GRP1_EnableClock(LL_AHB2_GRP1_PERIPH_GPIOA);
  /**ADC1 GPIO Configuration
  PA0   ------> ADC1_IN5
  PA1   ------> ADC1_IN6
  PA3   ------> ADC1_IN8
  PA4   ------> ADC1_IN9
  PA5   ------> ADC1_IN10
  */
  GPIO_InitStruct.Pin = LL_GPIO_PIN_0|LL_GPIO_PIN_1|LL_GPIO_PIN_3|LL_GPIO_PIN_4
                          |LL_GPIO_PIN_5;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* ADC1 DMA Init */

  /* ADC1 Init */
  LL_DMA_SetPeriphRequest(DMA2, LL_DMA_CHANNEL_3, LL_DMA_REQUEST_0);

  LL_DMA_SetDataTransferDirection(DMA2, LL_DMA_CHANNEL_3, LL_DMA_DIRECTION_PERIPH_TO_MEMORY);

  LL_DMA_SetChannelPriorityLevel(DMA2, LL_DMA_CHANNEL_3, LL_DMA_PRIORITY_LOW);

  LL_DMA_SetMode(DMA2, LL_DMA_CHANNEL_3, LL_DMA_MODE_NORMAL);

  LL_DMA_SetPeriphIncMode(DMA2, LL_DMA_CHANNEL_3, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA2, LL_DMA_CHANNEL_3, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA2, LL_DMA_CHANNEL_3, LL_DMA_PDATAALIGN_HALFWORD);

  LL_DMA_SetMemorySize(DMA2, LL_DMA_CHANNEL_3, LL_DMA_MDATAALIGN_HALFWORD);

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */
  /** Common config
  */
  ADC_InitStruct.Resolution = LL_ADC_RESOLUTION_12B;
  ADC_InitStruct.DataAlignment = LL_ADC_DATA_ALIGN_RIGHT;
  ADC_InitStruct.LowPowerMode = LL_ADC_LP_MODE_NONE;
  LL_ADC_Init(ADC1, &ADC_InitStruct);
  ADC_REG_InitStruct.TriggerSource = LL_ADC_REG_TRIG_SOFTWARE;
  ADC_REG_InitStruct.SequencerLength = LL_ADC_REG_SEQ_SCAN_ENABLE_6RANKS;
  ADC_REG_InitStruct.SequencerDiscont = LL_ADC_REG_SEQ_DISCONT_DISABLE;
  ADC_REG_InitStruct.ContinuousMode = LL_ADC_REG_CONV_SINGLE;
  ADC_REG_InitStruct.DMATransfer = LL_ADC_REG_DMA_TRANSFER_LIMITED;
  ADC_REG_InitStruct.Overrun = LL_ADC_REG_OVR_DATA_PRESERVED;
  LL_ADC_REG_Init(ADC1, &ADC_REG_InitStruct);
  LL_ADC_SetCommonPathInternalCh(__LL_ADC_COMMON_INSTANCE(ADC1), LL_ADC_PATH_INTERNAL_VREFINT);

   /* Disable ADC deep power down (enabled by default after reset state) */
   LL_ADC_DisableDeepPowerDown(ADC1);
   /* Enable ADC internal voltage regulator */
   LL_ADC_EnableInternalRegulator(ADC1);
   /* Delay for ADC internal voltage regulator stabilization. */
   /* Compute number of CPU cycles to wait for, from delay in us. */
   /* Note: Variable divided by 2 to compensate partially */
   /* CPU processing cycles (depends on compilation optimization). */
   /* Note: If system core clock frequency is below 200kHz, wait time */
   /* is only a few CPU processing cycles. */
   uint32_t wait_loop_index;
   wait_loop_index = ((LL_ADC_DELAY_INTERNAL_REGUL_STAB_US * (SystemCoreClock / (100000 * 2))) / 10);
   while(wait_loop_index != 0)
     {
   wait_loop_index--;
     }
  ADC_CommonInitStruct.CommonClock = LL_ADC_CLOCK_ASYNC_DIV1;
  LL_ADC_CommonInit(__LL_ADC_COMMON_INSTANCE(ADC1), &ADC_CommonInitStruct);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_1, LL_ADC_CHANNEL_5);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_5, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_CHANNEL_5, LL_ADC_SINGLE_ENDED);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_2, LL_ADC_CHANNEL_6);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_6, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_CHANNEL_6, LL_ADC_SINGLE_ENDED);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_3, LL_ADC_CHANNEL_8);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_8, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_CHANNEL_8, LL_ADC_SINGLE_ENDED);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_4, LL_ADC_CHANNEL_9);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_9, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_CHANNEL_9, LL_ADC_SINGLE_ENDED);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_5, LL_ADC_CHANNEL_10);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_10, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_CHANNEL_10, LL_ADC_SINGLE_ENDED);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_6, LL_ADC_PATH_INTERNAL_VREFINT);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_PATH_INTERNAL_VREFINT, LL_ADC_SAMPLINGTIME_92CYCLES_5);
  LL_ADC_SetChannelSingleDiff(ADC1, LL_ADC_PATH_INTERNAL_VREFINT, LL_ADC_SINGLE_ENDED);
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 8000;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 10000;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 100;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_ENABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.BreakFilter = 0;
  sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
  sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
  sBreakDeadTimeConfig.Break2Filter = 0;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */
  HAL_TIM_MspPostInit(&htim1);

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

  LL_USART_InitTypeDef USART_InitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_USART2);

  LL_AHB2_GRP1_EnableClock(LL_AHB2_GRP1_PERIPH_GPIOA);
  /**USART2 GPIO Configuration
  PA2   ------> USART2_TX
  PA15 (JTDI)   ------> USART2_RX
  */
  GPIO_InitStruct.Pin = LL_GPIO_PIN_2;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_7;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LL_GPIO_PIN_15;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_3;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USART2 DMA Init */

  /* USART2_RX Init */
  LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_6, LL_DMA_REQUEST_2);

  LL_DMA_SetDataTransferDirection(DMA1, LL_DMA_CHANNEL_6, LL_DMA_DIRECTION_PERIPH_TO_MEMORY);

  LL_DMA_SetChannelPriorityLevel(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PRIORITY_HIGH);

  LL_DMA_SetMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MODE_CIRCULAR);

  LL_DMA_SetPeriphIncMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA1, LL_DMA_CHANNEL_6, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA1, LL_DMA_CHANNEL_6, LL_DMA_MDATAALIGN_BYTE);

  /* USART2_TX Init */
  LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_7, LL_DMA_REQUEST_2);

  LL_DMA_SetDataTransferDirection(DMA1, LL_DMA_CHANNEL_7, LL_DMA_DIRECTION_MEMORY_TO_PERIPH);

  LL_DMA_SetChannelPriorityLevel(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PRIORITY_MEDIUM);

  LL_DMA_SetMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MODE_NORMAL);

  LL_DMA_SetPeriphIncMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA1, LL_DMA_CHANNEL_7, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA1, LL_DMA_CHANNEL_7, LL_DMA_MDATAALIGN_BYTE);

  /* USART2 interrupt Init */
  NVIC_SetPriority(USART2_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(USART2_IRQn);

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  USART_InitStruct.BaudRate = 115200;
  USART_InitStruct.DataWidth = LL_USART_DATAWIDTH_8B;
  USART_InitStruct.StopBits = LL_USART_STOPBITS_1;
  USART_InitStruct.Parity = LL_USART_PARITY_NONE;
  USART_InitStruct.TransferDirection = LL_USART_DIRECTION_TX_RX;
  USART_InitStruct.HardwareFlowControl = LL_USART_HWCONTROL_NONE;
  USART_InitStruct.OverSampling = LL_USART_OVERSAMPLING_16;
  LL_USART_Init(USART2, &USART_InitStruct);
  LL_USART_ConfigAsyncMode(USART2);
  LL_USART_Enable(USART2);
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* Init with LL driver */
  /* DMA controller clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_DMA1);
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_DMA2);

  /* DMA interrupt init */
  /* DMA1_Channel4_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
  /* DMA1_Channel5_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);
  /* DMA1_Channel6_IRQn interrupt configuration */
  NVIC_SetPriority(DMA1_Channel6_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA1_Channel6_IRQn);
  /* DMA1_Channel7_IRQn interrupt configuration */
  NVIC_SetPriority(DMA1_Channel7_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA1_Channel7_IRQn);
  /* DMA2_Channel3_IRQn interrupt configuration */
  NVIC_SetPriority(DMA2_Channel3_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA2_Channel3_IRQn);

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
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(CSM_1PPS_DIR_GPIO_Port, CSM_1PPS_DIR_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, LD3_Pin|SOM_SD_BOOT_EN_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(SOM_SYS_RST_GPIO_Port, SOM_SYS_RST_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin : CSM_1PPS_DIR_Pin */
  GPIO_InitStruct.Pin = CSM_1PPS_DIR_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(CSM_1PPS_DIR_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : POWER_EN_ZER_EN_N_Pin */
  GPIO_InitStruct.Pin = POWER_EN_ZER_EN_N_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(POWER_EN_ZER_EN_N_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : XCHANGE_1PPS_Pin */
  GPIO_InitStruct.Pin = XCHANGE_1PPS_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(XCHANGE_1PPS_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : XCHANGE_RESET_Pin PWR_BTN_N_Pin */
  GPIO_InitStruct.Pin = XCHANGE_RESET_Pin|PWR_BTN_N_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : LD3_Pin SOM_SYS_RST_Pin SOM_SD_BOOT_EN_Pin */
  GPIO_InitStruct.Pin = LD3_Pin|SOM_SYS_RST_Pin|SOM_SD_BOOT_EN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI9_5_IRQn, 5, 0);
  HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);

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
    osDelay(1);
  }
  /* USER CODE END 5 */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM15 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM15) {
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
