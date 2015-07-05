// File ../design/DCT1D_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// Title       : DCT1D
// Design      : MDCT Core
// Author      : Michal Krepa
//
//------------------------------------------------------------------------------
//
// File        : DCT1D.VHD
// Created     : Sat Mar 5 7:37 2006
//
//------------------------------------------------------------------------------
//
//  Description : 1D Discrete Cosine Transform (1st stage)
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
//------------------------------------------------------------------------------
// ENTITY
//------------------------------------------------------------------------------
// no timescale needed

module DCT1D
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
  parameter DA_W        = ROMDATA_W+IP_W
)
(
 input wire 		       clk,
 input wire 		       rst,
 input wire [IP_W-1:0] 	       dcti,
 input wire 		       idv,

 // the original VHDL passed 2D arrays, Verilog doesn't support
 // 2D arrays as ports (systemverilog does).  The 2D arrays are
 // passed as flat ports and reconstructed as 2D array
 //input wire [8:0][ROMDATA_W-1:0] romedatao,
 //input wire [8:0][ROMDATA_W-1:0] romodatao,
 //output wire [ROMADDR_W-1:0] romeaddro [0:8],
 //output wire [ROMADDR_W-1:0] romoaddro [0:8],

 input wire [ROMDATA_W*9-1:0]  romedatao_flat,
 input wire [ROMDATA_W*9-1:0]  romodatao_flat,
 output wire [ROMADDR_W*9-1:0] romeaddro_flat,
 output wire [ROMADDR_W*9-1:0] romoaddro_flat,
 
 output wire 		       odv,
 output wire [OP_W-1:0]        dcto,
  
 output wire [RAMADRR_W-1:0]   ramwaddro,
 output wire [RAMDATA_W-1:0]   ramdatai,
 output wire 		       ramwe,
 output wire 		       wmemsel
);

    //--**************************************************************
    //--**************************************************************
    reg [IP_W:0] databuf_reg  [N - 1:0];
    reg [IP_W:0] latchbuf_reg [N - 1:0];    
    reg  [(RAMADRR_W/2) - 1:0] col_reg         = 0;
    reg  [(RAMADRR_W/2) - 1:0] row_reg         = 0;
    wire [(RAMADRR_W/2) - 1:0] rowr_reg;
    reg  [(RAMADRR_W/2) - 1:0] inpcnt_reg      = 0;    
    reg 		       ramwe_s         = 1'b0;
    reg 		       wmemsel_reg     = 1'b0;
    reg 		       stage2_reg      = 1'b0;
    reg [RAMADRR_W - 1 :0]     stage2_cnt_reg  = 1;    
    reg [(RAMADRR_W/2) - 1 :0] col_2_reg       = 0;
    reg [RAMADRR_W - 1 :0]     ramwaddro_s     = 0;

    //--**************************************************************
    //--**************************************************************
    reg 		       even_not_odd    = 1'b0;
    reg 		       even_not_odd_d1 = 1'b0;
    reg 		       even_not_odd_d2 = 1'b0;
    reg 		       even_not_odd_d3 = 1'b0;
    
    reg 		       ramwe_d1        = 1'b0;
    reg 		       ramwe_d2        = 1'b0;
    reg 		       ramwe_d3        = 1'b0;
    reg 		       ramwe_d4        = 1'b0;
    
    reg [RAMADRR_W - 1:0]      ramwaddro_d1    = 0;
    reg [RAMADRR_W - 1:0]      ramwaddro_d2    = 0;
    reg [RAMADRR_W - 1:0]      ramwaddro_d3    = 0;
    reg [RAMADRR_W - 1:0]      ramwaddro_d4    = 0;
    
    reg 		       wmemsel_d1      = 1'b0;
    reg 		       wmemsel_d2      = 1'b0;
    reg 		       wmemsel_d3      = 1'b0;
    reg 		       wmemsel_d4      = 1'b0;

    wire [ROMDATA_W-1:0]  romedatao [0:8];
    wire [ROMDATA_W-1:0]  romodatao [0:8];
    reg [ROMADDR_W-1:0]  romeaddro [0:8];
    reg [ROMADDR_W-1:0]  romoaddro [0:8];    

    reg [ROMDATA_W-1:0]  romedatao_d1 [0:8];
    reg [ROMDATA_W-1:0]  romedatao_d2 [0:8];
    reg [ROMDATA_W-1:0]  romedatao_d3 [0:8];
    
    reg [ROMDATA_W-1:0]  romodatao_d1 [0:8];
    reg [ROMDATA_W-1:0]  romodatao_d2 [0:8];
    reg [ROMDATA_W-1:0]  romodatao_d3 [0:8];
    
    
    reg [DA_W - 1:0] 	 dcto_1 = 0;
    reg [DA_W - 1:0] 	 dcto_2 = 0;
    reg [DA_W - 1:0] 	 dcto_3 = 0;
    reg [DA_W - 1:0] 	 dcto_4 = 0;

    /**
     * conversion note, in Verilog (not SV) 2D arrays cannot be
     * passed as ports.  The 2D arrays need to be flatten to a 
     * port and unflattened from a port.
     */
    genvar gi;
    generate
	for(gi=0; gi<9; gi=gi+1) begin
	    // select [RDW-1:0](0+8:0), [2*RDW-1:RDW](RDW+8:0), ...
	    assign romedatao[gi] = romedatao_flat[ROMDATA_W*gi +: ROMDATA_W];
	    assign romodatao[gi] = romodatao_flat[ROMDATA_W*gi +: ROMDATA_W];
	    
	    assign romeaddro_flat[ROMADDR_W*gi +: ROMADDR_W] = romeaddro[gi];
	    assign romoaddro_flat[ROMADDR_W*gi +: ROMADDR_W] = romoaddro[gi];
	end
    endgenerate

    //--**************************************************************
    //--**************************************************************

    assign ramwaddro = ramwaddro_d4;
    assign ramwe = ramwe_d4;
    assign ramdatai = dcto_4[DA_W - 1:12];
    assign wmemsel = wmemsel_d4;

    integer ii, jj;

    //--**************************************************************
    //--**************************************************************
    always @(posedge clk or posedge rst) begin
	if(rst == 1'b1) begin
	    inpcnt_reg  <= 0; 
	    
	    for(ii=0; ii<IP_W; ii=ii+1) begin
		latchbuf_reg[ii] <= 0;
		databuf_reg[ii]  <= 0;
	    end
	    
            stage2_reg     <= 1'b0;
            stage2_cnt_reg <= {(((RAMADRR_W - 1))-((0))+1){1'b1}};
	    
            ramwe_s        <= 1'b0;
            ramwaddro_s    <= 0; 
            col_reg        <= 0; 
            row_reg        <= 0; 
            wmemsel_reg    <= 1'b0;
            col_2_reg      <= 0;  
	end 
	else begin
	    
	    stage2_reg <= 1'b0;
	    ramwe_s    <= 1'b0;
	    
	    //------------------------------
	    // 1st stage
	    //------------------------------
	    if(idv == 1'b1) begin
		inpcnt_reg <= inpcnt_reg + 1;

		// the following loop achieves the same as the
		// VHDL array slice
		//   latchbuf_reg[N - 2:0] <= latchbuf_reg[N - 1:1];
		for(jj=0; jj<N-1; jj=jj+1) begin
		    latchbuf_reg[jj] <= latchbuf_reg[jj+1];
		end		
		latchbuf_reg[N - 1] <= ({1'b0,dcti}) - LEVEL_SHIFT;
		
		if(inpcnt_reg == (N - 1)) begin
		    // after this sum databuf_reg is in range of -256 to 254 (min to max) 
		    databuf_reg[0] <= latchbuf_reg[1] + ((({1'b0,dcti}) - LEVEL_SHIFT));
		    databuf_reg[1] <= latchbuf_reg[2] + latchbuf_reg[7];
		    databuf_reg[2] <= latchbuf_reg[3] + latchbuf_reg[6];
		    databuf_reg[3] <= latchbuf_reg[4] + latchbuf_reg[5];
		    databuf_reg[4] <= latchbuf_reg[1] - ((({1'b0,dcti}) - LEVEL_SHIFT));	    
		    databuf_reg[5] <= latchbuf_reg[2] - latchbuf_reg[7];
		    databuf_reg[6] <= latchbuf_reg[3] - latchbuf_reg[6];
		    databuf_reg[7] <= latchbuf_reg[4] - latchbuf_reg[5];
		    stage2_reg <= 1'b1;
		end
	    end
	    
	    //------------------------------
	    //------------------------------
	    // 2nd stage
	    //------------------------------
	    if(stage2_cnt_reg < N) begin
		stage2_cnt_reg <= stage2_cnt_reg + 1;
		
		// write RAM
		ramwe_s <= 1'b1;
		// reverse col/row order for transposition purpose
		ramwaddro_s <= {col_2_reg,row_reg};
		// increment column counter
		col_reg <= col_reg + 1;
		col_2_reg <= col_2_reg + 1;
		
		// finished processing one input row
		if(col_reg == 0) begin
		    row_reg <= row_reg + 1;
		    // switch to 2nd memory
		    if(row_reg == (N - 1)) begin
			wmemsel_reg <=  ~wmemsel_reg;
			col_reg     <= 0; //{(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
		    end
		end
	    end
	    if(stage2_reg == 1'b1) begin	  
		stage2_cnt_reg <= 0; //{(((RAMADRR_W - 1))-((0))+1){1'b0}};	  
		col_reg        <= 1; 
		col_2_reg      <= 0; //{(((RAMADRR_W / 2 - 1))-((0))+1){1'b0}};
	    end
	    //--------------------------------   
	end
    end
    
    // output data pipeline
    always @(posedge clk or posedge rst) begin
	if(rst == 1'b1) begin
	    even_not_odd <= 1'b0;
	    even_not_odd_d1 <= 1'b0;
	    even_not_odd_d2 <= 1'b0;
	    even_not_odd_d3 <= 1'b0;
	    ramwe_d1 <= 1'b0;
	    ramwe_d2 <= 1'b0;
	    ramwe_d3 <= 1'b0;
	    ramwe_d4 <= 1'b0;
	    
	    ramwaddro_d1 <= 0;
	    ramwaddro_d2 <= 0;
	    ramwaddro_d3 <= 0;
	    ramwaddro_d4 <= 0;
     
	    wmemsel_d1 <= 1'b0;
	    wmemsel_d2 <= 1'b0;
	    wmemsel_d3 <= 1'b0;
	    wmemsel_d4 <= 1'b0;
	    
	    dcto_1 <= {(((DA_W - 1))-((0))+1){1'b0}};
	    dcto_2 <= {(((DA_W - 1))-((0))+1){1'b0}};
	    dcto_3 <= {(((DA_W - 1))-((0))+1){1'b0}};
	    dcto_4 <= {(((DA_W - 1))-((0))+1){1'b0}};
	    
	end 
	else begin
	    even_not_odd    <= stage2_cnt_reg[0];
	    even_not_odd_d1 <= even_not_odd;
	    even_not_odd_d2 <= even_not_odd_d1;
	    even_not_odd_d3 <= even_not_odd_d2;
	    
	    ramwe_d1 <= ramwe_s;
	    ramwe_d2 <= ramwe_d1;
	    ramwe_d3 <= ramwe_d2;
	    ramwe_d4 <= ramwe_d3;
	    
	    ramwaddro_d1 <= ramwaddro_s;
	    ramwaddro_d2 <= ramwaddro_d1;
	    ramwaddro_d3 <= ramwaddro_d2;
	    ramwaddro_d4 <= ramwaddro_d3;
	    
	    wmemsel_d1 <= wmemsel_reg;
	    wmemsel_d2 <= wmemsel_d1;
	    wmemsel_d3 <= wmemsel_d2;
	    wmemsel_d4 <= wmemsel_d3;
	    
	    if (1'b0 == even_not_odd) begin
		dcto_1 <= romedatao[0] + (romedatao[1] << 1) + (romedatao[2] << 2);
	    end
	    else begin
		dcto_1 <= romodatao[0] + (romodatao[1] << 1) + (romodatao[2] <<2);
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
	end
    end

    integer kk;
    always @(posedge clk or posedge rst) begin
	if (rst == 1'b1) begin
	    for(kk=0; kk<8; kk=kk+1) begin
		romeaddro[kk] <= 0;
		romoaddro[kk] <= 0;
	    end
	end
	else begin
	    for(kk=0; kk<8; kk=kk+1) begin
		romeaddro[kk] <= {col_reg[RAMADRR_W/2-1:1], 
				  databuf_reg[0][kk], 
				  databuf_reg[1][kk],
				  databuf_reg[2][kk], 
				  databuf_reg[3][kk]};
		romoaddro[kk] <= {col_reg[RAMADRR_W/2-1:1], 
				  databuf_reg[4][kk], 
				  databuf_reg[5][kk],
				  databuf_reg[6][kk], 
				  databuf_reg[7][kk]};
	    end
	end
    end

    always @(posedge clk or posedge rst) begin
	if (1'b1 == rst) begin
	    for (kk=0; kk<8; kk=kk+1) begin
		romedatao_d1[kk] <= 0;
		romodatao_d1[kk] <= 0;
		romedatao_d2[kk] <= 0;
		romodatao_d2[kk] <= 0;
		romedatao_d3[kk] <= 0;
		romodatao_d3[kk] <= 0;		
	    end
	end
	else begin
	    for (kk=0; kk<8; kk=kk+1) begin
		romedatao_d1[kk] <= romedatao[kk];
		romodatao_d1[kk] <= romodatao[kk];
		romedatao_d2[kk] <= romedatao_d1[kk];
		romodatao_d2[kk] <= romodatao_d1[kk];
		romedatao_d3[kk] <= romedatao_d2[kk];
		romodatao_d3[kk] <= romodatao_d2[kk];

	    end
	end
    end
    
    
endmodule
