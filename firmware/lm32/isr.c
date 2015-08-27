#include <generated/csr.h>
#include <irq.h>
#include <uart.h>

#include "hdmi_in0.h"
#include "hdmi_in1.h"

void isr(void);
void isr(void)
{
	unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << UART_INTERRUPT))
		uart_isr();
	if(irqs & (1 << HDMI_IN0_INTERRUPT))
		hdmi_in0_isr();
	if(irqs & (1 << HDMI_IN1_INTERRUPT))
		hdmi_in1_isr();
}
