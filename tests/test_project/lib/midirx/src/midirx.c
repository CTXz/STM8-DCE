/*
 * Copyright (C) 2023 Patrick Pedersen

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
 */

#include "midirx.h"
#include "midirx_msg.h"

// See header file for documentation
void (*_midi_msg_callback)(midi_msg_t *msg) = NULL;
void midirx_on_midi_msg(void (*callback)(midi_msg_t *msg))
{
	_midi_msg_callback = callback;
}

// See header file for documentation
void (*_sysex_msg_callback)(uint8_t *data, size_t len) = NULL;
void midirx_on_sysex_msg(void (*callback)(uint8_t *data, size_t len))
{
	_sysex_msg_callback = callback;
}

// See header file for documentation
bool (*_midi_status_filter)(midi_status_t status);
void midirx_set_status_filter(bool (*callback)(midi_status_t status))
{
	_midi_status_filter = callback;
}
