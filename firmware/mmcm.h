#ifndef __MMCM_H
#define __MMCM_H

#include <generated/csr.h>

#ifdef CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR

void hdmi_out0_mmcm_write(int adr, int data);
int hdmi_out0_mmcm_read(int adr);
void hdmi_in0_clocking_mmcm_write(int adr, int data);
int hdmi_in0_clocking_mmcm_read(int adr);

void mmcm_config_for_clock(int freq);
#endif

void mmcm_dump(void);

#endif
