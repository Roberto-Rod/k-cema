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
#include "lwip.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "serial_buffer_task.h"
#include "serial_cmd_task.h"
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
typedef StaticTask_t osStaticThreadDef_t;
typedef StaticQueue_t osStaticMessageQDef_t;
typedef StaticSemaphore_t osStaticSemaphoreDef_t;
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

I2C_HandleTypeDef hi2c3;

TIM_HandleTypeDef htim6;

/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
uint32_t defaultTaskBuffer[ 256 ];
osStaticThreadDef_t defaultTaskControlBlock;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_mem = &defaultTaskBuffer[0],
  .stack_size = sizeof(defaultTaskBuffer),
  .cb_mem = &defaultTaskControlBlock,
  .cb_size = sizeof(defaultTaskControlBlock),
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for serialBufferTask */
osThreadId_t serialBufferTaskHandle;
uint32_t serialBufferTaskBuffer[ 256 ];
osStaticThreadDef_t serialBufferTaskControlBlock;
const osThreadAttr_t serialBufferTask_attributes = {
  .name = "serialBufferTask",
  .stack_mem = &serialBufferTaskBuffer[0],
  .stack_size = sizeof(serialBufferTaskBuffer),
  .cb_mem = &serialBufferTaskControlBlock,
  .cb_size = sizeof(serialBufferTaskControlBlock),
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for serialCmdTask */
osThreadId_t serialCmdTaskHandle;
uint32_t serialCmdTaskBuffer[ 512 ];
osStaticThreadDef_t serialCmdTaskControlBlock;
const osThreadAttr_t serialCmdTask_attributes = {
  .name = "serialCmdTask",
  .stack_mem = &serialCmdTaskBuffer[0],
  .stack_size = sizeof(serialCmdTaskBuffer),
  .cb_mem = &serialCmdTaskControlBlock,
  .cb_size = sizeof(serialCmdTaskControlBlock),
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for serialCmdRxData */
osMessageQueueId_t serialCmdRxDataHandle;
uint8_t serialCmdRxDataBuffer[ 128 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialCmdRxDataControlBlock;
const osMessageQueueAttr_t serialCmdRxData_attributes = {
  .name = "serialCmdRxData",
  .cb_mem = &serialCmdRxDataControlBlock,
  .cb_size = sizeof(serialCmdRxDataControlBlock),
  .mq_mem = &serialCmdRxDataBuffer,
  .mq_size = sizeof(serialCmdRxDataBuffer)
};
/* Definitions for serialCmdTxData */
osMessageQueueId_t serialCmdTxDataHandle;
uint8_t serialCmdTxDataBuffer[ 1024 * sizeof( uint8_t ) ];
osStaticMessageQDef_t serialCmdTxDataControlBlock;
const osMessageQueueAttr_t serialCmdTxData_attributes = {
  .name = "serialCmdTxData",
  .cb_mem = &serialCmdTxDataControlBlock,
  .cb_size = sizeof(serialCmdTxDataControlBlock),
  .mq_mem = &serialCmdTxDataBuffer,
  .mq_size = sizeof(serialCmdTxDataBuffer)
};
/* Definitions for uart1TxSemaphore */
osSemaphoreId_t uart1TxSemaphoreHandle;
osStaticSemaphoreDef_t uart1TxSemaphoreControlBlock;
const osSemaphoreAttr_t uart1TxSemaphore_attributes = {
  .name = "uart1TxSemaphore",
  .cb_mem = &uart1TxSemaphoreControlBlock,
  .cb_size = sizeof(uart1TxSemaphoreControlBlock),
};
/* Definitions for adc1Semaphore */
osSemaphoreId_t adc1SemaphoreHandle;
osStaticSemaphoreDef_t adc1SemaphoreControlBlock;
const osSemaphoreAttr_t adc1Semaphore_attributes = {
  .name = "adc1Semaphore",
  .cb_mem = &adc1SemaphoreControlBlock,
  .cb_size = sizeof(adc1SemaphoreControlBlock),
};
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_I2C3_Init(void);
static void MX_ADC1_Init(void);
static void MX_ADC2_Init(void);
static void MX_TIM6_Init(void);
void StartDefaultTask(void *argument);
extern void sbt_SerialBufferTask(void *argument);
extern void sct_SerialCmdTask(void *argument);

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
  MX_USART1_UART_Init();
  MX_I2C3_Init();
  MX_ADC1_Init();
  MX_ADC2_Init();
  MX_TIM6_Init();
  /* USER CODE BEGIN 2 */

  /* USER CODE END 2 */

  /* Init scheduler */
  osKernelInitialize();

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* Create the semaphores(s) */
  /* creation of uart1TxSemaphore */
  uart1TxSemaphoreHandle = osSemaphoreNew(1, 1, &uart1TxSemaphore_attributes);

  /* creation of adc1Semaphore */
  adc1SemaphoreHandle = osSemaphoreNew(1, 1, &adc1Semaphore_attributes);

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* creation of serialCmdRxData */
  serialCmdRxDataHandle = osMessageQueueNew (128, sizeof(uint8_t), &serialCmdRxData_attributes);

  /* creation of serialCmdTxData */
  serialCmdTxDataHandle = osMessageQueueNew (1024, sizeof(uint8_t), &serialCmdTxData_attributes);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of serialBufferTask */
  serialBufferTaskHandle = osThreadNew(sbt_SerialBufferTask, NULL, &serialBufferTask_attributes);

  /* creation of serialCmdTask */
  serialCmdTaskHandle = osThreadNew(sct_SerialCmdTask, NULL, &serialCmdTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  sbt_init_data.no_uarts					= 1;
  sbt_init_data.uarts[0].huart 				= USART1;
  sbt_init_data.uarts[0].dma_device 		= DMA2;
  sbt_init_data.uarts[0].rx_dma_stream 		= LL_DMA_STREAM_2;
  sbt_init_data.uarts[0].rx_data_queue	 	= serialCmdRxDataHandle;
  sbt_init_data.uarts[0].tx_dma_stream 		= LL_DMA_STREAM_7;
  sbt_init_data.uarts[0].tx_semaphore 		= uart1TxSemaphoreHandle;
  sbt_init_data.uarts[0].tx_data_queue 		= serialCmdTxDataHandle;
  sbt_InitTask(sbt_init_data);

  sct_init_data.tx_data_queue		= serialCmdTxDataHandle;
  sct_init_data.rx_data_queue		= serialCmdRxDataHandle;
  sct_init_data.i2c_device			= &hi2c3;
  sct_init_data.bit_adc_device 		= ADC1;
  sct_init_data.bit_adc_dma_device  = DMA2;
  sct_init_data.bit_adc_dma_stream 	= LL_DMA_STREAM_0;
  sct_init_data.bit_adc_semaphore 	= adc1SemaphoreHandle;
  sct_init_data.pps_gpio_pin		= PPS_IN_Pin;
  sct_init_data.pps_gpio_irq		= EXTI0_IRQn;
  /* IF path I/O pins... */
  sct_init_data.rx_path_sw_3_a_port	    = RX_PATH_SW_3_A_GPIO_Port;
  sct_init_data.rx_path_sw_3_a_pin	    = RX_PATH_SW_3_A_Pin;
  sct_init_data.rx_path_sw_3_b_port     = RX_PATH_SW_3_B_GPIO_Port;
  sct_init_data.rx_path_sw_3_b_pin      = RX_PATH_SW_3_B_Pin;
  sct_init_data.rx_path_sw_4_a_port     = RX_PATH_SW_4_A_GPIO_Port;
  sct_init_data.rx_path_sw_4_a_pin      = RX_PATH_SW_4_A_Pin;
  sct_init_data.rx_path_sw_4_b_port     = RX_PATH_SW_4_B_GPIO_Port;
  sct_init_data.rx_path_sw_4_b_pin      = RX_PATH_SW_4_B_Pin;
  sct_init_data.rx_path_sw_5_vc_port 	= RX_PATH_SW_5_VC_GPIO_Port;
  sct_init_data.rx_path_sw_5_vc_pin  	= RX_PATH_SW_5_VC_Pin;
  sct_init_data.rx_path_sw_6_vc_port 	= RX_PATH_SW_6_VC_GPIO_Port;
  sct_init_data.rx_path_sw_6_vc_pin  	= RX_PATH_SW_6_VC_Pin;
  /* RF detector resources... */
  sct_init_data.rf_det_adc_device			= ADC2;
  sct_init_data.rf_det_adc_channel			= LL_ADC_CHANNEL_8;
  sct_init_data.rf_det_timer				= &htim6;
  sct_init_data.rx_path_det_en_port			= RX_PATH_DET_EN_GPIO_Port;
  sct_init_data.rx_path_det_en_pin			= RX_PATH_DET_EN_Pin;
  sct_init_data.rx_path_pk_det_dischrg_port	= RX_PATH_PK_DET_DISCHRG_GPIO_Port;
  sct_init_data.rx_path_pk_det_dischrg_pin	= RX_PATH_PK_DET_DISCHRG_Pin;
  /* Loopback I/O signal pairs...*/
  sct_init_data.lb_test_io_pairs[0].pin_a_port = IO_PAIR_1_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[0].pin_a_pin = IO_PAIR_1_A_Pin;
  sct_init_data.lb_test_io_pairs[0].pin_b_port = IO_PAIR_1_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[0].pin_b_pin =IO_PAIR_1_B_Pin ;
  sct_init_data.lb_test_io_pairs[1].pin_a_port = IO_PAIR_2_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[1].pin_a_pin = IO_PAIR_2_A_Pin;
  sct_init_data.lb_test_io_pairs[1].pin_b_port = IO_PAIR_2_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[1].pin_b_pin = IO_PAIR_2_B_Pin;
  sct_init_data.lb_test_io_pairs[2].pin_a_port = IO_PAIR_3_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[2].pin_a_pin = IO_PAIR_3_A_Pin;
  sct_init_data.lb_test_io_pairs[2].pin_b_port = IO_PAIR_3_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[2].pin_b_pin = IO_PAIR_3_B_Pin;
  sct_init_data.lb_test_io_pairs[3].pin_a_port = IO_PAIR_4_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[3].pin_a_pin = IO_PAIR_4_A_Pin;
  sct_init_data.lb_test_io_pairs[3].pin_b_port = IO_PAIR_4_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[3].pin_b_pin = IO_PAIR_4_B_Pin;
  sct_init_data.lb_test_io_pairs[4].pin_a_port = IO_PAIR_5_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[4].pin_a_pin = IO_PAIR_5_A_Pin;
  sct_init_data.lb_test_io_pairs[4].pin_b_port = IO_PAIR_5_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[4].pin_b_pin = IO_PAIR_5_B_Pin;
  sct_init_data.lb_test_io_pairs[5].pin_a_port = IO_PAIR_6_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[5].pin_a_pin = IO_PAIR_6_A_Pin;
  sct_init_data.lb_test_io_pairs[5].pin_b_port = IO_PAIR_6_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[5].pin_b_pin = IO_PAIR_6_B_Pin;
  sct_init_data.lb_test_io_pairs[6].pin_a_port = IO_PAIR_7_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[6].pin_a_pin = IO_PAIR_7_A_Pin;
  sct_init_data.lb_test_io_pairs[6].pin_b_port = IO_PAIR_7_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[6].pin_b_pin = IO_PAIR_7_B_Pin;
  sct_init_data.lb_test_io_pairs[7].pin_a_port = IO_PAIR_8_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[7].pin_a_pin = IO_PAIR_8_A_Pin;
  sct_init_data.lb_test_io_pairs[7].pin_b_port = IO_PAIR_8_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[7].pin_b_pin = IO_PAIR_8_B_Pin;
  sct_init_data.lb_test_io_pairs[8].pin_a_port = IO_PAIR_9_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[8].pin_a_pin = IO_PAIR_9_A_Pin;
  sct_init_data.lb_test_io_pairs[8].pin_b_port = IO_PAIR_9_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[8].pin_b_pin = IO_PAIR_9_B_Pin;
  sct_init_data.lb_test_io_pairs[9].pin_a_port = IO_PAIR_10_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[9].pin_a_pin = IO_PAIR_10_A_Pin;
  sct_init_data.lb_test_io_pairs[9].pin_b_port = IO_PAIR_10_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[9].pin_b_pin = IO_PAIR_10_B_Pin;
  sct_init_data.lb_test_io_pairs[10].pin_a_port = IO_PAIR_11_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[10].pin_a_pin = IO_PAIR_11_A_Pin;
  sct_init_data.lb_test_io_pairs[10].pin_b_port = IO_PAIR_11_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[10].pin_b_pin = IO_PAIR_11_B_Pin;
  sct_init_data.lb_test_io_pairs[11].pin_a_port = IO_PAIR_12_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[11].pin_a_pin = IO_PAIR_12_A_Pin;
  sct_init_data.lb_test_io_pairs[11].pin_b_port = IO_PAIR_12_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[11].pin_b_pin = IO_PAIR_12_B_Pin;
  sct_init_data.lb_test_io_pairs[12].pin_a_port = IO_PAIR_13_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[12].pin_a_pin = IO_PAIR_13_A_Pin;
  sct_init_data.lb_test_io_pairs[12].pin_b_port = IO_PAIR_13_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[12].pin_b_pin = IO_PAIR_13_B_Pin;
  sct_init_data.lb_test_io_pairs[13].pin_a_port = IO_PAIR_14_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[13].pin_a_pin = IO_PAIR_14_A_Pin;
  sct_init_data.lb_test_io_pairs[13].pin_b_port = IO_PAIR_14_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[13].pin_b_pin = IO_PAIR_14_B_Pin;
  sct_init_data.lb_test_io_pairs[14].pin_a_port = IO_PAIR_15_A_GPIO_Port;
  sct_init_data.lb_test_io_pairs[14].pin_a_pin = IO_PAIR_15_A_Pin;
  sct_init_data.lb_test_io_pairs[14].pin_b_port = IO_PAIR_15_B_GPIO_Port;
  sct_init_data.lb_test_io_pairs[14].pin_b_pin = IO_PAIR_15_B_Pin;
  /* GPO Pins... */
  sct_init_data.gpo_pins[0].port	= ETH_PHY_LED_EN_GPIO_Port;
  sct_init_data.gpo_pins[0].pin		= ETH_PHY_LED_EN_Pin;
  strncpy(sct_init_data.gpo_pins[0].name, "ETH_PHY_LED_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[1].port	= RX_PATH_3V3_IF_EN_GPIO_Port;
  sct_init_data.gpo_pins[1].pin		= RX_PATH_3V3_IF_EN_Pin;
  strncpy(sct_init_data.gpo_pins[1].name, "RX_PATH_3V3_IF_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[2].port	= TX_PATH_3V3_TX_EN_GPIO_Port;
  sct_init_data.gpo_pins[2].pin		= TX_PATH_3V3_TX_EN_Pin;
  strncpy(sct_init_data.gpo_pins[2].name, "TX_PATH_3V3_TX_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[3].port	= TX_PATH_5V0_TX_EN_GPIO_Port;
  sct_init_data.gpo_pins[3].pin		= TX_PATH_5V0_TX_EN_Pin;
  strncpy(sct_init_data.gpo_pins[3].name, "TX_PATH_5V0_TX_EN", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  sct_init_data.gpo_pins[4].port	= ETH_PHY_RESET_N_GPIO_Port;
  sct_init_data.gpo_pins[4].pin		= ETH_PHY_RESET_N_Pin;
  strncpy(sct_init_data.gpo_pins[4].name, "ETH_PHY_RESET_N", SCT_GPIO_PIN_NAME_MAX_LEN - 1);
  /* I2C bus to the loop back test board GPIO signal definitions... */
  sct_init_data.lb_i2c_scl_pin_port = I2C_SCL_UUT_GPIO_Port;
  sct_init_data.lb_i2c_scl_pin = I2C_SCL_UUT_Pin;
  sct_init_data.lb_i2c_sda_pin_port = I2C_SDA_UUT_GPIO_Port;
  sct_init_data.lb_i2c_sda_pin = I2C_SDA_UUT_Pin;




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

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_BYPASS;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 25;
  RCC_OscInitStruct.PLL.PLLN = 180;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Activate the Over-Drive mode
  */
  if (HAL_PWREx_EnableOverDrive() != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
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
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_ADC1);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOC);
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
  /**ADC1 GPIO Configuration
  PC0   ------> ADC1_IN10
  PC2   ------> ADC1_IN12
  PC3   ------> ADC1_IN13
  PA3   ------> ADC1_IN3
  PA4   ------> ADC1_IN4
  PA5   ------> ADC1_IN5
  PA6   ------> ADC1_IN6
  */
  GPIO_InitStruct.Pin = LL_GPIO_PIN_0|LL_GPIO_PIN_2|LL_GPIO_PIN_3;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LL_GPIO_PIN_3|LL_GPIO_PIN_4|LL_GPIO_PIN_5|LL_GPIO_PIN_6;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* ADC1 DMA Init */

  /* ADC1 Init */
  LL_DMA_SetChannelSelection(DMA2, LL_DMA_STREAM_0, LL_DMA_CHANNEL_0);

  LL_DMA_SetDataTransferDirection(DMA2, LL_DMA_STREAM_0, LL_DMA_DIRECTION_PERIPH_TO_MEMORY);

  LL_DMA_SetStreamPriorityLevel(DMA2, LL_DMA_STREAM_0, LL_DMA_PRIORITY_LOW);

  LL_DMA_SetMode(DMA2, LL_DMA_STREAM_0, LL_DMA_MODE_NORMAL);

  LL_DMA_SetPeriphIncMode(DMA2, LL_DMA_STREAM_0, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA2, LL_DMA_STREAM_0, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA2, LL_DMA_STREAM_0, LL_DMA_PDATAALIGN_HALFWORD);

  LL_DMA_SetMemorySize(DMA2, LL_DMA_STREAM_0, LL_DMA_MDATAALIGN_HALFWORD);

  LL_DMA_DisableFifoMode(DMA2, LL_DMA_STREAM_0);

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */
  /** Common config
  */
  ADC_InitStruct.Resolution = LL_ADC_RESOLUTION_12B;
  ADC_InitStruct.DataAlignment = LL_ADC_DATA_ALIGN_RIGHT;
  ADC_InitStruct.SequencersScanMode = LL_ADC_SEQ_SCAN_ENABLE;
  LL_ADC_Init(ADC1, &ADC_InitStruct);
  ADC_REG_InitStruct.TriggerSource = LL_ADC_REG_TRIG_SOFTWARE;
  ADC_REG_InitStruct.SequencerLength = LL_ADC_REG_SEQ_SCAN_ENABLE_9RANKS;
  ADC_REG_InitStruct.SequencerDiscont = LL_ADC_REG_SEQ_DISCONT_DISABLE;
  ADC_REG_InitStruct.ContinuousMode = LL_ADC_REG_CONV_SINGLE;
  ADC_REG_InitStruct.DMATransfer = LL_ADC_REG_DMA_TRANSFER_LIMITED;
  LL_ADC_REG_Init(ADC1, &ADC_REG_InitStruct);
  LL_ADC_REG_SetFlagEndOfConversion(ADC1, LL_ADC_REG_FLAG_EOC_UNITARY_CONV);
  ADC_CommonInitStruct.CommonClock = LL_ADC_CLOCK_SYNC_PCLK_DIV4;
  ADC_CommonInitStruct.Multimode = LL_ADC_MULTI_INDEPENDENT;
  LL_ADC_CommonInit(__LL_ADC_COMMON_INSTANCE(ADC1), &ADC_CommonInitStruct);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_1, LL_ADC_CHANNEL_3);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_3, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_2, LL_ADC_CHANNEL_4);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_4, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_3, LL_ADC_CHANNEL_5);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_5, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_4, LL_ADC_CHANNEL_6);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_6, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_5, LL_ADC_CHANNEL_10);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_10, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_6, LL_ADC_CHANNEL_12);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_12, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_7, LL_ADC_CHANNEL_13);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_13, LL_ADC_SAMPLINGTIME_112CYCLES);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_8, LL_ADC_CHANNEL_TEMPSENSOR);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_TEMPSENSOR, LL_ADC_SAMPLINGTIME_112CYCLES);
  LL_ADC_SetCommonPathInternalCh(__LL_ADC_COMMON_INSTANCE(ADC1), LL_ADC_PATH_INTERNAL_TEMPSENSOR);
  /** Configure Regular Channel
  */
  LL_ADC_REG_SetSequencerRanks(ADC1, LL_ADC_REG_RANK_9, LL_ADC_CHANNEL_VREFINT);
  LL_ADC_SetChannelSamplingTime(ADC1, LL_ADC_CHANNEL_VREFINT, LL_ADC_SAMPLINGTIME_112CYCLES);
  LL_ADC_SetCommonPathInternalCh(__LL_ADC_COMMON_INSTANCE(ADC1), LL_ADC_PATH_INTERNAL_VREFINT);
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief ADC2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC2_Init(void)
{

  /* USER CODE BEGIN ADC2_Init 0 */

  /* USER CODE END ADC2_Init 0 */

  LL_ADC_InitTypeDef ADC_InitStruct = {0};
  LL_ADC_REG_InitTypeDef ADC_REG_InitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_ADC2);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOB);
  /**ADC2 GPIO Configuration
  PB0   ------> ADC2_IN8
  */
  GPIO_InitStruct.Pin = LL_GPIO_PIN_0;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ANALOG;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  LL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USER CODE BEGIN ADC2_Init 1 */

  /* USER CODE END ADC2_Init 1 */
  /** Common config
  */
  ADC_InitStruct.Resolution = LL_ADC_RESOLUTION_12B;
  ADC_InitStruct.DataAlignment = LL_ADC_DATA_ALIGN_RIGHT;
  ADC_InitStruct.SequencersScanMode = LL_ADC_SEQ_SCAN_ENABLE;
  LL_ADC_Init(ADC2, &ADC_InitStruct);
  ADC_REG_InitStruct.TriggerSource = LL_ADC_REG_TRIG_SOFTWARE;
  ADC_REG_InitStruct.SequencerLength = LL_ADC_REG_SEQ_SCAN_DISABLE;
  ADC_REG_InitStruct.SequencerDiscont = LL_ADC_REG_SEQ_DISCONT_DISABLE;
  ADC_REG_InitStruct.ContinuousMode = LL_ADC_REG_CONV_SINGLE;
  ADC_REG_InitStruct.DMATransfer = LL_ADC_REG_DMA_TRANSFER_NONE;
  LL_ADC_REG_Init(ADC2, &ADC_REG_InitStruct);
  LL_ADC_REG_SetFlagEndOfConversion(ADC2, LL_ADC_REG_FLAG_EOC_UNITARY_CONV);
  /** Configure Regular Channel  */
  LL_ADC_REG_SetSequencerRanks(ADC2, LL_ADC_REG_RANK_1, LL_ADC_CHANNEL_8);
  LL_ADC_SetChannelSamplingTime(ADC2, LL_ADC_CHANNEL_8, LL_ADC_SAMPLINGTIME_112CYCLES);
  /* USER CODE BEGIN ADC2_Init 2 */

  /* USER CODE END ADC2_Init 2 */

}

