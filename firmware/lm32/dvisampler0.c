#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <system.h>
#include <generated/csr.h>
#include <hw/flags.h>

#include "dvisampler0.h"

int dvisampler0_debug;
int dvisampler0_fb_index;

#define FRAMEBUFFER_COUNT 4
#define FRAMEBUFFER_MASK (FRAMEBUFFER_COUNT - 1)

#define DVISAMPLER_FRAMEBUFFERS_BASE 0x00000000
#define DVISAMPLER_FRAMEBUFFERS_SIZE 1280*720*4

unsigned int dvisampler0_framebuffer_base(char n) {
	return DVISAMPLER_FRAMEBUFFERS_BASE + n*DVISAMPLER_FRAMEBUFFERS_SIZE;
}

static int dvisampler0_fb_slot_indexes[2];
static int dvisampler0_next_fb_index;
static int dvisampler0_hres, dvisampler0_vres;

extern void processor_update(void);

void dvisampler0_isr(void)
{
	int fb_index = -1;
	int length;
	int expected_length;
	unsigned int address_min, address_max;

	address_min = DVISAMPLER_FRAMEBUFFERS_BASE & 0x0fffffff;
	address_max = address_min + DVISAMPLER_FRAMEBUFFERS_SIZE*FRAMEBUFFER_COUNT;
	if((dvisampler0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler0_dma_slot0_address_read() < address_min) || (dvisampler0_dma_slot0_address_read() > address_max)))
		printf("dvisampler0: slot0: stray DMA\n");
	if((dvisampler0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler0_dma_slot1_address_read() < address_min) || (dvisampler0_dma_slot1_address_read() > address_max)))
		printf("dvisampler0: slot1: stray DMA\n");

	if((dvisampler0_resdetection_hres_read() != dvisampler0_hres)
	  || (dvisampler0_resdetection_vres_read() != dvisampler0_vres)) {
		/* Dump frames until we get the expected resolution */
		if(dvisampler0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler0_dma_slot0_address_write(dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[0]));
			dvisampler0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
		}
		if(dvisampler0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler0_dma_slot1_address_write(dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[1]));
			dvisampler0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
		}
		return;
	}

	expected_length = dvisampler0_hres*dvisampler0_vres*2;
	if(dvisampler0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler0_dma_slot0_address_read() - (dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[0]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler0_fb_slot_indexes[0];
			dvisampler0_fb_slot_indexes[0] = dvisampler0_next_fb_index;
			dvisampler0_next_fb_index = (dvisampler0_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler0: slot0: unexpected frame length: %d\n", length);
		dvisampler0_dma_slot0_address_write(dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[0]));
		dvisampler0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	}
	if(dvisampler0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler0_dma_slot1_address_read() - (dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[1]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler0_fb_slot_indexes[1];
			dvisampler0_fb_slot_indexes[1] = dvisampler0_next_fb_index;
			dvisampler0_next_fb_index = (dvisampler0_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler0: slot1: unexpected frame length: %d\n", length);
		dvisampler0_dma_slot1_address_write(dvisampler0_framebuffer_base(dvisampler0_fb_slot_indexes[1]));
		dvisampler0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	}

	if(fb_index != -1)
		dvisampler0_fb_index = fb_index;
	processor_update();
}

static int dvisampler0_connected;
static int dvisampler0_locked;

void dvisampler0_init_video(int hres, int vres)
{
	unsigned int mask;

	dvisampler0_clocking_pll_reset_write(1);
	dvisampler0_connected = dvisampler0_locked = 0;
	dvisampler0_hres = hres; dvisampler0_vres = vres;

	dvisampler0_dma_frame_size_write(hres*vres*2);
	dvisampler0_fb_slot_indexes[0] = 0;
	dvisampler0_dma_slot0_address_write(dvisampler0_framebuffer_base(0));
	dvisampler0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler0_fb_slot_indexes[1] = 1;
	dvisampler0_dma_slot1_address_write(dvisampler0_framebuffer_base(1));
	dvisampler0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler0_next_fb_index = 2;

	dvisampler0_dma_ev_pending_write(dvisampler0_dma_ev_pending_read());
	dvisampler0_dma_ev_enable_write(0x3);
	mask = irq_getmask();
	mask |= 1 << DVISAMPLER0_INTERRUPT;
	irq_setmask(mask);

	dvisampler0_fb_index = 3;
}

void dvisampler0_disable(void)
{
	unsigned int mask;

	mask = irq_getmask();
	mask &= ~(1 << DVISAMPLER0_INTERRUPT);
	irq_setmask(mask);

	dvisampler0_dma_slot0_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler0_dma_slot1_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler0_clocking_pll_reset_write(1);
}

void dvisampler0_clear_framebuffers(void)
{
	flush_l2_cache();
}

static int dvisampler0_d0, dvisampler0_d1, dvisampler0_d2;

void dvisampler0_print_status(void)
{
	dvisampler0_data0_wer_update_write(1);
	dvisampler0_data1_wer_update_write(1);
	dvisampler0_data2_wer_update_write(1);
	printf("dvisampler0: ph:%4d %4d %4d // charsync:%d%d%d [%d %d %d] // WER:%3d %3d %3d // chansync:%d // res:%dx%d\n",
		dvisampler0_d0, dvisampler0_d1, dvisampler0_d2,
		dvisampler0_data0_charsync_char_synced_read(),
		dvisampler0_data1_charsync_char_synced_read(),
		dvisampler0_data2_charsync_char_synced_read(),
		dvisampler0_data0_charsync_ctl_pos_read(),
		dvisampler0_data1_charsync_ctl_pos_read(),
		dvisampler0_data2_charsync_ctl_pos_read(),
		dvisampler0_data0_wer_value_read(),
		dvisampler0_data1_wer_value_read(),
		dvisampler0_data2_wer_value_read(),
		dvisampler0_chansync_channels_synced_read(),
		dvisampler0_resdetection_hres_read(),
		dvisampler0_resdetection_vres_read());
}

static int wait_idelays(void)
{
	int ev;

	ev = 0;
	elapsed(&ev, 1);
	while(dvisampler0_data0_cap_dly_busy_read()
	  || dvisampler0_data1_cap_dly_busy_read()
	  || dvisampler0_data2_cap_dly_busy_read()) {
		if(elapsed(&ev, identifier_frequency_read() >> 6) == 0) {
			printf("dvisampler0: IDELAY busy timeout\n");
			return 0;
		}
	}
	return 1;
}

int dvisampler0_calibrate_delays(void)
{
	dvisampler0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	if(!wait_idelays())
		return 0;
	dvisampler0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler0_data0_cap_phase_reset_write(1);
	dvisampler0_data1_cap_phase_reset_write(1);
	dvisampler0_data2_cap_phase_reset_write(1);
	dvisampler0_d0 = dvisampler0_d1 = dvisampler0_d2 = 0;
	return 1;
}

int dvisampler0_adjust_phase(void)
{
	switch(dvisampler0_data0_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d0--;
			dvisampler0_data0_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d0++;
			dvisampler0_data0_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler0_data1_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d1--;
			dvisampler0_data1_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d1++;
			dvisampler0_data1_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler0_data2_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d2--;
			dvisampler0_data2_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler0_d2++;
			dvisampler0_data2_cap_phase_reset_write(1);
			break;
	}
	return 1;
}

int dvisampler0_init_phase(void)
{
	int o_d0, o_d1, o_d2;
	int i, j;

	for(i=0;i<100;i++) {
		o_d0 = dvisampler0_d0;
		o_d1 = dvisampler0_d1;
		o_d2 = dvisampler0_d2;
		for(j=0;j<1000;j++) {
			if(!dvisampler0_adjust_phase())
				return 0;
		}
		if((abs(dvisampler0_d0 - o_d0) < 4) && (abs(dvisampler0_d1 - o_d1) < 4) && (abs(dvisampler0_d2 - o_d2) < 4))
			return 1;
	}
	return 0;
}

int dvisampler0_phase_startup(void)
{
	int ret;
	int attempts;

	attempts = 0;
	while(1) {
		attempts++;
		dvisampler0_calibrate_delays();
		if(dvisampler0_debug)
			printf("dvisampler0: delays calibrated\n");
		ret = dvisampler0_init_phase();
		if(ret) {
			if(dvisampler0_debug)
				printf("dvisampler0: phase init OK\n");
			return 1;
		} else {
			printf("dvisampler0: phase init failed\n");
			if(attempts > 3) {
				printf("dvisampler0: giving up\n");
				dvisampler0_calibrate_delays();
				return 0;
			}
		}
	}
}

static void dvisampler0_check_overflow(void)
{
	if(dvisampler0_frame_overflow_read()) {
		printf("dvisampler0: FIFO overflow\n");
		dvisampler0_frame_overflow_write(1);
	}
}

static int dvisampler0_clocking_locked_filtered(void)
{
	static int lock_start_time;
	static int lock_status;

	if(dvisampler0_clocking_locked_read()) {
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

void dvisampler0_service(void)
{
	static int last_event;

	if(dvisampler0_connected) {
		if(!dvisampler0_edid_hpd_notif_read()) {
			if(dvisampler0_debug)
				printf("dvisampler0: disconnected\n");
			dvisampler0_connected = 0;
			dvisampler0_locked = 0;
			dvisampler0_clocking_pll_reset_write(1);
			dvisampler0_clear_framebuffers();
		} else {
			if(dvisampler0_locked) {
				if(dvisampler0_clocking_locked_filtered()) {
					if(elapsed(&last_event, identifier_frequency_read()/2)) {
						dvisampler0_adjust_phase();
						if(dvisampler0_debug)
							dvisampler0_print_status();
					}
				} else {
					if(dvisampler0_debug)
						printf("dvisampler0: lost PLL lock\n");
					dvisampler0_locked = 0;
					dvisampler0_clear_framebuffers();
				}
			} else {
				if(dvisampler0_clocking_locked_filtered()) {
					if(dvisampler0_debug)
						printf("dvisampler0: PLL locked\n");
					dvisampler0_phase_startup();
					if(dvisampler0_debug)
						dvisampler0_print_status();
					dvisampler0_locked = 1;
				}
			}
		}
	} else {
		if(dvisampler0_edid_hpd_notif_read()) {
			if(dvisampler0_debug)
				printf("dvisampler0: connected\n");
			dvisampler0_connected = 1;
			dvisampler0_clocking_pll_reset_write(0);
		}
	}
	dvisampler0_check_overflow();
}
