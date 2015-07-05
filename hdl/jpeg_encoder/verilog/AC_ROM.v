// File ../design/AC_ROM_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  AC_ROM.vhd
//
// Project   : JPEG_ENC
//
// Module    : AC_ROM
//
// Content   : AC_ROM Luminance
//
// Description : 
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

// no timescale needed

module AC_ROM
(
 input wire 	   CLK,
 input wire 	   RST,
 input wire [3:0]  runlength,
 input wire [3:0]  VLI_size,
 output reg [4:0]  VLC_AC_size,
 output reg [15:0] VLC_AC
);
    
    wire [7:0] 	   rom_addr;  

    assign rom_addr = {runlength,VLI_size};
    
    //-----------------------------------------------------------------
    // AC-ROM
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    VLC_AC_size <= {5{1'b0}};
            VLC_AC <= {16{1'b0}};
        end 
	else begin
	    case(runlength)
	      4'h 0 : begin
		  case(VLI_size)
		    4'h 0 : begin
			VLC_AC_size <= (4);
			VLC_AC <= (4'b 1010);
		    end
		    4'h 1 : begin
			VLC_AC_size <= (2);
			VLC_AC <= (2'b 00);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (2);
			VLC_AC <= (2'b 01);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (3);
			VLC_AC <= (3'b 100);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (4);
			VLC_AC <= (4'b 1011);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (5);
			VLC_AC <= (5'b 11010);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (7);
			VLC_AC <= (7'b 1111000);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (8);
			VLC_AC <= (8'b 11111000);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (10);
			VLC_AC <= (10'b 1111110110);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000010);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000011);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 1 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (4);
			VLC_AC <= (4'b 1100);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (5);
			VLC_AC <= (5'b 11011);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (7);
			VLC_AC <= (7'b 1111001);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (9);
			VLC_AC <= (9'b 111110110);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (11);
			VLC_AC <= (11'b 11111110110);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000100);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000101);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000110);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110000111);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001000);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 2 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (5);
			VLC_AC <= (5'b 11100);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (8);
			VLC_AC <= (8'b 11111001);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (10);
			VLC_AC <= (10'b 1111110111);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (12);
			VLC_AC <= (12'b 111111110100);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001001);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001010);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001011);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001100);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001101);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001110);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 3 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (6);
			VLC_AC <= (6'b 111010);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (9);
			VLC_AC <= (9'b 111110111);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (12);
			VLC_AC <= (12'b 111111110101);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110001111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 4 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (6);
			VLC_AC <= (6'b 111011);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (10);
			VLC_AC <= (10'b 1111111000);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010110);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110010111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 5 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (7);
			VLC_AC <= (7'b 1111010);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (11);
			VLC_AC <= (11'b 11111110111);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011110);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110011111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 6 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (7);
			VLC_AC <= (7'b 1111011);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (12);
			VLC_AC <= (12'b 111111110110);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100110);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110100111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 7 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (8);
			VLC_AC <= (8'b 11111010);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (12);
			VLC_AC <= (12'b 111111110111);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101110);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110101111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 8 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (9);
			VLC_AC <= (9'b 111111000);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (15);
			VLC_AC <= (15'b 111111111000000);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110110);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110110111);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111000);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111001);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111010);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111011);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111100);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111101);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h 9 : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (9);
			VLC_AC <= (9'b 111111001);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111110);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111110111111);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000000);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000001);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000010);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000011);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000100);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000101);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000110);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h A : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (9);
			VLC_AC <= (9'b 111111010);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111000111);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001000);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001001);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001010);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001011);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001100);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001101);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001110);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111001111);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h B : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (10);
			VLC_AC <= (10'b 1111111001);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010000);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010001);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010010);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010011);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010100);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010101);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010110);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111010111);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011000);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h C : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (10);
			VLC_AC <= (10'b 1111111010);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011001);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011010);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011011);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011100);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011101);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011110);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111011111);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100000);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100001);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h D : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (11);
			VLC_AC <= (11'b 11111111000);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100010);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100011);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100100);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100101);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100110);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111100111);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101000);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101001);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101010);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h E : begin
		  case(VLI_size)
		    4'h 1 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101011);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101100);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101101);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101110);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111101111);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110000);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110001);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110010);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110011);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110100);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      4'h F : begin
		  case(VLI_size)
		    4'h 0 : begin
			VLC_AC_size <= (11);
			VLC_AC <= (11'b 11111111001);
		    end
		    4'h 1 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110101);
		    end
		    4'h 2 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110110);
		    end
		    4'h 3 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111110111);
		    end
		    4'h 4 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111000);
		    end
		    4'h 5 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111001);
		    end
		    4'h 6 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111010);
		    end
		    4'h 7 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111011);
		    end
		    4'h 8 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111100);
		    end
		    4'h 9 : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111101);
		    end
		    4'h A : begin
			VLC_AC_size <= (16);
			VLC_AC <= (16'b 1111111111111110);
		    end
		    default : begin
			VLC_AC_size <= (0);
			VLC_AC <= (1'b 0);
		    end
		  endcase
	      end
	      default : begin
		  VLC_AC_size <= {5{1'b0}};
		  VLC_AC <= {16{1'b0}};
	      end
	    endcase
	end
    end
    

endmodule
