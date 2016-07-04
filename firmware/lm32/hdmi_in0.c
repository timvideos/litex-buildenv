#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <system.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>

#ifdef CSR_HDMI_IN0_BASE

#include "hdmi_in0.h"

int hdmi_in0_debug;
int hdmi_in0_fb_index;

#define FRAMEBUFFER_COUNT 4
#define FRAMEBUFFER_MASK (FRAMEBUFFER_COUNT - 1)

#define HDMI_IN0_FRAMEBUFFERS_BASE 0x01000000
#define HDMI_IN0_FRAMEBUFFERS_SIZE 1920*1080*2

//#define CLEAN_COMMUTATION
//#define DEBUG

unsigned int hdmi_in0_framebuffer_base(char n) {
	return HDMI_IN0_FRAMEBUFFERS_BASE + n*HDMI_IN0_FRAMEBUFFERS_SIZE;
}

static int hdmi_in0_fb_slot_indexes[2];
static int hdmi_in0_next_fb_index;
static int hdmi_in0_hres, hdmi_in0_vres;

extern void processor_update(void);

void hdmi_in0_isr(void)
{
	int fb_index = -1;
	int length;
	int expected_length;
	unsigned int address_min, address_max;

	address_min = HDMI_IN0_FRAMEBUFFERS_BASE & 0x0fffffff;
	address_max = address_min + HDMI_IN0_FRAMEBUFFERS_SIZE*FRAMEBUFFER_COUNT;
	if((hdmi_in0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((hdmi_in0_dma_slot0_address_read() < address_min) || (hdmi_in0_dma_slot0_address_read() > address_max)))
		printf("dvisampler0: slot0: stray DMA\r\n");
	if((hdmi_in0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((hdmi_in0_dma_slot1_address_read() < address_min) || (hdmi_in0_dma_slot1_address_read() > address_max)))
		printf("dvisampler0: slot1: stray DMA\r\n");

#ifdef CLEAN_COMMUTATION
	if((hdmi_in0_resdetection_hres_read() != hdmi_in0_hres)
	  || (hdmi_in0_resdetection_vres_read() != hdmi_in0_vres)) {
		/* Dump frames until we get the expected resolution */
		if(hdmi_in0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
			hdmi_in0_dma_slot0_address_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[0]));
			hdmi_in0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
		}
		if(hdmi_in0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
			hdmi_in0_dma_slot1_address_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[1]));
			hdmi_in0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
		}
		return;
	}
#endif

	expected_length = hdmi_in0_hres*hdmi_in0_vres*2;
	if(hdmi_in0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = hdmi_in0_dma_slot0_address_read() - (hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[0]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = hdmi_in0_fb_slot_indexes[0];
			hdmi_in0_fb_slot_indexes[0] = hdmi_in0_next_fb_index;
			hdmi_in0_next_fb_index = (hdmi_in0_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else {
#ifdef DEBUG
			printf("dvisampler0: slot0: unexpected frame length: %d\r\n", length);
#endif
		}
		hdmi_in0_dma_slot0_address_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[0]));
		hdmi_in0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	}
	if(hdmi_in0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING) {
		length = hdmi_in0_dma_slot1_address_read() - (hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[1]) & 0x0fffffff);
		if(length == expected_length) {
			fb_index = hdmi_in0_fb_slot_indexes[1];
			hdmi_in0_fb_slot_indexes[1] = hdmi_in0_next_fb_index;
			hdmi_in0_next_fb_index = (hdmi_in0_next_fb_index + 1) & FRAMEBUFFER_MASK;
		} else {
#ifdef DEBUG
			printf("dvisampler0: slot1: unexpected frame length: %d\r\n", length);
#endif
		}
		hdmi_in0_dma_slot1_address_write(hdmi_in0_framebuffer_base(hdmi_in0_fb_slot_indexes[1]));
		hdmi_in0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	}

	if(fb_index != -1)
		hdmi_in0_fb_index = fb_index;
	processor_update();
}

static int hdmi_in0_connected;
static int hdmi_in0_locked;

