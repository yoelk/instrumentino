#ifndef _controlino_cfg_h_
#define _controlino_cfg_h_

/*******************************************************************************
 * (1) Define the board to be used. See "supportedBoards.h" for available options
 ******************************************************************************/
#include "supported_boards.h"
#define BOARD_FAMILY	BOARD_FAMILY_ARDUINO
#define BOARD 			ARDUINO_BOARD_NANO

/*******************************************************************************
 * (2) External library support
 *
 * Here you should specify which extra libraries you want to use.
 * Please comment/uncomment the appropriate define statements.
 ******************************************************************************/
//#define USE_ARDUINO_PID					// http://playground.arduino.cc/Code/PIDLibrary

#endif // _controlino_cfg_h_
