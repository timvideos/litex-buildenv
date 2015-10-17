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
#include "vendorCommands.h"
#include "prom.h"
#include "prog.h"
#include "defs.h"
#include "debug.h"

#include "cdc.h"
#include "uvc.h"

extern const uint8 dev_strings[];
void TD_Init(void);
void TD_Poll(void);
void livePatch(uint8 patchClass, uint8 newByte);

// General-purpose diagnostic code, for debugging. See CMD_GET_DIAG_CODE vendor command.
__xdata uint8 m_diagnosticCode = 0;

void fifoSetEnabled(uint8 mode) {
	// Ensure that CTL1 & CTL2 (fx2GotData_in & fx2GotRoom_in) default low (unasserted). This
	// prevents the FX2 from falsely informing the FPGA that it's ready to talk when fifo mode is
	// disabled.
	GPIFIDLECTL = 0x00;

	if ( mode == 0x01 ) {
		IFCONFIG = (bmIFCLKSRC | bm3048MHZ | bmIFCLKOE | bmFIFOS);
	} else {
		IFCONFIG = (bmIFCLKSRC | bm3048MHZ | bmIFCLKOE | bmPORTS);
	}
}

// Called once at startup
//
void mainInit(void) {

	__xdata uint8 thisByte = 0xFF;
	__xdata uint16 blockSize;

	

	// This is only necessary for cases where you want to load firmware into the RAM of an FX2 that
	// has already loaded firmware from an EEPROM. It should definitely be removed for firmwares
	// which are themselves to be loaded from EEPROM.
#ifndef EEPROM
	RENUMERATE_UNCOND();
#endif

// Needs to be matched to stuff in HDMI2USB/cypress/hdmi2usb.c TD_Init
// void TD_Init(void)             // Called once at startup

	
	// Clear wakeup (see AN15813: http://www.cypress.com/?docID=4633)
	WAKEUPCS = bmWU | bmDPEN | bmWUEN;
	WAKEUPCS = bmWU | bmDPEN | bmWUEN;

	// Disable alternate functions for PORTA 0,1,3 & 7.
	PORTACFG = 0x00;

	/*
	// Return FIFO settings back to default just in case previous firmware messed with them.
	SYNCDELAY; PINFLAGSAB = 0x00;
	SYNCDELAY; PINFLAGSCD = 0x00;
	SYNCDELAY; FIFOPINPOLAR = 0x00;

	// Global settings
	SYNCDELAY; REVCTL = (bmDYN_OUT | bmENH_PKT); // 0x03
	SYNCDELAY; CPUCS = bmCLKSPD1;  // 48MHz 0x10

	// Drive IFCLK at 48MHz, enable slave FIFOs
	//SYNCDELAY; IFCONFIG = (bmIFCLKSRC | bm3048MHZ | bmIFCLKOE | bmFIFOS);
	SYNCDELAY; IFCONFIG = (bmIFCLKSRC | bm3048MHZ | bmIFCLKOE | bmPORTS); // 0xe0

	// EP1OUT & EP1IN
	SYNCDELAY; EP1OUTCFG = (bmVALID | bmBULK); // 0xa0
	SYNCDELAY; EP1INCFG = (bmVALID | bmBULK); // 0xa0

	// EP2OUT & EP6IN are quad-buffered bulk endpoints
	SYNCDELAY; EP2CFG = (bmVALID | bmBULK); // 0xa0
	SYNCDELAY; EP4CFG = 0x00;
	SYNCDELAY; EP6CFG = (bmVALID | bmBULK | bmDIR); // 0xe0
	SYNCDELAY; EP8CFG = 0x00;

	// EP2OUT & EP6IN automatically commit packets
	SYNCDELAY; EP2FIFOCFG = bmAUTOOUT; // 0x10
	SYNCDELAY; EP4FIFOCFG = 0x00;
	SYNCDELAY; EP6FIFOCFG = bmAUTOIN; // 0x08
	SYNCDELAY; EP8FIFOCFG = 0x00;

	// Reset FIFOs for EP2OUT & EP6IN
	SYNCDELAY; FIFORESET = bmNAKALL; // 0x80
	SYNCDELAY; FIFORESET = 2;  // reset EP2OUT
	SYNCDELAY; FIFORESET = 6;  // reset EP6IN
	SYNCDELAY; FIFORESET = 0x00;

	// Arm EP1OUT
	EP1OUTBC = 0x00;

	// Arm the EP2OUT buffers. Done four times because it's quad-buffered
	SYNCDELAY; OUTPKTEND = bmSKIP | 2;  // EP2OUT 0x82
	SYNCDELAY; OUTPKTEND = bmSKIP | 2;
	SYNCDELAY; OUTPKTEND = bmSKIP | 2;
	SYNCDELAY; OUTPKTEND = bmSKIP | 2;


	// Auto-commit 512-byte packets from EP6IN (master may commit early by asserting PKTEND)
	SYNCDELAY; EP6AUTOINLENH = 0x02;
	SYNCDELAY; EP6AUTOINLENL = 0x00;
	
	// Turbo I2C
	I2CTL |= bm400KHZ;

	// Auto-pointers
	AUTOPTRSETUP = bmAPTREN | bmAPTR1INC | bmAPTR2INC; // 0x07

	// Port lines all inputs...
	IOA = 0xFF;
	OEA = 0x00;
	IOB = 0xFF;
	OEB = 0x00;
	IOC = 0xFF;
	OEC = 0x00;
	IOD = 0xFF;
	OED = 0x00;
	IOE = 0xFF;
	OEE = 0x00;

#ifdef EEPROM
	#ifdef BSP
		#include STR(boards/BSP.c)
	#endif
#endif
	*/
	I2CTL |= bm400KHZ;
	TD_Init();
	
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

/*
code from HDMI2USB/cypress/hdmi2usb.c

void TD_Poll(void)             // Called repeatedly while the device is idle
{

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
*/
	TD_Poll();
	// If there is a shift operation pending, execute it now.
	//progShiftExecute();
}

