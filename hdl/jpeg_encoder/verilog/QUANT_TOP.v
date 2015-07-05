// File ../design/QUANT_TOP_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  QUANT_TOP.vhd
//
// Project   : JPEG_ENC
//
// Module    : QUANT_TOP
//
// Content   : Quantizer Top level
//
// Description : Quantizer Top level
//
// Spec.     : 
//
// Author    : Michal Krepa
//
//-----------------------------------------------------------------------------
// History :
// 20090328: (MK): Initial Creation.
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
//-----------------------------------------------------------------------------
// no timescale needed

module QUANT_TOP
(
 input wire 	    CLK,
 input wire 	    RST,
 input wire 	    start_pb,
 output reg 	    ready_pb,


 input wire [15:0]  qua_sm_settings_x_cnt,
 input wire [15:0]  qua_sm_settings_y_cnt,
 input wire [2:0]   qua_sm_settings_cmp_idx,
 
 input wire 	    rle_buf_sel,
 input wire [5:0]   rle_rdaddr,
 output wire [11:0] rle_data,
 
 output wire 	    zig_buf_sel,
 output wire [5:0]  zig_rd_addr,
 input wire [11:0]  zig_data,
 
 input wire [7:0]   qdata,
 input wire [6:0]   qaddr,
 input wire 	    qwren
);

    wire [11:0]     dbuf_data;
    wire [11:0]     dbuf_q;
    wire 	    dbuf_we;
    wire [6:0] 	    dbuf_waddr;
    wire [6:0] 	    dbuf_raddr;
    
    wire [11:0]     zigzag_di;
    wire 	    zigzag_divalid;
    
    wire [11:0]     quant_dout;
    wire 	    quant_dovalid;
    
    reg [5:0] 	    wr_cnt;
    reg [5:0] 	    rd_cnt;
    reg [5:0] 	    rd_en_d;
    reg 	    rd_en;
    
    reg 	    zig_buf_sel_s;
    wire [5:0] 	    zz_rd_addr;
    wire 	    fifo_empty;  
    
    assign zig_rd_addr = (rd_cnt);
    assign rle_data = dbuf_q;
    assign zig_buf_sel = zig_buf_sel_s;
    assign zigzag_di = zig_data;
    assign zigzag_divalid = rd_en_d[0];
    
    //-----------------------------------------------------------------
    // Quantizer
    //-----------------------------------------------------------------
    quantizer
      #(.SIZE_C(12), .RAMQADDR_W(7), .RAMQDATA_W(8))
    U_quantizer
      (.rst      (RST                      ),   
       .clk      (CLK			   ),
       .di       (zigzag_di		   ),
       .divalid  (zigzag_divalid	   ),
       .qdata    (qdata			   ),
       .qwaddr   (qaddr			   ),
       .qwren    (qwren			   ),
       .cmp_idx  (qua_sm_settings_cmp_idx  ),
       .doq      (quant_dout		   ),
       .dovalid  (quant_dovalid            )   
       );
    
  //-----------------------------------------------------------------
  // DBUF
  //-----------------------------------------------------------------
    RAMZ
      #(.RAMADDR_W(7), .RAMDATA_W(12))
    U_RAMZ
      (.d      (dbuf_data  ),
       .waddr  (dbuf_waddr ),
       .raddr  (dbuf_raddr ),
       .we     (dbuf_we	   ),
       .clk    (CLK	   ),
       .q      (dbuf_q     ) 
      );
    
    assign dbuf_data = quant_dout;
    assign dbuf_waddr = {( ~rle_buf_sel),(wr_cnt)};
    assign dbuf_we = quant_dovalid;
    assign dbuf_raddr = {rle_buf_sel,rle_rdaddr};
    
    //-----------------------------------------------------------------
    // Counter1
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    rd_en <= 1'b 0;
	    rd_en_d <= {6{1'b0}};
	    rd_cnt <= {6{1'b0}};
	end 
	else begin
	    //rd_en_d <= rd_en_d(rd_en_d'length-2 downto 0) & rd_en;
	    rd_en_d <= {rd_en_d[6 - 2:0],rd_en};
	    if(start_pb == 1'b 1) begin
		rd_cnt <= {6{1'b0}};
            rd_en <= 1'b 1;
	end
	    if(rd_en == 1'b 1) begin
		if(rd_cnt == (64 - 1)) begin
		    rd_cnt <= {6{1'b0}};
		rd_en <= 1'b 0;
            end
		else begin
		    rd_cnt <= rd_cnt + 1;
		end
	    end
	end
    end

    //-----------------------------------------------------------------
    // wr_cnt
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    wr_cnt <= {6{1'b0}};
	    ready_pb <= 1'b0;
        end 
	else begin
	    ready_pb <= 1'b0;
	    if(start_pb == 1'b1) begin
		wr_cnt <= {6{1'b0}};
	    end
	    
	    if(quant_dovalid == 1'b1) begin
		if(wr_cnt == (64 - 1)) begin
		    wr_cnt <= {6{1'b0}};
                end
		else begin
		    wr_cnt <= wr_cnt + 1;
		end
		
		// give ready ahead to save cycles!
		if(wr_cnt == (64 - 1 - 3)) begin
		    ready_pb <= 1'b1;
		end
	    end
	end
    end

    //-----------------------------------------------------------------
    // zig_buf_sel
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    zig_buf_sel_s <= 1'b0;
	end 
	else begin
	    if(start_pb == 1'b1) begin
		zig_buf_sel_s <=  ~zig_buf_sel_s;
	    end
	end
    end


endmodule
