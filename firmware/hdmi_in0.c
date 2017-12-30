#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <time.h>
#include <system.h>
#include <generated/csr.h>
#include <generated/mem.h>
#include <hw/flags.h>
#include "extra-flags.h"

#include "stdio_wrap.h"

#ifdef CSR_HDMI_IN0_BASE

#include "hdmi_in0.h"

int hdmi_in0_debug;
int hdmi_in0_fb_index;

//#define CLEAN_COMMUTATION
//#define DEBUG

fb_ptrdiff_t hdmi_in0_framebuffer_base(char n) {
	return HDMI_IN0_FRAMEBUFFERS_BASE + n * FRAMEBUFFER_SIZE;
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
	address_max = address_min + FRAMEBUFFER_SIZE*FRAMEBUFFER_COUNT;
	if((hdmi_in0_dma_slot0_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((hdmi_in0_dma_slot0_address_read() < address_min) || (hdmi_in0_dma_slot0_address_read() > address_max)))
		wprintf("dvisampler0: slot0: stray DMA\n");
	if((hdmi_in0_dma_slot1_status_read() == DVISAMPLER_SLOT_PENDING)
		&& ((hdmi_in0_dma_slot1_address_read() < address_min) || (hdmi_in0_dma_slot1_address_read() > address_max)))
		wprintf("dvisampler0: slot1: stray DMA\n");

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
			wprintf("dvisampler0: slot0: unexpected frame length: %d\n", length);
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
			wprintf("dvisampler0: slot1: unexpected frame length: %d\n", length);
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
	hdmi_in0_hres = hres; hdmi_in0_vres = vres;

	hdmi_in0_enable();
}

void hdmi_in0_enable(void)
{
	unsigned int mask;
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
	hdmi_in0_clocking_pll_reset_write(1);
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
	hdmi_in0_clocking_mmcm_reset_write(1);
#endif
	hdmi_in0_connected = hdmi_in0_locked = 0;

	hdmi_in0_dma_frame_size_write(hdmi_in0_hres*hdmi_in0_vres*2);
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

bool hdmi_in0_status(void)
{
	unsigned int mask = irq_getmask();
	mask &= (1 << HDMI_IN0_INTERRUPT);
	return (mask != 0);
}

void hdmi_in0_disable(void)
{
	unsigned int mask;

	mask = irq_getmask();
	mask &= ~(1 << HDMI_IN0_INTERRUPT);
	irq_setmask(mask);

	hdmi_in0_dma_slot0_status_write(DVISAMPLER_SLOT_EMPTY);
	hdmi_in0_dma_slot1_status_write(DVISAMPLER_SLOT_EMPTY);
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
	hdmi_in0_clocking_pll_reset_write(1);
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
	hdmi_in0_clocking_mmcm_reset_write(1);
#endif
}

void hdmi_in0_clear_framebuffers(void)
{
	int i;
	flush_l2_cache();
	volatile unsigned int *framebuffer = (unsigned int *)(MAIN_RAM_BASE + HDMI_IN0_FRAMEBUFFERS_BASE);
	for(i=0; i<(FRAMEBUFFER_SIZE*FRAMEBUFFER_COUNT)/4; i++) {
		framebuffer[i] = 0x80108010; /* black in YCbCr 4:2:2*/
	}
}

static int hdmi_in0_d0, hdmi_in0_d1, hdmi_in0_d2;

void hdmi_in0_print_status(void)
{
	hdmi_in0_data0_wer_update_write(1);
	hdmi_in0_data1_wer_update_write(1);
	hdmi_in0_data2_wer_update_write(1);
	wprintf("dvisampler0: ph:%4d %4d %4d // charsync:%d%d%d [%d %d %d] // WER:%3d %3d %3d // chansync:%d // res:%dx%d\n",
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

#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
static int wait_idelays(void)
{
	int ev;

	ev = 0;
	elapsed(&ev, 1);
	while(hdmi_in0_data0_cap_dly_busy_read()
	  || hdmi_in0_data1_cap_dly_busy_read()
	  || hdmi_in0_data2_cap_dly_busy_read()) {
		if(elapsed(&ev, SYSTEM_CLOCK_FREQUENCY >> 6) == 0) {
			wprintf("dvisampler0: IDELAY busy timeout (%hhx %hhx %hhx)\n",
				hdmi_in0_data0_cap_dly_busy_read(),
				hdmi_in0_data1_cap_dly_busy_read(),
				hdmi_in0_data2_cap_dly_busy_read());
			return 0;
		}
	}
	return 1;
}
#endif

int hdmi_in0_calibrate_delays(int freq)
{
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
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
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
	int i, phase_detector_delay;
	hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_RST);
	hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_RST);
	hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_RST);
	hdmi_in0_data0_cap_phase_reset_write(1);
	hdmi_in0_data1_cap_phase_reset_write(1);
	hdmi_in0_data2_cap_phase_reset_write(1);
	hdmi_in0_d0 = hdmi_in0_d1 = hdmi_in0_d2 = 0;

	/* preload slave phase detector idelay with 90° phase shift
	  (78 ps taps on 7-series) */
	phase_detector_delay = 10000000/(4*freq*78);
	for(i=0; i<phase_detector_delay; i++) {
		hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_SLAVE_INC);
		hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_SLAVE_INC);
		hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_SLAVE_INC);
	}
