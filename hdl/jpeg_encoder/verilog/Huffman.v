// File ../design/Huffman_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  Huffman.vhd
//
// Project   : JPEG_ENC
//
// Module    : Huffman
//
// Content   : Huffman Encoder
//
// Description : Huffman encoder core
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

module Huffman
(
 input wire 	   CLK,
 input wire 	   RST,
 
 input wire 	   start_pb,
 output reg 	   ready_pb,
 
 input wire [2:0]  huf_sm_cmp_idx,
 input wire 	   sof,
 input wire [15:0] img_size_x,
 input wire [15:0] img_size_y,
 
 output wire 	   rle_buf_sel,
 output wire 	   rd_en,
 input wire [3:0]  runlength,
 
 input wire [3:0]  VLI_size,
 input wire [11:0] VLI,
 
 input wire 	   d_val,
 input wire 	   rle_fifo_empty,
 
 input wire 	   bs_buf_sel,
 output wire 	   bs_fifo_empty,
 input wire 	   bs_rd_req,
 output wire [7:0] bs_packed_byte
);

    

    parameter [1:0]
      IDLE    = 0,
      RUN_VLC = 1,
      RUN_VLI = 2,
      PAD     = 3;
    
    parameter C_M = 23;
    parameter BLK_SIZE = 64;
    
    reg [1:0] 	   state;  //signal state : unsigned(7 downto 0);
    reg 	   rle_buf_sel_s = 1'b0;
    reg 	   first_rle_word = 1'b0;
    reg [C_M - 1:0] word_reg = 0;
    reg [4:0] 	    bit_ptr = 0;
    
    wire [1:0] 	    num_fifo_wrs;
    wire [15:0]     VLI_ext;
    wire [4:0] 	    VLI_ext_size;
    
    reg 	    ready_HFW = 1'b0;
    reg [7:0] 	    fifo_wbyte = 0;
    reg [1:0] 	    fifo_wrt_cnt = 0;
    reg 	    fifo_wren = 1'b0;
    reg 	    last_block = 1'b0;
    reg [31:0] 	    image_area_size = 0;
    reg [27:0] 	    block_cnt = 0;
    reg [4:0] 	    VLC_size = 0;
    reg [15:0] 	    VLC = 0;
    
    wire [3:0] 	    VLC_DC_size;
    wire [8:0] 	    VLC_DC;
    wire [4:0] 	    VLC_AC_size;
    wire [15:0]     VLC_AC;
    wire 	    vlc_vld;
    
    reg 	    d_val_d1;
    reg 	    d_val_d2;
    reg 	    d_val_d3;
    reg 	    d_val_d4;
    
    reg [3:0] 	    VLI_size_d;
    reg [11:0] 	    VLI_d;
    reg [3:0] 	    VLI_size_d1;
    reg [11:0] 	    VLI_d1;
    
    reg 	    HFW_running = 1'b0;
    
    wire [3:0] 	    runlength_r;
    
    reg [3:0] 	    VLI_size_r;
    reg [11:0] 	    VLI_r;
    
    reg 	    rd_en_s = 1'b0;
    reg [7:0] 	    pad_byte = 0;
    reg 	    pad_reg = 1'b0;
    
    wire [3:0] 	    VLC_CR_DC_size;
    wire [10:0]     VLC_CR_DC;
    wire [4:0] 	    VLC_CR_AC_size;
    wire [15:0]     VLC_CR_AC;
    
    reg 	    start_pb_d1 = 1'b0;  

    // loop index
    integer 	    i;
    
    assign rle_buf_sel = rle_buf_sel_s;
    assign rd_en = rd_en_s;
    assign vlc_vld = rd_en_s;
    
    //-----------------------------------------------------------------
    // latch FIFO Q
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    VLI_size_r <= {4{1'b0}};
	    VLI_r      <= {12{1'b0}};
        end 
	else begin
	    if(d_val == 1'b1) begin
		VLI_size_r <= VLI_size;
		VLI_r      <= VLI;
	    end
	end
    end

    //-----------------------------------------------------------------
    // DC_ROM Luminance
    //-----------------------------------------------------------------
    DC_ROM
      U_DC_ROM
	(.CLK         (CLK),
	 .RST         (RST),
	 .VLI_size    (VLI_size),
	 .VLC_DC_size (VLC_DC_size),
	 .VLC_DC      (VLC_DC)
	 );
    
    //-----------------------------------------------------------------
    // AC_ROM Luminance
    //-----------------------------------------------------------------
    AC_ROM
      U_AC_ROM
	(.CLK         (CLK),
	 .RST         (RST),
	 .runlength   (runlength),
	 .VLI_size    (VLI_size),
	 .VLC_AC_size (VLC_AC_size),
	 .VLC_AC      (VLC_AC)
	 );
    
    //-----------------------------------------------------------------
    // DC_ROM Chrominance
    //-----------------------------------------------------------------
    DC_CR_ROM
      U_DC_CR_ROM
	(.CLK         (CLK),
	 .RST         (RST),
	 .VLI_size    (VLI_size),
	 .VLC_DC_size (VLC_CR_DC_size),
	 .VLC_DC      (VLC_CR_DC)
	 );
    
    //-----------------------------------------------------------------
    // AC_ROM Chrominance
    //-----------------------------------------------------------------
    AC_CR_ROM
      #()
    U_AC_CR_ROM
      (.CLK         (CLK),
       .RST         (RST),
       .runlength   (runlength),
       .VLI_size    (VLI_size),
       .VLC_AC_size (VLC_CR_AC_size),
       .VLC_AC      (VLC_CR_AC)
       );
    
    //-----------------------------------------------------------------
    // Double Fifo
    //-----------------------------------------------------------------
    DoubleFifo
      #()
    U_DoubleFifo
      (
       .CLK                (CLK            ),
       .RST                (RST	      ),
       //-- HUFFMAN	      		      
       .data_in            (fifo_wbyte     ),
       .wren               (fifo_wren      ),
       //-- BYTE STUFFER   		      
       .buf_sel            (bs_buf_sel     ),
       .rd_req             (bs_rd_req      ),
       .fifo_empty         (bs_fifo_empty  ),
       .data_out           (bs_packed_byte )
       );
    
    //-----------------------------------------------------------------
    // RLE buf_sel
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    rle_buf_sel_s <= 1'b 0;
	end 
	else begin
	    if(start_pb == 1'b 1) begin
		rle_buf_sel_s <=  ~rle_buf_sel_s;
	    end
	end
    end
    
    //-----------------------------------------------------------------
    // mux for DC/AC ROM Luminance/Chrominance
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    VLC_size <= {5{1'b0}};
            VLC <= {16{1'b0}};
        end 
	else begin
	    // DC
	    if(first_rle_word == 1'b 1) begin
		// luminance
		if(huf_sm_cmp_idx < 2) begin
		    VLC_size <= {1'b 0,VLC_DC_size};
		    //VLC      <= resize(VLC_DC, VLC'length);
		    VLC <= (VLC_DC);
		    // chrominance
		end
		else begin
		    VLC_size <= {1'b 0,VLC_CR_DC_size};
		    //VLC      <= resize(VLC_CR_DC, VLC'length);
		    VLC <= (VLC_CR_DC);
		end
		// AC
	    end
	    else begin
		// luminance
		if(huf_sm_cmp_idx < 2) begin
		    VLC_size <= VLC_AC_size;
		    VLC <= VLC_AC;
		    // chrominance
		end
		else begin
		    VLC_size <= VLC_CR_AC_size;
		    VLC <= VLC_CR_AC;
		end
	    end
	end
    end
    
    //-----------------------------------------------------------------
    // Block Counter / Last Block detector
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    image_area_size <= {32{1'b0}};
	    last_block <= 1'b0;
        end 
	else begin
	    image_area_size <= ((img_size_x)) * ((img_size_y));
	    if(sof == 1'b 1) begin
		block_cnt <= {28{1'b0}};
	    end
	    else if(start_pb == 1'b 1) begin
		block_cnt <= block_cnt + 1;
	    end
	    if(block_cnt == image_area_size[31:5]) begin
		last_block <= 1'b 1;
	    end
	    else begin
		last_block <= 1'b 0;
	    end
	end
    end
    
    assign VLI_ext = {4'b 0000,VLI_d1};
    assign VLI_ext_size = {1'b 0,VLI_size_d1};
    
    //-----------------------------------------------------------------
    // delay line
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    VLI_d <= {12{1'b0}};
	    VLI_size_d <= {4{1'b0}};
	    VLI_d1 <= {12{1'b0}};
            VLI_size_d1 <= {4{1'b0}};
            d_val_d1 <= 1'b0;
            d_val_d2 <= 1'b0;
            d_val_d3 <= 1'b0;
            d_val_d4 <= 1'b0;
        end 
	else begin
	    VLI_d1 <= VLI_r;
	    VLI_size_d1 <= VLI_size_r;
	    VLI_d <= VLI_d1;
	    VLI_size_d <= VLI_size_d1;
	    d_val_d1 <= d_val;
	    d_val_d2 <= d_val_d1;
	    d_val_d3 <= d_val_d2;
	    d_val_d4 <= d_val_d3;
	end
    end
    
    //-----------------------------------------------------------------
    // HandleFifoWrites
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    ready_HFW     <= 1'b0;
	    fifo_wrt_cnt  <= {2{1'b0}};
	    fifo_wren     <= 1'b0;
	    fifo_wbyte    <= {8{1'b0}};
	    rd_en_s       <= 1'b0;
	    start_pb_d1   <= 1'b0;
	end 
	else begin
	    fifo_wren   <= 1'b0;
	    ready_HFW   <= 1'b0;
	    rd_en_s     <= 1'b0;
	    start_pb_d1 <= start_pb;
	    
	    if(start_pb_d1 == 1'b1) begin
		rd_en_s <= 1'b1 &  ~rle_fifo_empty;
	    end
	    
	    if(HFW_running == 1'b1 && ready_HFW == 1'b0) begin
		// there is no at least one integer byte to write this time
		if(num_fifo_wrs == 0) begin
		    ready_HFW <= 1'b1;
		    if(state == RUN_VLI) begin
			rd_en_s <= 1'b1 &  ~rle_fifo_empty;
		    end
		    // single byte write to FIFO
		end
		else begin
		    fifo_wrt_cnt <= fifo_wrt_cnt + 1;
		    fifo_wren <= 1'b1;
		    // last byte write
		    if((fifo_wrt_cnt + 1) == num_fifo_wrs) begin
			ready_HFW <= 1'b1;
			if(state == RUN_VLI) begin
			    rd_en_s <= 1'b1 &  ~rle_fifo_empty;
			end
			fifo_wrt_cnt <= {2{1'b0}};
		    end
		end
	    end

	    
	    case(fifo_wrt_cnt)
	      2'b00 : begin
		  fifo_wbyte <= (word_reg[C_M - 1:C_M - 8]);
	      end
	      2'b01 : begin
		  fifo_wbyte <= (word_reg[C_M - 8 - 1:C_M - 16]);
	      end
	      default : begin
		  fifo_wbyte <= {8{1'b0}};
	      end
	    endcase
	    
	    if(pad_reg == 1'b1) begin
		fifo_wbyte <= pad_byte;
	    end
	end
    end
    
    // divide by 8
    assign num_fifo_wrs = bit_ptr[4:3];
    
    //-----------------------------------------------------------------
    // Variable Length Processor FSM
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    ready_pb <= 1'b0;
	    first_rle_word <= 1'b 0;
	    state <= IDLE;
	    word_reg <= {(((C_M - 1))-((0))+1){1'b0}};
	    bit_ptr <= {5{1'b0}};
	    HFW_running <= 1'b 0;
	    pad_reg <= 1'b 0;
	    pad_byte <= {8{1'b0}};
	end 
	else begin
	    ready_pb <= 1'b0;
	    
	    case(state)
	      IDLE : begin
		  if(start_pb == 1'b1) begin
		      first_rle_word <= 1'b1;
		      state <= RUN_VLC;
		  end
	      end
	      
	      RUN_VLC : begin
		  // data valid DC or data valid AC
		  if((d_val_d1 == 1'b 1 && first_rle_word == 1'b 1) || (d_val == 1'b 1 && first_rle_word == 1'b 0)) begin
		      for (i=0; i <= C_M - 1; i = i + 1) begin
			  if(i < VLC_size) begin
			      word_reg[C_M - 1 - bit_ptr - i] <= VLC[VLC_size - 1 - i];
			  end
		      end
		      
		      //bit_ptr <= bit_ptr + resize(VLC_size,bit_ptr'length);
		      bit_ptr <= bit_ptr + ((VLC_size));
		      
		      // HandleFifoWrites
		      HFW_running <= 1'b1;
		      // HandleFifoWrites completed
		  end
		  else if(HFW_running == 1'b1 && (num_fifo_wrs == 0 || (fifo_wrt_cnt + 1) == num_fifo_wrs)) begin
		      // shift word reg left to skip bytes already written to FIFO
		      // @todo: check manual conversion
		      //word_reg <= shift_left(word_reg, to_integer(num_fifo_wrs & "000"));
		      word_reg <= (word_reg << {num_fifo_wrs, 3'b000});
		      
		      // adjust bit pointer after some bytes were written to FIFO
		      // modulo 8 operation
		      bit_ptr <= bit_ptr - {num_fifo_wrs,3'b000};
		      HFW_running <= 1'b 0;
		      first_rle_word <= 1'b 0;
		      state <= RUN_VLI;
		  end
	      end
	      
	      RUN_VLI : begin
		  if(HFW_running == 1'b0) begin
		      for (i=0; i <= C_M - 1; i = i + 1) begin
			  if(i < VLI_ext_size) begin
			      word_reg[C_M - 1 - bit_ptr - i] <= VLI_ext[VLI_ext_size - 1 - i];
			  end
		      end
		      //bit_ptr <= bit_ptr + resize(VLI_ext_size, bit_ptr'length);
		      bit_ptr <= bit_ptr + ((VLI_ext_size));
		      // HandleFifoWrites
		      HFW_running <= 1'b1;
		      // HandleFifoWrites completed
		  end
		  else if(HFW_running == 1'b1 && (num_fifo_wrs == 0 || (fifo_wrt_cnt + 1) == num_fifo_wrs)) begin
		      // shift word reg left to skip bytes already written to FIFO
		      // @todo: check manual conversion
		      //word_reg <= shift_left(word_reg, to_integer(num_fifo_wrs & "000"));
		      word_reg <= (word_reg << {num_fifo_wrs, 3'b000});
		      
		      // adjust bit pointer after some bytes were written to FIFO
		      // modulo 8 operation
		      bit_ptr <= bit_ptr - {num_fifo_wrs,3'b000};
		      HFW_running <= 1'b0;
		      // end of block
		      if(rle_fifo_empty == 1'b1) begin
			  // end of segment
			  if ((bit_ptr - {num_fifo_wrs, 3'b000} != 0) && last_block == 1) begin
			      state <= PAD;
			  end
			  else begin
			      ready_pb <= 1;
			      state <= IDLE;			      
			  end
		      end
		      else begin
			  state <= RUN_VLC;
		      end
		  end
		  // end of segment which requires bit padding
	      end
	      
	      PAD : begin
		  if(HFW_running == 1'b0) begin
		      // 1's bit padding to integer number of bytes
		      for (i=0; i <= 7; i = i + 1) begin
			  if(i < bit_ptr) begin
			      pad_byte[7 - i] <= word_reg[C_M - 1 - i];
			  end
			  else begin
			      pad_byte[7 - i] <= 1'b1;
			  end
		      end
		      pad_reg <= 1'b1;
		      //bit_ptr <= to_unsigned(8, bit_ptr'length);
		      bit_ptr <= (8);
		      // HandleFifoWrites
		      HFW_running <= 1'b1;
		  end
		  else if(HFW_running == 1'b 1 && (num_fifo_wrs == 0 || (fifo_wrt_cnt + 1) == num_fifo_wrs)) begin
		      bit_ptr <= {5{1'b0}};
		       HFW_running <= 1'b0;
		       pad_reg <= 1'b0;
		       ready_pb <= 1'b1;
		       state <= IDLE;
		   end
	      end
	      
	      default : begin
	      end
	      
	    endcase
	    
	    if(sof == 1'b1) begin
		bit_ptr <= {5{1'b0}};
	    end
	end
  end
    
endmodule
