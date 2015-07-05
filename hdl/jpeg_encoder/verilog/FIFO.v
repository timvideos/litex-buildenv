// File ../design/FIFO_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
// vhd2vl settings:
//   Verilog Module Declaration Style: 1995

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

// //////////////////////////////////////////////////////////////////////////////
// /// Copyright (c) 2013, Jahanzeb Ahmad
// /// All rights reserved.
// ///
// /// Redistribution and use in source and binary forms, with or without modification, 
// /// are permitted provided that the following conditions are met:
// ///
// ///  - Redistributions of source code must retain the above copyright notice, 
// ///    this list of conditions and the following disclaimer.
// ///  - Redistributions in binary form must reproduce the above copyright notice, 
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
// ///  - http://opensource.org/licenses/MIT
// ///  - http://copyfree.org/licenses/mit/license.txt
// ///
// //////////////////////////////////////////////////////////////////////////////
// no timescale needed

module FIFO
#(
  parameter DATA_WIDTH = 12,
  parameter ADDR_WIDTH = 2
)
(
 input  wire rst,
 input  wire clk,
 input  wire rinc,
 input  wire winc,
 input  wire [DATA_WIDTH - 1:0] datai,
 output wire [DATA_WIDTH - 1:0] datao,
 output wire fullo,
 output wire emptyo,
 output wire [ADDR_WIDTH:0] count
);

    reg [ADDR_WIDTH - 1:0]  raddr_reg;
    reg [ADDR_WIDTH - 1:0]  waddr_reg;
    reg [ADDR_WIDTH:0] 	    count_reg;
    wire 		    rd_en_reg;
    wire 		    wr_en_reg;
    reg 		    empty_reg;
    reg 		    full_reg;
    
    wire [DATA_WIDTH - 1:0] ramq;
    wire [DATA_WIDTH - 1:0] ramd;
    wire [ADDR_WIDTH - 1:0] ramwaddr;
    wire 		    ramenw;
    wire [ADDR_WIDTH - 1:0] ramraddr;
    wire 		    ramenr;
    
    parameter ZEROS_C = 0;
    parameter ONES_C  = 1;

    RAMF
      #(.RAMD_W(DATA_WIDTH), .RAMA_W(ADDR_WIDTH))
    U_RAMF
      (.d      (ramd),
       .waddr  (ramwaddr),
       .raddr  (ramraddr),
       .we     (ramenw),
       .clk    (clk),
       .q      (ramq)
       );

    
    assign ramd = datai;
    assign ramwaddr = (waddr_reg);
    assign ramenw = wr_en_reg;
    assign ramraddr = (raddr_reg);
    assign ramenr = 1'b 1;
    assign datao = ramq;
    assign emptyo = empty_reg;
    assign fullo = full_reg;
    assign rd_en_reg = (rinc &  ~empty_reg);
    assign wr_en_reg = (winc &  ~full_reg);
    assign count = (count_reg);
    
    always @(posedge clk) begin
	if(rst == 1'b 1) begin
	    empty_reg <= 1'b 1;
	end
	else begin
	    if(count_reg == ((ZEROS_C)) || (count_reg == 1 && rd_en_reg == 1'b 1 && wr_en_reg == 1'b 0)) begin
		empty_reg <= 1'b 1;
	    end
	    else begin
		empty_reg <= 1'b 0;
	    end
	end
    end
    
    always @(posedge clk) begin
	if(rst == 1'b 1) begin
	    full_reg <= 1'b 0;
	end
	else begin
	    if  (count_reg == 2**ADDR_WIDTH   ||
		 (count_reg == (2**ADDR_WIDTH)-1 &&
		  1'b1 == wr_en_reg && 1'b0 == rd_en_reg)) begin
		full_reg <= 1'b1;
	    end
	    else begin
		full_reg <= 1'b0;
	    end	      
	end
    end
    
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    raddr_reg <= {(((ADDR_WIDTH - 1))-((0))+1){1'b0}};
    end
	else begin
	    if((rd_en_reg == 1'b 1)) begin
		raddr_reg <= raddr_reg + 1;
	    end
	end
    end
    
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    waddr_reg <= {(((ADDR_WIDTH - 1))-((0))+1){1'b0}};
    end
	else begin
	    if(wr_en_reg == 1'b1) begin
		waddr_reg <= waddr_reg + 1;
	    end
	end
    end
    
    always @(posedge clk) begin
	if(rst == 1'b1) begin
	    count_reg <= {(((ADDR_WIDTH))-((0))+1){1'b0}};
        end
	else begin
	    if((rd_en_reg == 1'b1 && wr_en_reg == 1'b0) || 
	       (rd_en_reg == 1'b0 && wr_en_reg == 1'b1)) begin
		if(rd_en_reg == 1'b 1) begin
		    count_reg <= count_reg - 1;
		end
		else begin
		    count_reg <= count_reg + 1;
		end
	    end
	end
    end
    
endmodule