#endif
	return 1;
}

int hdmi_in0_adjust_phase(void)
{
	switch(hdmi_in0_data0_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_DEC |
				                             DVISAMPLER_DELAY_SLAVE_DEC);
#endif
			hdmi_in0_d0--;
			hdmi_in0_data0_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data0_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_INC |
				                             DVISAMPLER_DELAY_SLAVE_INC);
#endif
			hdmi_in0_d0++;
			hdmi_in0_data0_cap_phase_reset_write(1);
			break;
	}
	switch(hdmi_in0_data1_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_DEC |
				                             DVISAMPLER_DELAY_SLAVE_DEC);
#endif
			hdmi_in0_d1--;
			hdmi_in0_data1_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data1_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_INC |
				                             DVISAMPLER_DELAY_SLAVE_INC);
#endif
			hdmi_in0_d1++;
			hdmi_in0_data1_cap_phase_reset_write(1);
			break;
	}
	switch(hdmi_in0_data2_cap_phase_read()) {
		case DVISAMPLER_TOO_LATE:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_DEC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_DEC |
				                             DVISAMPLER_DELAY_SLAVE_DEC);
#endif
			hdmi_in0_d2--;
			hdmi_in0_data2_cap_phase_reset_write(1);
			break;
		case DVISAMPLER_TOO_EARLY:
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_INC);
			if(!wait_idelays())
				return 0;
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_data2_cap_dly_ctl_write(DVISAMPLER_DELAY_MASTER_INC |
				                             DVISAMPLER_DELAY_SLAVE_INC);
#endif
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

int hdmi_in0_phase_startup(int freq)
{
	int ret;
	int attempts;

	attempts = 0;
	while(1) {
		attempts++;
		hdmi_in0_calibrate_delays(freq);
		if(hdmi_in0_debug)
			wprintf("dvisampler0: delays calibrated\n");
		ret = hdmi_in0_init_phase();
		if(ret) {
			if(hdmi_in0_debug)
				wprintf("dvisampler0: phase init OK\n");
			return 1;
		} else {
			wprintf("dvisampler0: phase init failed\n");
			if(attempts > 3) {
				wprintf("dvisampler0: giving up\n");
				hdmi_in0_calibrate_delays(freq);
				return 0;
			}
		}
	}
}

static void hdmi_in0_check_overflow(void)
{
	if(hdmi_in0_frame_overflow_read()) {
		wprintf("dvisampler0: FIFO overflow\n");
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
				if(elapsed(&lock_start_time, SYSTEM_CLOCK_FREQUENCY/4))
					lock_status = 2;
				break;
			case 2:
				return 1;
		}
	} else
		lock_status = 0;
	return 0;
}

void hdmi_in0_service(int freq)
{
	static int last_event;

	if(hdmi_in0_connected) {
		if(!hdmi_in0_edid_hpd_notif_read()) {
			if(hdmi_in0_debug)
				wprintf("dvisampler0: disconnected\n");
			hdmi_in0_connected = 0;
			hdmi_in0_locked = 0;
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_clocking_pll_reset_write(1);
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_clocking_mmcm_reset_write(1);
#endif
			hdmi_in0_clear_framebuffers();
		} else {
			if(hdmi_in0_locked) {
				if(hdmi_in0_clocking_locked_filtered()) {
					if(elapsed(&last_event, SYSTEM_CLOCK_FREQUENCY/2)) {
						hdmi_in0_adjust_phase();
						if(hdmi_in0_debug)
							hdmi_in0_print_status();
					}
				} else {
					if(hdmi_in0_debug)
						wprintf("dvisampler0: lost PLL lock\n");
					hdmi_in0_locked = 0;
					hdmi_in0_clear_framebuffers();
				}
			} else {
				if(hdmi_in0_clocking_locked_filtered()) {
					if(hdmi_in0_debug)
						wprintf("dvisampler0: PLL locked\n");
					hdmi_in0_phase_startup(freq);
					if(hdmi_in0_debug)
						hdmi_in0_print_status();
					hdmi_in0_locked = 1;
				}
			}
		}
	} else {
		if(hdmi_in0_edid_hpd_notif_read()) {
			if(hdmi_in0_debug)
				wprintf("dvisampler0: connected\n");
			hdmi_in0_connected = 1;
#ifdef CSR_HDMI_IN0_CLOCKING_PLL_RESET_ADDR
			hdmi_in0_clocking_pll_reset_write(0);
#elif CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
			hdmi_in0_clocking_mmcm_reset_write(0);
#endif
		}
	}
	hdmi_in0_check_overflow();
}

#endif
