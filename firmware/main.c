#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <hw/flags.h>
#include <console.h>

static char *readstr(void)
{
	char c[2];
	static char s[64];
	static int ptr = 0;

	if(readchar_nonblock()) {
		c[0] = readchar();
		c[1] = 0;
		switch(c[0]) {
			case 0x7f:
			case 0x08:
				if(ptr > 0) {
					ptr--;
					putsnonl("\x08 \x08");
				}
				break;
			case 0x07:
				break;
			case '\r':
			case '\n':
				s[ptr] = 0x00;
				putsnonl("\n");
				ptr = 0;
				return s;
			default:
				if(ptr >= (sizeof(s) - 1))
					break;
				putsnonl(c);
				s[ptr] = c[0];
				ptr++;
				break;
		}
	}
	return NULL;
}

static void console_service(void)
{
	char *str;

	str = readstr();
	if(str == NULL) return;

	if(strcmp(str, "reboot") == 0) asm("call r0");
}

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("HDMI2USB testing software built "__DATE__" "__TIME__"\n");

	time_init();

	while(1) {
		console_service();
	}

	return 0;
}
