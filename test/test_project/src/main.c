/*
 * Copyright (C) 2023 Patrick Pedersen, TU-DO Makerspace

 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.

 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * Description: Main firmware code for the Dampflog Interface Board.
 *
 */

#include <stdio.h>

#include <stm8s.h>
#include <stm8s_it.h>

#include <log.h>
#include <msp49xx.h>
#include <midirx.h>

////////////////////////////////////////////
// Defines (Pins, Magic Numbers, etc.)
////////////////////////////////////////////

// Meta

#define FIMRWARE_REV "0.1"
#define SOURCE_CODE "https://github.com/TU-DO-Makerspace/Dampflog"

// DAC

#define CS_PORT GPIOC
#define CS_PIN GPIO_PIN_4

#define SCK_PORT GPIOC
#define SCK_PIN GPIO_PIN_5

#define MOSI_PORT GPIOC
#define MOSI_PIN GPIO_PIN_6

#define LDAC_PORT GPIOD
#define LDAC_PIN GPIO_PIN_2

#define MAX_DAC_VALUE 0x0FFF

// GATE

#define GATE_PORT GPIOC
#define GATE_PIN GPIO_PIN_3

#define OPEN_GATE() GPIO_WriteHigh(GATE_PORT, GATE_PIN)
#define CLOSE_GATE() GPIO_WriteLow(GATE_PORT, GATE_PIN)

// UART + MIDI + SYSEX

#define EEPROM_MIDI_2_DAC_LUT_START FLASH_DATA_START_PHYSICAL_ADDRESS

#define UART_PORT GPIOD
#define UART_TX_PIN GPIO_PIN_5
#define UART_RX_PIN GPIO_PIN_6

#define UART_MIDI_BAUD 31250

#define MIDI_N_NOTES MIDI_DATA_MAX_VAL + 1

#define SYSEX_MANUFACTURER_ID 0x7D // Manufacturer ID for private use

#define SYSEX_SET_DAC 0x01

#define SYSEX_SET_GATE 0x02
#define SYSEX_SET_GATE_CLOSE_VAL 0x00
#define SYSEX_SET_GATE_OPEN_VAL 0x01

#define SYSEX_WRITE_MIDI_2_DAC_LUT 0x03

////////////////////////////////////////////
// Global MIDI to DAC Look-up Table
////////////////////////////////////////////

uint16_t midi2dac[MIDI_N_NOTES];

////////////////////////////////////////////
// DAC Configuration
////////////////////////////////////////////

const mcp49xx_cfg cfg = {
	.dac = WRITE,
	.buffer = DAC_BUF_ON,
	.gain = DAC_GAIN_1X,
	.shutdown = DAC_ACTIVE,
};

////////////////////////////////////////////
// Peripheral Setup
////////////////////////////////////////////

/**
 * @brief Sets up the GPIO's
 */
