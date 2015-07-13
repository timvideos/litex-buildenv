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
#include <delay.h>
#include "prog.h"
#include "defs.h"
#include "../../vendorCommands.h"
#include "debug.h"

////////////////////////////////////////////////////////////////////////////////////////////////////
// NeroProg Stuff
////////////////////////////////////////////////////////////////////////////////////////////////////

static __xdata uint32 m_numBits = 0UL;
static __xdata ProgOp m_progOp = PROG_NOP;
static __xdata uint8 m_flagByte = 0x00;

// THIS MUST BE THE FIRST FUNCTION IN THE FILE!
//
// Transition the JTAG state machine to another state: clock "transitionCount" bits from
// "bitPattern" into TMS, LSB-first.
//
void progClockFSM(uint32 bitPattern, uint8 transitionCount) {
	while ( transitionCount-- ) {
		TCK = 0;
		TMS = bitPattern & 1;
		bitPattern >>= 1;
		TCK = 1;
	}
	TCK = 0;
}

// JTAG-clock the supplied byte into TDI, LSB first.
//
// Lifted from:
//   http://ixo-jtag.svn.sourceforge.net/viewvc/ixo-jtag/usb_jtag/trunk/device/c51/hw_nexys.c
//
static void shiftOut(uint8 c) {
	/* Shift out byte c:
	 *
	 * 8x {
	 *   Output least significant bit on TDI
	 *   Raise TCK
	 *   Shift c right
	 *   Lower TCK
	 * }
	 */
	
	(void)c; /* argument passed in DPL */
	
	__asm
		mov  A,DPL
		;; Bit0
		rrc  A
		mov  _TDI,C
		setb _TCK
		;; Bit1
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit2
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit3
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit4
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit5
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit6
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		;; Bit7
		rrc  A
		clr  _TCK
		mov  _TDI,C
		setb _TCK
		nop
		clr  _TCK
	__endasm;
}

// JTAG-clock all 512 bytes from the EP2OUT FIFO buffer
//
static void blockShiftBits(uint8 count) {
	__asm
		mov    _AUTOPTRH1, #_EP1OUTBUF >> 8
		mov    _AUTOPTRL1, #_EP1OUTBUF
		mov    r0, dpl
	bsoLoop:
		clr    _TCK
		mov    a, _AUTODAT1
		rrc    a
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		rrc    a
		clr    _TCK
		mov    _TDI, c
		setb   _TCK
		djnz   r0, bsoLoop
		clr    _TCK
	__endasm;
}
// Clock the specified number of bytes from EP1IN into port A.
//
static void blockShiftBytes(uint8 count) {
	__asm
		mov    _AUTOPTRH1, #_EP1OUTBUF >> 8
		mov    _AUTOPTRL1, #_EP1OUTBUF
		mov    r0, dpl
	byteLoop:
		clr    _TCK
		mov    _IOA, _AUTODAT1
		setb   _TCK
		djnz   r0, byteLoop
		clr    _TCK
	__endasm;
}

// JTAG-clock the supplied byte into TDI, MSB first. Return the byte clocked out of TDO.
//
// Lifted from:
//   http://ixo-jtag.svn.sourceforge.net/viewvc/ixo-jtag/usb_jtag/trunk/device/c51/hw_nexys.c
//
static uint8 shiftInOut(uint8 c) {
	/* Shift out byte c, shift in from TDO:
	 *
	 * 8x {
	 *   Read carry from TDO
	 *   Output least significant bit on TDI
	 *   Raise TCK
	 *   Shift c right, append carry (TDO) at left
	 *   Lower TCK
	 * }
	 * Return c.
	 */
	
	(void)c; /* argument passed in DPL */
	
	__asm
		mov  A, DPL

		;; Bit0
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit1
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit2
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit3
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit4
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit5
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit6
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		clr  _TCK
		;; Bit7
		mov  C, _TDO
		rrc  A
		mov  _TDI, C
		setb _TCK
		nop
		clr  _TCK
		
		mov  DPL, A
		ret
	__endasm;

	/* return value in DPL */

	return c;
}

// Kick off a shift operation. Next time progExecuteShift() runs, it will execute the shift.
//
void progShiftBegin(uint32 numBits, ProgOp progOp, uint8 flagByte) {
	m_numBits = numBits;
	m_progOp = progOp;
	m_flagByte = flagByte;
}

// The minimum number of bytes necessary to store x bits
//
#define bitsToBytes(x) ((x>>3) + (x&7 ? 1 : 0))

static const __xdata uint8 *m_inPtr;
static __xdata uint8 *m_outPtr;

