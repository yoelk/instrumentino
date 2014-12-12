################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
/Applications/Arduino\ 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/libraries/SoftwareSerial/SoftwareSerial.cpp 

CPP_DEPS += \
./Libraries/SoftwareSerial/SoftwareSerial.cpp.d 

LINK_OBJ += \
./Libraries/SoftwareSerial/SoftwareSerial.cpp.o 


# Each subdirectory must supply rules for building sources it contributes
Libraries/SoftwareSerial/SoftwareSerial.cpp.o: /Applications/Arduino\ 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/libraries/SoftwareSerial/SoftwareSerial.cpp
	@echo 'Building file: $<'
	@echo 'Starting C++ compile'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-g++" -c -g -Os -w -fno-exceptions -ffunction-sections -fdata-sections -MMD -mmcu=atmega2560 -DF_CPU=16000000L -DARDUINO=152    -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/cores/arduino" -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/variants/mega" -I"/Users/joel/Documents/workspace/Arduino/libs/libraries/PID_v1" -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/libraries/SoftwareSerial" -I"/Users/joel/Documents/workspace/Arduino/libs/libraries/PID_AutoTune_v0" -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -D__IN_ECLIPSE__=1 -x c++ "$<"  -o  "$@"
	@echo 'Finished building: $<'
	@echo ' '


