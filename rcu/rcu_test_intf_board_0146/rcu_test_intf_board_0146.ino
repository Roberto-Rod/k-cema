
////////////////////////////////////////////////////////////////////////////////
//
// Copyright 2020 Kirintec Ltd. All rights reserved.
//
// This sketch provides Arduino Nano functionality for the RCU KT-000-0146-00
// test interfac board.  Functionality provided:
//
// - Generates 1PPS output pulse to -0146 board using Timer 1
// - Verifies 1PPS input pulse accuracy to +/- 100 us
// - Samples and prints state of -0146 digital outputs:
//    - XCHANGE_RESET
//    - ZEROISE_POWER_ENABLE 
//    - POWER_BUTTON - 
// - Samples and prints voltage of -0146 analog outputs:
//    - +12 V
//    - +3.3 V
// - Peforms a loopback test at 57.6 kbaud on the XCHANGE UART interface.
//   NOTE, the loopback test uses a SoftwareSerial UART, the reference 
//   documentation states that interrupts are disabled when receiving which can
//   cause issues with millis() and micros() accuracy.  Not seen during test
//   and absolute timing accuracy is not required for functional test but 
//   something to be aware of.
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "SoftwareSerial.h"

////////////////////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////////////////////

// I/O pin constants
const int dip_pps_pin = 2;
const int su_rxd_pin = 3;
const int su_txd_pin = 4;
const int dip_xchange_rst_pin = 5;
const int dip_pwr_zero_en_pin = 6;
const int dip_pwr_btn_pin = 7;
const int dop_pps_pin = 12;
const int dop_led_pin = 13;
const int aip_12v_pin = A0;
const int aip_3v3_pin = A1;

// Timer 1 constants to generate 1PPS signal:
// Counter value high = 65536 - (16MHz / 256 / 10 ms)
// Counter value high = 65536 - (16MHz / 256 / 990 ms)
const int timer1_counter_high = 0xFD8F;
const int timer1_counter_low = 0xE4D;

const unsigned long serial_update_rate = 500UL;

const int aip_running_average_len = 5;
const float aip_adc_scale_factor = 0.07498; // ~75 mV per ADC step

const unsigned long dip_1pps_no_detect_limit = 1100000UL; // 1.1 seconds
const unsigned long dip_1pps_test_tolerance = 100UL; // 100 us
const unsigned long dip_1pps_min_period_limit = 1000000UL - dip_1pps_test_tolerance; 
const unsigned long dip_1pps_max_period_limit = 1000000UL + dip_1pps_test_tolerance; 

const int su_loopback_test_depth = 10;
const unsigned long su_loopback_timeout = 10000UL;  // 1-byte at 115200 baud should
                                                    // be echoed within 10 ms 
const long su_baud_rate = 57600;
const long u_baud_rate = 115200;                                                    

////////////////////////////////////////////////////////////////////////////////
// Globals
////////////////////////////////////////////////////////////////////////////////
unsigned long g_pps_edge_time_us = 0UL;
SoftwareSerial g_xchange_uart = SoftwareSerial(su_rxd_pin, su_txd_pin); 

////////////////////////////////////////////////////////////////////////////////
// Default sketch setup() function
////////////////////////////////////////////////////////////////////////////////
void setup() {
  // put your setup code here, to run once:
  setup_io_pins();
  // Open serial port, set data rate to 115200 bps
  Serial.begin(u_baud_rate); 
  // Timer 1 is used to generate 1PPS output pulse
  initialise_timer1();
  // Analog signals use internal 1.1 V reference
  analogReference(EXTERNAL);
  // Attach interrupt for detecting rising edge of 1PPS input signal
  attachInterrupt(digitalPinToInterrupt(dip_pps_pin), dip_pps_isr, RISING);
  // Start the software serial driver
  g_xchange_uart.begin(su_baud_rate);
  g_xchange_uart.listen(); 
}

