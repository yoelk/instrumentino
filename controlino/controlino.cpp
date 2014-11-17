/*
	controlino.cpp - Library for controling an Arduino using the USB
	Created by Joel Koenka, April 2014
	Released under GPLv3

	controlino let's a user control the Arduino pins by issuing simple serial commands such as "Read" "Write" etc.
	It was originally written to be used with Instrumentino, the open-source GUI platform for experimental settings,
	but can also be used for other purposes.
	For Instrumentino, see:
	http://www.sciencedirect.com/science/article/pii/S0010465514002112	- Release article
	https://pypi.python.org/pypi/instrumentino/1.0						- Package in PyPi
	https://github.com/yoelk/instrumentino								- Code in GitHub
 */

#include "Arduino.h"
#include "HardwareSerial.h"
#include "SoftwareSerial.h"
#include "string.h"
#include "PID_v1.h"

#ifdef __cplusplus
extern "C" {
#endif
void loop();
void setup();
#ifdef __cplusplus
} // extern "C"
#endif

// ------------------------------------------------------------
// Board specific part
// ------------------------------------------------------------
// arduino board. Only one should be defined
#define ARDUINO_BOARD_NANO
//#define ARDUINO_BOARD_MEGA

// Arduino MEGA definitions
#ifdef ARDUINO_BOARD_MEGA
	extern HardwareSerial Serial1;
	extern HardwareSerial Serial2;
	extern HardwareSerial Serial3;
	#define SERIAL1
	#define SERIAL2
	#define SERIAL3
	#define HARD_SER_MAX_PORTS	3
	#define DIGI_PINS			54
#endif

// Arduino Nano definitions
#ifdef ARDUINO_BOARD_NANO
	#define HARD_SER_MAX_PORTS	0
	#define DIGI_PINS			13
#endif

// ------------------------------------------------------------
// Definitions
// ------------------------------------------------------------

// arduino definitions
#define ANAL_OUT_VAL_MAX		255

// serial
extern HardwareSerial Serial;
#define SERIAL0_BAUD		115200
#define RX_BUFF_SIZE		200
#define ARGV_MAX			30
#define SOFT_SER_MSG_SIZE	100
#define SOFT_SER_MAX_PORTS	4

// PID
#define PID_RELAY_MAX_VARS	4

// software serial descriptor
typedef struct {
	SoftwareSerial* handler;
	char txMsg[SOFT_SER_MSG_SIZE];
	char rxMsg[SOFT_SER_MSG_SIZE];
	int txMsgLen;
	int rxMsgLen;
} SoftSerialDesc;

// PID-relay variable descriptor
typedef struct {
	PID* handler;
	int pinAnalIn;
	int pinDigiOut;
	double inputVar;
	double outputVar;
	unsigned long windowSize;
	unsigned long windowStartTime;
	double setPoint;
	boolean isOn;
} PidRelayDesc;

// ------------------------------------------------------------
// Globals
// ------------------------------------------------------------

char doneString[5] = "done";

// Buffer to keep incoming commands and a pointer to it
char msg[RX_BUFF_SIZE];
char *pMsg;

// Descriptors for hardware and software serial
SoftSerialDesc softSerDescs[SOFT_SER_MAX_PORTS];
HardwareSerial* hardSerHandler[HARD_SER_MAX_PORTS];

// Descriptors for PID controlled variables
PidRelayDesc pidRelayDescs[PID_RELAY_MAX_VARS];

// Pin blinking
boolean startBlinking = false;
int blinkingPin;
unsigned long blinkLastChangeMs;
unsigned long blinkingDelayMs;

// ------------------------------------------------------------
// Utility functions
// ------------------------------------------------------------

/***
 * Set [pin number] [in | out]
 *
 * Set a digital pin mode
 */
void cmdSet(char **argV) {
	int pin = strtol(argV[1], NULL, 10);
	char* mode = argV[2];

	if (strcasecmp(mode, "in") == 0) {
		pinMode(pin, INPUT);
	} else if (strcasecmp(mode, "out") == 0) {
		pinMode(pin, OUTPUT);
	} else {
		return;
	}
}

