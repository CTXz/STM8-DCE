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
 * Description: Provides structs and functions to drive MCP49xx DACs.
 *
 */

#ifndef _MSP49XX_H_INCLUDED
#define _MSP49XX_H_INCLUDED

#include <stm8s.h>

////////////////////////////////////////////////////////
// Enums for DAC configuration
// Refer to your DAC's datasheet for more information.
////////////////////////////////////////////////////////

/* Configuration data is sent as a 4-bit header (bit 15-
 * -12) when writing to the DAC. Bit 16 is ignored and
 *  bit 11-0 represent the value to be written to the DAC.
 */

/* Bit 15 - DAC Select
 * - On 49x1's, this bit defines if the value is written to
 *   the DAC or ignored.
 * - On 49x2's, this bit defines which DAC (A or B) is selected.
 */
typedef enum
{
	WRITE = 0,  // 49x1's
	IGNORE = 1, // 49x1's
	DAC_A = 0,  // 49x2's
	DAC_B = 1   // 49x2's
} DAC;

typedef DAC DAC_APPLY; // 49x1's only have one DAC, so the bit is interpreted as apply or ignore

// Bit 14 - Input Buffer Control
typedef enum
{
	DAC_BUF_OFF = 0,
	DAC_BUF_ON = 1
} DAC_BUF;

// Bit 13 - Gain Selection
typedef enum
{
	DAC_GAIN_1X = 1,
	DAC_GAIN_2X = 0
} DAC_GAIN;

// Bit 12 - Output Shutdown Control
typedef enum
{
	DAC_SHUTDOWN = 0,
	DAC_ACTIVE = 1
} DAC_SHDN;

////////////////////////////////////////////////////////
// Structs
////////////////////////////////////////////////////////

/**
 * @brief Configuration struct for MCP49xx DACs.
 * Struct used to configure the MCP49xx DACs. Pass an initialized
 * instance of this struct to the mcp49xx_data() function to generate
 * the 16-bit data to be sent to the DAC.
 */
typedef struct
{
	DAC dac;
	DAC_BUF buffer;
	DAC_GAIN gain;
	DAC_SHDN shutdown;
} mcp49xx_cfg;

////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////

typedef uint16_t mcp49xx_data_t;

/**
 * @brief Generates the 16-bit data to be sent to the DAC.
 * @param cfg Configuration struct for the DAC.
 * @param value Value to be written to the DAC.
 * @return 16-bit data to be sent to the DAC via SPI.
 */
mcp49xx_data_t mcp49xx_data(mcp49xx_cfg *cfg, uint16_t value);

#endif