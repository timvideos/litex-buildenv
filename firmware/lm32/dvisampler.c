#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <system.h>
#include <generated/csr.h>
#include <hw/flags.h>

#include "dvisampler.h"

int dvisampler_debug;

#define FRAMEBUFFER_COUNT 4
#define FRAMEBUFFER_MASK (FRAMEBUFFER_COUNT - 1)

#define DVISAMPLER_FRAMEBUFFERS_BASE 0x00000000
#define DVISAMPLER_FRAMEBUFFERS_SIZE 1280*720*4

static unsigned int dvisampler_framebuffer_base(char n) {
	return DVISAMPLER_FRAMEBUFFERS_BASE + n*DVISAMPLER_FRAMEBUFFERS_SIZE;
}

static int dvisampler_fb_slot_indexes[2];
static int dvisampler_next_fb_index;
static int dvisampler_hres, dvisampler_vres;

void dvisampler_isr(void)
{
	int fb_index = -1;
	int length;
	int expected_length;
	unsigned int address_min, address_max;

	address_min = DVISAMPLER_FRAMEBUFFERS_BASE & 0x0fffffff;
	address_max = address_min + DVISAMPLER_FRAMEBUFFERS_SIZE*FRAMEBUFFER_COUNT;
	if((dvisampler_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler_dma_slot0_address_read() < address_min) || (dvisampler_dma_slot0_address_read() > address_max)))
		printf("dvisampler: slot0: stray DMA\n");
	if((dvisampler_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((dvisampler_dma_slot1_address_read() < address_min) || (dvisampler_dma_slot1_address_read() > address_max)))
		printf("dvisampler: slot1: stray DMA\n");

	if((dvisampler_resdetection_hres_read() != dvisampler_hres)
	  || (dvisampler_resdetection_vres_read() != dvisampler_vres)) {
		/* Dump frames until we get the expected resolution */
		if(dvisampler_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler_dma_slot0_address_write(dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[0]));
			dvisampler_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
		}
		if(dvisampler_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
			dvisampler_dma_slot1_address_write(dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[1]));
			dvisampler_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
		}
		return;
	}

	expected_length = dvisampler_hres*dvisampler_vres*4;
	if(dvisampler_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler_dma_slot0_address_read() - (dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[0]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler_fb_slot_indexes[0];
			dvisampler_fb_slot_indexes[0] = dvisampler_next_fb_index;
			dvisampler_next_fb_index = (dvisampler_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler: slot0: unexpected frame length: %d\n", length);
		dvisampler_dma_slot0_address_write(dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[0]));
		dvisampler_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	}
	if(dvisampler_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = dvisampler_dma_slot1_address_read() - (dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[1]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = dvisampler_fb_slot_indexes[1];
			dvisampler_fb_slot_indexes[1] = dvisampler_next_fb_index;
			dvisampler_next_fb_index = (dvisampler_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else
			printf("dvisampler: slot1: unexpected frame length: %d\n", length);
		dvisampler_dma_slot1_address_write(dvisampler_framebuffer_base(dvisampler_fb_slot_indexes[1]));
		dvisampler_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	}

	if(fb_index != -1)
		fb_fi_base0_write(dvisampler_framebuffer_base(fb_index));
}

static int dvisampler_connected;
static int dvisampler_locked;

void dvisampler_init_video(int hres, int vres)
{
	unsigned int mask;

	dvisampler_clocking_pll_reset_write(1);
	dvisampler_connected = dvisampler_locked = 0;
	dvisampler_hres = hres; dvisampler_vres = vres;

	dvisampler_dma_frame_size_write(hres*vres*4);
	dvisampler_fb_slot_indexes[0] = 0;
	dvisampler_dma_slot0_address_write(dvisampler_framebuffer_base(0));
	dvisampler_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler_fb_slot_indexes[1] = 1;
	dvisampler_dma_slot1_address_write(dvisampler_framebuffer_base(1));
	dvisampler_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	dvisampler_next_fb_index = 2;

	dvisampler_dma_ev_pending_write(dvisampler_dma_ev_pending_read());
	dvisampler_dma_ev_enable_write(0x3);
	mask = irq_getmask();
	mask |= 1 << DVISAMPLER_INTERRUPT;
	irq_setmask(mask);

	fb_fi_base0_write(dvisampler_framebuffer_base(3));

}

void dvisampler_disable(void)
{
	unsigned int mask;

	mask = irq_getmask();
	mask &= ~(1 << DVISAMPLER_INTERRUPT);
	irq_setmask(mask);

	dvisampler_dma_slot0_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler_dma_slot1_status_write(DVISAMPLER_SLOT_EMPTY);
	dvisampler_clocking_pll_reset_write(1);
}

void dvisampler_clear_framebuffers(void)
{
	flush_l2_cache();
}

static int dvisampler_d0, dvisampler_d1, dvisampler_d2;

void dvisampler_print_status(void)
{
	dvisampler_data0_wer_update_write(1);
	dvisampler_data1_wer_update_write(1);
	dvisampler_data2_wer_update_write(1);
	printf("dvisampler: ph:%4d %4d %4d // charsync:%d%d%d [%d %d %d] // WER:%3d %3d %3d // chansync:%d // res:%dx%d\n",
		dvisampler_d0, dvisampler_d1, dvisampler_d2,
		dvisampler_data0_charsync_char_synced_read(),
		dvisampler_data1_charsync_char_synced_read(),
		dvisampler_data2_charsync_char_synced_read(),
		dvisampler_data0_charsync_ctl_pos_read(),
		dvisampler_data1_charsync_ctl_pos_read(),
		dvisampler_data2_charsync_ctl_pos_read(),
		dvisampler_data0_wer_value_read(),
		dvisampler_data1_wer_value_read(),
		dvisampler_data2_wer_value_read(),
		dvisampler_chansync_channels_synced_read(),
		dvisampler_resdetection_hres_read(),
		dvisampler_resdetection_vres_read());
}

static int wait_idelays(void)
{
	int ev;

	ev = 0;
	elapsed(&ev, 1);
	while(dvisampler_data0_cap_dly_busy_read()
	  || dvisampler_data1_cap_dly_busy_read()
	  || dvisampler_data2_cap_dly_busy_read()) {
		if(elapsed(&ev, identifier_frequency_read() >> 6) == 0) {
			printf("dvisampler: IDELAY busy timeout\n");
			return 0;
		}
	}
	return 1;
}

int dvisampler_calibrate_delays(void)
{
	dvisampler_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	dvisampler_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	if(!wait_idelays())
		return 0;
	dvisampler_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	dvisampler_data0_cap_phase_reset_write(1);
	dvisampler_data1_cap_phase_reset_write(1);
	dvisampler_data2_cap_phase_reset_write(1);
	dvisampler_d0 = dvisampler_d1 = dvisampler_d2 = 0;
	return 1;
}

int dvisampler_adjust_phase(void)
{
	switch(dvisampler_data0_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler_d0--;
			dvisampler_data0_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler_d0++;
			dvisampler_data0_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler_data1_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler_d1--;
			dvisampler_data1_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler_d1++;
			dvisampler_data1_cap_phase_reset_write(1);
			break;
	}
	switch(dvisampler_data2_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			dvisampler_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			dvisampler_d2--;
			dvisampler_data2_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			dvisampler_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			dvisampler_d2++;
			dvisampler_data2_cap_phase_reset_write(1);
			break;
	}
	return 1;
}

int dvisampler_init_phase(void)
{
	int o_d0, o_d1, o_d2;
	int i, j;

	for(i=0;i<100;i++) {
		o_d0 = dvisampler_d0;
		o_d1 = dvisampler_d1;
		o_d2 = dvisampler_d2;
		for(j=0;j<1000;j++) {
			if(!dvisampler_adjust_phase())
				return 0;
		}
		if((abs(dvisampler_d0 - o_d0) < 4) && (abs(dvisampler_d1 - o_d1) < 4) && (abs(dvisampler_d2 - o_d2) < 4))
			return 1;
	}
	return 0;
}

int dvisampler_phase_startup(void)
{
	int ret;
	int attempts;

	attempts = 0;
	while(1) {
		attempts++;
		dvisampler_calibrate_delays();
		if(dvisampler_debug)
			printf("dvisampler: delays calibrated\n");
		ret = dvisampler_init_phase();
		if(ret) {
			if(dvisampler_debug)
				printf("dvisampler: phase init OK\n");
			return 1;
		} else {
			printf("dvisampler: phase init failed\n");
			if(attempts > 3) {
				printf("dvisampler: giving up\n");
				dvisampler_calibrate_delays();
				return 0;
			}
		}
	}
}

static void dvisampler_check_overflow(void)
{
	if(dvisampler_frame_overflow_read()) {
		printf("dvisampler: FIFO overflow\n");
		dvisampler_frame_overflow_write(1);
	}
}

static int dvisampler_clocking_locked_filtered(void)
{
	static int lock_start_time;
	static int lock_status;

	if(dvisampler_clocking_locked_read()) {
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

void dvisampler_service(void)
{
	static int last_event;

	if(dvisampler_connected) {
		if(!dvisampler_edid_hpd_notif_read()) {
			if(dvisampler_debug)
				printf("dvisampler: disconnected\n");
			dvisampler_connected = 0;
			dvisampler_locked = 0;
			dvisampler_clocking_pll_reset_write(1);
			dvisampler_clear_framebuffers();
		} else {
			if(dvisampler_locked) {
				if(dvisampler_clocking_locked_filtered()) {
					if(elapsed(&last_event, identifier_frequency_read()/2)) {
						dvisampler_adjust_phase();
						if(dvisampler_debug)
							dvisampler_print_status();
					}
				} else {
					if(dvisampler_debug)
						printf("dvisampler: lost PLL lock\n");
					dvisampler_locked = 0;
					dvisampler_clear_framebuffers();
				}
			} else {
				if(dvisampler_clocking_locked_filtered()) {
					if(dvisampler_debug)
						printf("dvisampler: PLL locked\n");
					dvisampler_phase_startup();
					if(dvisampler_debug)
						dvisampler_print_status();
					dvisampler_locked = 1;
				}
			}
		}
	} else {
		if(dvisampler_edid_hpd_notif_read()) {
			if(dvisampler_debug)
				printf("dvisampler: connected\n");
			dvisampler_connected = 1;
			dvisampler_clocking_pll_reset_write(0);
		}
	}
	dvisampler_check_overflow();
}