/***
 * Reset
 *
 * Reset all digital pins to INPUT
 */
void cmdReset() {
	for (int i = 0; i < DIGI_PINS; i++) {
		pinMode(i, INPUT);
	}
}

/***
 * BlinkPin
 *
 * Start blinking a pin (e.g pin 13 with the LED)
 */
void cmdBlinkPin(char **argV) {
	blinkingPin = strtol(argV[1], NULL, 10);
	blinkingDelayMs = strtol(argV[2], NULL, 10);

	pinMode(blinkingPin, OUTPUT);
	blinkLastChangeMs = millis();
	startBlinking = true;
}

/***
 * Read [pin1] [pin2] ....
 *
 * Read pin values
 * Pins are given in the following way: A0 A1 ... for analog pins
 * 										D0 D1 ... for digital pins
 * Answer is: val1 val2 ...
 */
void cmdRead(int argC, char **argV) {
	char pinType[2];
	int pin;
	int value;

	for (int i = 1; i <= argC; i++) {
		pinType[0] = argV[i][0];
		pinType[1] = NULL;
		pin = strtol(&(argV[i][1]), NULL, 10);

		if (strcasecmp(pinType, "D") == 0) {
			value = digitalRead(pin);
		} else if (strcasecmp(pinType, "A") == 0) {
			value = analogRead(pin);
		} else {
			return;
		}

		// Add read values to answer string
		Serial.print(value);
		if (i < argC) {
			Serial.print(' ');
		}
	}
}

/***
 * Write [pin number] [digi | anal] [value]
 *
 * Write a value to a pin
 */
void cmdWrite(char **argV) {
	int pin = strtol(argV[1], NULL, 10);
	char* type = argV[2];
	int value = strtol(argV[3], NULL, 10);

	if (strcasecmp(type, "digi") == 0) {
		if (value == 0) {
			digitalWrite(pin, LOW);
		} else {
			digitalWrite(pin, HIGH);
		}
	} else if (strcasecmp(type, "anal") == 0) {
		analogWrite(pin, max(0, min(ANAL_OUT_VAL_MAX, value)));
	} else {
		return;
	}
}

/***
 * SetPwmFreq [pin number] [divider]
 *
 * Change the PWM frequency by changing the clock divider
 * This should be done carefully, as the clocks may have other effects on the system.
 * Specifically, pins 5,6 are controlled by timer0, which is also in charge for the delay() function.
 *
 * The divider can get: 1,8,64,256,1024 		for pins 5,6,9,10;
 * 						1,8,32,64,128,256,1024	for pins 3,11
 */
void cmdSetPwmFreq(char **argV) {
	int pin = strtol(argV[1], NULL, 10);
	int divider = strtol(argV[2], NULL, 10);

	byte mode;
	if(pin == 5 || pin == 6 || pin == 9 || pin == 10) {
		switch(divider) {
			case 1: mode = 0x01; break; // 		5,6: 62500 Hz	| 9,10: 31250 Hz
			case 8: mode = 0x02; break; //		5,6: 7812.5 Hz	| 9,10: 3906.3 Hz
			case 64: mode = 0x03; break; //		5,6: 976.6 Hz	| 9,10: 488.3 Hz
			case 256: mode = 0x04; break; //	5,6: 244.1 Hz	| 9,10: 122 Hz
			case 1024: mode = 0x05; break;//	5,6: 61 Hz		| 9,10: 30.5 Hz
			default: return;
		}
		if(pin == 5 || pin == 6) {
#if defined(TCCR0B)
			TCCR0B = (TCCR0B & 0b11111000) | mode;
#endif
		} else {
#if defined(TCCR1B)
			TCCR1B = (TCCR1B & 0b11111000) | mode;
#endif
		}
	} else if(pin == 3 || pin == 11) {
		switch(divider) {
			case 1: mode = 0x01; break; //		31250 Hz
			case 8: mode = 0x02; break; //		3906.3 Hz
			case 32: mode = 0x03; break; //		976.6 Hz
			case 64: mode = 0x04; break; //		488.3 Hz
			case 128: mode = 0x05; break; //	244.1 Hz
			case 256: mode = 0x06; break; //	122 Hz
			case 1024: mode = 0x7; break; //	30.5 Hz
			default: return;
		}
#if defined(TCCR2B)
		TCCR2B = (TCCR2B & 0b11111000) | mode;
#endif
	}
}

