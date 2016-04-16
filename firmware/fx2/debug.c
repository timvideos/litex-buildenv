#include <fx2regs.h>
#include <makestuff.h>
#include "debug.h"

#ifdef DEBUG
__sbit __at 0xB3 USART; //0xB7 USART; // Port D7
#define BAUD 32

void usartInit(void) {
	USART = 1;
	OED |= 0xff; //0x80;
}

void usartSendByte(uint8 c) {
	(void)c; /* argument passed in DPL */
	__asm
		mov a, dpl
		mov r1, #9
		clr c
	loop:
		mov _USART, c
		rrc a
		mov r0, #BAUD
		djnz r0, .
		nop
		djnz r1, loop

		;; Stop bit
		setb _USART
		mov r0, #BAUD
		djnz r0, .
	__endasm;
}
void usartSendByteHex(uint8 byte) {
	__xdata uint8 ch;
	ch = (byte >> 4) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = byte & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
}
void usartSendWordHex(uint16 word) {
	__xdata uint8 ch;
	ch = (word >> 12) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 8) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 4) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 0) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
}
void usartSendLongHex(uint32 word) {
	__xdata uint8 ch;
	ch = (word >> 28) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 24) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 20) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 16) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 12) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 8) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 4) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
	ch = (word >> 0) & 0x0F;
	ch += (ch < 10 ) ? '0' : 'A' - 10;
	usartSendByte(ch);
}
void usartSendString(const char *s) {
	while ( *s ) {
		usartSendByte(*s++);
	}
}
#endif
