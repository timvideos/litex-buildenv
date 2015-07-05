// File ../design/SingleSM.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
// vhd2vl settings:
//  * Verilog Module Declaration Style: 2001

// vhd2vl is Free (libre) Software:
//   Copyright (C) 2001 Vincenzo Liguori - Ocean Logic Pty Ltd
//     http://www.ocean-logic.com
//   Modifications Copyright (C) 2006 Mark Gonzales - PMC Sierra Inc
//   Modifications (C) 2010 Shankar Giri
//   Modifications Copyright (C) 2002, 2005, 2008-2010 Larry Doolittle - LBNL
//     http://doolittle.icarus.com/~larry/vhd2vl/
//
//   vhd2vl comes with ABSOLUTELY NO WARRANTY.  Always check the resulting
//   Verilog for correctness, ideally with a formal verification tool.
//
//   You are welcome to redistribute vhd2vl under certain conditions.
//   See the license (GPLv2) file included with the source for details.

// The result of translation follows.  Its copyright status should be
// considered unchanged from the original VHDL.

//-----------------------------------------------------------------------------
// File Name :  SingleSM.vhd
//
// Project   : 
//
// Module    :
//
// Content   : 
//
// Description : 
//
// Spec.     : 
//
// Author    : Michal Krepa
//-----------------------------------------------------------------------------
// History :
// 20080301: (MK): Initial Creation.
//-----------------------------------------------------------------------------
// //////////////////////////////////////////////////////////////////////////////
// /// Copyright (c) 2013, Jahanzeb Ahmad
// /// All rights reserved.
// ///
// /// Redistribution and use in source and binary forms, with or without modification, 
// /// are permitted provided that the following conditions are met:
// ///
// ///  * Redistributions of source code must retain the above copyright notice, 
// ///    this list of conditions and the following disclaimer.
// ///  * Redistributions in binary form must reproduce the above copyright notice, 
// ///    this list of conditions and the following disclaimer in the documentation and/or 
// ///    other materials provided with the distribution.
// ///
// ///    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
// ///    EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
// ///    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
// ///    SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
// ///    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
// ///    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
// ///    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
// ///    WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
// ///    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
// ///   POSSIBILITY OF SUCH DAMAGE.
// ///
// ///
// ///  * http://opensource.org/licenses/MIT
// ///  * http://copyfree.org/licenses/mit/license.txt
// ///
// //////////////////////////////////////////////////////////////////////////////
// no timescale needed

module SingleSM
(
 input  wire 	   CLK,
 input  wire 	   RST,
 input  wire 	   start_i,
 output reg 	   idle_o,
 input  wire 	   idle_i,
 output reg 	   start_o,
 input  wire 	   pb_rdy_i,
 output reg 	   pb_start_o,
 output wire [1:0] fsm_o
);

    // from/to SM(m)
    // from/to SM(m+1)
    // from/to processing block
    // state debug

    parameter [1:0]
      IDLE = 0,
      WAIT_FOR_BLK_RDY = 1,
      WAIT_FOR_BLK_IDLE = 2;
    
    reg [1:0] 	   state;  
    
    assign fsm_o = state == IDLE ? 2'b00 : 
		   state == WAIT_FOR_BLK_RDY ? 2'b01 : 
		   state == WAIT_FOR_BLK_IDLE ? 2'b10 : 
		   2'b11;
    
    //----------------------------------------------------------------------------
    // FSM
    //----------------------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    idle_o <= 1'b0;
	    start_o <= 1'b0;
	    pb_start_o <= 1'b0;
	    state <= IDLE;
	end 
	else begin
	    idle_o <= 1'b0;
	    start_o <= 1'b0;
	    pb_start_o <= 1'b0;
	    
	    case(state)
	      IDLE : begin
		  idle_o <= 1'b1;
		  // this fsm is started
		  if(start_i == 1'b1) begin
		      state <= WAIT_FOR_BLK_RDY;
		      // start processing block associated with this FSM
		      pb_start_o <= 1'b1;
		      idle_o <= 1'b0;
		  end
	      end
	      
	      WAIT_FOR_BLK_RDY : begin
		  // wait until processing block completes
		  if(pb_rdy_i == 1'b1) begin
		      // wait until next FSM is idle before starting it
		      if(idle_i == 1'b1) begin
			  state <= IDLE;
			  start_o <= 1'b1;
		      end
		      else begin
			  state <= WAIT_FOR_BLK_IDLE;
		      end
		  end
	      end
	      
	      WAIT_FOR_BLK_IDLE : begin
		  if(idle_i == 1'b1) begin
		      state <= IDLE;
		      start_o <= 1'b1;
		  end
	      end
	      
	      default : begin
		  idle_o <= 1'b0;
		  start_o <= 1'b0;
		  pb_start_o <= 1'b0;
		  state <= IDLE;
	      end
	    endcase
	end
    end
    
endmodule