#define FIFO_MODE 0x0000

#define updatePort(port) \
	if ( CONCAT(OE, port) | bitMask ) { \
		CONCAT(OE, port) = drive ? (CONCAT(OE, port) | bitMask) : (CONCAT(OE, port) & ~bitMask); \
		CONCAT(IO, port) = high  ? (CONCAT(IO, port) | bitMask) : (CONCAT(IO, port) & ~bitMask); \
	} else { \
		CONCAT(IO, port) = high  ? (CONCAT(IO, port) | bitMask) : (CONCAT(IO, port) & ~bitMask); \
		CONCAT(OE, port) = drive ? (CONCAT(OE, port) | bitMask) : (CONCAT(OE, port) & ~bitMask); \
	} \
	tempByte = (CONCAT(IO, port) & bitMask) ? 0x01 : 0x00

uint8 portAccess(uint8 portNumber, uint8 bitMask, uint8 drive, uint8 high) {
	uint8 tempByte = 0x00;
	#ifdef DEBUG
		usartSendByteHex(portNumber);
		usartSendByte(':');
		usartSendByteHex(bitMask);
		usartSendByte(':');
		usartSendByteHex(drive);
		usartSendByte(':');
		usartSendByteHex(high);
		usartSendByte('\r');
	#endif
	switch ( portNumber ) {
	case 0:
		updatePort(A);
		break;
	case 1:
		updatePort(B);
		break;
	case 2:
		updatePort(C);
		break;
	case 3:
		updatePort(D);
		break;
	case 4:
		updatePort(E);
		break;
	}
	return tempByte;
}

