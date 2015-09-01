#include <stdio.h>
#include <stdlib.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include <system.h>

#include "pattern.h"

#define PATTERN_FRAMEBUFFER_BASE 0x02000000

unsigned int pattern_framebuffer_base(void) {
	return PATTERN_FRAMEBUFFER_BASE;
}

/* DRAM content in YCbCr 4:2:2, from pattern.py */
static const unsigned int color_bar[8] = {
	0x80ff80ff,
	0x00e194e1,
	0xabb200b2,
	0x2b951595,
	0xd469e969,
	0x544cff4c,
	0xff1d6f1d,
	0x80108010
};

static int inc_color(int color) {
	color++;
	return color%8;
}

void pattern_fill_framebuffer(int h_active, int m_active)
{
	int i;
	int color;
	flush_l2_cache();
	color = -1;
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + PATTERN_FRAMEBUFFER_BASE);
	for(i=0; i<h_active*m_active*2/4; i++) {
		if(i%(h_active/16) == 0)
			inc_color(color);
		if(color > 0)
			framebuffer[i] = color_bar[color];
	}
}
