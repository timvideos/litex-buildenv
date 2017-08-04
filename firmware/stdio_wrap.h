#include <stdarg.h>

#define STDIO_BUFFER_SIZE 256
char stdio_write_buffer[STDIO_BUFFER_SIZE];

char *translate_crlf(const char *s, int trailing_lf);

int wputs(const char *s);
int wputchar(int c);
int wprintf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
void wputsnonl(const char *s);

int sprintf(char *str, const char *format, ...)  __attribute__((format(printf, 2, 3)));
int snprintf(char *str, size_t size, const char *format, ...)  __attribute__((format(printf, 3, 4)));