void setup_gpios(void)
{
	// DAC (SPI)
	GPIO_Init(CS_PORT, CS_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(SCK_PORT, SCK_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(MOSI_PORT, MOSI_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);

	// Tie LDAC low since we only have one DAC.
	GPIO_Init(LDAC_PORT, LDAC_PIN, GPIO_MODE_OUT_PP_LOW_FAST);

	// MIDI/UART
	GPIO_Init(UART_PORT, UART_TX_PIN, GPIO_MODE_OUT_PP_HIGH_FAST);
	GPIO_Init(UART_PORT, UART_RX_PIN, GPIO_MODE_IN_PU_NO_IT);

	// GATE
	GPIO_Init(GATE_PORT, GATE_PIN, GPIO_MODE_OUT_PP_LOW_FAST);
}

/**
 * @brief Sets up the clocks
 */
void setup_clocks(void)
{
	CLK_DeInit();
	CLK_HSECmd(DISABLE);
	CLK_LSICmd(DISABLE);
	CLK_HSICmd(ENABLE);

	while (CLK_GetFlagStatus(CLK_FLAG_HSIRDY) == FALSE)
		;

	CLK_ClockSwitchCmd(ENABLE);
	CLK_HSIPrescalerConfig(CLK_PRESCALER_HSIDIV1);
	CLK_SYSCLKConfig(CLK_PRESCALER_CPUDIV1);
	CLK_ClockSwitchConfig(CLK_SWITCHMODE_AUTO, CLK_SOURCE_HSI, DISABLE, CLK_CURRENTCLOCKSTATE_ENABLE);

	CLK_PeripheralClockConfig(CLK_PERIPHERAL_SPI, ENABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_I2C, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_ADC, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_AWU, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_UART1, ENABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER1, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER2, DISABLE);
	CLK_PeripheralClockConfig(CLK_PERIPHERAL_TIMER4, DISABLE);
}

/**
 * @brief Set up
 */
void setup_spi(void)
{
	SPI_DeInit();
	SPI_Init(
	    SPI_FIRSTBIT_MSB,
	    SPI_BAUDRATEPRESCALER_2,
	    SPI_MODE_MASTER,
	    SPI_CLOCKPOLARITY_LOW,
	    SPI_CLOCKPHASE_1EDGE,
	    SPI_DATADIRECTION_1LINE_TX,
	    SPI_NSS_SOFT,
	    0x01); // > 0x00, else assertion will fail.
	SPI_Cmd(ENABLE);
}

/**
 * @brief Sets up the UART
 */
void setup_uart(void)
{
	UART1_DeInit();
	UART1_Init(
	    UART_MIDI_BAUD,
	    UART1_WORDLENGTH_8D,
	    UART1_STOPBITS_1,
	    UART1_PARITY_NO,
	    UART1_SYNCMODE_CLOCK_DISABLE,
	    UART1_MODE_TXRX_ENABLE);
	UART1_ITConfig(UART1_IT_RXNE_OR, ENABLE);
	enableInterrupts();
	UART1_Cmd(ENABLE);
}

/**
 * @brief Sets up the EEPROM
 */
void setup_eeprom(void)
{
	FLASH_DeInit();
	FLASH_SetProgrammingTime(FLASH_PROGRAMTIME_STANDARD);
}

////////////////////////////////////////////
// MIDI to DAC LUT
////////////////////////////////////////////

/**
 * @brief Initializes/Loads the MIDI to DAC LUT from "EEPROM" (Data flash)
 * @NOTE: Call this function before using the LUT (e.g. on startup)
 */
void midi2dac_from_eeprom()
{
	FLASH_Unlock(FLASH_MEMTYPE_DATA);
	while (FLASH_GetFlagStatus(FLASH_FLAG_DUL) == RESET);

	for (uint8_t i = 0; i < MIDI_N_NOTES; i++) {
		uint16_t addr = EEPROM_MIDI_2_DAC_LUT_START + (i * 2);
		uint8_t msb = FLASH_ReadByte(addr);
		uint8_t lsb = FLASH_ReadByte(addr + 1);
		midi2dac[i] = (msb << 8) | lsb;
	}

	FLASH_Lock(FLASH_MEMTYPE_DATA);
}

/**
 * @brief Burns a MIDI to DAC LUT entry to "EEPROM" (Data flash)
 * @param note MIDI note number
 * @param dacval DAC value
 *
 * Writes a MIDI to DAC LUT entry to "EEPROM" (Data flash).
 * Each DAC value is 12 bits wide, thus requiring two bytes of
 * flash storage.
 */
void midi2dac_write_eeprom(uint8_t note, uint16_t dacval)
{
	FLASH_Unlock(FLASH_MEMTYPE_DATA);
	while (FLASH_GetFlagStatus(FLASH_FLAG_DUL) == RESET);

	uint16_t addr = EEPROM_MIDI_2_DAC_LUT_START + (note * 2);
	uint8_t msb = dacval >> 8;
	uint8_t lsb = dacval & 0xFF;

	FLASH_ProgramByte(addr, msb);
	FLASH_ProgramByte(addr + 1, lsb);

	FLASH_Lock(FLASH_MEMTYPE_DATA);
}

////////////////////////////////////////////
// SPI
////////////////////////////////////////////

/**
 * @brief Writes 16 bits to SPI
 */
void spi_write16(uint16_t data)
{
	while (SPI_GetFlagStatus(SPI_FLAG_BSY))
		;
	GPIO_WriteLow(CS_PORT, CS_PIN);

	// Transmit MSB first.
	SPI_SendData(data >> 8);
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	// Transmit LSB.
	SPI_SendData(data & 0xFF);
	while (!SPI_GetFlagStatus(SPI_FLAG_TXE))
		;

	GPIO_WriteHigh(CS_PORT, CS_PIN);
}

////////////////////////////////////////////
// MIDI
////////////////////////////////////////////

/**
 * @brief Status filter callback to ignore irrelevant MIDI messages
 * @param status MIDI status byte passed by midirx
 * @return True if the message should be processed, false if it should be discarded
 */
bool status_filter(midi_status_t status)
{
	if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_ON) ||
	    midirx_status_is_cmd(status, MIDI_STAT_NOTE_OFF)) {
		return true;
	}

	return false;
}