/**
  * @brief I2C3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C3_Init(void)
{

  /* USER CODE BEGIN I2C3_Init 0 */

  /* USER CODE END I2C3_Init 0 */

  /* USER CODE BEGIN I2C3_Init 1 */

  /* USER CODE END I2C3_Init 1 */
  hi2c3.Instance = I2C3;
  hi2c3.Init.ClockSpeed = 400000;
  hi2c3.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c3.Init.OwnAddress1 = 0;
  hi2c3.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c3.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c3.Init.OwnAddress2 = 0;
  hi2c3.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c3.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c3) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Analogue filter
  */
  if (HAL_I2CEx_ConfigAnalogFilter(&hi2c3, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure Digital filter
  */
  if (HAL_I2CEx_ConfigDigitalFilter(&hi2c3, 0) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C3_Init 2 */

  /* USER CODE END I2C3_Init 2 */

}

/**
  * @brief TIM6 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM6_Init(void)
{

  /* USER CODE BEGIN TIM6_Init 0 */

  /* USER CODE END TIM6_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM6_Init 1 */

  /* USER CODE END TIM6_Init 1 */
  htim6.Instance = TIM6;
  htim6.Init.Prescaler = 9000;
  htim6.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim6.Init.Period = 65535;
  htim6.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim6) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim6, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM6_Init 2 */
  NVIC_EnableIRQ(TIM6_DAC_IRQn);
  /* USER CODE END TIM6_Init 2 */

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

  LL_USART_InitTypeDef USART_InitStruct = {0};

  LL_GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Peripheral clock enable */
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_USART1);

  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
  /**USART1 GPIO Configuration
  PA9   ------> USART1_TX
  PA10   ------> USART1_RX
  */
  GPIO_InitStruct.Pin = LL_GPIO_PIN_9|LL_GPIO_PIN_10;
  GPIO_InitStruct.Mode = LL_GPIO_MODE_ALTERNATE;
  GPIO_InitStruct.Speed = LL_GPIO_SPEED_FREQ_VERY_HIGH;
  GPIO_InitStruct.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStruct.Pull = LL_GPIO_PULL_NO;
  GPIO_InitStruct.Alternate = LL_GPIO_AF_7;
  LL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USART1 DMA Init */

  /* USART1_TX Init */
  LL_DMA_SetChannelSelection(DMA2, LL_DMA_STREAM_7, LL_DMA_CHANNEL_4);

  LL_DMA_SetDataTransferDirection(DMA2, LL_DMA_STREAM_7, LL_DMA_DIRECTION_MEMORY_TO_PERIPH);

  LL_DMA_SetStreamPriorityLevel(DMA2, LL_DMA_STREAM_7, LL_DMA_PRIORITY_LOW);

  LL_DMA_SetMode(DMA2, LL_DMA_STREAM_7, LL_DMA_MODE_NORMAL);

  LL_DMA_SetPeriphIncMode(DMA2, LL_DMA_STREAM_7, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA2, LL_DMA_STREAM_7, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA2, LL_DMA_STREAM_7, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA2, LL_DMA_STREAM_7, LL_DMA_MDATAALIGN_BYTE);

  LL_DMA_DisableFifoMode(DMA2, LL_DMA_STREAM_7);

  /* USART1_RX Init */
  LL_DMA_SetChannelSelection(DMA2, LL_DMA_STREAM_2, LL_DMA_CHANNEL_4);

  LL_DMA_SetDataTransferDirection(DMA2, LL_DMA_STREAM_2, LL_DMA_DIRECTION_PERIPH_TO_MEMORY);

  LL_DMA_SetStreamPriorityLevel(DMA2, LL_DMA_STREAM_2, LL_DMA_PRIORITY_HIGH);

  LL_DMA_SetMode(DMA2, LL_DMA_STREAM_2, LL_DMA_MODE_CIRCULAR);

  LL_DMA_SetPeriphIncMode(DMA2, LL_DMA_STREAM_2, LL_DMA_PERIPH_NOINCREMENT);

  LL_DMA_SetMemoryIncMode(DMA2, LL_DMA_STREAM_2, LL_DMA_MEMORY_INCREMENT);

  LL_DMA_SetPeriphSize(DMA2, LL_DMA_STREAM_2, LL_DMA_PDATAALIGN_BYTE);

  LL_DMA_SetMemorySize(DMA2, LL_DMA_STREAM_2, LL_DMA_MDATAALIGN_BYTE);

  LL_DMA_DisableFifoMode(DMA2, LL_DMA_STREAM_2);

  /* USART1 interrupt Init */
  NVIC_SetPriority(USART1_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(USART1_IRQn);

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  USART_InitStruct.BaudRate = 115200;
  USART_InitStruct.DataWidth = LL_USART_DATAWIDTH_8B;
  USART_InitStruct.StopBits = LL_USART_STOPBITS_1;
  USART_InitStruct.Parity = LL_USART_PARITY_NONE;
  USART_InitStruct.TransferDirection = LL_USART_DIRECTION_TX_RX;
  USART_InitStruct.HardwareFlowControl = LL_USART_HWCONTROL_NONE;
  USART_InitStruct.OverSampling = LL_USART_OVERSAMPLING_16;
  LL_USART_Init(USART1, &USART_InitStruct);
  LL_USART_ConfigAsyncMode(USART1);
  LL_USART_Enable(USART1);
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* Init with LL driver */
  /* DMA controller clock enable */
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_DMA2);

  /* DMA interrupt init */
  /* DMA2_Stream0_IRQn interrupt configuration */
  NVIC_SetPriority(DMA2_Stream0_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA2_Stream0_IRQn);
  /* DMA2_Stream2_IRQn interrupt configuration */
  NVIC_SetPriority(DMA2_Stream2_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA2_Stream2_IRQn);
  /* DMA2_Stream7_IRQn interrupt configuration */
  NVIC_SetPriority(DMA2_Stream7_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(),5, 0));
  NVIC_EnableIRQ(DMA2_Stream7_IRQn);

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
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOE, IO_PAIR_9_A_Pin|IO_PAIR_8_A_Pin|IO_PAIR_10_A_Pin|IO_PAIR_14_A_Pin
                          |IO_PAIR_13_A_Pin|RX_PATH_SW_3_B_Pin|RX_PATH_SW_3_A_Pin|RX_PATH_SW_4_A_Pin
                          |RX_PATH_SW_4_B_Pin|IO_PAIR_12_A_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, ETH_PHY_LED_EN_Pin|ETH_PHY_RESET_N_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, RX_PATH_3V3_IF_EN_Pin|MCU_LED_Pin|RX_PATH_PK_DET_DISCHRG_Pin|IO_PAIR_3_A_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, I2C_SCL_UUT_Pin|TX_PATH_3V3_TX_EN_Pin|TX_PATH_5V0_TX_EN_Pin|RX_PATH_DET_EN_Pin
                          |RX_PATH_SW_5_VC_Pin|RX_PATH_SW_6_VC_Pin|IO_PAIR_6_A_Pin|IO_PAIR_5_A_Pin
                          |IO_PAIR_7_A_Pin|IO_PAIR_15_A_Pin|I2C_SDA_UUT_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, IO_PAIR_11_A_Pin|IO_PAIR_1_A_Pin|IO_PAIR_2_A_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(IO_PAIR_4_A_GPIO_Port, IO_PAIR_4_A_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : IO_PAIR_9_B_Pin IO_PAIR_13_B_Pin IO_PAIR_14_B_Pin IO_PAIR_15_B_Pin
                           IO_PAIR_12_B_Pin IO_PAIR_6_B_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_9_B_Pin|IO_PAIR_13_B_Pin|IO_PAIR_14_B_Pin|IO_PAIR_15_B_Pin
                          |IO_PAIR_12_B_Pin|IO_PAIR_6_B_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

  /*Configure GPIO pins : IO_PAIR_9_A_Pin IO_PAIR_8_A_Pin IO_PAIR_10_A_Pin IO_PAIR_14_A_Pin
                           IO_PAIR_13_A_Pin RX_PATH_SW_3_B_Pin RX_PATH_SW_3_A_Pin RX_PATH_SW_4_A_Pin
                           RX_PATH_SW_4_B_Pin IO_PAIR_12_A_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_9_A_Pin|IO_PAIR_8_A_Pin|IO_PAIR_10_A_Pin|IO_PAIR_14_A_Pin
                          |IO_PAIR_13_A_Pin|RX_PATH_SW_3_B_Pin|RX_PATH_SW_3_A_Pin|RX_PATH_SW_4_A_Pin
                          |RX_PATH_SW_4_B_Pin|IO_PAIR_12_A_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

  /*Configure GPIO pin : PPS_IN_Pin */
  GPIO_InitStruct.Pin = PPS_IN_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(PPS_IN_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : ETH_PHY_LED_EN_Pin RX_PATH_3V3_IF_EN_Pin MCU_LED_Pin RX_PATH_PK_DET_DISCHRG_Pin
                           IO_PAIR_3_A_Pin ETH_PHY_RESET_N_Pin */
  GPIO_InitStruct.Pin = ETH_PHY_LED_EN_Pin|RX_PATH_3V3_IF_EN_Pin|MCU_LED_Pin|RX_PATH_PK_DET_DISCHRG_Pin
                          |IO_PAIR_3_A_Pin|ETH_PHY_RESET_N_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : IO_PAIR_11_B_Pin IO_PAIR_2_B_Pin IO_PAIR_7_B_Pin IO_PAIR_5_B_Pin
                           IO_PAIR_4_B_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_11_B_Pin|IO_PAIR_2_B_Pin|IO_PAIR_7_B_Pin|IO_PAIR_5_B_Pin
                          |IO_PAIR_4_B_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pins : I2C_SCL_UUT_Pin TX_PATH_3V3_TX_EN_Pin TX_PATH_5V0_TX_EN_Pin RX_PATH_DET_EN_Pin
                           RX_PATH_SW_5_VC_Pin RX_PATH_SW_6_VC_Pin IO_PAIR_6_A_Pin IO_PAIR_5_A_Pin
                           IO_PAIR_7_A_Pin IO_PAIR_15_A_Pin */
  GPIO_InitStruct.Pin = I2C_SCL_UUT_Pin|TX_PATH_3V3_TX_EN_Pin|TX_PATH_5V0_TX_EN_Pin|RX_PATH_DET_EN_Pin
                          |RX_PATH_SW_5_VC_Pin|RX_PATH_SW_6_VC_Pin|IO_PAIR_6_A_Pin|IO_PAIR_5_A_Pin
                          |IO_PAIR_7_A_Pin|IO_PAIR_15_A_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pins : IO_PAIR_8_B_Pin IO_PAIR_10_B_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_8_B_Pin|IO_PAIR_10_B_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : IO_PAIR_11_A_Pin IO_PAIR_1_A_Pin IO_PAIR_2_A_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_11_A_Pin|IO_PAIR_1_A_Pin|IO_PAIR_2_A_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : IO_PAIR_1_B_Pin IO_PAIR_3_B_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_1_B_Pin|IO_PAIR_3_B_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : IO_PAIR_4_A_Pin */
  GPIO_InitStruct.Pin = IO_PAIR_4_A_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(IO_PAIR_4_A_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : I2C_SDA_UUT_Pin */
  GPIO_InitStruct.Pin = I2C_SDA_UUT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_OD;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(I2C_SDA_UUT_GPIO_Port, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI0_IRQn, 5, 0);
  HAL_NVIC_EnableIRQ(EXTI0_IRQn);

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
void StartDefaultTask(void *argument)
{
  /* init code for LWIP */
  MX_LWIP_Init();
  /* USER CODE BEGIN 5 */
  /* Infinite loop */
  for(;;)
  {
	osDelay(1000);
	HAL_GPIO_TogglePin(MCU_LED_GPIO_Port, MCU_LED_Pin);
  }
  /* USER CODE END 5 */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM14 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM14) {
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
