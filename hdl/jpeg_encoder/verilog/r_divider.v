// File ../design/r_divider_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
// vhd2vl settings:
//  * Verilog Module Declaration Style: 1995

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
//                          COPYRIGHT (C) 2009                                --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// Title       : DIVIDER                                                      --
// Design      : Divider using reciprocal table                               --
// Author      : Michal Krepa                                                 --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// File        : R_DIVIDER.VHD                                                --
// Created     : Wed 18-03-2009                                               --
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
// MAIN DIVIDER top level
//------------------------------------------------------------------------------
// no timescale needed

module r_divider
(
 input wire rst,
 input wire clk,
 input wire [11:0] a,
 input wire [7:0] d,
 output reg [11:0] q
);

    wire [15:0] romr_datao;
    wire [7:0] 	romr_addr;
    wire [11:0] dividend;
    reg [11:0] 	dividend_d1 = 0;
    wire [15:0] reciprocal;
    
    reg [27:0] mult_out = 0;
    reg [11:0] mult_out_s = 0;
    
    wire   signbit;
    reg    signbit_d1 = 1'b 0;
    reg    signbit_d2 = 1'b 0;
    reg    signbit_d3 = 1'b 0;
    reg    round = 1'b 0;

    ROMR
      //#(.ROMADDR_W(8), .ROMDATA_W(16))
    U_ROMR
      (.addr    (romr_addr),
       .clk     (clk),
       .datao   (romr_datao)
       );
    
    assign romr_addr = d;
    assign reciprocal = (romr_datao);
    assign dividend = (a);
    
    //dividend(dividend'high);    
    assign signbit = dividend[11];
    
    always @(posedge clk or posedge rst) begin
        if(rst == 1'b1) begin
            mult_out <= {28{1'b0}};
	    mult_out_s <= {12{1'b0}};
       	    dividend_d1 <= {12{1'b0}};
	    q <= {12{1'b0}};
            signbit_d1 <= 1'b 0;
            signbit_d2 <= 1'b 0;
            signbit_d3 <= 1'b 0;
            round <= 1'b 0;
        end 
	else begin
	    signbit_d1 <= signbit;
	    signbit_d2 <= signbit_d1;
	    signbit_d3 <= signbit_d2;
	    if(signbit == 1'b 1) begin
		dividend_d1 <= (0 - dividend);
	    end
	    else begin
		dividend_d1 <= (dividend);
	    end
	    mult_out <= dividend_d1 * reciprocal;
	    if(signbit_d2 == 1'b 0) begin
		// mult_out_s <= resize(signed(mult_out(27 downto 16)), mult_out_s'length);
		mult_out_s <= ((mult_out[27:16]));
	    end
	    else begin
		// mult_out_s <= resize(0-signed(mult_out(27 downto 16)),mult_out_s'length);         
		mult_out_s <= (0 - ((mult_out[27:16])));
	    end
	    round <= mult_out[15];
	    if(signbit_d3 == 1'b 0) begin
		if(round == 1'b 1) begin
		    q <= (mult_out_s + 1);
		end
		else begin
		    q <= (mult_out_s);
		end
	    end
	    else begin
		if(round == 1'b 1) begin
		    q <= (mult_out_s - 1);
		end
		else begin
		    q <= (mult_out_s);
		end
	    end
	end
    end

endmodule
