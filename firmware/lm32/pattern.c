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

void pattern_fill_framebuffer(int h_active, int m_active)
{
	int i;
	int change_color;
	int color;
	flush_l2_cache();
	color = -1;
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + PATTERN_FRAMEBUFFER_BASE);
	for(i=0; i<h_active*m_active*2/4; i++) {
		change_color = i%(h_active/16) == 0;
		if(change_color)
			color++;
		color = color%8;
		switch(color) {
			case 0:
				framebuffer[i] = 0x80ff80ff; break;
			case 1:
				framebuffer[i] = 0x00e194e1; break;
			case 2:
				framebuffer[i] = 0xabb200b2; break;
			case 3:
				framebuffer[i] = 0x2b951595; break;
			case 4:
				framebuffer[i] = 0xd469e969; break;
			case 5:
				framebuffer[i] = 0x544cff4c; break;
			case 6:
				framebuffer[i] = 0xff1d6f1d; break;
			case 7:
				framebuffer[i] = 0x80108010;
				break;
		}
	}
}