static void jtagIsSendingIsReceiving(void) {
	__xdata uint16 bitsRead, bitsRemaining;
	__xdata uint8 bytesRead, bytesRemaining;
	while ( m_numBits ) {
		while ( EP01STAT & bmEP1OUTBSY );  // Wait for some EP1OUT data
		while ( EP01STAT & bmEP1INBSY );   // Wait for space for EP1IN data
		bitsRead = (m_numBits >= (ENDPOINT_SIZE<<3)) ? ENDPOINT_SIZE<<3 : m_numBits;
		bytesRead = EP1OUTBC;
		
		m_inPtr = EP1OUTBUF;
		m_outPtr = EP1INBUF;
		if ( bitsRead == m_numBits ) {
			// This is the last chunk
			__xdata uint8 tdoByte, tdiByte, leftOver, i;
			bitsRemaining = (bitsRead-1) & 0xFFF8;        // Now an integer number of bytes
			leftOver = (uint8)(bitsRead - bitsRemaining); // How many bits in last byte (1-8)
			bytesRemaining = (bitsRemaining>>3);
			while ( bytesRemaining-- ) {
				*m_outPtr++ = shiftInOut(*m_inPtr++);
			}
			tdiByte = *m_inPtr++;  // Now do the bits in the final byte
			tdoByte = 0x00;
			i = 1;
			while ( i && leftOver ) {
				leftOver--;
				if ( (m_flagByte & bmISLAST) && !leftOver ) {
					TMS = 1; // Exit Shift-DR state on next clock
				}
				TDI = tdiByte & 1;
				tdiByte >>= 1;
				if ( TDO ) {
					tdoByte |= i;
				}
				TCK = 1;
				TCK = 0;
				i <<= 1;
			}
			*m_outPtr = tdoByte;
		} else {
			// This is not the last chunk
			bytesRemaining = (bitsRead>>3);
			while ( bytesRemaining-- ) {
				*m_outPtr++ = shiftInOut(*m_inPtr++);
			}
		}
		EP1OUTBC = 0x00;  // ready to accept more data from host
		EP1INBC = bytesRead;  // send response back to host
		m_numBits -= bitsRead;
	}
	m_progOp = PROG_NOP;
}

static void jtagIsSendingNotReceiving(void) {
	__xdata uint16 bitsRead, bitsRemaining;
	__xdata uint8 bytesRead, bytesRemaining;
	while ( m_numBits ) {
		while ( EP01STAT & bmEP1OUTBSY );  // Wait for some EP2OUT data
		bitsRead = (m_numBits >= (ENDPOINT_SIZE<<3)) ? ENDPOINT_SIZE<<3 : m_numBits;
		bytesRead = EP1OUTBC;
		
		if ( bitsRead == m_numBits ) {
			// This is the last chunk
			__xdata uint8 tdiByte, leftOver, i;
			m_inPtr = EP1OUTBUF;
			bitsRemaining = (bitsRead-1) & 0xFFF8;        // Now an integer number of bytes
			leftOver = (uint8)(bitsRead - bitsRemaining); // How many bits in last byte (1-8)
			bytesRemaining = (bitsRemaining>>3);
			while ( bytesRemaining-- ) {
				shiftOut(*m_inPtr++);
			}
			tdiByte = *m_inPtr;  // Now do the bits in the final byte
			i = 1;
			while ( i && leftOver ) {
				leftOver--;
				if ( (m_flagByte & bmISLAST) && !leftOver ) {
					TMS = 1; // Exit Shift-DR state on next clock
				}
				TDI = tdiByte & 1;
				tdiByte >>= 1;
				TCK = 1;
				TCK = 0;
				i <<= 1;
			}
		} else {
			// This is not the last chunk, so we've to 512 bytes to shift
			blockShiftBits(64);
		}
		EP1OUTBC = 0x00;  // ready to accept more data from host
		m_numBits -= bitsRead;
	}
	m_progOp = PROG_NOP;
}

static void jtagNotSendingIsReceiving(void) {
	// The host is not giving us data, but is expecting a response (x0r)
	__xdata uint16 bitsRead, bitsRemaining;
	__xdata uint8 bytesRead, bytesRemaining;
	const __xdata uint8 tdiByte = (m_flagByte & bmSENDONES) ? 0xFF : 0x00;
	while ( m_numBits ) {
		while ( EP01STAT & bmEP1INBSY );   // Wait for space for EP1IN data
		bitsRead = (m_numBits >= (ENDPOINT_SIZE<<3)) ? ENDPOINT_SIZE<<3 : m_numBits;
		bytesRead = bitsToBytes(bitsRead);
		
		m_outPtr = EP1INBUF;
		if ( bitsRead == m_numBits ) {
			// This is the last chunk
			__xdata uint8 tdoByte, leftOver, i;
			bitsRemaining = (bitsRead-1) & 0xFFF8;        // Now an integer number of bytes
			leftOver = (uint8)(bitsRead - bitsRemaining); // How many bits in last byte (1-8)
			bytesRemaining = (bitsRemaining>>3);
			while ( bytesRemaining-- ) {
				*m_outPtr++ = shiftInOut(tdiByte);
			}
			tdoByte = 0x00;
			i = 1;
			TDI = tdiByte & 1;
			while ( i && leftOver ) {
				leftOver--;
				if ( (m_flagByte & bmISLAST) && !leftOver ) {
					TMS = 1; // Exit Shift-DR state on next clock
				}
				if ( TDO ) {
					tdoByte |= i;
				}
				TCK = 1;
				TCK = 0;
				i <<= 1;
			}
			*m_outPtr = tdoByte;
		} else {
			// This is not the last chunk
			bytesRemaining = (bitsRead>>3);
			while ( bytesRemaining-- ) {
				*m_outPtr++ = shiftInOut(tdiByte);
			}
		}
		EP1INBC = bytesRead;  // send response back to host
		m_numBits -= bitsRead;
	}
	m_progOp = PROG_NOP;
}