// Called when a vendor command is received
//
uint8 handleVendorCommand(uint8 cmd) {
	if (handleUVCCommand(cmd))
            return true;
	if (handleCDCCommand(cmd))
            return true;

/*
	switch(cmd) {
	// Set various mode bits, or fetch status information
	//
	case CMD_MODE_STATUS:
		if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			const __xdata uint16 param = SETUP_VALUE();
			const __xdata uint8 value = SETUPDAT[4];
			if ( param == FIFO_MODE ) {
				// Enable or disable FIFO mode
				fifoSetEnabled(value);
			} else {
				return false;
			}
		} else {
			// Get STATUS: return the diagnostic byte
			while ( EP0CS & bmEPBUSY );
			EP0BUF[0] = 'N';                     // Magic bytes (my cat's name)
			EP0BUF[1] = 'E';
			EP0BUF[2] = 'M';
			EP0BUF[3] = 'I';
			EP0BUF[4] = m_diagnosticCode;        // Last operation diagnostic code
			EP0BUF[5] = (IOA & bmBIT2) ? 0 : 1;  // Flags
			EP0BUF[6] = 0x11;                    // NeroProg endpoints
			EP0BUF[7] = 0x26;                    // CommFPGA endpoints
			EP0BUF[8] = 0xFF;                    // Firmware ID MSB
			EP0BUF[9] = 0xFF;                    // Firmware ID LSB
			EP0BUF[10] = (uint8)(DATE>>24);      // Version MSB
			EP0BUF[11] = (uint8)(DATE>>16);      // Version
			EP0BUF[12] = (uint8)(DATE>>8);       // Version
			EP0BUF[13] = (uint8)DATE;            // Version LSB
			EP0BUF[14] = 0x00;                   // Reserved
			EP0BUF[15] = 0x00;                   // Reserved
			
			// Return status packet to host
			EP0BCH = 0;
			SYNCDELAY;
			EP0BCL = 16;
		}
		return true;

	// Clock data into and out of the JTAG chain. Reads from EP2OUT and writes to EP4IN.
	//
	case CMD_PROG_CLOCK_DATA:
		if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			EP0BCL = 0x00;                                     // Allow host transfer in
			while ( EP0CS & bmEPBUSY );                        // Wait for data
			progShiftBegin(*((uint32 *)EP0BUF), (ProgOp)SETUPDAT[4], SETUPDAT[2]);  // Init numBits & flagByte
			return true;
			// Now that numBits & flagByte are set, this operation will continue in mainLoop()...
		}
		break;
		
	// Clock an (up to) 32-bit pattern LSB-first into TMS to change JTAG TAP states
	//
	case CMD_JTAG_CLOCK_FSM:
		if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			EP0BCL = 0x00;                                   // Allow host transfer in
			while ( EP0CS & bmEPBUSY );                      // Wait for data
			progClockFSM(*((uint32 *)EP0BUF), SETUPDAT[2]);  // Bit pattern, transitionCount
			return true;
		}
		break;
		
	// Execute a number of JTAG clocks.
	//
	case CMD_JTAG_CLOCK:
		if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			progClocks(*((uint32 *)(SETUPDAT+2)));
			return true;
		}
		break;

	// Set various mode bits, or fetch status information
	//
	case CMD_PORT_BIT_IO:
		if ( SETUP_TYPE == (REQDIR_DEVICETOHOST | REQTYPE_VENDOR) ) {
			const __xdata uint8 portNumber = SETUPDAT[2];
			const __xdata uint8 bitNumber = SETUPDAT[3];
			const __xdata uint8 drive = SETUPDAT[4];
			const __xdata uint8 high = SETUPDAT[5];
			if ( portNumber > 4 || bitNumber > 7 ) {
				return false;  // illegal port or bit
			}

			// Get the state of the port lines:
			while ( EP0CS & bmEPBUSY );
			EP0BUF[0] = portAccess(portNumber, (1<<bitNumber), drive, high);
			EP0BCH = 0;
			SYNCDELAY;
			EP0BCL = 1;
			return true;
		}
		break;

	case CMD_PORT_MAP:
		if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			__xdata uint8 patchClass = SETUPDAT[4];
			const __xdata uint8 patchPort = SETUPDAT[5];
			if ( patchClass == 0x00 ) {
				// Patch class zero is just an anchor for the less flexible Harvard architecture
				// micros like the AVR; since the FX2LP has a Von Neumann architecture it can
				// efficiently self-modify its code, so the port mapping can be done individually,
				// so there's no need for an anchor to group mapping operations together.
				return true;
			}
			patchClass--;
			if ( patchClass < 4 ) {
				const __xdata uint8 patchBit = SETUPDAT[2];
				livePatch(patchClass, 0x80 + (patchPort << 4) + patchBit);
			} else {
				livePatch(
					patchClass, 
					0x80 + (patchPort << 4)
				);
			}
			return true;
		}
		break;

	// Command to talk to the EEPROM
	//
	case CMD_READ_WRITE_EEPROM:
		if ( SETUP_TYPE == (REQDIR_DEVICETOHOST | REQTYPE_VENDOR) ) {
			// It's an IN operation - read from prom and send to host
			__xdata uint16 address = SETUP_VALUE();
			__xdata uint16 length = SETUP_LENGTH();
			__xdata uint16 chunkSize;
			__xdata uint8 i;
			while ( length ) {
				while ( EP0CS & bmEPBUSY );
				chunkSize = length < EP0BUF_SIZE ? length : EP0BUF_SIZE;
				for ( i = 0; i < chunkSize; i++ ) {
					EP0BUF[i] = 0x23;
				}
				promRead(SETUPDAT[4], address, chunkSize, EP0BUF);
				EP0BCH = 0;
				SYNCDELAY;
				EP0BCL = chunkSize;
				address += chunkSize;
				length -= chunkSize;
			}
		} else if ( SETUP_TYPE == (REQDIR_HOSTTODEVICE | REQTYPE_VENDOR) ) {
			// It's an OUT operation - read from host and send to prom
			__xdata uint16 address = SETUP_VALUE();
			__xdata uint16 length = SETUP_LENGTH();
			__xdata uint16 chunkSize;
			while ( length ) {
				EP0BCL = 0x00; // allow pc transfer in
				while ( EP0CS & bmEPBUSY ); // wait for data
				chunkSize = EP0BCL;
				promWrite(SETUPDAT[4], address, chunkSize, EP0BUF);
				address += chunkSize;
				length -= chunkSize;
			}
		}
		return true;
	}
*/

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
     
    SYNCDELAY; IFCONFIG = 0xE3; // Internal Clock, 48MHz, IFCLK output enable to pin, Normal Polarity, Synchronous FIFO, Nothing to do with GSTATE, Set interface mode to Slave FIFO.
    
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
    
    // Used by the CDC serial port (EP2 == TX, EP4 == RX)
	SYNCDELAY; EP2CFG = 0xA2;  // Activate, OUT Direction, BULK Type, 512  bytes Size, Double buffered
	SYNCDELAY; EP4CFG = 0xE2;  // Activate, IN  Direction, BULK Type, 512  bytes Size, Double buffered
    // Used by the video data
	SYNCDELAY; EP6CFG = 0xDA;  // Activate, IN  Direction, ISO  Type, 1024 bytes Size, Double buffered
	SYNCDELAY; EP8CFG = 0x00;  // Disable Endpoint 8
	
	// 0 INFM1 OEP1 AUTOOUT AUTOIN ZEROLENIN 0 WORDWIDE
	SYNCDELAY; EP2FIFOCFG = 0x10;  // Auto
	SYNCDELAY; EP4FIFOCFG = 0x0C;
	SYNCDELAY; EP6FIFOCFG = 0x0C;
	SYNCDELAY; EP8FIFOCFG = 0x00;
	
	SYNCDELAY; EP4AUTOINLENH = 0x02;
	SYNCDELAY; EP4AUTOINLENL = 0x00;
	SYNCDELAY; EP6AUTOINLENH = 0x04;
	SYNCDELAY; EP6AUTOINLENL = 0x00;
	
	SYNCDELAY; REVCTL = 0x03; // REVCTL.0 and REVCTL.1 set to 1
	SYNCDELAY; FIFORESET = 0x80; // Reset the FIFO
	SYNCDELAY; FIFORESET = 0x82;
	SYNCDELAY; FIFORESET = 0x84;
	SYNCDELAY; FIFORESET = 0x86;
	SYNCDELAY; FIFORESET = 0x00;


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
