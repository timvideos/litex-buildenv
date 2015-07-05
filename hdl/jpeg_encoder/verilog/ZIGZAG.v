// File ../design/ZIGZAG_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
// vhd2vl settings:
//  * Verilog Module Declaration Style: 1995

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

//------------------------------------------------------------------------------
//                                                                            --
//                          V H D L    F I L E                                --
//                          COPYRIGHT (C) 2006                                --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// Title       : ZIGZAG                                                       --
// Design      : MDCT CORE                                                    --
// Author      : Michal Krepa                                                 --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// File        : ZIGZAG.VHD                                                   --
// Created     : Sun Sep 3 2006                                               --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
//  Description : Zig-Zag scan                                                --
//                                                                            --
//------------------------------------------------------------------------------
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
//------------------------------------------------------------------------------
// no timescale needed

module ZIGZAG
#(
  parameter RAMADDR_W=6,
  parameter RAMDATA_W=12
)
(
 input wire 		       rst,
 input wire 		       clk,
 input wire [RAMDATA_W - 1:0]  di,
 input wire 		       divalid,
 input wire [5:0] 	       rd_addr,
 input wire 		       fifo_rden,
 output wire 		       fifo_empty,
 output wire [RAMDATA_W - 1:0] dout,
 output reg 		       dovalid,
 output reg [5:0] 	       zz_rd_addr
);
       
   wire 		    fifo_wr;
   wire [11:0] 		    fifo_q;
   wire 		    fifo_full;
   wire [6:0] 		    fifo_count;
   wire [11:0] 		    fifo_data_in;
   wire 		    fifo_empty_s;
   
   assign dout = fifo_q;
   assign fifo_empty = fifo_empty_s;
    
   //-----------------------------------------------------------------
   // FIFO (show ahead)
   //-----------------------------------------------------------------
    FIFO
      #(.DATA_WIDTH(12),
	.ADDR_WIDTH(6)
	)
    U_FIFO
      (.rst     (rst),
       .clk     (clk),
       .rinc    (fifo_rden),
       .winc    (fifo_wr),
       .datai   (fifo_data_in),
       .datao   (fifo_q),
       .fullo   (fifo_full),
       .emptyo  (fifo_empty_s),
       .count   (fifo_count)
       );   
    
    assign fifo_wr = divalid;
    assign fifo_data_in = di;

    wire [5:0] 	_zz_rd_addr;
    m_zz_rom U_ZZ_ROM
      (.rd_addr(rd_addr), .zz_rd_addr(_zz_rd_addr));
    
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    zz_rd_addr <= {6{1'b0}};
            dovalid <= 1'b0;
        end
	else begin
	    zz_rd_addr <= _zz_rd_addr; 
	    dovalid <= fifo_rden &  ~fifo_empty_s;
	end
    end   
   
endmodule
