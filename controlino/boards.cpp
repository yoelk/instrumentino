#include "controlino.h"

#if BOARD_FAMILY == BOARD_FAMILY_ARDUINO
/*******************************************************************************
 * Arduino
 ******************************************************************************/

// Channel types
ChannelTypeDesc channel_types[] = {
	{'A', 2, arduino_ch_pin_analog_read}, // Analog
	{'D', 1, arduino_ch_pin_digital_read, arduino_ch_pin_digital_write, arduino_ch_pin_digital_direction}, // Digital
	{'P', 2, NULL, arduino_ch_pin_pwm_write}, // PWM
    {'I', CH_BYTES_PER_DATAPOINT_UNKNOWN} // I2C
};
int channel_types_num (sizeof(channel_types) / sizeof(ChannelTypeDesc));

/**********
 * Wrapper functions for channel operations (read, write etc.)
 **********/

// Analog pins
uint32_t arduino_ch_pin_analog_read (int ch_num) {
	return analogRead(ch_num);
}

// Digital pins
uint32_t arduino_ch_pin_digital_read (int ch_num) {
	return digitalRead(ch_num);
}
void arduino_ch_pin_digital_write (int ch_num, uint32_t values[], int values_num) {
	digitalWrite(ch_num, values[0]);
}
void arduino_ch_pin_digital_direction (int ch_num, boolean isInput) {
	if (isInput) {
		pinMode(ch_num, INPUT);
	} else {
		pinMode(ch_num, OUTPUT);
	}
}

// PWM pins
void arduino_ch_pin_pwm_write (int ch_num, uint32_t values[], int values_num) {
	analogWrite(ch_num, values[0]);
}
#endif
