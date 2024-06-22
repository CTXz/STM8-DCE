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
 * Description: Defines functions exposed by the msp49xx.h header file.
 * 	    	For more information, please refer to the header file.
 *
 */

#include <msp49xx.h>

#define CFG_HEADER_DAC_BIT 15
#define CFG_HEADER_BUF_BIT 14
#define CFG_HEADER_GAIN_BIT 13
#define CFG_HEADER_SHDN_BIT 12

// See header file for documentation.
mcp49xx_data_t mcp49xx_data(mcp49xx_cfg *cfg, uint16_t value)
{
	// Configuration header
	uint16_t data = 0;
	data |= (cfg->dac << CFG_HEADER_DAC_BIT);
	data |= (cfg->buffer << CFG_HEADER_BUF_BIT);
	data |= (cfg->gain << CFG_HEADER_GAIN_BIT);
	data |= (cfg->shutdown << CFG_HEADER_SHDN_BIT);

	// DAC Value
	data |= (value & 0x0FFF); // Max 12 bits.

	return data;
}