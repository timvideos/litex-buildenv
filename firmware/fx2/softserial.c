#include "debug.h"
#include "softserial.h"

void soft_sio0_init( WORD baud_rate ) {
	usartInit();
}

void soft_putchar(char c) {
	switch (c) {
	case '\r':
	case '\n':
        	usartSendByte('\n');
        	usartSendByte('\r');
		break;
	default:	
	        usartSendByte(c);
	}
}

char soft_getchar(void) {
        return '0';
}
