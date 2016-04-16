/**
 * Copyright (C) 2009 Ubixum, Inc. 
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 **/
#include <stdio.h>

#include <fx2regs.h>
#include <fx2macros.h>
#include <serial.h>
#include <delay.h>
#include <autovector.h>
#include <lights.h>
#include <setupdat.h>
#include <eputils.h>
#include <i2c.h>

#include "cdc.h"

#define SYNCDELAY SYNCDELAY4

// -----------------------------------------------------------------------

BOOL cdcuser_set_line_rate(DWORD baud_rate) {
        if (baud_rate > 115200 || baud_rate < 2400)
            baud_rate = 115200;
	sio0_init(baud_rate);
	return TRUE;
}

void cdcuser_receive_data(BYTE* data, WORD length) {
        WORD i;
        for (i=0; i < length ; ++i) {
		SBUF0 = data[i];
		while(TI);
	}
}

void uart_init() {

	cdcuser_set_line_rate(9600);

    // Used by the CDC serial port (EP2 == TX, EP4 == RX)
	SYNCDELAY; EP2CFG = 0xA2;  // Activate, OUT Direction, BULK Type, 512  bytes Size, Double buffered
	SYNCDELAY; EP4CFG = 0xE2;  // Activate, IN  Direction, BULK Type, 512  bytes Size, Double buffered

	// arm ep2
	CDC_H2D_EP(BCL) = 0x80; // write once
	SYNCDELAY;
	CDC_H2D_EP(BCL) = 0x80; // do it again
	SYNCDELAY;

	// clear the cdc_queued_bytes
	cdc_queued_bytes = 0;

	ES0 = 1; /* enable serial interrupts */
	PS0 = 0; /* set serial interrupts to low priority */

	TI = 1; /* clear transmit interrupt */
	RI = 0; /* clear receiver interrupt */

}
