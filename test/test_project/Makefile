ifndef BUILD_DIR
$(error BUILD_DIR is not set)
endif

#######################################
# Toolchain
#######################################

CC = sdcc
LD = sdcc
AS = sdasstm8
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
# MIDI RX Library
#######################################

VPATH += lib/midirx/src
INCLUDE += -Ilib/midirx/include
INCLUDE += -Ilib/midirx/src

SRC_FILES += $(wildcard lib/midirx/src/*.c)

#######################################
# Project targets
#######################################

ASM = $(addprefix $(ASM_DIR)/, $(notdir $(SRC_FILES:.c=.asm)))
DCE_ASM = $(addprefix $(DCE_DIR)/, $(notdir $(ASM:.asm=.asm)))
OBJ = $(addprefix $(OBJ_DIR)/, $(notdir $(ASM:.asm=.rel)))

all: $(BUILD_DIR)/$(PROJECT).elf

elf: $(BUILD_DIR)/$(PROJECT).elf
obj: $(OBJ)
asm: $(ASM)
dce: $(DCE_ASM)

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