// File ../design/SUB_RAMZ_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
//                                                                            --
// Title       : SUB_RAMZ                                                         --
// Design      : EV_JPEG_ENC                                                         --
// Author      : Michal Krepa                                                 --                                                             --                                                           --
//                                                                            --
//------------------------------------------------------------------------------
//
// File        : SUB_RAMZ.VHD
// Created     : 22/03/2009
//
//------------------------------------------------------------------------------
//
//  Description : RAM memory simulation model
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

module SUB_RAMZ
#(
    parameter RAMADDR_W=6,
    parameter RAMDATA_W=12
)
(
    input wire [RAMDATA_W - 1:0]  d,
    input wire [RAMADDR_W - 1:0]  waddr,
    input wire [RAMADDR_W - 1:0]  raddr,
    input wire 			  we,
    input wire 			  clk,
    output wire [RAMDATA_W - 1:0] q
);

   //type mem_type is array ((2**RAMADDR_W)-1 downto 0) of 
   //  STD_LOGIC_VECTOR(RAMDATA_W-1 downto 0);
   //signal mem                    : mem_type;
   localparam MEM_SIZE = 2**RAMADDR_W;   
   reg [RAMDATA_W-1:0] mem[0:MEM_SIZE-1];   
   reg [RAMADDR_W-1:0] read_addr;  


    //-----------------------------------------------------------------------------
    //q_sg:
    //-----------------------------------------------------------------------------
    // q <= mem(TO_INTEGER(UNSIGNED(read_addr)));
    assign q = mem[read_addr];
    
  //-----------------------------------------------------------------------------
  //read_proc: -- register read address
  //-----------------------------------------------------------------------------
  always @(posedge clk) begin
    read_addr <= raddr;
  end

  //-----------------------------------------------------------------------------
  //write_proc: --write access
  //-----------------------------------------------------------------------------
  always @(posedge clk) begin
    if(we == 1'b1) begin
      //mem(TO_INTEGER(UNSIGNED(waddr))) <= d;
	mem[waddr] <= d;
    end
  end


endmodule
