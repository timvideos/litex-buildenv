#ifndef __CI_H
#define __CI_H

int ci_puts(const char *s);
int ci_printf(const char *fmt, ...);
void ci_putsnonl(const char *s);
void ci_prompt(void);
void ci_service(void);

#endif
