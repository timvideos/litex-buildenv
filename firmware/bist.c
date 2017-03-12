#include <generated/csr.h>
#ifdef CSR_GENERATOR_BASE
#include "bist.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <console.h>
#include "ci.h"


#define test_size 64*1024*1024

unsigned int ticks;
unsigned int speed;

static void busy_wait(unsigned int ds)
{
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(SYSTEM_CLOCK_FREQUENCY/10*ds);
	timer0_en_write(1);
	timer0_update_value_write(1);
	while(timer0_value_read()) timer0_update_value_write(1);
}

void bist_test(void) {
	while(readchar_nonblock() == 0) {
			// write
			printf("writing %d Mbytes...", test_size/(1024*1024));
			generator_reset_write(1);
			generator_reset_write(0);
			generator_base_write(0x10000);
			generator_length_write((test_size*8)/128);

			timer0_en_write(0);
			timer0_load_write(0xffffffff);
			timer0_en_write(1);

			generator_start_write(1);
			while(generator_done_read() == 0);

			timer0_update_value_write(1);
			ticks = timer0_value_read();
			ticks = 0xffffffff - ticks;
			speed = SYSTEM_CLOCK_FREQUENCY/ticks;
			speed = test_size*speed/1000000;
			speed = 8*speed;
			printf(" / %u Mbps\n", speed);

			// read
			printf("reading %d Mbytes...", test_size/(1024*1024));
			checker_reset_write(1);
			checker_reset_write(0);
			checker_base_write(0x10000);
			checker_length_write((test_size*8)/128);

			timer0_en_write(0);
			timer0_load_write(0xffffffff);
			timer0_en_write(1);

			checker_start_write(1);
			while(checker_done_read() == 0);

			timer0_update_value_write(1);
			ticks = timer0_value_read();
			ticks = 0xffffffff - ticks;
			speed = SYSTEM_CLOCK_FREQUENCY/ticks;
			speed = test_size*speed/1000000;
			speed = 8*speed;
			printf(" / %u Mbps\n", speed);

			// errors
#ifdef CSR_CHECKER_ERR_COUNT_ADDR
			printf("errors: %d\n", checker_err_count_read());
#endif
#ifdef CSR_CHECKER_ERRORS_ADDR
			printf("errors: %d\n", checker_errors_read());
#endif

			// delay
			busy_wait(10);
	}

}

#endif
