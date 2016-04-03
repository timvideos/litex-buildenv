#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <console.h>

#include "ci.h"
#include "telnet.h"


int ci_puts(const char *s)
{
	if(telnet_active)
		telnet_puts(s);
	else
		puts(s);
	return 0;
}

int ci_printf(const char *fmt, ...)
{
	if(telnet_active)
		return telnet_printf(fmt);
	else
		return printf(fmt);
}

void ci_putsnonl(const char *s)
{
	if(telnet_active)
		telnet_putsnonl(s);
	else
		putsnonl(s);
}

void ci_help(void)
{
	ci_puts("Available commands:");
	ci_puts("help        - this command");
	ci_puts("reboot      - reboot CPU");
}

static char *readstr(void)
{
	char c[2];
	static char s[64];
	static int ptr = 0;

	if(telnet_active) {
		if(telnet_readchar_nonblock()) {
			c[0] = telnet_readchar();
			c[1] = 0;
			switch(c[0]) {
				case 0x7f:
				case 0x08:
					if(ptr > 0) {
						ptr--;
					}
					break;
				case 0x07:
					break;
				case '\r':
					break;
				case '\n':
					s[ptr] = 0x00;
					ptr = 0;
					return s;
				default:
					if(ptr >= (sizeof(s) - 1))
						break;
					s[ptr] = c[0];
					ptr++;
					break;
			}
		}
	} else {
		if(readchar_nonblock()) {
			c[0] = readchar();
			c[1] = 0;
			switch(c[0]) {
				case 0x7f:
				case 0x08:
					if(ptr > 0) {
						ptr--;
						ci_putsnonl("\x08 \x08");
					}
					break;
				case 0x07:
					break;
				case '\r':
				case '\n':
					s[ptr] = 0x00;
					ci_putsnonl("\n");
					ptr = 0;
					return s;
				default:
					if(ptr >= (sizeof(s) - 1))
						break;
					ci_putsnonl(c);
					s[ptr] = c[0];
					ptr++;
					break;
			}
		}
	}

	return NULL;
}

static char *get_token_generic(char **str, char delimiter)
{
	char *c, *d;

	c = (char *)strchr(*str, delimiter);
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

static char *get_token(char **str)
{
	return get_token_generic(str, ' ');
}

static void reboot(void)
{
	asm("call r0");
}

void ci_prompt(void)
{
	ci_printf("RUNTIME>");
}

void ci_service(void)
{
	char *str;
	char *token;

	str = readstr();
	if(str == NULL) return;

	token = get_token(&str);
	if(strcmp(token, "help") == 0)
		ci_help();
	else if(strcmp(token, "reboot") == 0)
		reboot();

	ci_prompt();
}