/***
 * PidRelayCreate [pidVar] [pinAnalIn] [pinDigiOut] [windowSize] [Kp] [Ki] [Kd]
 *
 * Create a PID variable that controls a relay. window size is in ms.
 * See more information: http://playground.arduino.cc/Code/PIDLibraryRelayOutputExample
 */
void cmdPidRelayCreate(char **argV) {
	int pidVar = strtol(argV[1], NULL, 10);
	int pinAnalIn = strtol(argV[2], NULL, 10);
	int pinDigiOut = strtol(argV[3], NULL, 10);
	int windowSize = strtol(argV[4], NULL, 10);
	double kp = atof(argV[5]);
	double ki = atof(argV[6]);
	double kd = atof(argV[7]);

	if (pidVar < 1 || pidVar > PID_RELAY_MAX_VARS) {
		return;
	}

	// Init the PID variable
	PidRelayDesc* pidDesc = &pidRelayDescs[pidVar-1];
	pidDesc->pinAnalIn = pinAnalIn;
	pidDesc->pinDigiOut = pinDigiOut;
	pidDesc->windowSize = windowSize;
	pidDesc->handler = new PID(&pidDesc->inputVar, &pidDesc->outputVar, &pidDesc->setPoint, kp, ki, kd, DIRECT);
	pidDesc->handler->SetOutputLimits(0, pidDesc->windowSize);
	pidDesc->isOn = false;
}

/***
 * PidRelaySet [pidVar] [setpoint]
 *
 * Start controlling a relay using a PID variable
 */
void cmdPidRelaySet(char **argV) {
	int pidVar = strtol(argV[1], NULL, 10);
	int setPoint = strtol(argV[2], NULL, 10);

	if (pidVar < 1 || pidVar > PID_RELAY_MAX_VARS) {
		return;
	}

	PidRelayDesc* pidDesc = &pidRelayDescs[pidVar-1];
	pidDesc->setPoint = setPoint;
}

/***
 * PidRelayEnable [pidVar] [0 | 1]
 *
 * Start/Stop the control loop
 */
void cmdPidRelayEnable(char **argV) {
	int pidVar = strtol(argV[1], NULL, 10);
	int enable = strtol(argV[2], NULL, 10);

	if (pidVar < 1 || pidVar > PID_RELAY_MAX_VARS) {
		return;
	}

	PidRelayDesc* pidDesc = &pidRelayDescs[pidVar-1];
	pidDesc->windowStartTime = millis();

	// turn the PID on/off
	if (enable != 0) {
		pidDesc->isOn = true;
		pidDesc->handler->SetMode(AUTOMATIC);
	} else {
		pidDesc->isOn = false;
		pidDesc->handler->SetMode(MANUAL);
		digitalWrite(pidDesc->pinDigiOut, LOW);
	}
}

/***
 * HardSerConnect [baudrate] [port]
 *
 * Initiate a software serial connection. The rx-pin should have external interrupts
 */
void cmdHardSerConnect(char **argV) {
#if HARD_SER_MAX_PORTS > 0
	int baudrate = strtol(argV[1], NULL, 10);
	int currPort = strtol(argV[2], NULL, 10);

	if (currPort < 1 || currPort > HARD_SER_MAX_PORTS) {
		return;
	}

	// begin serial communication
	hardSerHandler[currPort-1]->begin(baudrate);
#endif
}

/***
 * SoftSerConnect [rx-pin number] [tx-pin number] [baudrate] [port]
 *
 * Initiate a software serial connection. The rx-pin should have external interrupts
 */