/**
 * @brief MIDI message callback, handles incoming MIDI messages
 * @param msg MIDI message passed by midirx
 *
 * Callback to handle incoming MIDI messages.
 * Currently the handler does the following:
 * 	- On NOTE ON:
 * 		- Set the DAC to the corresponding value
 * 		- Open the GATE
 * 	- On NOTE OFF:
 * 		- Close the GATE
 *	- Unhandled messages are discarded
 */
void handle_midi_msg(midi_msg_t *msg)
{
	const midi_status_t status = msg->status;
	// const uint8_t ch = midirx_get_ch(status);

	LOG_DEBUG("Processing MIDI Message: %02X, %02X, %02X", msg->status, msg->data1, msg->data2);

	if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_ON)) {
		const uint8_t note = msg->data1;

		LOG_DEBUG("Message is NOTE ON, Note: %d", note);

		// Should never occur, but just in case.
		if (note > MIDI_DATA_MAX_VAL) {
			LOG_DEBUG("Invalid NOTE ON, note is out of range (0-127)");
			return;
		}

		const uint16_t dacval = midi2dac[note];

		LOG_DEBUG("Note %d is mapped to DAC value %d", note, dacval);

		spi_write16(mcp49xx_data(&cfg, dacval));

		LOG_DEBUG("DAC set to %d", dacval);

		OPEN_GATE();
		LOG_DEBUG("Opened GATE");
	} else if (midirx_status_is_cmd(status, MIDI_STAT_NOTE_OFF)) {
		LOG_DEBUG("Message is NOTE OFF, Note: %d", msg->data1);

		CLOSE_GATE();
		LOG_DEBUG("Closed GATE");

		/* Please note that the GATE is OR'd with the analog
		 * gate input (GATE Jack and HOLD Switch), meaning that
		 * the gate will only be closed if the analog gate input
		 * is also closed. */
	} else {
		LOG_DEBUG("Unhandled MIDI message: %02X", status);
	}
}

////////////////////////////////////////////
// SYSEX
////////////////////////////////////////////

/**
 * @brief SYSEX message callback, handles incoming SYSEX messages
 * @param buf SYSEX message buffer passed by midirx
 * @param len Length of the SYSEX message
 *
 * Callback to handle incoming SYSEX messages.
 *
 * THe fomat of a SYSEX message is as follows:
 *
 * 	0xF0 <MANUFACTURER_ID> <MESSAGE_TYPE> <DATA1> <DATA2> ... 0xF7
 *
 * The expected manufacturer ID and possible message types are defined
 * in the defines section at the top of this file.
 *
 * Currently the handler does the following:
 * 	- On SET DAC <DAC VALUE MSB> <DAC VALUE LSB>:
 * 		- Set the DAC to the corresponding 12-bit value
 * 	- On SET GATE <GATE VALUE>:
 * 		- Open or close the GATE
 * 		- The GATE value is expected to be either 0x00 (close) or 0x01 (open)
 * 	- Invalid or unhandled messages are discarded
 *
 **/
