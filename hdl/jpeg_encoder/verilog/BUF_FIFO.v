// File ../design/BUF_FIFO_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name : BUF_FIFO.vhd
//
// Project   : JPEG_ENC
//
// Module    : BUF_FIFO
//
// Content   : Input FIFO Buffer
//
// Description : 
//
// Spec.     : 
//
// Author    : Michal Krepa
//
//-----------------------------------------------------------------------------
// History :
// 20090311: (MK): Initial Creation.
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


module BUF_FIFO
#(
  parameter C_PIXEL_BITS = 24
)
(
 input wire 			 CLK,
 input wire 			 RST,
 input wire [15:0] 		 img_size_x,
 input wire [15:0] 		 img_size_y,
 
 input wire 			 sof,
 input wire 			 iram_wren,
 input wire [C_PIXEL_BITS - 1:0] iram_wdata,
 output reg 			 fifo_almost_full,
 
 input wire 			 fdct_fifo_rd,
 output wire [23:0] 		 fdct_fifo_q,
 output reg 			 fdct_fifo_hf_full
);

    /// @todo: better home, these were in a global package in
    ///    the VHDL version.  Might need to use a header file,
    ///    don't believe the

    // C_EXTRA_LINES should be a multiple of 8 (documents indicate
    // 8 or 16) with 16 being the highest performance and 8 being
    // lowest area (least amount BRAM required).
    parameter C_EXTRA_LINES     = 16; //8;
    parameter C_MAX_LINE_WIDTH  = 1280;
    parameter C_NUM_LINES       = 8 + C_EXTRA_LINES;

    localparam RAMADDR_W = $clog2(C_MAX_LINE_WIDTH*C_NUM_LINES);
    localparam LINADDR_W = $clog2(C_NUM_LINES);
    
    
    reg [15:0] 			 pixel_cnt;
    wire [15:0] 		 line_cnt;
    wire [C_PIXEL_BITS - 1:0] 	 ramq;
    reg [C_PIXEL_BITS - 1:0] 	 ramd;
    
    reg [RAMADDR_W-1:0] ramwaddr;
    reg 		ramenw;    
    wire [RAMADDR_W-1:0] ramraddr;
    
    reg [3:0] 		 pix_inblk_cnt;
    reg [3:0] 		 pix_inblk_cnt_d1;
    reg [2:0] 		 line_inblk_cnt;
    reg [12:0] 		 read_block_cnt;
    reg [12:0] 		 read_block_cnt_d1;
    wire [12:0] 	 write_block_cnt;
    
    reg [16 + $clog2(C_NUM_LINES) - 1:0] ramraddr_int;
    reg [16 + $clog2(C_NUM_LINES) - 1:0] raddr_base_line;
    reg [15:0] 				 raddr_tmp;
    reg [RAMADDR_W-1:0] 		 ramwaddr_d1;
    
    wire [$clog2(C_NUM_LINES) - 1:0] 	 line_lock;
    reg [$clog2(C_NUM_LINES)  - 1:0] 	 memwr_line_cnt;
    reg [$clog2(C_NUM_LINES)  - 1 + 1:0] memrd_offs_cnt;
    reg [$clog2(C_NUM_LINES)  - 1:0] 	 memrd_line;
    reg [15:0] 				 wr_line_idx;
    reg [15:0] 				 rd_line_idx;
    reg 				 image_write_end;  
    
   
    //-----------------------------------------------------------------
    // RAM for SUB_FIFOs
    //-----------------------------------------------------------------
    SUB_RAMZ
      #(.RAMADDR_W(RAMADDR_W),
	.RAMDATA_W(C_PIXEL_BITS))
    U_SUB_RAMZ
      (.d     (ramd),
       .waddr (ramwaddr_d1),
       .raddr (ramraddr),
       .we    (ramenw),
       .clk   (CLK),
       .q     (ramq)
       );
    
    //-----------------------------------------------------------------
    // register RAM data input
    //-----------------------------------------------------------------   
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    ramenw <= 1'b 0;
	    ramd <= {(((C_PIXEL_BITS - 1))-((0))+1){1'b0}};
	end 
	else begin
	    ramd <= iram_wdata;
	    ramenw <= iram_wren;
	end
    end
    
    //-----------------------------------------------------------------
    // resolve RAM write address
    //-----------------------------------------------------------------    
    always @(posedge CLK or posedge RST) begin	
	if (RST == 1'b1) begin	    
	    pixel_cnt <= {16{1'b0}};	
            memwr_line_cnt <= {((($clog2(C_NUM_LINES) - 1))-((0))+1){1'b0}};
            wr_line_idx <= {16{1'b0}};
            ramwaddr <= {((($clog2(C_MAX_LINE_WIDTH * C_NUM_LINES) - 1))-((0))+1){1'b0}};
            ramwaddr_d1 <= {((($clog2(C_MAX_LINE_WIDTH * C_NUM_LINES) - 1))-((0))+1){1'b0}};
            image_write_end <= 1'b 0;
        end 
	else begin
	    ramwaddr_d1 <= ramwaddr;
	    if(iram_wren == 1'b 1) begin
		// end of line
		if(pixel_cnt == (((img_size_x)) - 1)) begin
		    pixel_cnt <= {16{1'b0}};
		   // absolute write line index
		   wr_line_idx <= wr_line_idx + 1;
		   if(wr_line_idx == (((img_size_y)) - 1)) begin
		       image_write_end <= 1'b 1;
		   end
		   // memory line index
	           if(memwr_line_cnt == (C_NUM_LINES - 1)) begin
		       memwr_line_cnt <= {((($clog2(C_NUM_LINES) - 1))-((0))+1){1'b0}};
		       ramwaddr <= {((($clog2(C_MAX_LINE_WIDTH * C_NUM_LINES) - 1))-((0))+1){1'b0}};
                   end
		   else begin
		       memwr_line_cnt <= memwr_line_cnt + 1;
		       ramwaddr <= ramwaddr + 1;
		   end
                end 
		else begin
		    pixel_cnt <= pixel_cnt + 1;
		    ramwaddr <= ramwaddr + 1;
		end
	    end
	    
	    if(sof == 1'b 1) begin
		pixel_cnt <= {16{1'b0}};
                ramwaddr <= {((($clog2(C_MAX_LINE_WIDTH * C_NUM_LINES) - 1))-((0))+1){1'b0}};
                memwr_line_cnt <= {((($clog2(C_NUM_LINES) - 1))-((0))+1){1'b0}};
                wr_line_idx <= {16{1'b0}};
                image_write_end <= 1'b0;
            end
	end
    end

    //-----------------------------------------------------------------
    // FIFO half full / almost full flag generation
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if (RST == 1'b1) begin
	    fdct_fifo_hf_full <= 1'b0;
	    fifo_almost_full <= 1'b0;
	end 
	else begin
	    if((rd_line_idx + 8) <= wr_line_idx) begin
		fdct_fifo_hf_full <= 1'b1;
	    end
	    else begin
		fdct_fifo_hf_full <= 1'b0;
	    end
	    fifo_almost_full <= 1'b0;
	    if(wr_line_idx == (rd_line_idx + C_NUM_LINES - 1)) begin
		if(pixel_cnt >= (((img_size_x)) - 1 - 1)) begin
		    fifo_almost_full <= 1'b1;
		end
	    end
	    else if(wr_line_idx > (rd_line_idx + C_NUM_LINES - 1)) begin
		fifo_almost_full <= 1'b1;
	    end
	end
    end

    //-----------------------------------------------------------------
    // read side
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin 
	    memrd_offs_cnt <= {((($clog2(C_NUM_LINES) - 1 + 1))-((0))+1){1'b0}};
            read_block_cnt <= {13{1'b0}};
	    pix_inblk_cnt <= {4{1'b0}};
            line_inblk_cnt <= {3{1'b0}};
            rd_line_idx <= {16{1'b0}};
            pix_inblk_cnt_d1 <= {4{1'b0}};
            read_block_cnt_d1 <= {13{1'b0}};
        end 
	else begin
	    pix_inblk_cnt_d1 <= pix_inblk_cnt;
	    read_block_cnt_d1 <= read_block_cnt;
	    
	    // BUF FIFO read
	    if(fdct_fifo_rd == 1'b 1) begin
		// last pixel in block
		if(pix_inblk_cnt == (8 - 1)) begin
		    pix_inblk_cnt <= {4{1'b0}};
		
		    // last line in 8
		    if(line_inblk_cnt == (8 - 1)) begin
		        line_inblk_cnt <= {3{1'b0}};
		        // last block in last line
		        if(read_block_cnt == (((img_size_x[15:3])) - 1)) begin
		    	read_block_cnt <= {13{1'b0}};
    	  	            rd_line_idx <= rd_line_idx + 8;
		            if((memrd_offs_cnt + 8) > (C_NUM_LINES - 1)) begin
                                memrd_offs_cnt <= memrd_offs_cnt + 8 - C_NUM_LINES;
		    	end
		    	else begin
		    	    memrd_offs_cnt <= memrd_offs_cnt + 8;
		    	end
		        end
		        else begin
		    	read_block_cnt <= read_block_cnt + 1;
		        end
                    end
		    else begin
		        line_inblk_cnt <= line_inblk_cnt + 1;
		    end		
                end
	        else begin
	            pix_inblk_cnt <= pix_inblk_cnt + 1;
	        end
	    end
	    
	    if((memrd_offs_cnt + ((line_inblk_cnt))) > (C_NUM_LINES - 1)) begin
		memrd_line <= memrd_offs_cnt[$clog2(C_NUM_LINES) - 1:0] + ((line_inblk_cnt)) - ((C_NUM_LINES));
	    end
	    else begin
		memrd_line <= memrd_offs_cnt[$clog2(C_NUM_LINES) - 1:0] + ((line_inblk_cnt));
	    end
	    
	    if(sof == 1'b1) begin
		memrd_line <= {((($clog2(C_NUM_LINES) - 1))-((0))+1){1'b0}};
                memrd_offs_cnt <= {((($clog2(C_NUM_LINES) - 1 + 1))-((0))+1){1'b0}};
                read_block_cnt <= {13{1'b0}};
                pix_inblk_cnt <= {4{1'b0}};
                line_inblk_cnt <= {3{1'b0}};
                rd_line_idx <= {16{1'b0}};
	    end
	end
    end

    // generate RAM data output based on 16 or 24 bit mode selection
    assign fdct_fifo_q = C_PIXEL_BITS == 16 ? 
			 {ramq[15:11],3'b 000,ramq[10:5],2'b 00,ramq[4:0],3'b 000} : 
		         (((ramq)));
    
    assign ramraddr = ramraddr_int[$clog2(C_MAX_LINE_WIDTH * C_NUM_LINES) - 1:0];
   
    //-----------------------------------------------------------------
    // resolve RAM read address
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    ramraddr_int <= {(((16 + $clog2(C_NUM_LINES) - 1))-((0))+1){1'b0}};
        end 
	else begin
	    raddr_base_line <= ((memrd_line)) * ((img_size_x));
	    raddr_tmp <= {read_block_cnt_d1,3'b000} + pix_inblk_cnt_d1;
	    ramraddr_int <= raddr_tmp + raddr_base_line;
	end
    end

endmodule

