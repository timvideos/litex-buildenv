#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nArty CPU testing software built "__DATE__" "__TIME__);

	while(1);

	return 0;
}