void handle_sysex_msg(uint8_t *buf, size_t len)
{
	LOG_DEBUG("Processing SYSEX message");

	if (len < 2) {
		LOG_DEBUG("SYSEX message is too short to be valid")
		return;
	}

	const uint8_t manufacturer_id = buf[0];
	const uint8_t message_type = buf[1];

	if (manufacturer_id != SYSEX_MANUFACTURER_ID) {
		LOG_DEBUG("Missmatching SYSEX Manufacturer ID");
		return;
	}

	switch (message_type) {
	case SYSEX_SET_DAC:
		if (len == 4) {
			LOG_DEBUG("Received SET DAC message");
			// Sysex only supports 7-bit data values.
			// To transmit the 12-bits required for the DAC,
			// we need to combine two 7-bit values into one 12-bit value.
			uint16_t value = buf[2] << 7 | buf[3];
			spi_write16(mcp49xx_data(&cfg, value));
			LOG_DEBUG("Set DAC to %d", value);
		} else {
			LOG_DEBUG("Bad SET DAC message");
		}
		break;
	case SYSEX_SET_GATE:
		if (len == 3) {
			LOG_DEBUG("Received SET GATE message");

			uint8_t value = buf[2];
			if (value == SYSEX_SET_GATE_CLOSE_VAL) {
				CLOSE_GATE();
				LOG_DEBUG("Closed gate");
			} else if (value == SYSEX_SET_GATE_OPEN_VAL) {
				OPEN_GATE();
				LOG_DEBUG("Opened gate");
			} else {
				LOG_DEBUG("Invalid GATE value");
			}
		} else {
			LOG_DEBUG("Bad SET GATE message");
		}
		break;
	case SYSEX_WRITE_MIDI_2_DAC_LUT:
		if (len == 5) {
			// disableInterrupts();

			LOG_DEBUG("Received WRITE MIDI 2 DAC LUT message");

			uint8_t note = buf[2];
			uint16_t dacval = buf[3] << 7 | buf[4];

			if (note > MIDI_DATA_MAX_VAL) {
				LOG_DEBUG("Invalid NOTE value");
				return;
			}

			if (dacval > MAX_DAC_VALUE) {
				LOG_DEBUG("Invalid DAC value");
				return;
			}

			midi2dac[note] = dacval;
			midi2dac_write_eeprom(note, dacval);

			// enableInterrupts();
		} else {
			LOG_DEBUG("Bad WRITE MIDI 2 DAC LUT message");
		}
	default:
		break;
	}
}

////////////////////////////////////////////
// Main
////////////////////////////////////////////

/**
 * @brief Main function
 *
 * Sets up callbacks and peripherals and then enters an infinite loop.
 * The callbacks are called by the midirx library through external interrupts.
 */
void main(void)
{
	// Initialization
	setup_clocks();

	setup_eeprom();
	midi2dac_from_eeprom();
	
	setup_gpios();
	setup_spi();

	midirx_set_status_filter(status_filter);
	midirx_on_midi_msg(handle_midi_msg);
	midirx_on_sysex_msg(handle_sysex_msg);
	setup_uart();

	LOG("Dampflog Interface Board")
	LOG("Firmware Revision: %s", FIMRWARE_REV);
	LOG("Source Code: %s", SOURCE_CODE);

	LOG("Listening for MIDI messages...");
	while (true)
		;
}

// See: https://community.st.com/s/question/0D50X00009XkhigSAB/what-is-the-purpose-of-define-usefullassert
#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
	while (TRUE) {
	}
}
#endif
