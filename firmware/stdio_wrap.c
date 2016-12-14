#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#include "telnet.h"

#include "stdio_wrap.h"

int wputs(const char *s)
{
#ifdef ETHMAC_BASE
	if(telnet_active)
		telnet_puts(s);
	else
#endif
		puts(s);
	return 0;
}

int wprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
int wprintf(const char *fmt, ...)
{
	int len;
	va_list args;
	va_start(args, fmt);
#ifdef ETHMAC_BASE
	if(telnet_active)
		len = telnet_vprintf(fmt, args);
	else
#endif
		len = vprintf(fmt, args);
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