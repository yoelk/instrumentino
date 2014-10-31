################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir.mk
-include arduino/core/subdir.mk
-include Libraries/SoftwareSerial/subdir.mk
-include Libraries/PID_v1/subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C++_DEPS)),)
-include $(C++_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
ifneq ($(strip $(CC_DEPS)),)
-include $(CC_DEPS)
endif
ifneq ($(strip $(CPP_DEPS)),)
-include $(CPP_DEPS)
endif
ifneq ($(strip $(CXX_DEPS)),)
-include $(CXX_DEPS)
endif
ifneq ($(strip $(C_UPPER_DEPS)),)
-include $(C_UPPER_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 
AR += \
/Users/joel/Documents/workspace/Arduino/controlino/Release/arduino.ar \

ELF += \
controlino.elf \

EEP += \
controlino.eep \

FLASH_IMAGE += \
controlino.hex \


# All Target
all: controlino

# Tool invocations
controlino: $(FLASH_IMAGE)
	@echo 'Building target: $@'
	@echo 'Printing size:'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-size" -A "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.hex"
	@echo 'Finished building target: $@'
	@echo ' '

/Users/joel/Documents/workspace/Arduino/controlino/Release/arduino.ar: $(AR_OBJ)
	@echo 'Starting archiver'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-ar" rcs "/Users/joel/Documents/workspace/Arduino/controlino/Release/arduino.ar"   $(AR_OBJ)
	@echo 'Finished building: $@'
	@echo ' '

controlino.elf: $(LINK_OBJ) $(AR)
	@echo 'Starting combiner'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-gcc" -Os -Wl,--gc-sections -mmcu=atmega328p -o "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.elf"   $(LINK_OBJ) $(AR)  "/Users/joel/Documents/workspace/Arduino/controlino/Release/arduino.ar" "-L/Users/joel/Documents/workspace/Arduino/controlino/Release" -lm
	@echo 'Finished building: $@'
	@echo ' '

controlino.eep: $(ELF)
	@echo 'Create eeprom image'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-objcopy" -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings --change-section-lma .eeprom=0 "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.elf" "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.eep"
	@echo 'Finished building: $@'
	@echo ' '

controlino.hex: $(EEP)
	@echo 'Create Flash image (ihex format)'
	"/Applications/Arduino 1.5.2.app/Contents/Resources/Java/hardware/tools/avr/bin/avr-objcopy" -O ihex -R .eeprom "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.elf" "/Users/joel/Documents/workspace/Arduino/controlino/Release/controlino.hex"
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(C_DEPS)$(AR)$(FLASH_IMAGE)$(EEP)$(CXX_DEPS)$(C++_DEPS)$(ELF)$(CC_DEPS)$(AR_OBJ)$(CPP_DEPS)$(LINK_OBJ)$(C_UPPER_DEPS)$(SIZEDUMMY) controlino
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets
