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
 * Description: Provides macros for logging over UART.
 *
 */

#ifndef _LOG_H_INCLUDED
#define _LOG_H_INCLUDED

#include <stdio.h>

/**
 * @brief Logs a message to UART
 * Logs a message to UART, including the file, line and function name.
 * @param ... Message to log, including format specifiers (i.e like printf()).
 */
#define LOG(...)                                             \
	printf("%s:%d, %s: ", __FILE__, __LINE__, __func__); \
	printf(__VA_ARGS__);                                 \
	printf("\n");

// Same as LOG(), but not built if DEBUG is not defined.
#ifdef DEBUG
#define LOG_DEBUG(...) LOG(__VA_ARGS__)
#else
#define LOG_DEBUG(...)
#endif

#endif // _LOG_H_INCLUDED