void hdmi_in0_init_video(int hres, int vres)
{
	unsigned int mask;

	hdmi_in0_clocking_pll_reset_write(1);
	hdmi_in0_connected = hdmi_in0_locked = 0;
	hdmi_in0_hres = hres; hdmi_in0_vres = vres;

	hdmi_in0_dma_frame_size_write(hres*vres*2);
	hdmi_in0_fb_slot_indexes[0] = 0;
	hdmi_in0_dma_slot0_address_write(hdmi_in0_framebuffer_base(0));
	hdmi_in0_dma_slot0_status_write(DVISAMPLER_SLOT_LOADED);
	hdmi_in0_fb_slot_indexes[1] = 1;
	hdmi_in0_dma_slot1_address_write(hdmi_in0_framebuffer_base(1));
	hdmi_in0_dma_slot1_status_write(DVISAMPLER_SLOT_LOADED);
	hdmi_in0_next_fb_index = 2;

	hdmi_in0_dma_ev_pending_write(hdmi_in0_dma_ev_pending_read());
	hdmi_in0_dma_ev_enable_write(0x3);
	mask = irq_getmask();
	mask |= 1 << HDMI_IN0_INTERRUPT;
	irq_setmask(mask);

	hdmi_in0_fb_index = 3;
}

void hdmi_in0_disable(void)
{
	unsigned int mask;

	mask = irq_getmask();
	mask &= ~(1 << HDMI_IN0_INTERRUPT);
	irq_setmask(mask);

	hdmi_in0_dma_slot0_status_write(DVISAMPLER_SLOT_EMPTY);
	hdmi_in0_dma_slot1_status_write(DVISAMPLER_SLOT_EMPTY);
	hdmi_in0_clocking_pll_reset_write(1);
}

void hdmi_in0_clear_framebuffers(void)
{
	int i;
	flush_l2_cache();
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + HDMI_IN0_FRAMEBUFFERS_BASE);
	for(i=0; i<(HDMI_IN0_FRAMEBUFFERS_SIZE*FRAMEBUFFER_COUNT)/4; i++) {
		framebuffer[i] = 0x80108010; /* black in YCbCr 4:2:2*/
	}
}

static int hdmi_in0_d0, hdmi_in0_d1, hdmi_in0_d2;

void hdmi_in0_print_status(void)
{
	hdmi_in0_data0_wer_update_write(1);
	hdmi_in0_data1_wer_update_write(1);
	hdmi_in0_data2_wer_update_write(1);
	printf("dvisampler0: ph:%4d %4d %4d // charsync:%d%d%d [%d %d %d] // WER:%3d %3d %3d // chansync:%d // res:%dx%d\r\n",
		hdmi_in0_d0, hdmi_in0_d1, hdmi_in0_d2,
		hdmi_in0_data0_charsync_char_synced_read(),
		hdmi_in0_data1_charsync_char_synced_read(),
		hdmi_in0_data2_charsync_char_synced_read(),
		hdmi_in0_data0_charsync_ctl_pos_read(),
		hdmi_in0_data1_charsync_ctl_pos_read(),
		hdmi_in0_data2_charsync_ctl_pos_read(),
		hdmi_in0_data0_wer_value_read(),
		hdmi_in0_data1_wer_value_read(),
		hdmi_in0_data2_wer_value_read(),
		hdmi_in0_chansync_channels_synced_read(),
		hdmi_in0_resdetection_hres_read(),
		hdmi_in0_resdetection_vres_read());
}

static int wait_idelays(void)
{
	int ev;

	ev = 0;
	elapsed(&ev, 1);
	while(hdmi_in0_data0_cap_dly_busy_read()
	  || hdmi_in0_data1_cap_dly_busy_read()
	  || hdmi_in0_data2_cap_dly_busy_read()) {
		if(elapsed(&ev, identifier_frequency_read() >> 6) == 0) {
			printf("dvisampler0: IDELAY busy timeout\r\n");
			return 0;
		}
	}
	return 1;
}

int hdmi_in0_calibrate_delays(void)
{
	hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_CAL|DVISAMPLER_DELAY_SLAVE_CAL);
	if(!wait_idelays())
		return 0;
	hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_RST|DVISAMPLER_DELAY_SLAVE_RST);
	hdmi_in0_data0_cap_phase_reset_write(1);
	hdmi_in0_data1_cap_phase_reset_write(1);
	hdmi_in0_data2_cap_phase_reset_write(1);
	hdmi_in0_d0 = hdmi_in0_d1 = hdmi_in0_d2 = 0;
	return 1;
}

