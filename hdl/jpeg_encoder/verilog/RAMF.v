// File ../design/RAMF_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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

// no timescale needed

module RAMF
#(
  parameter RAMD_W = 12,
  parameter RAMA_W = 6
  )
 (
  input wire [RAMD_W - 1:0] d,
  input wire [RAMA_W - 1:0] waddr,
  input wire [RAMA_W - 1:0] raddr,
  input wire 		      we,
  input wire 		      clk,
  output reg [RAMD_W - 1:0] q
 );     

   //type mem_type is array ((2**RAMA_W)-1 downto 0) of 
   //                            STD_LOGIC_VECTOR(RAMD_W-1 downto 0);
   //signal mem                    : mem_type;
   localparam MEM_SIZE = 2**RAMA_W;   
   reg [RAMD_W-1:0] mem [0:MEM_SIZE-1];   
   reg [RAMD_W-1:0] read_addr;
   
   //-----------------------------------------------------------------------------
   //q_sg:
   //-----------------------------------------------------------------------------
   //q <= mem(TO_INTEGER(UNSIGNED(read_addr)));
   always @(*) begin
      q = mem[read_addr];      
   end
   
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
      if(we == 1'b 1) begin
	 mem[waddr] <= d;
      end
   end
   
   //--------------------------------------------------------------------------------

endmodule
