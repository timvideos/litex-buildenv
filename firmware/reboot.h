#ifndef __REBOOT_H
#define __REBOOT_H

void reboot(void);
void __attribute__((noreturn)) boot(unsigned int r1, unsigned int r2, unsigned int r3, unsigned int addr);

#endif
