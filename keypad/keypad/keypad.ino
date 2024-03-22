/****************************************************************************/
/*
* Copyright 2020 Kirintec Ltd. All rights reserved.
*
* @file keypad.ino
*
* This sketch provides functionality for testing a KT-000-0147-00 K-CEMA 
* Active Keypad PCB.  A spring pin conector system should be used to connect
* the Nano to the single-piece connector pads on the KT-000-0147-00 board, J1
* 
* Board-to-board connections:
* 
* Nano  ->  KT-000-0147-00 J1

* GND   ->  1
* D2    ->  2
* D3    ->  3
* D4    ->  4
* D5    ->  5
* D6    ->  6
* GND   ->  7
* A5    ->  8 (I2C SCL, pull-up to 5V with 10 kOhm resistor)
* A4    ->  9 (I2C SDA, pull-up to 5V with 10 kOhm resistor)
* 5V    ->  10
* 
* Project   : K-CEMA
*
* Build instructions: Build and upload to Arduino Nano using Arduino IDE.
*                     Requires the Adafruit_MCP23017 library to be installed  
*                     and Adafruit_MCP23017.h modified to make the 
*                     writeRegister() member function public
*
****************************************************************************/
#include <Adafruit_MCP23017.h>

/*****************************************************************************
*
* Definitions
*
*****************************************************************************/
#define MCP0_I2C_ADDR     0
#define MCP1_I2C_ADDR     1
#define NO_LEDS           30
#define SERIAL_BAUD_RATE  115200
#define LOOP_DELAY_MS     1000
#define I2C_RESET_N_PIN   2
#define PWR_BTN_PIN       3
#define BTN0_PIN          4
#define BTN1_PIN          5
#define BTN2_PIN          6
#define ESC               27
#define CLS               "[2J"  /* Clear screen */
#define HOME              "[H"   /* Move cursor to top corner */
#define TITLE             "KT-000-0147-00 Test Utility - V1.0.0"

/*****************************************************************************
*
* Datatypes
*
*****************************************************************************/
typedef enum
{
  lc_off = 0,
  lc_green,
  lc_red,
  lc_yellow
}led_colours_t;

typedef struct
{
  uint8_t     i2c_addr;
  led_colours_t  colour;
  uint16_t    pin;
}led_t;

/*****************************************************************************
*
* Global Variables
*
*****************************************************************************/
led_t board_leds[NO_LEDS] = {
  {MCP0_I2C_ADDR, lc_green, 6U},
  {MCP0_I2C_ADDR, lc_yellow, 5U},
  {MCP0_I2C_ADDR, lc_red, 4U},
  {MCP0_I2C_ADDR, lc_green, 10U},
  {MCP0_I2C_ADDR, lc_yellow, 9U},
  {MCP0_I2C_ADDR, lc_red, 8U},
  {MCP1_I2C_ADDR, lc_green, 14U},
  {MCP1_I2C_ADDR, lc_yellow, 13U},
  {MCP1_I2C_ADDR, lc_red, 12U},
  {MCP1_I2C_ADDR, lc_green, 2U},
  {MCP1_I2C_ADDR, lc_yellow, 1U},
  {MCP1_I2C_ADDR, lc_red, 0U},
  {MCP0_I2C_ADDR, lc_green, 2U},
  {MCP0_I2C_ADDR, lc_yellow, 1U},
  {MCP0_I2C_ADDR, lc_red, 3U},
  {MCP0_I2C_ADDR, lc_green, 14U},
  {MCP0_I2C_ADDR, lc_yellow, 15U},
  {MCP0_I2C_ADDR, lc_red, 0U},
  {MCP0_I2C_ADDR, lc_green, 11U},
  {MCP0_I2C_ADDR, lc_yellow, 12U},
  {MCP0_I2C_ADDR, lc_red, 13U},
  {MCP1_I2C_ADDR, lc_green, 10U},
  {MCP1_I2C_ADDR, lc_yellow, 9U},
  {MCP1_I2C_ADDR, lc_red, 11U},
  {MCP1_I2C_ADDR, lc_green, 7U},
  {MCP1_I2C_ADDR, lc_yellow, 6U},
  {MCP1_I2C_ADDR, lc_red, 8U},
  {MCP1_I2C_ADDR, lc_green, 4U},
  {MCP1_I2C_ADDR, lc_yellow, 3U},
  {MCP1_I2C_ADDR, lc_red, 5U}
};

Adafruit_MCP23017 mcp0;
Adafruit_MCP23017 mcp1;

/*****************************************************************************/
/**
* Arduino sketch main setup() function, performs initialisation tasks that are
* run once at start of execution
*
* @param none
* @return none
*
******************************************************************************/
void setup() 
{    
  /* Deassert the active-low reset signal to the GPIO expanders */
  pinMode(I2C_RESET_N_PIN, OUTPUT);
  digitalWrite(I2C_RESET_N_PIN, HIGH);

  /* Initialise the button input pins */
  pinMode(PWR_BTN_PIN, INPUT_PULLUP);
  pinMode(BTN0_PIN, INPUT_PULLUP);
  pinMode(BTN1_PIN, INPUT_PULLUP);
  pinMode(BTN2_PIN, INPUT_PULLUP);

  /* Initialise serial port */
  Serial.begin(SERIAL_BAUD_RATE);
}

