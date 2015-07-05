// File ../design/RleDoubleFifo_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  RleDoubleFifo.vhd
//
// Project   : JPEG_ENC
//
// Module    : RleDoubleFifo
//
// Content   : RleDoubleFifo
//
// Description : 
//
// Spec.     : 
//
// Author    : Michal Krepa
//
//-----------------------------------------------------------------------------
// History :
// 20090228: (MK): Initial Creation.
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

module RleDoubleFifo
(
 input wire 	    CLK,
 input wire 	    RST,
 input wire [19:0]  data_in,
 input wire 	    wren,
 input wire 	    buf_sel,
 input wire 	    rd_req,
 output wire 	    fifo_empty,
 output wire [19:0] data_out
);


   wire 	    fifo1_rd;
   reg 		    fifo1_wr;
   wire [19:0] 	    fifo1_q;
   wire 	    fifo1_full;
   wire 	    fifo1_empty;
   wire [6:0] 	    fifo1_count;
   wire 	    fifo2_rd;
   reg 		    fifo2_wr;
   wire [19:0] 	    fifo2_q;
   wire 	    fifo2_full;
   wire 	    fifo2_empty;
   wire [6:0] 	    fifo2_count;
   reg [19:0] 	    fifo_data_in;
      
   //-----------------------------------------------------------------
   // FIFO 1
   //-----------------------------------------------------------------
   FIFO 
     #(.DATA_WIDTH(20), .ADDR_WIDTH(6))
   U_FIFO_1
     (.rst(RST),
      .clk(CLK),
      .rinc(fifo1_rd),
      .winc(fifo1_wr),
      .datai(fifo_data_in),
      .datao(fifo1_q),
      .fullo(fifo1_full),
      .emptyo(fifo1_empty),
      .count(fifo1_count)
      );
       
  //-----------------------------------------------------------------
  // FIFO 2
  //-----------------------------------------------------------------
   FIFO 
     #(.DATA_WIDTH(20), .ADDR_WIDTH(6))
   U_FIFO_2
     (.rst(RST),
      .clk(CLK),
      .rinc(fifo2_rd),
      .winc(fifo2_wr),
      .datai(fifo_data_in),
      .datao(fifo2_q),
      .fullo(fifo2_full),
      .emptyo(fifo2_empty),
      .count(fifo2_count)
      );
   
   
    //-----------------------------------------------------------------
    // mux2
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    fifo1_wr <= 1'b0;
	    fifo2_wr <= 1'b0;
	    fifo_data_in <= {20{1'b0}};
	end 
	else begin
	    if(buf_sel == 1'b0) begin
		fifo1_wr <= wren;
	    end
	    else begin
		fifo2_wr <= wren;
	    end
	    fifo_data_in <= data_in;
	end
    end

    //-----------------------------------------------------------------
    // mux3
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    //data_out   <= (others => '0');
	    //fifo1_rd   <= '0';
	    //fifo2_rd   <= '0';
	    //fifo_empty <= '0';
	end 
	else begin
	    if(buf_sel == 1'b1) begin
		//data_out   <= fifo1_q;
		//fifo1_rd   <= rd_req;
		//fifo_empty <= fifo1_empty;
	    end
	    else begin
		//data_out   <= fifo2_q;
		//fifo2_rd   <= rd_req;
		//fifo_empty <= fifo2_empty;
	    end
	end
    end
    
    assign fifo1_rd   = buf_sel == 1'b1 ? rd_req      : 1'b0;
    assign fifo2_rd   = buf_sel == 1'b0 ? rd_req      : 1'b0;
    assign data_out   = buf_sel == 1'b1 ? fifo1_q     : fifo2_q;
    assign fifo_empty = buf_sel == 1'b1 ? fifo1_empty : fifo2_empty;
    
    
endmodule
