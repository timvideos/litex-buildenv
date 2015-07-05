// File ../design/JFIFGen_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  JFIFGen.vhd
//
// Project   : JPEG_ENC
//
// Module    : JFIFGen
//
// Content   : JFIF Header Generator
//
// Description :
//
// Spec.     : 
//
// Author    : Michal Krepa
//
//-----------------------------------------------------------------------------
// History :
// 20090309: (MK): Initial Creation.
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

module JFIFGen
#(
  /// @todo: these were constnats from JPEG_PKG, not sure if
  ///    this should be repeated in each module or in a header
  ///    (ugh preprocessor) not sure if iverilog supports SV pkg.
  parameter C_HDR_SIZE = 623
)  
(
 input wire 	   CLK,
 input wire 	   RST,
 input wire 	   start,
 output reg 	   ready,
 input wire 	   eoi,
 input wire [23:0] num_enc_bytes,
 
 input wire 	   qwren,
 input wire [6:0]  qwaddr,
 input wire [7:0]  qwdata,
 
 input wire [31:0] image_size_reg,
 input wire 	   image_size_reg_wr,
 
 output reg [7:0]  ram_byte,
 output reg 	   ram_wren,
 output reg [23:0] ram_wraddr
);


    parameter C_SIZE_Y_H = 25;
    parameter C_SIZE_Y_L = 26;
    parameter C_SIZE_X_H = 27;
    parameter C_SIZE_X_L = 28;
    parameter C_EOI = 16'h FFD9;
    parameter C_QLUM_BASE = 44;
    parameter C_QCHR_BASE = 44 + 69;
    
    reg [7:0] 	   hr_data = 0;
    reg [9:0] 	   hr_waddr = 0;
    wire [9:0] 	   hr_raddr;
    reg 	   hr_we = 1'b0;
    wire [7:0] 	   hr_q;
    
    reg [2:0] 	   size_wr_cnt = 0;
    reg 	   size_wr = 1'b0;
    reg [9:0] 	   rd_cnt = 0;
    reg 	   rd_en = 1'b0;
    reg 	   rd_en_d1 = 1'b0;
    reg [9:0] 	   rd_cnt_d1 = 0;
    reg [9:0] 	   rd_cnt_d2 = 0;
    reg [1:0] 	   eoi_cnt = 0;
    reg 	   eoi_wr = 1'b0;
    reg 	   eoi_wr_d1 = 1'b0;
    

    //-----------------------------------------------------------------
    // Header RAM
    //-----------------------------------------------------------------
    HeaderRam 
      U_Header_RAM
	(
	 .d(hr_data),
	 .waddr(hr_waddr),
	 .raddr(hr_raddr),
	 .we(hr_we),
	 .clk(CLK),
	 .q(hr_q));
    
    assign hr_raddr = (rd_cnt);
    
    //-----------------------------------------------------------------
    // Host programming
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    size_wr_cnt <= {3{1'b0}};
       	    size_wr <= 1'b 0;
	    hr_we <= 1'b 0;
            hr_data <= {8{1'b0}};
            hr_waddr <= {10{1'b0}};
        end 
	else begin
	    hr_we <= 1'b 0;
	    if(image_size_reg_wr == 1'b 1) begin
		size_wr_cnt <= {3{1'b0}};
                size_wr <= 1'b 1;
	    end
      // write image size
      if(size_wr == 1'b 1) begin
        if(size_wr_cnt == 4) begin
          size_wr_cnt <= {3{1'b0}};
          size_wr <= 1'b 0;
        end
        else begin
          size_wr_cnt <= size_wr_cnt + 1;
          hr_we <= 1'b 1;
          case(size_wr_cnt)
                    // height H byte
          3'b 000 : begin
            hr_data <= image_size_reg[15:8];
            //hr_waddr <= std_logic_vector(to_unsigned(C_SIZE_Y_H,hr_waddr'length));
            hr_waddr <= ((C_SIZE_Y_H));
            // height L byte
          end
          3'b 001 : begin
            hr_data <= image_size_reg[7:0];
            //hr_waddr <= std_logic_vector(to_unsigned(C_SIZE_Y_L, hr_waddr'length));
            hr_waddr <= ((C_SIZE_Y_L));
            // width H byte
          end
          3'b 010 : begin
            hr_data <= image_size_reg[31:24];
            //hr_waddr <= std_logic_vector(to_unsigned(C_SIZE_X_H,hr_waddr'length));
            hr_waddr <= ((C_SIZE_X_H));
            // width L byte
          end
          3'b 011 : begin
            hr_data <= image_size_reg[23:16];
            //hr_waddr <= std_logic_vector(to_unsigned(C_SIZE_X_L,hr_waddr'length));
            hr_waddr <= ((C_SIZE_X_L));
          end
          default : begin
          end
          endcase
        end
        // write Quantization table
      end
      else if(qwren == 1'b 1) begin
        // luminance table select
        if(qwaddr[6] == 1'b 0) begin
          //hr_waddr <= std_logic_vector
          //              ( resize(unsigned(qwaddr(5 downto 0)), hr_waddr'length) + 
          //                to_unsigned(C_QLUM_BASE, hr_waddr'length));
          hr_waddr <= ((((qwaddr[5:0]))) + ((C_QLUM_BASE)));
        end
        else begin
          // chrominance table select
          hr_waddr <= ((((qwaddr[5:0]))) + ((C_QCHR_BASE)));
        end
        hr_we <= 1'b 1;
        hr_data <= qwdata;
      end
    end
  end

  //-----------------------------------------------------------------
  // CTRL
  //-----------------------------------------------------------------
  always @(posedge CLK or posedge RST) begin
    if(RST == 1'b 1) begin
      ready <= 1'b 0;
      rd_en <= 1'b 0;
      rd_cnt <= {10{1'b0}};
      rd_cnt_d1 <= {10{1'b0}};
      rd_cnt_d2 <= {10{1'b0}};
      rd_cnt_d1 <= {10{1'b0}};
      rd_en_d1 <= 1'b 0;
      eoi_wr_d1 <= 1'b 0;
      eoi_wr <= 1'b 0;
      eoi_cnt <= {2{1'b0}};
      ram_wren <= 1'b 0;
      ram_byte <= {8{1'b0}};
      ram_wraddr <= {24{1'b0}};
    end else begin
      ready <= 1'b 0;
      rd_cnt_d1 <= rd_cnt;
      rd_cnt_d2 <= rd_cnt_d1;
      rd_en_d1 <= rd_en;
      eoi_wr_d1 <= eoi_wr;
      // defaults: encoded data write
      ram_wren <= rd_en_d1;
      ram_wraddr <= ((rd_cnt_d1));
      ram_byte <= hr_q;
      // start JFIF
      if(start == 1'b 1 && eoi == 1'b 0) begin
        rd_cnt <= {10{1'b0}};
        rd_en <= 1'b 1;
      end
      else if(start == 1'b 1 && eoi == 1'b 1) begin
        eoi_wr <= 1'b 1;
        eoi_cnt <= {2{1'b0}};
      end
      // read JFIF Header
      if(rd_en == 1'b 1) begin
        if(rd_cnt == (C_HDR_SIZE - 1)) begin
          rd_en <= 1'b 0;
          ready <= 1'b 1;
        end
        else begin
          rd_cnt <= rd_cnt + 1;
        end
      end
      // EOI MARKER write
      if(eoi_wr == 1'b 1) begin
        if(eoi_cnt == 2) begin
          eoi_cnt <= {2{1'b0}};
          eoi_wr <= 1'b 0;
          ready <= 1'b 1;
        end
        else begin
          eoi_cnt <= eoi_cnt + 1;
          ram_wren <= 1'b 1;
          if(eoi_cnt == 0) begin
            ram_byte <= C_EOI[15:8];
            ram_wraddr <= num_enc_bytes;
          end
          else if(eoi_cnt == 1) begin
            ram_byte <= C_EOI[7:0];
            ram_wraddr <= (((num_enc_bytes)) + ((1)));
          end
        end
      end
    end
  end


endmodule