////////////////////////////////////////////////////////////////////////////////
// Default sketch loop() function
////////////////////////////////////////////////////////////////////////////////
void loop() {
  // put your main code here, to run repeatedly:
  static unsigned long now = 0UL, later = 0UL;

  now = millis();

  if (now > later){
    clear_serial_terminal();
    Serial.println("RCU Test Interface Board Utility for KT-000-0146-00:\n");
    print_serial_digital_ip_state();
    Serial.print("\n");
    print_serial_analog_ip_state();
    Serial.print("\n");
    print_serial_1pps_status();
    Serial.print("\n");
    print_serial_xchange_uart_test();

    later = now + serial_update_rate;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Setup I/O pin directions for the application
////////////////////////////////////////////////////////////////////////////////
void setup_io_pins(void) {
  pinMode(dip_xchange_rst_pin, INPUT);
  pinMode(dip_pwr_zero_en_pin, INPUT);
  pinMode(dip_pwr_btn_pin, INPUT);
  pinMode(aip_12v_pin, INPUT);
  pinMode(aip_3v3_pin, INPUT);
  
  pinMode(dop_pps_pin, OUTPUT);
  digitalWrite(dop_pps_pin, LOW);

  pinMode(dop_led_pin, OUTPUT);
  digitalWrite(dop_led_pin, HIGH);
}

////////////////////////////////////////////////////////////////////////////////
// Initialise Timer 1 to generate 1PPS signal
////////////////////////////////////////////////////////////////////////////////
void initialise_timer1(void) {
  noInterrupts();           // Disable all interrupts
  TCCR1A = 0;
  TCCR1B = 0;
  // 1PPS signal initialised to low 
  TCNT1 = timer1_counter_low;   // Preload timer
  TCCR1B |= (1 << CS12);    // Set prescaler to 256
  TIMSK1 |= (1 << TOIE1);   // Enable timer overflow interrupt
  interrupts();             // Enable all interrupts 
}

////////////////////////////////////////////////////////////////////////////////
// Clear the terminal window
////////////////////////////////////////////////////////////////////////////////
void clear_serial_terminal(void) {
  Serial.write(27); //ESC
  Serial.print("[2J");
  Serial.write(27); //ESC
  Serial.print("[H");  
}

////////////////////////////////////////////////////////////////////////////////
// Read and print digital input signal states
////////////////////////////////////////////////////////////////////////////////
void print_serial_digital_ip_state(void) {
  Serial.println("Digital inputs:");
  Serial.print("XCHANGE_RESET:\t\t");
  Serial.println(digitalRead(dip_xchange_rst_pin)); 
  Serial.print("ZEROISE_POWER_ENABLE:\t");
  Serial.println(digitalRead(dip_pwr_zero_en_pin)); 
  Serial.print("POWER_BUTTON:\t\t");
  Serial.println(digitalRead(dip_pwr_btn_pin)); 
}

////////////////////////////////////////////////////////////////////////////////
// Read and print analog input signal states
////////////////////////////////////////////////////////////////////////////////
void print_serial_analog_ip_state(void) {
  static float aip_12v_running_av_buf[aip_running_average_len];
  static float aip_3v3_running_av_buf[aip_running_average_len];
  static int running_av_idx = 0;
  float aip_12v_av = 0.0f;
  float aip_3v3_av = 0.0f;
  int i = 0;

  // Read ADC channels and add to running average buffers
  aip_12v_running_av_buf[running_av_idx] = (float)analogRead(aip_12v_pin) * aip_adc_scale_factor;
  aip_3v3_running_av_buf[running_av_idx++] = (float) analogRead(aip_3v3_pin) * aip_adc_scale_factor;
  
  if (running_av_idx >= aip_running_average_len) {
    running_av_idx = 0;
  }

  // Calculate average values
  for (i = 0; i < aip_running_average_len; i++) {
    aip_12v_av += aip_12v_running_av_buf[i];
    aip_3v3_av += aip_3v3_running_av_buf[i];
  }

  aip_12v_av /= aip_running_average_len;
  aip_3v3_av /= aip_running_average_len;
  
  Serial.println("Analog inputs:");
  Serial.print("+12V (V):\t\t");
  Serial.println(aip_12v_av); 
  Serial.print("+3V3 (V):\t\t");
  Serial.println(aip_3v3_av); 
}

////////////////////////////////////////////////////////////////////////////////
// Print status of 1PPS input
////////////////////////////////////////////////////////////////////////////////
void print_serial_1pps_status(void) {
  static unsigned long prev_1pps_edge = 0UL, delta = 0UL;
  unsigned long new_1pps_edge, now = micros();

  // Critical section, get time in us that last 1PPS rising edge was detected
  noInterrupts();
  new_1pps_edge = g_pps_edge_time_us;
  interrupts();

  Serial.println("1PPS period test:");
  Serial.print("1PPS period (us):\t");
  
  // Is the 1PPS signal present?
  if (((now - new_1pps_edge) > dip_1pps_no_detect_limit) ||
      ((new_1pps_edge - prev_1pps_edge) > dip_1pps_no_detect_limit)) {
    Serial.println("Signal Unavailable"); 
  }
  else {
    // Calculate new delta if an edge has occurred, otherwoise report last value
    if (new_1pps_edge != prev_1pps_edge) {
      delta =  new_1pps_edge - prev_1pps_edge;
    }
    Serial.println(delta);
    
    Serial.print("Test tolerance (us) +/-");
    Serial.print(dip_1pps_test_tolerance);

    if ((delta >= dip_1pps_min_period_limit) &&
        (delta <= dip_1pps_max_period_limit)) {
      Serial.println(" - PASS");
    }
    else {          
      Serial.println(" - FAIL");
    }      
  }
  
  prev_1pps_edge = new_1pps_edge;
}

////////////////////////////////////////////////////////////////////////////////
// Peform Xchange UART loopback test and print result
// Send a random value and check it is received correctly
////////////////////////////////////////////////////////////////////////////////
void print_serial_xchange_uart_test(void) {
  static bool test_history[su_loopback_test_depth];
  static int test_history_idx = 0;
  unsigned char rx_val, tx_val = (unsigned char)(random(0, 254) & 0xFFU);
  unsigned long later = micros() + su_loopback_timeout;
  int i;
  bool overall_result = true;

  Serial.println("XCHANGE UART loopback test:");
  Serial.print("tx_val: ");
  Serial.println(tx_val, HEX);
  
  g_xchange_uart.write(tx_val);

  do {
    rx_val = (unsigned char)g_xchange_uart.read();
    if (rx_val == tx_val) {
      break; 
    }
  } while (micros() < later);
  
  Serial.print("rx_val: ");
  Serial.print(rx_val, HEX);
  
  if (rx_val == tx_val) {
      Serial.println(" - PASS");
      test_history[test_history_idx++] = true;
  }
  else {
    Serial.println(" - FAIL");
    test_history[test_history_idx++] = false;
  }

  if (test_history_idx >= su_loopback_test_depth) {
    test_history_idx = 0;
  }
   Serial.print("Overall result of previous ");
   Serial.print(su_loopback_test_depth);
   Serial.print(" tests: ");

   for (i = 0; i < su_loopback_test_depth; ++i) {
    overall_result &= test_history[i];
   }

   if (overall_result) {
    Serial.println("PASS");
   }
   else {
    Serial.println("FAIL");
   }
}

////////////////////////////////////////////////////////////////////////////////
// Timer 1 interrupt routine
////////////////////////////////////////////////////////////////////////////////
ISR(TIMER1_OVF_vect) { 
  if (digitalRead(dop_pps_pin) == LOW) {
    digitalWrite(dop_pps_pin, HIGH);
    digitalWrite(dop_led_pin, HIGH);
    TCNT1 = timer1_counter_high;
  }
  else {
    digitalWrite(dop_pps_pin, LOW);
    digitalWrite(dop_led_pin, LOW);
    TCNT1 = timer1_counter_low;
  }
}

////////////////////////////////////////////////////////////////////////////////
// Interrupt routine for rising edge of 1PPS DIP
////////////////////////////////////////////////////////////////////////////////
void dip_pps_isr(void) {
  g_pps_edge_time_us = micros();
}
