// File ../design/ByteStuffer_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  ByteStuffer.vhd
//
// Project   : JPEG_ENC
//
// Module    : ByteStuffer
//
// Content   : ByteStuffer
//
// Description : ByteStuffer core
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

module ByteStuffer
#(
  /// @todo: these were constants from JPEG_PKG, not sure if
  ///    this should be repeated in each module or in a header
  ///    (ugh preprocessor) not sure if iverilog supports SV pkg.
  parameter C_HDR_SIZE = 623
)  
(
 input wire 	   CLK,
 input wire 	   RST,
 input wire 	   start_pb,
 output reg 	   ready_pb,
 
 input wire 	   sof,
 output reg [23:0] num_enc_bytes,
 input wire [9:0]  outram_base_addr,
 
 output wire 	   huf_buf_sel,
 input wire 	   huf_fifo_empty,
 output wire 	   huf_rd_req,
 input wire [7:0]  huf_packed_byte,
 
 output reg [7:0]  ram_byte,
 output reg 	   ram_wren,
 output reg [23:0] ram_wraddr
);

   
   reg [3:0] 	   huf_data_val;
   reg [15:0] 	   wdata_reg;
   reg [23:0] 	   wraddr = 0;
   reg [1:0] 	   wr_n_cnt = 0;
   reg 		   huf_buf_sel_s = 1'b0;
   reg 		   rd_en = 1'b0;
   reg 		   rd_en_d1 = 1'b0;
   reg 		   huf_rd_req_s = 1'b0;
   reg [7:0] 	   latch_byte = 0;
   reg 		   data_valid = 1'b0;
   reg 		   wait_for_ndata = 1'b0;  

   
   assign huf_buf_sel = huf_buf_sel_s;
   assign huf_rd_req = huf_rd_req_s;
   
    //-----------------------------------------------------------------
    // CTRL_SM
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    wr_n_cnt <= {2{1'b0}};
	    ready_pb <= 1'b0;
	    huf_rd_req_s <= 1'b0;
	    huf_data_val <= {4{1'b0}};
	    rd_en <= 1'b0;
	    rd_en_d1 <= 1'b0;
	    wdata_reg <= {16{1'b0}};
	    ram_wren <= 1'b0;
	    wraddr <= {24{1'b0}};
	    ram_wraddr <= {24{1'b0}};
	    ram_byte <= {8{1'b0}};
	    latch_byte <= {8{1'b0}};
	    wait_for_ndata <= 1'b0;
	    data_valid <= 1'b0;
        end 
	else begin
	    huf_rd_req_s <= 1'b0;
	    ready_pb <= 1'b0;
	    
	    //huf_data_val <= huf_data_val(huf_data_val'length-2 downto 0) & huf_rd_req_s;
	    huf_data_val <= {huf_data_val[2:0],huf_rd_req_s};
	    
	    rd_en_d1 <= rd_en;
	    ram_wren <= 1'b0;
	    data_valid <= 1'b0;
	    if(start_pb == 1'b1) begin
		rd_en <= 1'b1;
	    end
	    
	    // read FIFO until it becomes empty. wait until last byte read is
	    // serviced
	    if(rd_en_d1 == 1'b1 && wait_for_ndata == 1'b0) begin
		// FIFO empty
		if(huf_fifo_empty == 1'b1) begin
		    rd_en <= 1'b0;
		    rd_en_d1 <= 1'b0;
		    ready_pb <= 1'b1;
		end
		else begin
		    huf_rd_req_s <= 1'b1;
		    wait_for_ndata <= 1'b1;
		end
	    end
	    
	    // show ahead FIFO, capture data early
	    if(huf_rd_req_s == 1'b1) begin
		latch_byte <= huf_packed_byte;
		data_valid <= 1'b1;
	    end
	    if(huf_data_val[1] == 1'b1) begin
		wait_for_ndata <= 1'b0;
	    end
	    
	    // data from FIFO is valid
	    if(data_valid == 1'b1) begin
		// stuffing necessary
		if(latch_byte == 8'hFF) begin
		    // two writes are necessary for byte stuffing
		    wr_n_cnt <= 2'b10;
		    wdata_reg <= 16'hFF00;
		    // no stuffing
		end
		else begin
		    wr_n_cnt <= 2'b01;
		    wdata_reg <= {8'h00,latch_byte};
		end
	    end
	    if(wr_n_cnt > 0) begin
		wr_n_cnt <= wr_n_cnt - 1;
		ram_wren <= 1'b1;
		wraddr <= wraddr + 1;
	    end
	    // delayed to make address post-increment
	    ram_wraddr <= (wraddr);
	    // stuffing
	    if(wr_n_cnt == 2) begin
		ram_byte <= wdata_reg[15:8];
	    end
	    else if(wr_n_cnt == 1) begin
		ram_byte <= wdata_reg[7:0];
	    end
	    if(sof == 1'b1) begin
		wraddr <= (C_HDR_SIZE);
	    end
	end
   end

    //-----------------------------------------------------------------
    // HUFFMAN buf_sel
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    huf_buf_sel_s <= 1'b0;
	end 
	else begin
	    if(start_pb == 1'b1) begin
		huf_buf_sel_s <=  ~huf_buf_sel_s;
	    end
	end
    end
   
    //-----------------------------------------------------------------
    // num_enc_bytes
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    num_enc_bytes <= {24{1'b0}};
        end 
	else begin
	    // plus 2 for EOI marker last bytes
	    num_enc_bytes <= (wraddr + 2);
	end
    end


endmodule
