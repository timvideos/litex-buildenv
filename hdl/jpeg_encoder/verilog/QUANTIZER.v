// File ../design/QUANTIZER_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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

//------------------------------------------------------------------------------
//                                                                            --
//                          V H D L    F I L E                                --
//                          COPYRIGHT (C) 2006-2009                           --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// Title       : DIVIDER                                                      --
// Design      : DCT QUANTIZER                                                --
// Author      : Michal Krepa                                                 --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// File        : QUANTIZER.VHD                                                --
// Created     : Sun Aug 27 2006                                              --
//                                                                            --
//------------------------------------------------------------------------------
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

module quantizer
#(
  parameter SIZE_C     = 12,
  parameter RAMQADDR_W = 7,
  parameter RAMQDATA_W = 8
)
(
 input wire 		    rst,
 input wire 		    clk,
 input wire [SIZE_C - 1:0]  di,
 input wire 		    divalid,
 input wire [7:0] 	    qdata,
 input wire [6:0] 	    qwaddr,
 input wire 		    qwren,
 input wire [2:0] 	    cmp_idx,
 output wire [SIZE_C - 1:0] doq,
 output wire 		    dovalid
);

    parameter INTERN_PIPE_C = 3;
    localparam M = SIZE_C + INTERN_PIPE_C + 1;
    
    reg [RAMQADDR_W - 2:0]  romaddr_s;
    wire [RAMQADDR_W - 1:0] slv_romaddr_s;
    wire [RAMQDATA_W - 1:0] romdatao_s;
    wire [SIZE_C - 1:0]     divisor_s;
    wire [SIZE_C - 1:0]     remainder_s;
    wire [SIZE_C - 1:0]     do_s;
    wire 		    round_s;
    reg [SIZE_C - 1:0] 	    di_d1;
    reg [4:0] 		    pipeline_reg;
    reg [M - 1:0] 	    sign_bit_pipe;
    
    wire [SIZE_C - 1:0]     do_rdiv;
    reg 		    table_select;
    
    //--------------------------
    // RAMQ
    //--------------------------
    RAMZ
      #(.RAMADDR_W(RAMQADDR_W), .RAMDATA_W(RAMQDATA_W))
    U_RAMQ
      (.d     (qdata         ),
       .waddr (qwaddr	     ),
       .raddr (slv_romaddr_s ),
       .we    (qwren	     ),
       .clk   (clk	     ),
       .q     (romdatao_s    )
       );
    
    assign divisor_s[RAMQDATA_W - 1:0] = romdatao_s;
    assign divisor_s[SIZE_C - 1:RAMQDATA_W] = {(((SIZE_C - 1))-((RAMQDATA_W))+1){1'b0}};
    
    r_divider U_r_divider
      (.rst(rst),
       .clk(clk),
       .a(di_d1),
       .d(romdatao_s),
       .q(do_s)
       );
    
    assign doq = do_s;
    assign slv_romaddr_s = {table_select,(romaddr_s)};
    
    //----------------------------
    // Quantization sub table select
    //----------------------------
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    table_select <= 1'b0;
	end
	else begin
	    // luminance table select
	    if(cmp_idx < 2) begin
		table_select <= 1'b0;
		// chrominance table select
	    end
	    else begin
		table_select <= 1'b1;
	    end
	end
    end
    
    //--------------------------
    // address incrementer
    //--------------------------
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    romaddr_s <= {(((RAMQADDR_W - 2))-((0))+1){1'b0}};
	    pipeline_reg <= {5{1'b0}};
            di_d1 <= {(((SIZE_C - 1))-((0))+1){1'b0}};
            sign_bit_pipe <= {(((SIZE_C + INTERN_PIPE_C + 1 - 1))-((0))+1){1'b0}};
        end
        else begin
	    if(divalid == 1'b1) begin
		romaddr_s <= romaddr_s + 1;
	    end
	    //pipeline_reg <= pipeline_reg(pipeline_reg'length-2 downto 0) & divalid;
	    pipeline_reg <= {pipeline_reg[5 - 2:0], divalid};
	    di_d1 <= di;
	    sign_bit_pipe <= sign_bit_pipe[M-2 : 0];
	end
    end

    
    assign dovalid = pipeline_reg[4];


endmodule
