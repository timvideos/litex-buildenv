#include <stdarg.h>

int wputs(const char *s);
int wprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
void wputsnonl(const char *s);
