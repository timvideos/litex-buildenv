/*
 * Copyright 2015 Tim Ansell <mithro@mithis.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 2.1 of the License, or
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

#include <i2c.h>

// Convert a byte into the ASCII hex equivalent.
char hex(BYTE value) {
	if (value > 0x0f) {
		return '?';
	} else if (value > 0x09) {
		return 'a'+(value-0x0a);
	} else {
		return '0'+value;
	}
}

// Patch the serial number in the device descriptor table.
extern __xdata char dev_serial[];
void patch_serial_number(BYTE index, BYTE value) {
	dev_serial[index*4] = hex(value >> 4);
	dev_serial[index*4+2] = hex(value & 0xf);
}

#define PROM_ADDRESS 0x51
#define PROM_ID_OFFSET 0xf8
#define PROM_ID_SIZE 8

// Patch the USB serial number with information from the MAC address EEPROM.
void patch_usb_serial_number_with_eeprom_macaddress() {
	BYTE tempbyte = 0;
	BYTE i = 0;

	dev_serial[0] = 'f';
	//pSerial[2] = ((WORD)'e') << 8;

	for (i=0; i < PROM_ID_SIZE; i++) {
        	eeprom_read(PROM_ADDRESS, PROM_ID_OFFSET+i, 1, &tempbyte);
		patch_serial_number(i, tempbyte);
	}
}
