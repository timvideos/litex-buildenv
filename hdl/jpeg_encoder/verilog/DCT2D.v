// File ../design/DCT2D_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
//                          COPYRIGHT (C) 2006                                --
//                                                                            --
//------------------------------------------------------------------------------
//
// Title       : DCT2D
// Design      : MDCT Core
// Author      : Michal Krepa
//
//------------------------------------------------------------------------------
//
// File        : DCT2D.VHD
// Created     : Sat Mar 28 22:32 2006
//
//------------------------------------------------------------------------------
//
//  Description : 1D Discrete Cosine Transform (second stage)
//
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
// no timescale needed

module DCT2D
#(
  /// @todo: these were constants from MDCT_PKG, not sure if
  ///    this should be repeated in each module or in a header
  ///    (ugh preprocessor) not sure if iverilog supports SV pkg.
  parameter IP_W        = 8,  
  parameter OP_W        = 12,
  parameter N           = 8,
  parameter COE_W       = 12,
  parameter ROMDATA_W   = COE_W+2,
  parameter ROMADDR_W   = 6,
  parameter RAMDATA_W   = 10,  
  parameter RAMADRR_W   = 6,
  parameter LEVEL_SHIFT = 128,
  parameter DA_W        = ROMDATA_W+IP_W,
  parameter DA2_W       = DA_W+2

  
)
(
 input wire 		       clk,
 input wire 		       rst,
 input wire [RAMDATA_W - 1:0]  ramdatao,
 input wire 		       dataready,
 output wire 		       odv,
 output wire [OP_W - 1:0]      dcto,
 output wire [RAMADRR_W - 1:0] ramraddro,
 output wire 		       rmemsel,
 output reg 		       datareadyack,

 // the original VHDL passed 2D arrays, Verilog doesn't support
 // 2D arrays as ports (systemverilog does).  The 2D arrays are
 // passed as flat ports and reconstructed as 2D arrays.
 input wire  [ROMDATA_W*11-1:0] romedatao_flat,
 input wire  [ROMDATA_W*11-1:0] romodatao_flat,
 output wire [ROMADDR_W*11-1:0] romeaddro_flat,
 output wire [ROMADDR_W*11-1:0] romoaddro_flat

);

    reg [RAMDATA_W:0] 		databuf_reg[N - 1:0];
    reg [RAMDATA_W:0] 		latchbuf_reg[N - 1:0];
    
    reg [RAMADRR_W / 2 - 1:0] 	col_reg;
    reg [RAMADRR_W / 2 - 1:0] 	row_reg;
    reg [RAMADRR_W / 2 - 1:0] 	colram_reg;
    reg [RAMADRR_W / 2 - 1:0] 	rowram_reg;
    reg [RAMADRR_W / 2 - 1:0] 	colr_reg;
    reg [RAMADRR_W / 2 - 1:0] 	rowr_reg;
    
    reg 			rmemsel_reg;
    reg 			stage1_reg;
    reg 			stage2_reg;
    reg [RAMADRR_W - 1:0] 	stage2_cnt_reg;
    reg 			dataready_2_reg;
    
    reg 			even_not_odd;
    reg 			even_not_odd_d1;
    reg 			even_not_odd_d2;
    reg 			even_not_odd_d3;
    reg 			even_not_odd_d4;
    
    reg 			odv_d0;
    reg 			odv_d1;
    reg 			odv_d2;
    reg 			odv_d3;
    reg 			odv_d4;
    reg 			odv_d5;
    
    reg [DA2_W - 1:0] 		dcto_1;
    reg [DA2_W - 1:0] 		dcto_2;
    reg [DA2_W - 1:0] 		dcto_3;
    reg [DA2_W - 1:0] 		dcto_4;
    reg [DA2_W - 1:0] 		dcto_5;  


    wire [ROMDATA_W-1:0] 	romedatao [0:10];
    wire [ROMDATA_W-1:0] 	romodatao [0:10];
    reg [ROMADDR_W-1:0] 	romeaddro [0:10];
    reg [ROMADDR_W-1:0] 	romoaddro [0:10];

    /**
     * conversion note, in Verilog (not SV) 2D arrays cannot be
     * passed as ports.  The 2D arrays need to be flatten to a 
     * port and unflattened from a port.
     */
    genvar gi;
    generate
	for(gi=0; gi<11; gi=gi+1) begin
	    assign romedatao[gi] = romedatao_flat[ROMDATA_W*gi +: ROMDATA_W];
	    assign romodatao[gi] = romodatao_flat[ROMDATA_W*gi +: ROMDATA_W];
	    
	    assign romeaddro_flat[ROMADDR_W*gi +: ROMADDR_W] = romeaddro[gi];
	    assign romoaddro_flat[ROMADDR_W*gi +: ROMADDR_W] = romoaddro[gi];
	end
    endgenerate

    reg [ROMDATA_W-1:0]        romedatao_d1 [0:10];
    reg [ROMDATA_W-1:0]        romedatao_d2 [0:10];
    reg [ROMDATA_W-1:0]        romedatao_d3 [0:10];
    reg [ROMDATA_W-1:0]        romedatao_d4 [0:10];
					       
    reg [ROMDATA_W-1:0]        romodatao_d1 [0:10];
    reg [ROMDATA_W-1:0]        romodatao_d2 [0:10];
    reg [ROMDATA_W-1:0]        romodatao_d3 [0:10];
    reg [ROMDATA_W-1:0]        romodatao_d4 [0:10];

    assign ramraddro = rowr_reg & colr_reg;
    assign rmemsel = rmemsel_reg;

    integer ii;
    always @(posedge clk or posedge rst) begin	
	if (rst == 1'b1) begin    
	    stage2_cnt_reg <= {(((RAMADRR_W - 1))-((0))+1){1'b1}};
	
            rmemsel_reg <= 1'b0;
            stage1_reg  <= 1'b0;
            stage2_reg  <= 1'b0;
            colram_reg  <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
            rowram_reg  <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
	
            col_reg <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
            row_reg <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};

	    for(ii=0; ii<N; ii=ii+1) begin
        	latchbuf_reg[ii]  <= 0; 
            	databuf_reg[ii]   <= 0;
	    end
	
            odv_d0 <= 1'b0;
            colr_reg <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
            rowr_reg <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
            dataready_2_reg <= 1'b0;
        end 
	else begin
	    stage2_reg      <= 1'b0;
	    odv_d0          <= 1'b0;
	    datareadyack    <= 1'b0;
	    dataready_2_reg <= dataready;
	    
	    //--------------------------------
	    // read DCT 1D to barrel shifter
	    //--------------------------------
	    if(stage1_reg == 1'b1) begin
		latchbuf_reg[N-1] <= ramdatao;
		for(ii=0; ii<N-1; ii=ii+1) begin
		    latchbuf_reg[ii] <= latchbuf_reg[ii+1];
		end
		
		colram_reg <= colram_reg + 1;
		colr_reg <= colr_reg + 1;
		if(colram_reg == (N - 2)) begin
		    rowr_reg <= rowr_reg + 1;
		end
		if(colram_reg == (N - 1)) begin
		    rowram_reg <= rowram_reg + 1;
		    if(rowram_reg == (N - 1)) begin
			stage1_reg <= 1'b 0;
			colr_reg <= {(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
			// release memory
			rmemsel_reg <=  ~rmemsel_reg;
		    end

		    //-- after this sum databuf_reg is in range of -256 to 254 (min to max) 
		    databuf_reg[0] = latchbuf_reg[1] + ramdatao;
		    databuf_reg[1] = latchbuf_reg[2] + latchbuf_reg[7];
		    databuf_reg[2] = latchbuf_reg[3] + latchbuf_reg[6];		    
		    databuf_reg[3] = latchbuf_reg[4] + latchbuf_reg[5];
		    databuf_reg[4] = latchbuf_reg[1] + ramdatao;		    
		    databuf_reg[5] = latchbuf_reg[2] + latchbuf_reg[7];
		    databuf_reg[6] = latchbuf_reg[3] + latchbuf_reg[6];		    
		    databuf_reg[7] = latchbuf_reg[4] + latchbuf_reg[5];
		      
		    // 8 point input latched
		    stage2_reg <= 1'b1;
		end
	    end
	    
	    //------------------------------
	    // 2nd stage
	    //------------------------------
	    if(stage2_cnt_reg < N) begin
		stage2_cnt_reg <= stage2_cnt_reg + 1;
		
		// output data valid
		odv_d0 <= 1'b1;
		
		// increment column counter
		col_reg <= col_reg + 1;
		
		// finished processing one input row
		if(col_reg == (N - 1)) begin
		    row_reg <= row_reg + 1;
		end
	    end
	    
	    if(stage2_reg == 1'b1) begin
		stage2_cnt_reg <= 0;
	        col_reg        <= 1;
	    end
	    
	    //------------------------------
	    //--------------------------------
	    // wait for new data
	    //--------------------------------
	    // one of ram buffers has new data, process it
	    if(dataready == 1'b1 && dataready_2_reg == 1'b0) begin
		stage1_reg <= 1'b1;
		// to account for 1T RAM delay, increment RAM address counter
		colram_reg   <= 0;
		colr_reg     <= 1;
		datareadyack <= 1'b1;
	    end
	    //--------------------------------
	end
    end

    always @(posedge clk or posedge rst) begin
	if(rst == 1'b1) begin
	    even_not_odd <= 1'b 0;
	    even_not_odd_d1 <= 1'b 0;
	    even_not_odd_d2 <= 1'b 0;
	    even_not_odd_d3 <= 1'b 0;
	    even_not_odd_d4 <= 1'b 0;
	    
	    odv_d1 <= 1'b0;
	    odv_d2 <= 1'b0;
	    odv_d3 <= 1'b0;
	    odv_d4 <= 1'b0;
	    odv_d5 <= 1'b0;
	    
	    dcto_1 <= {(((DA2_W - 1))-((0))+1){1'b0}};
	    dcto_2 <= {(((DA2_W - 1))-((0))+1){1'b0}};
	    dcto_3 <= {(((DA2_W - 1))-((0))+1){1'b0}};
	    dcto_4 <= {(((DA2_W - 1))-((0))+1){1'b0}};
	    dcto_5 <= {(((DA2_W - 1))-((0))+1){1'b0}};
	end 
	else begin
	    even_not_odd <= stage2_cnt_reg[0];
	    even_not_odd_d1 <= even_not_odd;
	    even_not_odd_d2 <= even_not_odd_d1;
	    even_not_odd_d3 <= even_not_odd_d2;
	    even_not_odd_d4 <= even_not_odd_d3;
	    
	    odv_d1 <= odv_d0;
	    odv_d2 <= odv_d1;
	    odv_d3 <= odv_d2;
	    odv_d4 <= odv_d3;
	    odv_d5 <= odv_d4;

	    /// @todo see if these need to be cast to signed ($signed)
	    ///    both DCT1D and DCT2D
	    
	    if (1'b0 == even_not_odd) begin
		dcto_1 <= romedatao[0] + (romedatao[1] << 1) + (romedatao[2] << 2);
	    end
	    else begin
		dcto_1 <= romodatao[0] + (romodatao[1] << 1) + (romodatao[2] << 2);
	    end
	    
	    if (1'b0 == even_not_odd_d1) begin
		dcto_2 <= dcto_1 + (romedatao_d1[3] << 3) + (romedatao_d1[4] << 4);
	    end
	    else begin
		dcto_2 <= dcto_1 + (romodatao_d1[3] << 3) + (romodatao_d1[4] << 4);
	    end

	    if (1'b0 == even_not_odd_d2) begin
		dcto_3 <= dcto_2 + (romedatao_d2[5] << 5) + (romedatao_d2[6] << 6);
	    end
	    else begin
		dcto_3 <= dcto_2 + (romodatao_d2[5] << 5) + (romodatao_d2[6] << 6);
	    end
	    	    
	    if (1'b0 == even_not_odd_d3) begin
		dcto_4 <= dcto_3 + (romedatao_d3[7] << 7) + (romedatao_d3[8] << 8);
	    end
	    else begin
		dcto_4 <= dcto_3 + (romodatao_d3[7] << 7) + (romodatao_d3[8] << 8);
	    end
	    	    
	    if (1'b0 == even_not_odd_d4) begin
		dcto_5 <= dcto_4 + (romedatao_d4[9] << 9) + (romedatao_d4[10] << 10);
	    end
	    else begin
		dcto_5 <= dcto_4 + (romodatao_d4[9] << 9) + (romodatao_d4[10] << 10);
	    end
	end
    end
    
    assign dcto = dcto_5[DA2_W - 1:12];
    assign odv = odv_d5;
    
    integer jj;
    always @(posedge clk or posedge rst) begin
	if (1'b1 == rst) begin
	    for(jj=0; jj<11; jj=jj+1) begin
		romeaddro[jj] <= 0;
		romoaddro[jj] <= 0;
	    end
	end
	else begin
	    for(jj=0; jj<11; jj=11+1) begin
		// read precomputed MAC results from LUT
		romeaddro[jj] <= {col_reg[RAMADRR_W/2-1:1],
                                  databuf_reg[0][jj],
                                  databuf_reg[1][jj],
                                  databuf_reg[2][jj],
                                  databuf_reg[3][jj]}; 
		// odd
		romoaddro[jj] <= {col_reg[RAMADRR_W/2-1:1],
                                  databuf_reg[4][jj],
                                  databuf_reg[5][jj],
                                  databuf_reg[6][jj],
                                  databuf_reg[7][jj]}; 
	    end
	end
    end

    always @(posedge clk or posedge rst) begin
	if(1'b1 == rst) begin
	    for(jj=0; jj<11; jj=11+1) begin
		romedatao_d1[jj] <= 0;
		romedatao_d2[jj] <= 0;
		romedatao_d3[jj] <= 0;
		romedatao_d4[jj] <= 0;

		romodatao_d1[jj] <= 0;
		romodatao_d2[jj] <= 0;
		romodatao_d3[jj] <= 0;
		romodatao_d4[jj] <= 0;
	    end
	end
	else begin
	    for(jj=0; jj<11; jj=jj+1) begin
		romedatao_d1[jj] <= romedatao[jj];
		romedatao_d2[jj] <= romedatao_d1[jj];
		romedatao_d3[jj] <= romedatao_d2[jj];
		romedatao_d4[jj] <= romedatao_d3[jj];

		romodatao_d1[jj] <= romodatao[jj];   
		romodatao_d2[jj] <= romodatao_d1[jj];
		romodatao_d3[jj] <= romodatao_d2[jj];
		romodatao_d4[jj] <= romodatao_d3[jj];
	    end
	end
    end
    
endmodule
