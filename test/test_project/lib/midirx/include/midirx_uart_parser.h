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

#ifndef _MIDIRX_UART_PARSER_H_INCLUDED
#define _MIDIRX_UART_PARSER_H_INCLUDED

#include <stm8s.h>

/**
 * @brief Parses incoming UART data as MIDI messages
 *
 * The following function parses incoming UART data as MIDI.
 * It is intended to be called from an UART RX interrupt
 * service routine.
 *
 * Once a complete MIDI message has been received, the
 * @ref _midi_msg_callback function is called, which can
 * be set by the @ref midirx_on_midi_msg function.
 *
 * @param data Received UART data
 */
void midirx_parse_uart_rx(uint8_t data);

#endif // _MIDIRX_UART_PARSER_H_INCLUDED