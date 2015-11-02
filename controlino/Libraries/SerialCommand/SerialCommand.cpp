/**
 * SerialCommand - A Wiring/Arduino library to tokenize and parse commands
 * received over a serial port.
 * 
 * Copyright (C) 2014 Craig Versek
 * Copyright (C) 2012 Stefan Rado
 * Copyright (C) 2011 Steven Cogswell <steven.cogswell@gmail.com>
 *                    http://husks.wordpress.com
 * 
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
#include "SerialCommand.h"

/**
 * Constructor makes sure some things are set.
 */
SerialCommand::SerialCommand(Stream &port,
                             int maxCommands
                            )
  : _port(port),           // reference must be initialized right away
    _commandList(NULL),
    _commandCount(0),
    _defaultHandler(NULL),
    _term('\r'),           // default terminator for commands, newline character
    _last(NULL)
{
  _maxCommands = maxCommands;
  strcpy(_delim, " "); // strtok_r needs a null-terminated string
  clearBuffer();
  //allocate memory for the command list
  _commandList = (SerialCommandCallback *) calloc(maxCommands, sizeof(SerialCommandCallback));
}

/**
 * Adds a "command" and a handler function to the list of available commands.
 * This is used for matching a found token in the buffer, and gives the pointer
 * to the handler function to deal with it.
 */
void SerialCommand::addCommand(const char *command, void (*function)(SerialCommand)) {
  #ifdef SERIALCOMMAND_DEBUG
    Serial.print("Adding command (");
    Serial.print(_commandCount);
    Serial.print("): ");
    Serial.println(command);
  #endif
  if (_commandCount >= _maxCommands){
      #ifdef SERIALCOMMAND_DEBUG
      Serial.print("Error: maxCommands was exceeded");
      #endif
      return;
    }
  //make a new callback
  struct SerialCommandCallback new_callback;
  new_callback.command  = command;
  new_callback.function = function;
  _commandList[_commandCount] = new_callback;
  _commandCount++;
}

/**
 * This sets up a handler to be called in the event that the receveived command string
 * isn't in the list of commands.
 */
void SerialCommand::setDefaultHandler(void (*function)(const char *, SerialCommand)) {
  _defaultHandler = function;
}


/**
 * This checks the Serial stream for characters, and assembles them into a buffer.
 * When the terminator character (default '\n') is seen, it starts parsing the
 * buffer for a prefix command, and calls handlers setup by addCommand() member
 */
void SerialCommand::readSerial() {
  while (_port.available() > 0) {
    char inChar = _port.read();   // Read single available character, there may be more waiting
    #ifdef SERIALCOMMAND_DEBUG
      Serial.print(inChar);       // Echo back to serial stream
    #endif

    if (inChar == _term) {        // Check for the terminator (default '\r') meaning end of command
      #ifdef SERIALCOMMAND_DEBUG
        Serial.print("Received: ");
        Serial.println(_buffer);
      #endif

      char *command = strtok_r(_buffer, _delim, &_last);   // Search for command at start of buffer
      if (command != NULL) {
        bool matched = false;
        for (int i = 0; i < _commandCount; i++) {
          #ifdef SERIALCOMMAND_DEBUG
            Serial.print("Comparing [");
            Serial.print(command);
            Serial.print("] to [");
            Serial.print(_commandList[i].command);
            Serial.println("]");
          #endif

          // Compare the found command against the list of known commands for a match
          if (strcmp(command, _commandList[i].command) == 0) {
            #ifdef SERIALCOMMAND_DEBUG
              Serial.print("Matched Command: ");
              Serial.println(command);
            #endif

            // Execute the stored handler function for the command,
            // passing in the "this" current SerialCommand object
            (*_commandList[i].function)(*this);
            matched = true;
            break;
          }
        }
        if (!matched && (_defaultHandler != NULL)) {
          (*_defaultHandler)(command, *this);
        }
      }
      clearBuffer();
    }
    else if (isprint(inChar)) {     // Only printable characters into the buffer
      if (_bufPos < SERIALCOMMAND_BUFFER) {
        _buffer[_bufPos++] = inChar;  // Put character into buffer
        _buffer[_bufPos] = '\0';      // Null terminate
      } else {
        #ifdef SERIALCOMMAND_DEBUG
          Serial.println("Line buffer is full - increase SERIALCOMMAND_BUFFER");
        #endif
      }
    }
  }
}

/*
 * Clear the input buffer.
 */
void SerialCommand::clearBuffer() {
  _buffer[0] = '\0';
  _bufPos = 0;
}

/**
 * Retrieve the next token ("word" or "argument") from the command buffer.
 * Returns NULL if no more tokens exist.
 */
char *SerialCommand::next() {
  return strtok_r(NULL, _delim, &_last);
}

/*
 * forward all writes to the encapsulated "port" Stream object
 */
size_t SerialCommand::write(uint8_t val) {
  return _port.write(val);
}

/*
 * forward all writes to the encapsulated "port" Stream object
 */
size_t SerialCommand::write(const uint8_t *buffer, size_t size) {
  return _port.write(buffer, size);
}
