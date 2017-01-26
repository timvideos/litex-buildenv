#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <console.h>
#include <system.h>

#include "ci.h"

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nNeTV2 CPU testing software built "__DATE__" "__TIME__);

	time_init();
	ci_prompt();
	while(1) {
		ci_service();
	}

	return 0;
}

