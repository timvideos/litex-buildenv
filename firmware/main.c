#include <stdio.h>
#include <stdlib.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <generated/csr.h>
#include <hw/flags.h>
#include <console.h>

#include "config.h"
#include "ci.h"
#include "processor.h"

static void ui_service(void)
{
}

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();

	printf("Mixxeo software rev. %08x built "__DATE__" "__TIME__"\n\n", MSC_GIT_ID);

	config_init();
	time_init();
	//processor_start(config_get(CONFIG_KEY_RESOLUTION));

	while(1) {
		//processor_service();
		//ui_service();
		ci_service();
	}

	return 0;
}