void cmdSoftSerConnect(char **argV) {
	int pinIn = strtol(argV[1], NULL, 10);
	int pinOut = strtol(argV[2], NULL, 10);
	int baudrate = strtol(argV[3], NULL, 10);
	int currPort = strtol(argV[4], NULL, 10);

	if (currPort < 1 || currPort > SOFT_SER_MAX_PORTS) {
		return;
	}

	// init softSerial struct
	softSerDescs[currPort-1].rxMsgLen = 0;
	softSerDescs[currPort-1].txMsgLen = 0;
	softSerDescs[currPort-1].handler = new SoftwareSerial(pinIn, pinOut, false);
	softSerDescs[currPort-1].handler->begin(baudrate);
}

/***
 * SerSend [hard | soft] [port]
 *
 * After this command, each character sent is mirrored to the chosen serial
 * port until the NULL character (0x00) is sent (also mirrored)
 */
void cmdSerSend(char **argV) {
	boolean isSoftSerial = (strcasecmp(argV[1], "soft") == 0);
	int currPort = strtol(argV[2], NULL, 10);

	Serial.println(doneString);

	if (currPort < 1 || currPort > (isSoftSerial)? SOFT_SER_MAX_PORTS : HARD_SER_MAX_PORTS) {
		return;
	}
	if (isSoftSerial) {
		softSerDescs[currPort-1].txMsgLen = 0;
	}

	// mirror the hardware serial and the software serial
	while (true) {
		if (Serial.available()) {
			char c = Serial.read();
			if (isSoftSerial) {
				softSerDescs[currPort-1].txMsg[softSerDescs[currPort-1].txMsgLen++] = c;
			} else {
#if HARD_SER_MAX_PORTS > 0
				hardSerHandler[currPort-1]->write(c);
#else
				return;
#endif
			}

			if (isSoftSerial && c == '\0') {
				// acknowledge, send the message, and remember the answer
				Serial.println(doneString);
				delay(10);
				for (int i = 0; i < softSerDescs[currPort-1].txMsgLen; i++) {
					softSerDescs[currPort-1].handler->write(softSerDescs[currPort-1].txMsg[i]);
				}
				softSerDescs[currPort-1].rxMsgLen = 0;
				while (!Serial.available()) {
					if (softSerDescs[currPort-1].handler->available() && softSerDescs[currPort-1].rxMsgLen < SOFT_SER_MSG_SIZE) {
						softSerDescs[currPort-1].rxMsg[softSerDescs[currPort-1].rxMsgLen++] = softSerDescs[currPort-1].handler->read();
					}
				}
				return;
			}
		}
	}
}

/***
 * SerReceive [hard | soft] [port]
 *
 * Empty the RX buffer of a serial port to the control serial port
 */
void cmdSerReceive(char **argV) {
	boolean isSoftSerial = (strcasecmp(argV[1], "soft") == 0);
	int currPort = strtol(argV[2], NULL, 10);

	if (currPort < 1 || currPort > (isSoftSerial)? SOFT_SER_MAX_PORTS : HARD_SER_MAX_PORTS) {
		return;
	}

	if (isSoftSerial) {
		for (int i = 0; i < softSerDescs[currPort-1].rxMsgLen && i < SOFT_SER_MSG_SIZE; i++) {
			Serial.write(softSerDescs[currPort-1].rxMsg[i]);
		}
	} else {
	#if HARD_SER_MAX_PORTS > 0
		while (hardSerHandler[currPort-1]->available()) {
			Serial.write(hardSerHandler[currPort-1]->read());
		}
	#else
		return;
	#endif
	}
}

// ------------------------------------------------------------
// Main functions
// ------------------------------------------------------------

/***
 * The setup function is called once at startup of the sketch
 */
void setup() {
	Serial.begin(SERIAL0_BAUD);
	pMsg = msg;

	// Init hardware serial ports if they exist
	for (int i = 0; i < HARD_SER_MAX_PORTS; i++)
	{
		switch (i + 1) {
		#ifdef SERIAL1
			case 1:
				hardSerHandler[i] = &Serial1;
				break;
		#endif
		#ifdef SERIAL2
			case 2:
				hardSerHandler[i] = &Serial2;
				break;
		#endif
		#ifdef SERIAL3
			case 3:
				hardSerHandler[i] = &Serial3;
				break;
		#endif
		}
	}
}

