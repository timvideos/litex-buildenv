#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <console.h>
#include <generated/csr.h>
#include <generated/mem.h>

extern void boot_helper(unsigned int r1, unsigned int r2, unsigned int r3, unsigned int addr);
static void __attribute__((noreturn)) boot(unsigned int r1, unsigned int r2, unsigned int r3, unsigned int addr)
{
	printf("Booting program at 0x%x.\n", addr);
	uart_sync();
	irq_setmask(0);
	irq_setie(0);
	flush_cpu_icache();
	boot_helper(r1, r2, r3, addr);
	while(1);
}

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

static char *get_token(char **str)
{
	char *c, *d;

	c = (char *)strchr(*str, ' ');
	if(c == NULL) {
		d = *str;
		*str = *str+strlen(*str);
		return d;
	}
	*c = 0;
	d = *str;
	*str = c+1;
	return d;
}

static void help(void)
{
	puts("reboot                          - reboot CPU");
	puts("help                            - this command");
}

static void reboot(void)
{
	boot(0, 0, 0, CONFIG_CPU_RESET_ADDR);
}

static void ci_prompt(void)
{
	printf("STUB>");
}

static void ci_service(void)
{
	char *str;
	char *token;

	str = readstr();
	if(str == NULL) return;

	token = get_token(&str);

	if(strcmp(token, "help") == 0) {
		puts("Available commands:");
		help();
	}
	else if(strcmp(token, "reboot") == 0) reboot();

	ci_prompt();
}

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("Stub firmware booting...\n");
	puts("\nLiteX-Buildenv Stub Firmware, built "__DATE__" "__TIME__"\n");
	puts("Type \"help\" for help\n");
	ci_prompt();

	while(1) {
		ci_service();
	}

	return 0;
}
