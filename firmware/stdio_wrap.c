#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>

#include "stdio_wrap.h"

int wputs(const char *s)
{
	puts(s);
	return 0;
}

int wprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
int wprintf(const char *fmt, ...)
{
	int len;
	va_list args;
	va_start(args, fmt);
	len = vprintf(fmt, args);
	va_end(args);
	return len;
}

void wputsnonl(const char *s)
{
	putsnonl(s);
}