static void jtagNotSendingNotReceiving(void) {
	// The host is not giving us data, and does not need a response (x0n)
	__xdata uint32 bitsRemaining, bytesRemaining;
	const __xdata uint8 tdiByte = (m_flagByte & bmSENDONES) ? 0xFF : 0x00;
	__xdata uint8 leftOver;
	bitsRemaining = (m_numBits-1) & 0xFFFFFFF8;    // Now an integer number of bytes
	leftOver = (uint8)(m_numBits - bitsRemaining); // How many bits in last byte (1-8)
	bytesRemaining = (bitsRemaining>>3);
	while ( bytesRemaining-- ) {
		shiftOut(tdiByte);
	}
	TDI = tdiByte & 1;
	while ( leftOver ) {
		leftOver--;
		if ( (m_flagByte & bmISLAST) && !leftOver ) {
			TMS = 1; // Exit Shift-DR state on next clock
		}
		TCK = 1;
		TCK = 0;
	}
	m_progOp = PROG_NOP;
}

static void doProgram(bool isParallel) {
	__xdata uint8 bytesRead;
	while ( m_numBits ) {
		while ( EP01STAT & bmEP1OUTBSY );  // Wait for some EP1OUT data
		bytesRead = EP1OUTBC;
		if ( isParallel ) {
			blockShiftBytes(bytesRead);
		} else {
			blockShiftBits(bytesRead);
		}
		EP1OUTBC = 0x00;  // ready to accept more data from host
		m_numBits -= bytesRead;
	}
	m_progOp = PROG_NOP;
}

static void progSerRecv(void) {
	// Read bytes from SPI
	__xdata uint8 chunkSize, i;
	while ( m_numBits ) {
		while ( EP01STAT & bmEP1INBSY );   // Wait for space for EP1IN data
		chunkSize = (m_numBits >= ENDPOINT_SIZE) ? ENDPOINT_SIZE : m_numBits;
		m_outPtr = EP1INBUF;
		i = chunkSize;
		while ( i ) {
			*m_outPtr++ = shiftInOut(0x00);
			i--;
		}
		EP1INBC = chunkSize;  // send response back to host
		m_numBits -= chunkSize;
	}
	m_progOp = PROG_NOP;
}

// Actually execute the shift operation initiated by progBeginShift(). This is done in a
// separate method because vendor commands cannot read & write to bulk endpoints.
//
void progShiftExecute(void) {
	switch ( m_progOp ) {
	case PROG_JTAG_ISSENDING_ISRECEIVING:
		// The host is giving us data, and is expecting a response (xdr)
		jtagIsSendingIsReceiving();
		break;
	case PROG_JTAG_ISSENDING_NOTRECEIVING:
		// The host is giving us data, but does not need a response (xdn)
		jtagIsSendingNotReceiving();
		break;
	case PROG_JTAG_NOTSENDING_ISRECEIVING:
		// The host is not giving us data, but is expecting a response (x0r)
		jtagNotSendingIsReceiving();
		break;
	case PROG_JTAG_NOTSENDING_NOTRECEIVING:
		jtagNotSendingNotReceiving();
		break;
	case PROG_PARALLEL:
		doProgram(true);
		break;
	case PROG_SPI_SEND:
		doProgram(false);
		break;
	case PROG_SPI_RECV:
		progSerRecv();
		break;
	case PROG_NOP:
	default:
		break;
	}
}

// Keep TMS and TDI as they are, and clock the JTAG state machine "numClocks" times.
// This is tuned to be as close to 2us per clock as possible (500kHz).
//
void progClocks(uint32 numClocks) {
	__asm
		mov r2, dpl
		mov r3, dph
		mov r4, b
		mov r5, a
	jcLoop:
		; TCK is high for 12 cycles (1us):
		setb _TCK              ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle

		; TCK is low for 12 cycles (1us):
		clr _TCK               ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		nop                    ; 1 cycle
		dec r2                 ; 1 cycle
		cjne r2, #255, jcLoop  ; 4 cycles

		; The high-order bytes introduce some jitter:
		dec r3
		cjne r3, #255, jcLoop
		dec r4
		cjne r4, #255, jcLoop
		dec r5
		cjne r5, #255, jcLoop
	__endasm;
}
