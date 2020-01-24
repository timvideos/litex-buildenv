#include "pcie.h"
#include "framebuffer.h"

// Last 4 bytes of the buffer area
volatile unsigned int * pcie_in_fb_index = (unsigned int*)(MAIN_RAM_BASE + FRAMEBUFFER_BASE_PCIE + 4 * FRAMEBUFFER_SIZE - sizeof(unsigned int));
volatile unsigned int * pcie_out_fb_index = (unsigned int*)(MAIN_RAM_BASE + FRAMEBUFFER_BASE_PCIE + 8 * FRAMEBUFFER_SIZE - sizeof(unsigned int));

unsigned int pcie_in_framebuffer_base(char n) {
	return FRAMEBUFFER_BASE_PCIE + n * FRAMEBUFFER_SIZE;
}
