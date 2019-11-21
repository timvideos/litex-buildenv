#ifndef __PCIE_H
#define __PCIE_H

extern volatile unsigned int * pcie_out_fb_index;
extern volatile unsigned int * pcie_in_fb_index;
unsigned int pcie_in_framebuffer_base(char);

#endif
