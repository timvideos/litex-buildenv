#include <generated/csr.h>

#include <irq.h>
#include <stdio.h>
#include <system.h>
#include <uart.h>

#include "reboot.h"

#ifndef CONFIG_CPU_RESET_ADDR
#define CONFIG_CPU_RESET_ADDR 0
#warning "CPU reset address was not defined! Using 0."
#endif

extern void boot_helper(unsigned int r1, unsigned int r2, unsigned int r3, unsigned int addr);

void reboot(void)
{
	boot(0, 0, 0, CONFIG_CPU_RESET_ADDR);
}

void __attribute__((noreturn)) boot(unsigned int r1, unsigned int r2, unsigned int r3, unsigned int addr)
{
	printf("Booting program at 0x%x.\n", addr);
	uart_sync();
	irq_setmask(0);
	irq_setie(0);
	flush_cpu_icache();
	boot_helper(r1, r2, r3, addr);
	while(1);
}
