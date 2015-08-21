#include <stdio.h>
#include <stdlib.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <console.h>

#include "config.h"
#include "ci.h"
#include "processor.h"
#include "encoder.h"

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	puts("\nHDMI2USB firmware  http://timvideos.us/");
	printf("Revision %08x built "__DATE__" "__TIME__"\n", MSC_GIT_ID);

	ci_prompt();
	config_init();
	time_init();
#ifdef ENCODER_BASE
		encoder_enable(0);
#endif
	processor_start(config_get(CONFIG_KEY_RESOLUTION));
	while(1) {
		processor_service();
		ci_service();
#ifdef ENCODER_BASE
		encoder_service();
#endif
	}

	return 0;
}
