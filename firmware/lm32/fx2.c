#include <generated/csr.h>
#ifdef CSR_FX2_RESET_OUT_ADDR
#include <stdio.h>

static void fx2_wait(void)
{
	unsigned int i;
	for(i=0;i<1000;i++) __asm__("nop");
}

static void fx2_load(void)
{
        printf("fx2: Waiting for FX2 to load firmware.\n");
}

void fx2_reboot(void)
{
        printf("fx2: Turning off.\n");
	fx2_reset_out_write(0);
	fx2_wait();
	fx2_reset_out_write(1);
        printf("fx2: Turning on.\n");
	fx2_load();
        printf("fx2: Booted.\n");
}

#endif
