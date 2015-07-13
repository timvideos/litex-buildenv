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
#include <makestuff.h>
#include "progOffsets.h"

const uint16 *__xdata classList[] = {tdoList, tdiList, tmsList, tckList, ioaList};

// Base address of JTAG code
void progClockFSM(uint32 bitPattern, uint8 transitionCount);

void livePatch(uint8 patchClass, uint8 newByte) {
	__xdata uint8 *__xdata const codeBase = (__xdata uint8 *)progClockFSM;
	__xdata uint16 thisOffset;
	const uint16 *__xdata ptr = classList[patchClass];
	thisOffset = *ptr++;
	while ( thisOffset ) {
		*(codeBase + thisOffset) = newByte;
		thisOffset = *ptr++;
	}	
}