/*****************************************************************************/
/**
* Arduino sketch main loop() function
*
* @param none
* @return none
*
******************************************************************************/
void loop() 
{
  static led_colours_t current_colour = lc_green;
  uint32_t start_time = millis();
  uint32_t end_time = 0U;

  /* Calling set_leds() each iteration as there is no detection of when the 
   *  KT-00-0147-00 board is connected */
  setup_leds();
  set_all_leds(current_colour);

  current_colour = current_colour + 1;
  if (current_colour > lc_yellow) 
  {
    current_colour = lc_off;
  }
  
  /* Print button state to the serial terminal */
  Serial.write(27);
  Serial.print(CLS);
  Serial.write(27);
  Serial.print(HOME);
  Serial.println(TITLE);
  Serial.print("PWR_BTN:\t");
  Serial.println(digitalRead(PWR_BTN_PIN));
  Serial.print("BTN0:\t\t");
  Serial.println(digitalRead(BTN0_PIN));
  Serial.print("BTN1:\t\t");
  Serial.println(digitalRead(BTN1_PIN));
  Serial.print("BTN2:\t\t");
  Serial.println(digitalRead(BTN2_PIN));

  Serial.print("Run-time:\t");
  Serial.print(start_time / 1000U);
  Serial.println(" seconds");

  end_time = millis();

  delay(LOOP_DELAY_MS - (end_time - start_time));
}


/*****************************************************************************/
/**
* Initialises the MCP23017 devices with all GPIO pinst set as outputs, set 
* IODIRx bits to zero.  Set the initial state of all LEDs to off, OLATx bits 
* HIGH
*
* @param none
* @return none
*
******************************************************************************/
void setup_leds(void)
{
  /* Initialise the 2x MC{23017 device instances */
  mcp0.begin(MCP0_I2C_ADDR); 
  mcp1.begin(MCP1_I2C_ADDR); 
  
  /* Set all pins as outputs and all LEDs off */
  mcp0.writeRegister(MCP23017_IODIRA, 0x00U);
  mcp0.writeRegister(MCP23017_IODIRB, 0x00U);
  mcp0.writeRegister(MCP23017_OLATA, 0x07FU);
  mcp0.writeRegister(MCP23017_OLATB, 0x0FFU);

  mcp1.writeRegister(MCP23017_IODIRA, 0x00U);
  mcp1.writeRegister(MCP23017_IODIRB, 0x00U);
  mcp1.writeRegister(MCP23017_OLATA, 0x0FFU);
  mcp1.writeRegister(MCP23017_OLATB, 0x0FFU); 
}


/*****************************************************************************/
/**
* Sets all the LEDs to the specified colour or off, LEDs are off when output
* is HIGH, function starts with all LEDs off and then determines which ones
* need to be turned on by iterating through list of board LEDs
*
* @param colour one of ld_Colours_t enumerated values
* @return none
*
******************************************************************************/
void set_all_leds(led_colours_t colour)
{
  uint8_t mcp0_olata = 0x7FU;  /* All LEDs off */
  uint8_t mcp0_olatb = 0xFFU;
  uint8_t mcp1_olata = 0xFFU;
  uint8_t mcp1_olatb = 0xFFU;
  uint16_t dev0_gpo = 0xFF7FU;
  uint16_t dev1_gpo = 0xFFFFU;
  int16_t i = 0;

  if (colour != lc_off)
  {
    for (i = 0; i < NO_LEDS; ++i)
    {
      if ((board_leds[i].colour == colour) &&
        (board_leds[i].i2c_addr == MCP0_I2C_ADDR))
      {
        dev0_gpo &= (~(1 << board_leds[i].pin));
      }
      else if ((board_leds[i].colour == colour) &&
          (board_leds[i].i2c_addr == MCP1_I2C_ADDR))
      {
        dev1_gpo &= (~(1 << board_leds[i].pin));
      }
      else
      {
      }
    }

    mcp0_olata = (uint8_t)(dev0_gpo & 0xFFU);
    mcp0_olatb = (uint8_t)((dev0_gpo >> 8) & 0xFFU);

    mcp1_olata = (uint8_t)(dev1_gpo & 0xFFU);
    mcp1_olatb = (uint8_t)((dev1_gpo >> 8) & 0xFFU);
  }

  mcp0.writeRegister(MCP23017_OLATA, mcp0_olata);
  mcp0.writeRegister(MCP23017_OLATB, mcp0_olatb);
  
  mcp1.writeRegister(MCP23017_OLATA, mcp1_olata);
  mcp1.writeRegister(MCP23017_OLATB, mcp1_olatb);
}
