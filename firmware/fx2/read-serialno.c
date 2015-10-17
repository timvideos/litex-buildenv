
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
void patch_serial_number_with_eeprom_macaddress() {
	BYTE tempbyte = 0;

	dev_serial[0] = 'f';
	//pSerial[2] = ((WORD)'e') << 8;

	for (int i=0; i < PROM_ID_SIZE; i++) {
        	eeprom_read(PROM_ADDRESS, PROM_ID_OFFSET+i, 1, &tempbyte);
		patch_serial_number(i, tempbyte);
	}
}
