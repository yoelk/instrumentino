################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CPP_SRCS += \
../controlino.cpp 

CPP_DEPS += \
./controlino.cpp.d 

LINK_OBJ += \
./controlino.cpp.o 


# Each subdirectory must supply rules for building sources it contributes
controlino.cpp.o: ../controlino.cpp
	@echo 'Building file: $<'
	@echo 'Starting C++ compile'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-g++" -c -g -Os -w -fno-exceptions -ffunction-sections -fdata-sections -MMD -mmcu=atmega328p -DF_CPU=16000000L -DARDUINO=152    -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/cores/arduino" -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/variants/eightanaloginputs" -I"/Users/joel/workspace/arduino/libraries/PID_v1" -I"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/arduino/avr/libraries/SoftwareSerial" -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -D__IN_ECLIPSE__=1 -x c++ "$<"  -o  "$@"
	@echo 'Finished building: $<'
	@echo ' '