/***
 * The loop function is called in an endless loop
 */
void loop() {
	char c, argC;
	char *argV[ARGV_MAX];
	int i, pin;
	unsigned long curMs;

	// Take care of blinking LED
	if (startBlinking == true) {
		curMs = millis();
		if (curMs > blinkLastChangeMs + blinkingDelayMs) {
			blinkLastChangeMs = curMs;
			if (digitalRead(blinkingPin) == HIGH) {
				digitalWrite(blinkingPin, LOW);
			} else {
				digitalWrite(blinkingPin, HIGH);
			}
		}
	}

	// Take care PID-relay variables
	for (i = 0; i < PID_RELAY_MAX_VARS; i++) {
		if (pidRelayDescs[i].isOn) {
			pidRelayDescs[i].inputVar = analogRead(pidRelayDescs[i].pinAnalIn);
			pidRelayDescs[i].handler->Compute();

			// turn relay on/off according to the PID output
			curMs = millis();
			if (curMs - pidRelayDescs[i].windowStartTime > pidRelayDescs[i].windowSize) {
				//time to shift the Relay Window
				pidRelayDescs[i].windowStartTime += pidRelayDescs[i].windowSize;
			}
			if (pidRelayDescs[i].outputVar > curMs - pidRelayDescs[i].windowStartTime) {
				digitalWrite(pidRelayDescs[i].pinDigiOut, HIGH);
			}
			else {
				digitalWrite(pidRelayDescs[i].pinDigiOut, LOW);
			}
		}
	}

	// Read characters from the control serial port and act upon them
	if (Serial.available()) {
		c = Serial.read();
		switch (c) {
		case '\n':
			break;
		case '\r':
			// end the string and init pMsg
			Serial.println("");
			*(pMsg++) = NULL;
			pMsg = msg;
			// parse the command line statement and break it up into space-delimited
			// strings. the array of strings will be saved in the argV array.
			i = 0;
			argV[i] = strtok(msg, " ");

			do {
				argV[++i] = strtok(NULL, " ");
			} while ((i < ARGV_MAX) && (argV[i] != NULL));

			// save off the number of arguments
			argC = i;
			pin = strtol(argV[1], NULL, 10);

			if (strcasecmp(argV[0], "Set") == 0) {
				cmdSet(argV);
			} else if (strcasecmp(argV[0], "Reset") == 0) {
				cmdReset();
			} else if (strcasecmp(argV[0], "BlinkPin") == 0) {
				cmdBlinkPin(argV);
			} else if (strcasecmp(argV[0], "Read") == 0) {
				cmdRead(argC, argV);
			} else if (strcasecmp(argV[0], "Write") == 0) {
				cmdWrite(argV);
			} else if (strcasecmp(argV[0], "SetPwmFreq") == 0) {
				cmdSetPwmFreq(argV);
			} else if (strcasecmp(argV[0], "PidRelayCreate") == 0) {
				cmdPidRelayCreate(argV);
			} else if (strcasecmp(argV[0], "PidRelaySet") == 0) {
				cmdPidRelaySet(argV);
			} else if (strcasecmp(argV[0], "PidRelayEnable") == 0) {
				cmdPidRelayEnable(argV);
			} else if (strcasecmp(argV[0], "HardSerConnect") == 0) {
				cmdHardSerConnect(argV);
			} else if (strcasecmp(argV[0], "SoftSerConnect") == 0) {
				cmdSoftSerConnect(argV);
			} else if (strcasecmp(argV[0], "SerSend") == 0) {
				cmdSerSend(argV);
			} else if (strcasecmp(argV[0], "SerReceive") == 0) {
				cmdSerReceive(argV);
			} else {
				// Wrong command
				return;
			}

			// Acknowledge the command
			Serial.println(doneString);
			break;
		default:
			// Record the received character
			if (isprint(c) && pMsg < msg + sizeof(msg)) {
				*(pMsg++) = c;
			}
			break;
		}
	}
}
