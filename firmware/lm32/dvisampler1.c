#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <system.h>
#include <generated/csr.h>
#include <hw/flags.h>

#include "dvisampler1.h"

int dvisampler1_debug;
int dvisampler1_fb_index;

#define FRAMEBUFFER_COUNT 4
#define FRAMEBUFFER_MASK (FRAMEBUFFER_COUNT - 1)

#define DVISAMPLER_FRAMEBUFFERS_BASE 0x01000000
#define DVISAMPLER_FRAMEBUFFERS_SIZE 1280*720*4

unsigned int dvisampler1_framebuffer_base(char n) {
	return DVISAMPLER_FRAMEBUFFERS_BASE + n*DVISAMPLER_FRAMEBUFFERS_SIZE;
}

static int dvisampler1_fb_slot_indexes[2];
static int dvisampler1_next_fb_index;
static int dvisampler1_hres, dvisampler1_vres;

extern void processor_update(void);

void dvisampler1_isr(void)
{
	int fb_index = -1;
	int length;
	int expected_length;
	unsigned int address_min, address_max;

	address_min = DVISAMPLER_FRAMEBUFFERS_BASE & 0x0fffffff;
	address_max = address_min + DVISAMPLER_FRAMEBUFFERS_SIZE*FRAMEBUFFER_COUNT;
	if((dvisampler1_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler1_dma_slot0_address_read() < address_min) || (dvisampler1_dma_slot0_address_read() > address_max)))
		printf("dvisampler1: slot0: stray DMA\n");
	if((dvisampler1_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler1_dma_slot1_address_read() < address_min) || (dvisampler1_dma_slot1_address_read() > address_max)))
		printf("dvisampler1: slot1: stray DMA\n");

	if((dvisampler1_resdetection_hres_read() != dvisampler1_hres)
	  || (dvisampler1_resdetection_vres_read() != dvisampler1_vres)) {
		/* Dump frames until we get the expected resolution */
		if(dvisampler1_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler1_dma_slot0_address_write(dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[0]));
			dvisampler1_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
		}
		if(dvisampler1_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler1_dma_slot1_address_write(dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[1]));
			dvisampler1_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
		}
		return;
	}

	expected_length = dvisampler1_hres*dvisampler1_vres*2;
	if(dvisampler1_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler1_dma_slot0_address_read() - (dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[0]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler1_fb_slot_indexes[0];
			dvisampler1_fb_slot_indexes[0] = dvisampler1_next_fb_index;
			dvisampler1_next_fb_index = (dvisampler1_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler1: slot0: unexpected frame length: %d\n", length);
		dvisampler1_dma_slot0_address_write(dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[0]));
		dvisampler1_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	}
	if(dvisampler1_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler1_dma_slot1_address_read() - (dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[1]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler1_fb_slot_indexes[1];
			dvisampler1_fb_slot_indexes[1] = dvisampler1_next_fb_index;
			dvisampler1_next_fb_index = (dvisampler1_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler1: slot1: unexpected frame length: %d\n", length);
		dvisampler1_dma_slot1_address_write(dvisampler1_framebuffer_base(dvisampler1_fb_slot_indexes[1]));
		dvisampler1_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	}

	if(fb_index != -1)
		dvisampler1_fb_index = fb_index;

	processor_update();
}

static int dvisampler1_connected;
static int dvisampler1_locked;

void dvisampler1_init_video(int hres, int vres)
{
	unsigned int mask;

	dvisampler1_clocking_pll_reset_write(1);
	dvisampler1_connected = dvisampler1_locked = 0;
	dvisampler1_hres = hres; dvisampler1_vres = vres;

	dvisampler1_dma_frame_size_write(hres*vres*2);
	dvisampler1_fb_slot_indexes[0] = 0;
	dvisampler1_dma_slot0_address_write(dvisampler1_framebuffer_base(0));
	dvisampler1_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler1_fb_slot_indexes[1] = 1;
	dvisampler1_dma_slot1_address_write(dvisampler1_framebuffer_base(1));
	dvisampler1_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler1_next_fb_index = 2;

	dvisampler1_dma_ev_pending_write(dvisampler1_dma_ev_pending_read());
	dvisampler1_dma_ev_enable_write(0x3);
	mask = irq_getmask();
	mask |= 1 << DVISAMPLER1_INTERRUPT;
	irq_setmask(mask);

	dvisampler1_fb_index = 3;
}

void dvisampler1_disable(void)
{
	unsigned int mask;

	mask = irq_getmask();
	mask &= ~(1 << DVISAMPLER1_INTERRUPT);
	irq_setmask(mask);

	dvisampler1_dma_slot0_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler1_dma_slot1_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler1_clocking_pll_reset_write(1);
}

void dvisampler1_clear_framebuffers(void)
{
	flush_l2_cache();
}

static int dvisampler1_d0, dvisampler1_d1, dvisampler1_d2;

void dvisampler1_print_status(void)
{
	dvisampler1_data0_wer_update_write(1);
	dvisampler1_data1_wer_update_write(1);
	dvisampler1_data2_wer_update_write(1);
	printf("dvisampler1: ph:%4d %4d %4d // charsync:%d%d%d [%d %d %d] // WER:%3d %3d %3d // chansync:%d // res:%dx%d\n",
		dvisampler1_d0, dvisampler1_d1, dvisampler1_d2,
		dvisampler1_data0_charsync_char_synced_read(),
		dvisampler1_data1_charsync_char_synced_read(),
		dvisampler1_data2_charsync_char_synced_read(),
		dvisampler1_data0_charsync_ctl_pos_read(),
		dvisampler1_data1_charsync_ctl_pos_read(),
		dvisampler1_data2_charsync_ctl_pos_read(),
		dvisampler1_data0_wer_value_read(),
		dvisampler1_data1_wer_value_read(),
		dvisampler1_data2_wer_value_read(),
		dvisampler1_chansync_channels_synced_read(),
		dvisampler1_resdetection_hres_read(),
		dvisampler1_resdetection_vres_read());
}

static int wait_idelays(void)
{
	int ev;

	ev = 0;
	elapsed(&ev, 1);
	while(dvisampler1_data0_cap_dly_busy_read()
	  || dvisampler1_data1_cap_dly_busy_read()
	  || dvisampler1_data2_cap_dly_busy_read()) {
		if(elapsed(&ev, identifier_frequency_read() >> 6) == 0) {
			printf("dvisampler1: IDELAY busy timeout\n");
			return 0;
		}
	}
	return 1;
}

int dvisampler1_calibrate_delays(void)
{
	dvisampler1_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler1_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler1_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	if(!wait_idelays())
		return 0;
	dvisampler1_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler1_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler1_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler1_data0_cap_phase_reset_write(1);
	dvisampler1_data1_cap_phase_reset_write(1);
	dvisampler1_data2_cap_phase_reset_write(1);
	dvisampler1_d0 = dvisampler1_d1 = dvisampler1_d2 = 0;
	return 1;
}

int dvisampler1_adjust_phase(void)
{
	switch(dvisampler1_data0_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler1_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d0--;
			dvisampler1_data0_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler1_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d0++;
			dvisampler1_data0_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler1_data1_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler1_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d1--;
			dvisampler1_data1_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler1_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d1++;
			dvisampler1_data1_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler1_data2_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler1_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d2--;
			dvisampler1_data2_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler1_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler1_d2++;
			dvisampler1_data2_cap_phase_reset_write(1);
			break;
	}
	return 1;
}

int dvisampler1_init_phase(void)
{
	int o_d0, o_d1, o_d2;
	int i, j;

	for(i=0;i<100;i++) {
		o_d0 = dvisampler1_d0;
		o_d1 = dvisampler1_d1;
		o_d2 = dvisampler1_d2;
		for(j=0;j<1000;j++) {
			if(!dvisampler1_adjust_phase())
				return 0;
		}
		if((abs(dvisampler1_d0 - o_d0) < 4) && (abs(dvisampler1_d1 - o_d1) < 4) && (abs(dvisampler1_d2 - o_d2) < 4))
			return 1;
	}
	return 0;
}

int dvisampler1_phase_startup(void)
{
	int ret;
	int attempts;

	attempts = 0;
	while(1) {
		attempts++;
		dvisampler1_calibrate_delays();
		if(dvisampler1_debug)
			printf("dvisampler1: delays calibrated\n");
		ret = dvisampler1_init_phase();
		if(ret) {
			if(dvisampler1_debug)
				printf("dvisampler1: phase init OK\n");
			return 1;
		} else {
			printf("dvisampler1: phase init failed\n");
			if(attempts > 3) {
				printf("dvisampler1: giving up\n");
				dvisampler1_calibrate_delays();
				return 0;
			}
		}
	}
}

static void dvisampler1_check_overflow(void)
{
	if(dvisampler1_frame_overflow_read()) {
		printf("dvisampler1: FIFO overflow\n");
		dvisampler1_frame_overflow_write(1);
	}
}

static int dvisampler1_clocking_locked_filtered(void)
{
	static int lock_start_time;
	static int lock_status;

	if(dvisampler1_clocking_locked_read()) {
		switch(lock_status) {
			case 0:
				elapsed(&lock_start_time, -1);
				lock_status = 1;
				break;
			case 1:
				if(elapsed(&lock_start_time, identifier_frequency_read()/4))
					lock_status = 2;
				break;
			case 2:
				return 1;
		}
	} else
		lock_status = 0;
	return 0;
}

void dvisampler1_service(void)
{
	static int last_event;

	if(dvisampler1_connected) {
		if(!dvisampler1_edid_hpd_notif_read()) {
			if(dvisampler1_debug)
				printf("dvisampler1: disconnected\n");
			dvisampler1_connected = 0;
			dvisampler1_locked = 0;
			dvisampler1_clocking_pll_reset_write(1);
			dvisampler1_clear_framebuffers();
		} else {
			if(dvisampler1_locked) {
				if(dvisampler1_clocking_locked_filtered()) {
					if(elapsed(&last_event, identifier_frequency_read()/2)) {
						dvisampler1_adjust_phase();
						if(dvisampler1_debug)
							dvisampler1_print_status();
					}
				} else {
					if(dvisampler1_debug)
						printf("dvisampler1: lost PLL lock\n");
					dvisampler1_locked = 0;
					dvisampler1_clear_framebuffers();
				}
			} else {
				if(dvisampler1_clocking_locked_filtered()) {
					if(dvisampler1_debug)
						printf("dvisampler1: PLL locked\n");
					dvisampler1_phase_startup();
					if(dvisampler1_debug)
						dvisampler1_print_status();
					dvisampler1_locked = 1;
				}
			}
		}
	} else {
		if(dvisampler1_edid_hpd_notif_read()) {
			if(dvisampler1_debug)
				printf("dvisampler1: connected\n");
			dvisampler1_connected = 1;
			dvisampler1_clocking_pll_reset_write(0);
		}
	}
	dvisampler1_check_overflow();
}
