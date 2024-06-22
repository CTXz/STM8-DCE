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
 * Description: Template main file for STM8S103F3P6 PlatformIO projects
 */

#include <stdio.h>

#include "midirx.h"
#include "midirx_uart_parser.h"
#include "midirx_msg.h"

typedef enum {
	STATUS,
	DATA1,
	DATA2,
	SYSEX
} midi_rx_state_t;

/**
 * @brief Calls callback functions after a MIDI message has been received
 * @param msg Pointer to a @ref midi_msg_t struct
 */
inline void on_midi_rx_complete(midi_msg_t *msg)
{
	if (_midi_msg_callback == NULL)
		return;

	_midi_msg_callback(msg);
}

#ifdef SYSEX_ENABLED

#ifndef MAX_SYSEX_LEN
#error "MAX_SYSEX_LEN must be defined if SysEx is enabled"
#endif

typedef enum {
	RECEIVING,
	DONE,
	LEN_EXCEEDED,
	INVALID
} sysex_rx_state_t;

inline void on_sysex_complete(uint8_t *data, size_t len)
{
	if (_sysex_msg_callback == NULL)
		return;

	_sysex_msg_callback(data, len);
}

inline sysex_rx_state_t parse_sysex(uint8_t data)
{
	static uint8_t buf[MAX_SYSEX_LEN];
	static size_t buf_index = 0;

	if (data == MIDI_STAT_SYSEX_END) {
		if (buf_index > 0) {
			on_sysex_complete(buf, buf_index);
			buf_index = 0;
		}

		return DONE;
	}

	if (!midirx_is_data(data))
		return INVALID;

	if (buf_index == MAX_SYSEX_LEN) {
		buf_index = 0;
		return LEN_EXCEEDED;
	}

	buf[buf_index++] = data;
	return RECEIVING;
}

#endif

// See header file for documentation
void midirx_parse_uart_rx(uint8_t data)
{
	static midi_msg_t msg;
	static midi_rx_state_t state = STATUS;

	switch (state) {
	case STATUS:
		if (!midirx_is_status(data)) {
			return;
		}

#ifdef SYSEX_ENABLED
		if (midirx_status_is_cmd(data, MIDI_STAT_SYSEX)) {
			state = SYSEX;
			return;
		}
#endif
		if (_midi_status_filter != NULL &&
		    !_midi_status_filter(data)) {
			return;
		}

		msg.status = data;
		state = DATA1;

		break;

#ifdef SYSEX_ENABLED
	case SYSEX:
		if (parse_sysex(data) != RECEIVING)
			state = STATUS;
		break;
#endif

	case DATA1:
		if (!midirx_is_data(data)) {
			state = STATUS;
			return;
		}

		msg.data1 = data;
		state = DATA2;
		break;

	case DATA2:
		if (!midirx_is_data(data)) {
			state = STATUS;
			return;
		}

		msg.data2 = data;
		state = STATUS;
		on_midi_rx_complete(&msg);
		break;
	}
}