#######################################
# Toolchain
#######################################

CC = sdcc
LD = sdcc
AS = sdasstm8
FLASH = stm8flash
OBJCOPY = stm8-objcopy
SIZE = stm8-size
DCE = stm8dce

MKDIR = mkdir
CP = cp

# Find the standard library path dynamically
STDLIB_PATH := $(shell dirname $(shell which sdcc))/../share/sdcc/lib/stm8/stm8.lib

#######################################
# Build options
#######################################

# MCU Variant
DEFINE = -DSTM8S103 # Change to your STM8S variant

# Defines
DEFINE +=

# Include directories
INCLUDE = $(addprefix -I, \
	include/ \
	src/ \
)

# Compiler flags
CC_FLAGS = -mstm8 --out-fmt-elf

# Project name
PROJECT = blinky

# Build directory
BUILD_DIR = build

# Assembly files
ASM_DIR = $(BUILD_DIR)/asm
AS_FLAGS = -plosg -ff

# Dead Code Elimination
DCE_DIR = $(BUILD_DIR)/dce
DCE_FLAGS =

# Object files
OBJ_DIR = $(BUILD_DIR)/obj

# Source files
VPATH += src
SRC_FILES = $(wildcard src/*.c) # Compile all .c files in src directory

# Libraries
LIBS = $(STDLIB_PATH)

# Linker flags
LD_FLAGS = -mstm8 --out-fmt-elf --opt-code-size

# ELF to HEX flags
OBJCOPY_FLAGS = --remove-section=".debug*" --remove-section=SSEG --remove-section=INITIALIZED --remove-section=DATA

# Size Check
RAM_SIZE = 1024
FLASH_SIZE = 8192

#######################################
# Flash Options
#######################################

FLASH_FLAGS = -c stlinkv2 -p stm8s103f3

#######################################
# Standard Peripheral Library
#######################################

VPATH += lib/STM8S_StdPeriph_Driver/src
INCLUDE += -Ilib/STM8S_StdPeriph_Driver/inc

# Comment/Uncomment according to your STM8S variant
# Which peripherals apply to your STM8S variant can be found out
# by looking at the STM8S_StdPeriph_Driver/inc/stm8s.h file

STDPER_SRC 	+= stm8s_adc1.c
# STDPER_SRC 	+= stm8s_adc2.c
STDPER_SRC 	+= stm8s_awu.c
STDPER_SRC 	+= stm8s_beep.c
# STDPER_SRC 	+= stm8s_can.c
STDPER_SRC 	+= stm8s_clk.c
STDPER_SRC 	+= stm8s_exti.c
STDPER_SRC 	+= stm8s_flash.c
STDPER_SRC 	+= stm8s_gpio.c
STDPER_SRC 	+= stm8s_i2c.c
STDPER_SRC 	+= stm8s_itc.c
STDPER_SRC 	+= stm8s_iwdg.c
STDPER_SRC 	+= stm8s_rst.c
STDPER_SRC 	+= stm8s_spi.c
STDPER_SRC 	+= stm8s_tim1.c
STDPER_SRC 	+= stm8s_tim2.c
# STDPER_SRC 	+= stm8s_tim3.c
# STDPER_SRC 	+= stm8s_tim4.c
# STDPER_SRC 	+= stm8s_tim5.c
# STDPER_SRC 	+= stm8s_tim6.c
STDPER_SRC 	+= stm8s_uart1.c
# STDPER_SRC 	+= stm8s_uart2.c
# STDPER_SRC 	+= stm8s_uart3.c
# STDPER_SRC 	+= stm8s_uart4.c
STDPER_SRC 	+= stm8s_wwdg.c

SRC_FILES += $(STDPER_SRC)

#######################################
# Project targets
#######################################

ASM = $(addprefix $(ASM_DIR)/, $(notdir $(SRC_FILES:.c=.asm)))
DCE_ASM = $(addprefix $(DCE_DIR)/, $(notdir $(ASM:.asm=.asm)))
OBJ = $(addprefix $(OBJ_DIR)/, $(notdir $(ASM:.asm=.rel)))

all: size_check $(BUILD_DIR)/$(PROJECT).ihx

# Upload/Flash
flash: $(BUILD_DIR)/$(PROJECT).ihx size_check
	$(FLASH) $(FLASH_FLAGS) -w $<

upload: flash

hex: $(BUILD_DIR)/$(PROJECT).ihx
elf: $(BUILD_DIR)/$(PROJECT).elf
obj: $(OBJ)
asm: $(ASM)
dce: $(DCE_ASM)

$(BUILD_DIR)/$(PROJECT).ihx: $(BUILD_DIR)/$(PROJECT).elf
	$(OBJCOPY) $(OBJCOPY_FLAGS) $< -O ihex $@

# ELF file
$(BUILD_DIR)/$(PROJECT).elf: $(OBJ)
	@$(MKDIR) -p $(BUILD_DIR)
	$(LD) $(LD_FLAGS) -o $@ $(LIBS) $^

$(ASM_DIR)/%.asm: %.c
	@$(MKDIR) -p $(ASM_DIR)
	$(CC) $< $(CC_FLAGS) $(INCLUDE) $(DEFINE) -S -o $@

$(DCE_DIR)/%.asm: $(ASM)
	@$(MKDIR) -p $(DCE_DIR)
	$(DCE) $(DCE_FLAGS) -o $(DCE_DIR) $(LIBS) $^

$(OBJ_DIR)/%.rel: $(DCE_DIR)/%.asm
	@$(MKDIR) -p $(OBJ_DIR)
	$(AS) $(AS_FLAGS) -o $@ $<

# Clean
clean:
	rm -rf $(ASM_DIR)/ $(DCE_DIR) $(BUILD_DIR)/

# Prints size of firmware and checks if it fits into the flash and ram of the target device
# The RAM size is based on the DATA section of the ELF file
# The flash size is based on the ihx file which strips out any RAM related sections
size_check: $(BUILD_DIR)/$(PROJECT).ihx $(BUILD_DIR)/$(PROJECT).elf
	@echo "\nPROGRAM SIZE:"; \
	TOO_LARGE_RAM=0; \
	TOO_LARGE_FLASH=0; \
	USED_RAM=$$($(SIZE) -A $(BUILD_DIR)/$(PROJECT).elf | grep -o 'DATA.*[0-9]* ' | grep -o '[0-9]*' || echo 0 ); \
	USED_RAM=$$(echo $$USED_RAM | tr -d '[:space:]' ); \
	RAM_SIZE=$$(echo $(RAM_SIZE) | tr -d '[:space:]' ); \
	echo "------------------------------------------------------"; \
	echo "RAM:\tUsed $$USED_RAM bytes from $$RAM_SIZE bytes ($$(((100 * USED_RAM)/$(RAM_SIZE)))%)"; \
	if [ $$USED_RAM -gt $(RAM_SIZE) ]; then \
		TOO_LARGE_RAM=1; \
	fi; \
	USED_FLASH=$$($(SIZE) -A $(BUILD_DIR)/$(PROJECT).ihx | grep -o 'Total.*[0-9]' | grep -o '[0-9]*' || echo 0 ); \
	USED_FLASH=$$(echo $$USED_FLASH | tr -d '[:space:]' ); \
	FLASH_SIZE=$$(echo $(FLASH_SIZE) | tr -d '[:space:]' ); \
	echo "FLASH:\tUsed $$USED_FLASH bytes from $$FLASH_SIZE bytes ($$(((100 * USED_FLASH)/$(FLASH_SIZE)))%)"; \
	if [ $$USED_FLASH -gt $(FLASH_SIZE) ]; then \
		TOO_LARGE_FLASH=1; \
	fi; \
	echo "------------------------------------------------------"; \
	if [ $$TOO_LARGE_RAM -eq 1 ]; then echo "ERROR: Program exceeds RAM!"; fi; \
	if [ $$TOO_LARGE_FLASH -eq 1 ]; then echo "ERROR: Program exceeds FLASH!"; fi; \
	if [ $$TOO_LARGE_RAM -eq 1 ] || [ $$TOO_LARGE_FLASH -eq 1 ]; then exit 1; fi
