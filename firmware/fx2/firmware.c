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

#ifdef DEBUG 
#include "softserial.h"
#include <stdio.h>
#define putchar soft_putchar
#define getchar soft_getchar
#else
#define printf(...)
#endif

#include <fx2macros.h>
#include <fx2ints.h>
#include <autovector.h>
#include <delay.h>
#include <setupdat.h>

#include "cdc.h"

#define SYNCDELAY SYNCDELAY4

volatile __bit dosud=FALSE;
volatile __bit dosuspend=FALSE;

// custom functions
extern void main_loop();
extern void main_init();


void main() {

#ifdef DEBUG
 SETCPUFREQ(CLK_48M); // required for sio0_init 
 // main_init can still set this to whatever you want.
 soft_sio0_init(57600); // needed for printf if debug defined
#endif

 main_init();

 // set up interrupts.
 USE_USB_INTS();
 
 ENABLE_SUDAV();
 ENABLE_USBRESET();
 ENABLE_HISPEED(); 
 ENABLE_SUSPEND();
 ENABLE_RESUME();

 EA=1;

// iic files (c2 load) don't need to renumerate/delay
// trm 3.6
#ifndef NORENUM
 RENUMERATE();
#else
 USBCS &= ~bmDISCON;
#endif
 
 while(TRUE) {

     main_loop();

     if (dosud) {
       dosud=FALSE;
       handle_setupdata();
     }

#ifdef SUSPEND_ENABLED
     if (dosuspend) {
        dosuspend=FALSE;
        do {
           printf ( "I'm going to Suspend.\n" );
           WAKEUPCS |= bmWU|bmWU2; // make sure ext wakeups are cleared
           SUSPEND=1;
           PCON |= 1;
           __asm
           nop
           nop
           nop
           nop
           nop
           nop
           nop
           __endasm;
        } while ( !remote_wakeup_allowed && REMOTE_WAKEUP()); 
        printf ( "I'm going to wake up.\n");

        // resume
        // trm 6.4
        if ( REMOTE_WAKEUP() ) {
            delay(5);
            USBCS |= bmSIGRESUME;
            delay(15);
            USBCS &= ~bmSIGRESUME;
        }

     }
#endif
 } // end while

} // end main

void resume_isr() __interrupt RESUME_ISR {
 CLEAR_RESUME();
}
  
void sudav_isr() __interrupt SUDAV_ISR {
 dosud=TRUE;
 CLEAR_SUDAV();
}
void usbreset_isr() __interrupt USBRESET_ISR {
 handle_hispeed(FALSE);
 CLEAR_USBRESET();
}
void hispeed_isr() __interrupt HISPEED_ISR {
 handle_hispeed(TRUE);
 CLEAR_HISPEED();
}

void suspend_isr() __interrupt SUSPEND_ISR {
 dosuspend=TRUE;
 CLEAR_SUSPEND();
}


void ISR_USART0(void) __interrupt 4 __critical {
	if (RI) {
		RI=0;
		if (!cdc_can_send()) {
			// Mark overflow
		} else {
			cdc_queue_data(SBUF0);
		}
		// FIXME: Should use a timer, rather then sending one byte at a
		// time.
		cdc_send_queued_data();
	}
	if (TI) {
		TI=0;
//		transmit();
	}
}

