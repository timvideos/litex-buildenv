#include <stdio.h>
#include <stdlib.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <system.h>
#include <time.h>

#include "pattern.h"

#define PATTERN_FRAMEBUFFER_BASE 0x02000000
#define PATTERN_FRAMEBUFFER_SIZE 1280*720*2

unsigned int pattern_framebuffer_base(void) {
	return PATTERN_FRAMEBUFFER_BASE;
}

void pattern_fill_framebuffer(void)
{
	int i;
	flush_l2_cache();
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + PATTERN_FRAMEBUFFER_BASE);
	for(i=0; i<PATTERN_FRAMEBUFFER_SIZE/4; i++) {
			framebuffer[i] = 0xf0296e29; /* blue in YCbCr 4:2:2 */
	}
}
