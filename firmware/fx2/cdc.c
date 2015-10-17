
#include <fx2regs.h>
#include <fx2macros.h>
#include <delay.h>

#include "cdc.h"

#define SYNCDELAY SYNCDELAY4

volatile WORD cdc_queued_bytes = 0;

struct usb_cdc_line_coding cdc_current_line_coding = {
  .bDTERate0 = LSB(2400),
  .bDTERate1 = MSB(2400),
  .bDTERate2 = 0,
  .bDTERate3 = 0,
  .bCharFormat = USB_CDC_1_STOP_BITS,
  .bParityType = USB_CDC_NO_PARITY,
  .bDataBits = 8
};

void cdc_receive_poll() {
	if ( !(EP2468STAT & bmCDC_H2D_EP(EMPTY)) ) {
		WORD bytes = MAKEWORD(CDC_H2D_EP(BCH),CDC_H2D_EP(BCL));
		cdcuser_receive_data(CDC_H2D_EP(FIFOBUF), bytes);
		CDC_H2D_EP(BCL) = 0x80; // Mark us ready to receive again.
	}
	// FIXME: Send the interrupt thingy
}

BOOL cdc_handle_command(BYTE cmd) {
	int i;
	BYTE* line_coding = (BYTE*)&cdc_current_line_coding;
        DWORD baud_rate = 0;

	switch(cmd) {
	case USB_CDC_REQ_SET_LINE_CODING:
		EUSB = 0 ;
		SUDPTRCTL = 0x01;
		EP0BCL = 0x00;
		SUDPTRCTL = 0x00;
		EUSB = 1;

		while (EP0BCL != 7);
			SYNCDELAY;

		for (i=0;i<7;i++)
			line_coding[i] = EP0BUF[i];

		// FIXME: Make this following line work rather then the if statement chain!
//                baud_rate = MAKEDWORD(
//			MAKEWORD(cdc_current_line_coding.bDTERate3, cdc_current_line_coding.bDTERate2),
//			MAKEWORD(cdc_current_line_coding.bDTERate1, cdc_current_line_coding.bDTERate0));
		baud_rate = MAKEDWORD(
			MAKEWORD(line_coding[3], line_coding[2]),
			MAKEWORD(line_coding[1], line_coding[0]));

		if (!cdcuser_set_line_rate(baud_rate))
			; //EP0STALL();

		return TRUE;

	case USB_CDC_REQ_GET_LINE_CODING:
		SUDPTRCTL = 0x01;
				
		for (i=0;i<7;i++)
			EP0BUF[i] = line_coding[i];

		EP0BCH = 0x00;
		SYNCDELAY;
		EP0BCL = 7;
		SYNCDELAY;
		while (EP0CS & 0x02);
		SUDPTRCTL = 0x00;
				
		return TRUE;

	case USB_CDC_REQ_SET_CONTROL_LINE_STATE:
		return TRUE;

	default:
		return FALSE;
	}
}
