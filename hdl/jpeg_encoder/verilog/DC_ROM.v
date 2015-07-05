// File ../design/DC_ROM_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  DC_ROM.vhd
//
// Project   : JPEG_ENC
//
// Module    : DC_ROM
//
// Content   : DC_ROM Luminance
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

module DC_ROM
(
 input wire 	  CLK,
 input wire 	  RST,
 input wire [3:0] VLI_size,
 output reg [3:0] VLC_DC_size,
 output reg [8:0] VLC_DC
);


  //-----------------------------------------------------------------
  // DC-ROM
  //-----------------------------------------------------------------
  always @(posedge CLK or posedge RST) begin
    if(RST == 1'b 1) begin
      VLC_DC_size <= 4'h 0;
      VLC_DC <= {9{1'b0}};
    end else begin
      case(VLI_size)
      4'h 0 : begin
        VLC_DC_size <= 4'h 2;
        VLC_DC <= (2'b 00);
      end
      4'h 1 : begin
        VLC_DC_size <= 4'h 3;
        VLC_DC <= (3'b 010);
      end
      4'h 2 : begin
        VLC_DC_size <= 4'h 3;
        VLC_DC <= (3'b 011);
      end
      4'h 3 : begin
        VLC_DC_size <= 4'h 3;
        VLC_DC <= (3'b 100);
      end
      4'h 4 : begin
        VLC_DC_size <= 4'h 3;
        VLC_DC <= (3'b 101);
      end
      4'h 5 : begin
        VLC_DC_size <= 4'h 3;
        VLC_DC <= (3'b 110);
      end
      4'h 6 : begin
        VLC_DC_size <= 4'h 4;
        VLC_DC <= (4'b 1110);
      end
      4'h 7 : begin
        VLC_DC_size <= 4'h 5;
        VLC_DC <= (5'b 11110);
      end
      4'h 8 : begin
        VLC_DC_size <= 4'h 6;
        VLC_DC <= (6'b 111110);
      end
      4'h 9 : begin
        VLC_DC_size <= 4'h 7;
        VLC_DC <= (7'b 1111110);
      end
      4'h A : begin
        VLC_DC_size <= 4'h 8;
        VLC_DC <= (8'b 11111110);
      end
      4'h B : begin
        VLC_DC_size <= 4'h 9;
        VLC_DC <= (9'b 111111110);
      end
      default : begin
        VLC_DC_size <= 4'h 0;
        VLC_DC <= {9{1'b0}};
      end
      endcase
    end
  end


endmodule
