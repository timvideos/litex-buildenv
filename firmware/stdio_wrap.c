#include <assert.h>
#include <console.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#include <generated/mem.h> // Needed for ETHMAC_BASE

#include "telnet.h"

#include "stdio_wrap.h"

/* Transform LF -> CRLF in s, putting the result in stdio_write_buffer
 */
char *translate_crlf(const char *s, int trailing_lf) {
	assert(tailing_lf == 0 || trailing_lf == 1);
	char *out = stdio_write_buffer;
	char *end = stdio_write_buffer + STDIO_BUFFER_SIZE - 2 - trailing_lf;
	while (*s != '\0' && out < end) {
		if (*s == '\n') {
			assert(out < end);
			*out++ = '\r';
		}
		assert(out < end);
		*out++ = *s++;
	}
	if (trailing_lf) {
		*out++ = '\r';
	}
	*out++ = '\0';
	return stdio_write_buffer;
}

int wputs(const char *s)
{
	char *s_crlf = translate_crlf(s, 1);
#ifdef ETHMAC_BASE
	if(telnet_active)
		telnet_puts(s_crlf);
	else
#endif
		puts(s_crlf);
	return 0;
}

int wputchar(int c)
{
#ifdef ETHMAC_BASE
	if(telnet_active) {
		if(c == '\n') {
			telnet_putchar('\r');
		}
		telnet_putchar(c);
	} else {
#endif
		if(c == '\n') {
			putchar('\r');
		}
		putchar(c);
#ifdef ETHMAC_BASE
	}
#endif
	return 0;
}

int wprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
int wprintf(const char *fmt, ...)
{
	int len;
	va_list args;
	va_start(args, fmt);

	char *fmt_crlf = translate_crlf(fmt, 0);

#ifdef ETHMAC_BASE
	if(telnet_active)
		len = telnet_vprintf(fmt_crlf, args);
	else
#endif
		len = vprintf(fmt_crlf, args);
	va_end(args);
	return len;
}

void wputsnonl(const char *s)
{
#ifdef ETHMAC_BASE
	if(telnet_active)
		telnet_putsnonl(s);
	else
#endif
		putsnonl(s);
}
