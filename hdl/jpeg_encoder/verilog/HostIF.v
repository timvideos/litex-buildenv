// File ../design/HostIF_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name : HostIF.vhd
//
// Project   : JPEG_ENC
//
// Module    : HostIF
//
// Content   : Host Interface (Xilinx OPB v2.1)
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

module HostIF
(
 input wire 	    CLK,
 input wire 	    RST,
 
 input wire [31:0]  OPB_ABus,
 input wire [3:0]   OPB_BE,
 input wire [31:0]  OPB_DBus_in,
 input wire 	    OPB_RNW,
 input wire 	    OPB_select,
 output reg [31:0]  OPB_DBus_out,
 output reg 	    OPB_XferAck,
 output wire 	    OPB_retry,
 output wire 	    OPB_toutSup,
 output wire 	    OPB_errAck,

 output reg [7:0]   qdata,
 output reg [6:0]   qaddr,
 output reg 	    qwren,
 input wire 	    jpeg_ready,
 input wire 	    jpeg_busy,
 output wire [9:0]  outram_base_addr,
 input wire [23:0]  num_enc_bytes,
 output wire [15:0] img_size_x,
 output wire [15:0] img_size_y,
 output reg 	    img_size_wr,
 output reg 	    sof
);

    // OPB
    // Quantizer RAM
    // CTRL
    // ByteStuffer
    // others        

    // @todo: verify these constants, some converted funky?
    parameter C_ENC_START_REG        = 32'h0000_0000;
    parameter C_IMAGE_SIZE_REG       = 32'h0000_0004;
    parameter C_IMAGE_RAM_ACCESS_REG = 32'h0000_0008;
    parameter C_ENC_STS_REG          = 32'h0000_000C;
    parameter C_COD_DATA_ADDR_REG    = 32'h0000_0010;
    parameter C_ENC_LENGTH_REG       = 32'h0000_0014;
    parameter C_QUANTIZER_RAM_LUM    = 32'h0000_0100; 
    parameter C_QUANTIZER_RAM_CHR    = 32'h0000_0200; 
    //parameter C_IMAGE_RAM            = 32'h0010_0000; 
    parameter C_IMAGE_RAM_BASE       = 32'h0010_0000;
    
    reg [31:0] enc_start_reg;
    reg [31:0] image_size_reg;
    reg [31:0] image_ram_access_reg;
    reg [31:0] enc_sts_reg;
    reg [31:0] cod_data_addr_reg;
    reg [31:0] enc_length_reg;
    reg        rd_dval;
    reg [31:0] data_read;
    reg        write_done;
    reg        OPB_select_d;  

    //-----------------------------------------------------------------------------
    // Architecture: begin
    //-----------------------------------------------------------------------------
    
    assign OPB_retry = 1'b0;
    assign OPB_toutSup = 1'b0;
    assign OPB_errAck = 1'b0;
    assign img_size_x = image_size_reg[31:16];
    assign img_size_y = image_size_reg[15:0];
    assign outram_base_addr = cod_data_addr_reg[9:0];
    
    //-----------------------------------------------------------------
    // OPB read
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    OPB_DBus_out <= {32{1'b0}};
	    rd_dval <= 1'b0;
	    data_read <= {32{1'b0}};
        end 
	else begin
	    rd_dval <= 1'b0;
	    OPB_DBus_out <= data_read;
	    if(OPB_select == 1'b 1 && OPB_select_d == 1'b0) begin
		// only double word transactions are be supported
		if(OPB_RNW == 1'b 1 && OPB_BE == 4'hF) begin
		    case(OPB_ABus)
		      C_ENC_START_REG : begin
			  data_read <= enc_start_reg;
			  rd_dval <= 1'b1;
		      end
		      C_IMAGE_SIZE_REG : begin
			  data_read <= image_size_reg;
			  rd_dval <= 1'b1;
		      end
		      C_IMAGE_RAM_ACCESS_REG : begin
			  data_read <= image_ram_access_reg;
			  rd_dval <= 1'b1;
		      end
		      C_ENC_STS_REG : begin
			  data_read <= enc_sts_reg;
			  rd_dval <= 1'b1;
		      end
		      C_COD_DATA_ADDR_REG : begin
			  data_read <= cod_data_addr_reg;
			  rd_dval <= 1'b1;
		      end
		      C_ENC_LENGTH_REG : begin
			  data_read <= enc_length_reg;
			  rd_dval <= 1'b1;
		      end
		      default : begin
			  data_read <= {32{1'b0}};
		      end
		    endcase
		end
	    end
	end
    end
    
    //-----------------------------------------------------------------
    // OPB write
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    qwren <= 1'b0;
	    write_done <= 1'b0;
	    enc_start_reg <= {32{1'b0}};
	    image_size_reg <= {32{1'b0}};
	    image_ram_access_reg <= {32{1'b0}};
	    enc_sts_reg <= {32{1'b0}};
	    cod_data_addr_reg <= {32{1'b0}};
	    enc_length_reg <= {32{1'b0}};
	    qdata <= {8{1'b0}};
	    qaddr <= {7{1'b0}};
	    OPB_select_d <= 1'b0;
	    sof <= 1'b0;
	    img_size_wr <= 1'b0;
	end 
	else begin
	    qwren <= 1'b0;
	    write_done <= 1'b0;
	    sof <= 1'b0;
	    img_size_wr <= 1'b0;
	    OPB_select_d <= OPB_select;
	    if(OPB_select == 1'b1 && OPB_select_d == 1'b0) begin
		// only double word transactions are be supported
		if(OPB_RNW == 1'b0 && OPB_BE == 4'hF) begin
		    case(OPB_ABus)
		      C_ENC_START_REG : begin
			  enc_start_reg <= OPB_DBus_in;
			  write_done <= 1'b 1;
			  if(OPB_DBus_in[0] == 1'b1) begin
			      sof <= 1'b 1;
			  end
		      end
		      C_IMAGE_SIZE_REG : begin
			  image_size_reg <= OPB_DBus_in;
			  img_size_wr <= 1'b1;
			  write_done <= 1'b1;
		      end
		      C_IMAGE_RAM_ACCESS_REG : begin
			  image_ram_access_reg <= OPB_DBus_in;
			  write_done <= 1'b1;
		      end
		      C_ENC_STS_REG : begin
			  enc_sts_reg <= {32{1'b0}};
			  write_done <= 1'b1;
		      end
		      C_COD_DATA_ADDR_REG : begin
			  cod_data_addr_reg <= OPB_DBus_in;
			  write_done <= 1'b1;
		      end
		      C_ENC_LENGTH_REG : begin
			  //enc_length_reg <= OPB_DBus_in;
			  write_done <= 1'b1;
		      end
		      default : begin
		      end
		    endcase
		    
		    if ((OPB_ABus & C_QUANTIZER_RAM_LUM) == C_QUANTIZER_RAM_LUM) begin
			qdata <= OPB_DBus_in;
			qaddr <= {1'b0, OPB_ABus[7:2]};
			qwren <= 1'b1;
			write_done <= 1'b1;
		    end

		    if ((OPB_ABus & C_QUANTIZER_RAM_CHR) == C_QUANTIZER_RAM_CHR) begin
			qdata <= OPB_DBus_in;
			qaddr <= {1'b1, OPB_ABus[7:2]};
			qwren <= 1'b1;
			write_done <= 1'b1;
		    end
		end
	    end
	    // special handling of status reg
	    if(jpeg_ready == 1'b1) begin
		// set jpeg done flag
		enc_sts_reg[1] <= 1'b1;
	    end
	    enc_sts_reg[0] <= jpeg_busy;
	    enc_length_reg <= {32{1'b0}};
	    enc_length_reg[23:0] <= num_enc_bytes;
	end
    end
    
    //-----------------------------------------------------------------
    // transfer ACK
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    OPB_XferAck <= 1'b0;
	end 
	else begin
	    OPB_XferAck <= rd_dval | write_done;
	end
    end
    

endmodule
