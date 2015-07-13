/*
 * Copyright (C) 2009-2012 Chris McClelland
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef PROM_H
#define PROM_H

#include <makestuff.h>

bool promRead(bool bank, uint16 addr, uint8 length, __xdata uint8 *buf);
bool promWrite(bool bank, uint16 addr, uint8 length, const __xdata uint8 *buf);

bool promStartRead(bool bank, uint16 address);
bool promNextByte(void);
uint8 promPeekByte(void);
bool promStopRead(void);

#endif
