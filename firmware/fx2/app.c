/*
 * Copyright (C) 2009-2012 Chris McClelland
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <fx2regs.h>
#include <fx2macros.h>
#include <eputils.h>
#include <delay.h>
#include <setupdat.h>
#include <makestuff.h>
#include "defs.h"
#include "debug.h"

#include "cdc.h"
#include "uvc.h"
#include "read-serialno.h"

extern const uint8 dev_strings[];
void TD_Init(void);
void TD_Poll(void);

// Called once at startup
//
extern void uart_init();
void mainInit(void) {
#ifdef BOARD_opsis
	patch_usb_serial_number_with_eeprom_macaddress();
#endif

	// This is only necessary for cases where you want to load firmware into the RAM of an FX2 that
	// has already loaded firmware from an EEPROM. It should definitely be removed for firmwares
	// which are themselves to be loaded from EEPROM.
#ifndef EEPROM
	RENUMERATE_UNCOND();
#endif

	// Clear wakeup (see AN15813: http://www.cypress.com/?docID=4633)
	WAKEUPCS = bmWU | bmDPEN | bmWUEN;
	WAKEUPCS = bmWU | bmDPEN | bmWUEN;

	// Disable alternate functions for PORTA 0,1,3 & 7.
	PORTACFG = 0x00;

	I2CTL |= bm400KHZ;

	TD_Init();
	
	uart_init();

#ifdef DEBUG
	usartInit();
	{
		const uint8 *s = dev_strings;
		uint8 len;
		s = s + *s;
		len = (*s)/2 - 1;
		s += 2;
		while ( len ) {
			usartSendByte(*s);
			s += 2;
			len--;
		}
		usartSendByte(' ');
		len = (*s)/2 - 1;
		s += 2;
		while ( len ) {
			usartSendByte(*s);
			s += 2;
			len--;
		}
		usartSendByte('\r');
	}
#endif
}

// Called repeatedly while the device is idle
//
void mainLoop(void) {
	TD_Poll();
	cdc_receive_poll();
}

// Called when a vendor command is received
//
uint8 handleVendorCommand(uint8 cmd) {
	if (handleUVCCommand(cmd))
            return true;
	if (cdc_handle_command(cmd))
            return true;

	return false;  // unrecognised command
}

void TD_Init(void)             // Called once at startup
{
	// Return FIFO setings back to default just in case previous firmware messed with them.
	SYNCDELAY; PINFLAGSAB   = 0x00;
	SYNCDELAY; PINFLAGSCD   = 0x00;
	SYNCDELAY; FIFOPINPOLAR = 0x00;
	
	// Global settings
	//SYNCDELAY; REVCTL = 0x03;
	SYNCDELAY; CPUCS  = ((CPUCS & ~bmCLKSPD) | bmCLKSPD1);  // 48MHz
	
    /* IFCONFIG Register
     *      Structure: 
     *          BIT 7   : IFCLKSRC, FIFO/GPIF Clock Source, 
     *                      Selects b/w internal and external sources: 0 = external, 1 = internal
     *          BIT 6   : 3048MHZ, Internal FIFO/GPIF Clock Frequency. 
     *                      Selects b/w the 30- and 48-MHz internal clock: 0 = 30 MHz, 1 = 48 MHz. This bit has no effect when IFCONFIG.7 = 0.
     *          BIT 5   : IFCLKOE, IFCLK pin output enable. 
     *                      Output enable for the internal clock source: 0 = disable(tristate), 1 = enable(drive). This bit has no effect when IFCONFIG.7 = 0.
     *          BIT 4   : IFCLKPOL, Invert the IFCLK signal. 
     *                      Inverts the polarity of the interface clock (whether it’s internal or external): 0 = normal, 1 = inverted.
     *          BIT 3   : ASYNC, FIFO/GPIF Asynchronous Mode
     *                      When ASYNC=0, the FIFO/GPIF operate synchronously: a clock is supplied either internally or externally on the IFCLK pin; the FIFO control signals function as read and write enable signals for the clock signal.
     *                      When ASYNC=1, the FIFO/GPIF operate asynchronously: no clock signal input to IFCLK isrequired; the FIFO control signals function directly as read and write strobes.
     *          BIT 2   : GSTATE, Drive GSTATE [2:0] on PORTE [2:0].
     *                      When GSTATE=1, three bits in Port E take on the signals shown in Table 15-6. The GSTATE bits, which indicate GPIF states, are used for diagnostic purposes. 
     *          BIT 1-0 : IFCFG, Select Interface Mode (Ports, GPIF, or Slave FIFO)
     *                      Required to be 0b11 for Slave FIFO. See Page 15-16 TRM
     */
     
    // Internal Clock, 48MHz, IFCLK output enable to pin, Normal Polarity, 
	// Synchronous FIFO, Nothing to do with GSTATE, Set interface mode to Slave FIFO.
    SYNCDELAY; IFCONFIG = 0xE3; 
    
	// EP1OUT & EP1IN
    /* 
     * Endpoint 1 IN/OUT Configuration Registers
     *      Structure:
     *          BIT 7   : VALID, Activate an Endpoint. Set VALID=1 to activate an endpoint, and VALID=0 to de-activate it.
     *          BIT 6   : Unused
     *          BIT 5-4 : TYPE, Defines the Endpoint Type
     *                           _______________________________
     *                          | TYPE1 | TYPE0 | Endpoint Type |
     *                          |_______|_______|_______________|
     *                          | 0     | 0     |   Invalid     |
     *                          | 0     | 1     |   Invalid     |
     *                          | 1     | 0     | BULK (default)|
     *                          | 1     | 1     |  INTERRUPT    |
     *                          |_______|_______|_______________|
     * 
     *          BIT 3-0 : Unused
     */

    // Used by the CDC serial port (Polling / Interrupt?)
    SYNCDELAY; EP1OUTCFG = 0x00;  // Disable Endpoint1 OUT
	SYNCDELAY; EP1INCFG  = 0xA0;  // Activate Endpoint1 IN,BULK Type
    
    // VALID DIR TYPE1 TYPE0 SIZE 0 BUF1 BUF0
    /* EPxCGF Register for configuring Endpoints
     * 
     * EPxCGF, x = 2, 4, 6 & 8
     * 
     *      Structure:
     *          Bit 7   : VALID, Set VALID=1 to activate an endpoint, and VALID=0 to de-activate it
     *          Bit 6   : DIR, 0=OUT, 1=IN
     *          BIT 5-4 : TYPE, Defines the Endpoint Type
     *                           _______________________________
     *                          | TYPE1 | TYPE0 | Endpoint Type |
     *                          |_______|_______|_______________|
     *                          | 0     | 0     |   Invalid     |
     *                          | 0     | 1     | ISOCHRONOUS   |
     *                          | 1     | 0     | BULK (default)|
     *                          | 1     | 1     |  INTERRUPT    |
     *                          |_______|_______|_______________|
     *           
     *          BIT 3   : SIZE, Sets Size of Endpoint Buffer.0 = 512 bytes, 1 = 1024 bytes
     *                      Note: Endpoints 4 and 8 can only be 512 bytes. Endpoints 2 and 6 are selectable.
     *          BIT 2   : Unused
     *          BIT 1-0 : Buffering Type/Amount 
     *                       _________________________
     *                      | BUF1 | BUF0 | Buffering |
     *                      |______|______|___________|
     *                      |   0  |   0  |   Quad    |
     *                      |   0  |   1  |  Invalid  |
     *                      |   1  |   0  |  Double   |
     *                      |   1  |   1  |  Triple   |
     *                      |______|______|___________|
     */
    
    // Used by the video data
	SYNCDELAY; EP6CFG = 0xDA;  // Activate, IN  Direction, ISO  Type, 1024 bytes Size, Double buffered
	SYNCDELAY; EP8CFG = 0x00;  // Disable Endpoint 8
	
	// 0 INFM1 OEP1 AUTOOUT AUTOIN ZEROLENIN 0 WORDWIDE
	SYNCDELAY; EP6FIFOCFG = 0x0C;
	SYNCDELAY; EP6AUTOINLENH = 0x04;
	SYNCDELAY; EP6AUTOINLENL = 0x00;

	SYNCDELAY; EP8FIFOCFG = 0x00;
	
	//SYNCDELAY; REVCTL = 0x03; // REVCTL.0 and REVCTL.1 set to 1
	SYNCDELAY; REVCTL = 0x00; // REVCTL.0 and REVCTL.1 set to 1
	RESETFIFOS();
}

void TD_Poll(void)             // Called repeatedly while the device is idle
{
	// CDC Polling?
	if (!(EP1INCS & 0x02))      // check if EP1IN is available
 	{
		EP1INBUF[0] = 0x0A;       // if it is available, then fill the first 10 bytes of the buffer with 
		EP1INBUF[1] = 0x20;       // appropriate data. 
		EP1INBUF[2] = 0x00;
		EP1INBUF[3] = 0x00;
		EP1INBUF[4] = 0x00;
		EP1INBUF[5] = 0x00;
		EP1INBUF[6] = 0x00;
		EP1INBUF[7] = 0x02;
		EP1INBUF[8] = 0x00;
		EP1INBUF[9] = 0x00;
		EP1INBC = 10;            // manually commit once the buffer is filled
	}
}
