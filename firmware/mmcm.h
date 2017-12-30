#ifndef __MMCM_H
#define __MMCM_H

#include <generated/csr.h>

typedef void (*mmcm_write_t)(int,int);
typedef int (*mmcm_read_t)(int);

typedef struct {
	mmcm_write_t write;
	mmcm_read_t  read;
} MMCM;

void mmcm_config_for_clock(MMCM *mmcm, int freq);
void mmcm_dump(MMCM *mmcm);
void mmcm_dump_all(void);

#ifdef CSR_HDMI_OUT0_DRIVER_CLOCKING_MMCM_RESET_ADDR
void hdmi_out0_driver_clocking_mmcm_write(int adr, int data);
int hdmi_out0_driver_clocking_mmcm_read(int adr);
extern MMCM hdmi_out0_driver_clocking_mmcm;
#endif

#ifdef CSR_HDMI_IN0_CLOCKING_MMCM_RESET_ADDR
void hdmi_in0_clocking_mmcm_write(int adr, int data);
int hdmi_in0_clocking_mmcm_read(int adr);
extern MMCM hdmi_in0_clocking_mmcm;
#endif

#endif
