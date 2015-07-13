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
#ifndef DEFS_H
#define DEFS_H

// Make SYNCDELAY look like the Cypress code
#define SYNCDELAY SYNCDELAY4;

// Size of endpoint zero buffer
#define EP0BUF_SIZE 0x40

// OUTPKTEND bits
#define bmSKIP bmBIT7

// IFCONFIG bits
#define bmPORTS 0
#define bmGPIF  (bmIFCFG1)
#define bmFIFOS (bmIFCFG1 | bmIFCFG0)

// EPxCFG bits
#define bmBULK bmBIT5
#define bmBUF2X bmBIT1

// EP01STAT bits
#define bmEP1INBSY bmBIT2
#define bmEP1OUTBSY bmBIT1

// AUTOPTRSETUP
#define bmAPTREN bmBIT0
#define bmAPTR1INC bmBIT1
#define bmAPTR2INC bmBIT2

// REVCTL bits
#define bmDYN_OUT (1<<1)
#define bmENH_PKT (1<<0)

// USB command macros, copied from Dean Camera's LUFA package
#define REQDIR_DEVICETOHOST (1 << 7)
#define REQDIR_HOSTTODEVICE (0 << 7)
#define REQTYPE_CLASS       (1 << 5)
#define REQTYPE_STANDARD    (0 << 5)
#define REQTYPE_VENDOR      (2 << 5)

__sfr __at 0x9c AUTODAT1;
__sfr __at 0x9f AUTODAT2;

// Defines to allow use of camelCase.
#define mainInit(x) main_init(x)
#define mainLoop(x) main_loop(x)
#define handleVendorCommand handle_vendorcommand

#endif
