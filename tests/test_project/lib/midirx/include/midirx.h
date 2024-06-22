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

#ifndef _MIDIRX_INCLUDED
#define _MIDIRX_INCLUDED

#include <stddef.h>

#include <stm8s.h>

#include "midirx_msg.h"
#include "midirx_notes.h"
#include "midirx_uart_parser.h"

/**
 * @brief Calls the provided callback function when a MIDI message has been received
 * @param callback Pointer to a callback function
 * @note The callback function must take a pointer to a @ref midi_msg_t struct as its only argument
 */
void midirx_on_midi_msg(void (*callback)(midi_msg_t *msg));
extern void (*_midi_msg_callback)(midi_msg_t *msg); ///< Pointer to the callback function

void midirx_on_sysex_msg(void (*callback)(uint8_t *data, size_t len));
extern void (*_sysex_msg_callback)(uint8_t *data, size_t len);

/**
 * @brief Calls a callback function which pre-emptively filters incoming MIDI messages based on their status byte
 *
 * The following function accepts a filter function which takes a MIDI status byte and a MIDI channel as arguments.
 * If the filter function returns true, the MIDI message is further processed and the on_midi_msg callback is called,
 * otherwise it is discarded, saving plenty of processing time.
 */
void midirx_set_status_filter(bool (*callback)(midi_status_t status));
extern bool (*_midi_status_filter)(midi_status_t status);

#endif // _MIDIRX_INCLUDED