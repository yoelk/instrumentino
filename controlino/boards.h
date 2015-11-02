#ifndef _boards_h_
#define _boards_h_

#include "controlino_cfg.h"

/*******************************************************************************
 * Arduino boards
 ******************************************************************************/
#if BOARD_FAMILY == BOARD_FAMILY_ARDUINO
#include "Arduino.h"

/**********
 * Wrapper functions for channel operations (read, write etc.)
 **********/
// Analog pins
uint32_t arduino_ch_pin_analog_read (int ch_num);

// Digital pins
uint32_t arduino_ch_pin_digital_read (int ch_num);
void arduino_ch_pin_digital_write (int ch_num, uint32_t values[], int values_num);
void arduino_ch_pin_digital_direction (int ch_num, boolean isInput);

// PWM pins
void arduino_ch_pin_pwm_write (int ch_num, uint32_t values[], int values_num);

/**********
 * Hardware definitions
 **********/
// Arduino Uno
#if BOARD == BOARD_ARDUINO_UNO
#endif

// Arduino Leonardo
#if BOARD == BOARD_ARDUINO_LEONARDO
	#define HARD_SER_MAX_PORTS	1
	extern HardwareSerial Serial1;
#endif

// Arduino Due
#if BOARD == BOARD_ARDUINO_DUE
	#define HARD_SER_MAX_PORTS	3
	extern HardwareSerial Serial1;
	extern HardwareSerial Serial2;
	extern HardwareSerial Serial3;
#endif

// Arduino Yun
#if BOARD == BOARD_ARDUINO_YUN
#endif

// Arduino Tre
#if BOARD == BOARD_ARDUINO_TRE
#endif

// Arduino Zero
#if BOARD == BOARD_ARDUINO_ZERO
#endif

// Arduino Micro
#if BOARD == BOARD_ARDUINO_MICRO
#endif

// Arduino Mega ADK
#if BOARD == BOARD_ARDUINO_MEGA_ADK
	#define HARD_SER_MAX_PORTS	3
	extern HardwareSerial Serial1;
	extern HardwareSerial Serial2;
	extern HardwareSerial Serial3;
#endif

// Arduino Mega 2560
#if BOARD == BOARD_ARDUINO_MEGA_2560
	#define HARD_SER_MAX_PORTS	3
	extern HardwareSerial Serial1;
	extern HardwareSerial Serial2;
	extern HardwareSerial Serial3;
#endif

// Arduino Ethernet
#if BOARD == BOARD_ARDUINO_ETHERNET
#endif

// Arduino Nano
#if BOARD == BOARD_ARDUINO_NANO
#endif

// Arduino Lilypad
#if BOARD == BOARD_ARDUINO_LILIPAD
#endif

// Arduino Lilypad Simple
#if BOARD == BOARD_ARDUINO_LILYPAD_SIMPLE
#endif

// Arduino Lilypad Simple Snap
#if BOARD == BOARD_ARDUINO_LILYPAD_SIMPLE_SNAP
#endif

// Arduino Lilypad USB
#if BOARD == BOARD_ARDUINO_LILYPAD_USB
#endif

// Arduino Pro
#if BOARD == BOARD_ARDUINO_PRO
#endif

// Arduino Pro Mini
#if BOARD == BOARD_ARDUINO_PRO_MINI
#endif

// Arduino Fio
#if BOARD == BOARD_ARDUINO_FIO
#endif

#endif // BOARD == BOARD_ARDUINO_UNO

#endif // _boards_h_
