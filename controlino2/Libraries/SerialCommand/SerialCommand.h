/**
 * SerialCommand - A Wiring/Arduino library to tokenize and parse commands
 * received over a serial port.
 * 
 * Copyright (C) 2012 Stefan Rado
 * Copyright (C) 2011 Steven Cogswell <steven.cogswell@gmail.com>
 *                    http://husks.wordpress.com
 * 
 * Version 20120522
 * 
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef SerialCommand_h
#define SerialCommand_h

#if defined(WIRING) && WIRING >= 100
  #include <Wiring.h>
#elif defined(ARDUINO) && ARDUINO >= 100
  #include <Arduino.h>
#else
  #include <WProgram.h>
#endif
#include <string.h>
#include <Stream.h>

// Size of the input buffer in bytes (maximum length of one command plus arguments)
#define SERIALCOMMAND_BUFFER 64

#define SERIALCOMMAND_MAXCOMMANDS_DEFAULT 10

// Uncomment the next line to run the library in debug mode (verbose messages)
//#define SERIALCOMMAND_DEBUG

/******************************************************************************/
// SerialCommand (extends Print) 
// so that callbacks print 
class SerialCommand : public Print {
  public:
    SerialCommand(Stream &port,
                  int maxCommands = SERIALCOMMAND_MAXCOMMANDS_DEFAULT
                 );       // Constructor
    void addCommand(const char *command, void(*function)(SerialCommand));           // Add a command to the processing dictionary.
    void addCommand(__FlashStringHelper *command, void(*function)(SerialCommand));  // Add a command to the processing dictionary.
    void setDefaultHandler(void (*function)(const char *, SerialCommand));          // A handler to call when no valid command received.

    void readSerial();    // Main entry point.
    void clearBuffer();   // Clears the input buffer.
    char *next();         // Returns pointer to next token found in command buffer (for getting arguments to commands).
    //provide method for printing
    size_t write(uint8_t val);
    size_t write(const uint8_t *buffer, size_t size);

  private:
    //Stream object for data IO
    Stream &_port;
    // Command/handler dictionary
    struct SerialCommandCallback {
      const char *command;
      void (*function)(SerialCommand);
    };                                     // Data structure to hold Command/Handler function key-value pairs
    SerialCommandCallback *_commandList;   // Actual definition for command/handler array
    int  _commandCount;
    int  _maxCommands;

    // Pointer to the default handler function
    void (*_defaultHandler)(const char *, SerialCommand);

    char _delim[2]; // null-terminated list of character to be used as delimeters for tokenizing (default " ")
    char _term;     // Character that signals end of command (default '\n')

    char _buffer[SERIALCOMMAND_BUFFER + 1]; // Buffer of stored characters while waiting for terminator character
    int  _bufPos;                        // Current position in the buffer
    char *_last;                         // State variable used by strtok_r during processing
};

#endif //SerialCommand_h
