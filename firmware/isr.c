#include <generated/csr.h>
#include <irq.h>
#include <uart.h>

#include "hdmi_in0.h"
void isr(void);
void isr(void)
{
	unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << UART_INTERRUPT))
		uart_isr();
#ifdef CSR_HDMI_IN0_BASE
	if(irqs & (1 << HDMI_IN0_INTERRUPT))
		hdmi_in0_isr();
#endif
}
