////////////////////////////////////////////////////////////////////////////////
//
// Copyright 2020 Kirintec Ltd. All rights reserved.
//
// This sketch reads the MAC address from a Microchip 24AA025E48 I2C EEPROM
// with pre-programmed EUI-48 node identity.
//
// The read EUI-48 MAC address value is printed to the serial port so it can
// be viewed using the Arduino IDE Serial Monitor or a terminal program
// such as HyperTerminal.  The serial baud rate is 115200.
//
// The sketch will work on an Arduino Uno or Nano with the following 
// assumptions:
// - the 24AA025E48 I2C bus is connected to the Pins A4 (SDA) and A5 (SCL)
// - the 24AA025E48 A[2:0] pins are all connected to GND so that the device
//   7-bit I2C address is 0x50
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <Wire.h>

////////////////////////////////////////////////////////////////////////////////
// Dwfinitions and constants
////////////////////////////////////////////////////////////////////////////////
#define I2C_ADDRESS           0x50
#define MAC_MEM_ADDRESS       0xFAU
#define MAC_ADDRESS_BYTE_LEN  6U
#define SERIAL_BAUD_RATE      115200

////////////////////////////////////////////////////////////////////////////////
// Default sketch setup() function - as this sketch only executes once all of 
// the processing occurs with this function
////////////////////////////////////////////////////////////////////////////////
void setup() {
  byte mac[MAC_ADDRESS_BYTE_LEN] = {0x00U}; 
  char tmp_buf[32];
  unsigned int i;

  // Start I2C Wire drive in master mode
  Wire.begin();     
  // Initialise serial port
  Serial.begin(SERIAL_BAUD_RATE);
  
  // Read MAC address from 24AA025E48 ROM and print to serial port
  Serial.println("Reading MAC address from ROM...");

  for (i = 0U; i < MAC_ADDRESS_BYTE_LEN; i++) {
    mac[i] = read_register(MAC_MEM_ADDRESS + i);  
  }
   
  sprintf(tmp_buf, "MAC Address: %02X:%02X:%02X:%02X:%02X:%02X", 
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.println(tmp_buf);
}

////////////////////////////////////////////////////////////////////////////////
// Default sketch loop() function  - as this sketch only executes once all of 
// the processing occurs with the setup() function
////////////////////////////////////////////////////////////////////////////////
void loop() {
  // Do nothing
}

////////////////////////////////////////////////////////////////////////////////
// Read a byte from the specified memory address and return it
////////////////////////////////////////////////////////////////////////////////
byte read_register(byte mem_addr) {  
  // Write out the device memory address to read
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.write(mem_addr); 
  Wire.endTransmission();

  // Read byte from I2C bus
  Wire.requestFrom(I2C_ADDRESS, 1); 
  
  // Wait for byte read to copmplete
  while(!Wire.available())  {  
  }

  return Wire.read();
} 
