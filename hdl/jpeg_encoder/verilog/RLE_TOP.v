// File ../design/RLE_TOP_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name : RLE_TOP.vhd
//
// Project   : JPEG_ENC
//
// Module    : RLE_TOP
//
// Content   : Run Length Encoder top level
//
// Description : 
//
// Spec.     : 
//
// Author    : Michal Krepa
//
//-----------------------------------------------------------------------------
// History :
// 20090301: (MK): Initial Creation.
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

module RLE_TOP(
 input wire 	    CLK,
 input wire 	    RST,
 input wire 	    start_pb,
 output reg 	    ready_pb,
 input wire [2:0]   rss_cmp_idx,   // was rle_sm_settings.cmp_idx
	       
 input wire 	    huf_buf_sel,
 input wire 	    huf_rden,
 output wire [3:0]  huf_runlength,
 output wire [3:0]  huf_size,
 output wire [11:0] huf_amplitude,
 output wire 	    huf_dval,
 output wire 	    huf_fifo_empty,
	       
 output wire 	    qua_buf_sel,
 output wire [5:0]  qua_rd_addr,
 input wire [11:0]  qua_data,
 input wire 	    sof
);

    wire [19:0]     dbuf_data;
    wire [19:0]     dbuf_q;
    wire 	    dbuf_we;
    wire [3:0] 	    rle_runlength;
    wire [3:0] 	    rle_size;
    wire [11:0]     rle_amplitude;
    wire 	    rle_dovalid;
    wire [11:0]     rle_di;
    wire 	    rle_divalid;
    reg 	    qua_buf_sel_s;
    reg 	    huf_dval_p0;
    reg [5:0] 	    wr_cnt;  



    assign huf_runlength = dbuf_q[19:16];
    assign huf_size = dbuf_q[15:12];
    assign huf_amplitude = dbuf_q[11:0];
    assign qua_buf_sel = qua_buf_sel_s;
    
    //-----------------------------------------------------------------
    // RLE Core
    //-----------------------------------------------------------------
    rle
      #(.RAMADDR_W(6), .RAMDATA_W(12))
    U_rle
      (.rst             (RST           ),
       .clk             (CLK	       ),
       .di              (rle_di	       ),
       .start_pb        (start_pb      ),
       .sof             (sof           ),
       
       //--rle_sm_settings => rle_sm_settings,
       .rss_cmp_idx (rss_cmp_idx),
			 
       .runlength       (rle_runlength ), 
       .size            (rle_size      ),
       .amplitude       (rle_amplitude ),
       .dovalid         (rle_dovalid   ),
       .rd_addr         (qua_rd_addr   )
       );
    
  assign rle_di = qua_data;
    
    //-----------------------------------------------------------------
    // Double Fifo
    //-----------------------------------------------------------------
    RleDoubleFifo
      #()
    U_RleDoubleFifo
	(.CLK             (CLK            ),
	 .RST             (RST		  ),
	 //-- RLE			  
	 .data_in         (dbuf_data	  ),
	 .wren            (dbuf_we	  ),
	 //-- HUFFMAN			  
	 .buf_sel         (huf_buf_sel	  ),
	 .rd_req          (huf_rden	  ),
	 .fifo_empty      (huf_fifo_empty ),
	 .data_out        (dbuf_q         )
	 );

    
    assign dbuf_data = {rle_runlength,rle_size,rle_amplitude};
    assign dbuf_we = rle_dovalid;
    
    //-----------------------------------------------------------------
    // ready_pb
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    ready_pb <= 1'b 0;
	    wr_cnt <= {6{1'b0}};
	end 
	else begin
	    ready_pb <= 1'b0;
	    if(start_pb == 1'b1) begin
		wr_cnt <= {6{1'b0}};
	    end
	    
	    // detect EOB (0,0) - end of RLE block
	    if(rle_dovalid == 1'b1) begin
		// ZERO EXTENSION
		if(((rle_runlength)) == 15 && ((rle_size)) == 0) begin
		    wr_cnt <= wr_cnt + 16;
		end
		else begin
		    //wr_cnt <= wr_cnt + 1 + resize(unsigned(rle_runlength), wr_cnt'length);
		    wr_cnt <= wr_cnt + 1 + (((rle_runlength)));
		end
	  
		// EOB can only be on AC!
		if (dbuf_data == 0 && wr_cnt != 0) begin
		    ready_pb <= 1'b1;
		end
		else begin
		    if ((wr_cnt + rle_runlength) == 64-1) begin
			ready_pb <= 1'b1;
		    end
		end
	    end
	end
    end

    //-----------------------------------------------------------------
    // fdct_buf_sel
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    qua_buf_sel_s <= 1'b 0;
	end 
	else begin
	    if(start_pb == 1'b 1) begin
		qua_buf_sel_s <=  ~qua_buf_sel_s;
	    end
	end
    end

    //-----------------------------------------------------------------
    // output data valid
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    huf_dval_p0 <= 1'b0;
	    //huf_dval    <= '0';
	end 
	else begin
	    huf_dval_p0 <= huf_rden;
	    //huf_dval    <= huf_rden;
	end
    end

    assign huf_dval = huf_rden;

endmodule
