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
 * Description: Defines functions relevant for logging over UART.
 *
 */

#include <stdio.h>
#include <stm8s.h>
#include <log.h>

// Defines putchar() to complete the stdio.h interface.
int putchar(int c)
{
	while (UART1_GetFlagStatus(UART1_FLAG_TXE) != SET)
		;
	UART1_SendData8(c);
	return c;
}