int hdmi_in0_adjust_phase(void)
{
	switch(hdmi_in0_data0_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d0--;
			hdmi_in0_data0_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d0++;
			hdmi_in0_data0_cap_phase_reset_write(1);
			break;
	}
	switch(hdmi_in0_data1_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d1--;
			hdmi_in0_data1_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d1++;
			hdmi_in0_data1_cap_phase_reset_write(1);
			break;
	}
	switch(hdmi_in0_data2_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d2--;
			hdmi_in0_data2_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
			hdmi_in0_d2++;
			hdmi_in0_data2_cap_phase_reset_write(1);
			break;
	}
	return 1;
}

int hdmi_in0_init_phase(void)
{
	int o_d0, o_d1, o_d2;
	int i, j;

	for(i=0;i<100;i++) {
		o_d0 = hdmi_in0_d0;
		o_d1 = hdmi_in0_d1;
		o_d2 = hdmi_in0_d2;
		for(j=0;j<1000;j++) {
			if(!hdmi_in0_adjust_phase())
				return 0;
		}
		if((abs(hdmi_in0_d0 - o_d0) < 4) && (abs(hdmi_in0_d1 - o_d1) < 4) && (abs(hdmi_in0_d2 - o_d2) < 4))
			return 1;
	}
	return 0;
}

int hdmi_in0_phase_startup(void)
{
	int ret;
	int attempts;

	attempts = 0;
	while(1) {
		attempts++;
		hdmi_in0_calibrate_delays();
		if(hdmi_in0_debug)
			printf("dvisampler0: delays calibrated\r\n");
		ret = hdmi_in0_init_phase();
		if(ret) {
			if(hdmi_in0_debug)
				printf("dvisampler0: phase init OK\r\n");
			return 1;
		} else {
			printf("dvisampler0: phase init failed\r\n");
			if(attempts > 3) {
				printf("dvisampler0: giving up\r\n");
				hdmi_in0_calibrate_delays();
				return 0;
			}
		}
	}
}

static void hdmi_in0_check_overflow(void)
{
	if(hdmi_in0_frame_overflow_read()) {
		printf("dvisampler0: FIFO overflow\r\n");
		hdmi_in0_frame_overflow_write(1);
	}
}

static int hdmi_in0_clocking_locked_filtered(void)
{
	static int lock_start_time;
	static int lock_status;

	if(hdmi_in0_clocking_locked_read()) {
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

void hdmi_in0_service(void)
{
	static int last_event;

	if(hdmi_in0_connected) {
		if(!hdmi_in0_edid_hpd_notif_read()) {
			if(hdmi_in0_debug)
				printf("dvisampler0: disconnected\r\n");
			hdmi_in0_connected = 0;
			hdmi_in0_locked = 0;
			hdmi_in0_clocking_pll_reset_write(1);
			hdmi_in0_clear_framebuffers();
		} else {
			if(hdmi_in0_locked) {
				if(hdmi_in0_clocking_locked_filtered()) {
					if(elapsed(&last_event, identifier_frequency_read()/2)) {
						hdmi_in0_adjust_phase();
						if(hdmi_in0_debug)
							hdmi_in0_print_status();
					}
				} else {
					if(hdmi_in0_debug)
						printf("dvisampler0: lost PLL lock\r\n");
					hdmi_in0_locked = 0;
					hdmi_in0_clear_framebuffers();
				}
			} else {
				if(hdmi_in0_clocking_locked_filtered()) {
					if(hdmi_in0_debug)
						printf("dvisampler0: PLL locked\r\n");
					hdmi_in0_phase_startup();
					if(hdmi_in0_debug)
						hdmi_in0_print_status();
					hdmi_in0_locked = 1;
				}
			}
		}
	} else {
		if(hdmi_in0_edid_hpd_notif_read()) {
			if(hdmi_in0_debug)
				printf("dvisampler0: connected\r\n");
			hdmi_in0_connected = 1;
			hdmi_in0_clocking_pll_reset_write(0);
		}
	}
	hdmi_in0_check_overflow();
}

#endif
