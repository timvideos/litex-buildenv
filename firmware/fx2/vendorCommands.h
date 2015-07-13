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
#ifndef VENDORCOMMANDS_H
#define VENDORCOMMANDS_H

// Vendor commands
#define CMD_MODE_STATUS       0x80
#define CMD_PROG_CLOCK_DATA   0x81
#define CMD_JTAG_CLOCK_FSM    0x82
#define CMD_JTAG_CLOCK        0x83
#define CMD_CALCULATOR        0x84
#define CMD_PORT_BIT_IO       0x85
#define CMD_PORT_MAP          0x86
#define CMD_BOOTLOADER        0x87
#define CMD_READ_WRITE_EEPROM 0xA2

typedef enum {
	PROG_NOP,
	PROG_JTAG_ISSENDING_ISRECEIVING,
	PROG_JTAG_ISSENDING_NOTRECEIVING,
	PROG_JTAG_NOTSENDING_ISRECEIVING,
	PROG_JTAG_NOTSENDING_NOTRECEIVING,
	PROG_PARALLEL,
	PROG_SPI_SEND,
	PROG_SPI_RECV
} ProgOp;

#define bmISLAST       (1<<0)
#define bmSENDONES     (1<<1)

#endif
