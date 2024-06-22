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

#ifndef _MIDIRX_MSG_H_INCLUDED
#define _MIDIRX_MSG_H_INCLUDED

#include <stm8s.h>
#include <stdbool.h>

#define MIDI_DATA_MAX_VAL 127

#define MIDI_DATA_MSB_MASK 0x80
#define MIDI_STAT_CH_CMD_MSK 0xF0
#define MIDI_STAT_CH_MSK 0x0F

#define MIDI_STAT_SYS_COMMON_START 0xF0

// https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message
typedef enum {
	MIDI_STAT_NOTE_OFF		= 0x80,
	MIDI_STAT_NOTE_ON		= 0x90,
	MIDI_STAT_POLY_AT		= 0xA0,
	MIDI_STAT_CTRL_CHG		= 0xB0,
	MIDI_STAT_PRG_CHG		= 0xC0,
	MIDI_STAT_CHN_AT		= 0xD0,
	MIDI_STAT_PITCH_BND		= 0xE0,
	MIDI_STAT_SYSEX			= 0xF0,
	MIDI_STAT_MTC_QF		= 0xF1,
	MIDI_STAT_SONG_POS		= 0xF2,
	MIDI_STAT_SONG_SEL		= 0xF3,
	MIDI_STAT_TUNE_REQ		= 0xF6,
	MIDI_STAT_SYSEX_END		= 0xF7,
	MIDI_STAT_TIMING_CLK		= 0xF8,
	MIDI_STAT_TIMING_START		= 0xFA,
	MIDI_STAT_TIMING_CONTINUE	= 0xFB,
	MIDI_STAT_TIMING_STOP		= 0xFC,
	MIDI_STAT_ACTIVE_SENSING	= 0xFE,
	MIDI_STAT_SYSTEM_RESET		= 0xFF,
} midi_status_cmd_t;

typedef uint8_t midi_status_t;
typedef uint8_t midi_data_t;

typedef struct {
	midi_status_t status;
	midi_data_t data1;
	midi_data_t data2;
} midi_msg_t;

inline bool _is_ch_msg(midi_status_t status_byte)
{
	uint8_t msb4 = status_byte & MIDI_STAT_CH_CMD_MSK;
	return (msb4 < MIDI_STAT_SYS_COMMON_START);
}

/**
 * @brief Returns if a status byte matches a MIDI command
 * @param status_byte MIDI status byte
 * @param cmd MIDI command to match
 * @return True if the status byte matches the command
 */
inline bool midirx_status_is_cmd(midi_status_t status_byte, midi_status_cmd_t cmd)
{
	if (_is_ch_msg(status_byte))
		return (status_byte & MIDI_STAT_CH_CMD_MSK) == cmd;
	else
		return status_byte == cmd;
}

/**
 * @brief Returns the channel from a MIDI status byte
 * @note Only use this function if the status byte contains a channel
 * @param status_byte MIDI status byte
 * @return MIDI channel
 */
inline uint8_t midirx_get_ch(midi_status_t status_byte)
{
	return status_byte & MIDI_STAT_CH_MSK;
}

/**
 * @brief Returns if the byte is a MIDI status byte
 *
 * This function can be used to determine if a byte is a status byte.
 *
 * A status byte must always have the most significant bit set.
 *
 * This function is also useful to prevent misaligned data if the
 * MCU cannot receive data fast enough.
 *
 * @param data byte of data
 * @return true if the data is a status byte
 */
inline bool midirx_is_status(uint8_t data)
{
	return (data & MIDI_DATA_MSB_MASK);
}

/**
 * @brief Returns if the byte is a MIDI data byte
 *
 * This function can be used to determine if a byte is a data byte.
 *
 * A data byte must always have the most significant bit set.
 *
 * This function is also useful to prevent misaligned data if the
 * MCU cannot receive data fast enough.
 *
 * @param data byte of data
 * @return true if the data is a data byte
 */
#define midirx_is_data(data) (!midirx_is_status(data))

#endif //_MIDIRX_MSG_H_INCLUDED