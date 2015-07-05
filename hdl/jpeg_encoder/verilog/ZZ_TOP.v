// File ../design/ZZ_TOP_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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

//-----------------------------------------------------------------------------
// File Name :  ZZ_TOP.vhd
//
// Project   : JPEG_ENC
//
// Module    : ZZ_TOP
//
// Content   : ZigZag Top level
//
// Description : Zig Zag scan
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

module ZZ_TOP
(
 input wire 	    CLK,
 input wire 	    RST,
 // CTRL
 input wire 	    start_pb,
 output reg 	    ready_pb,
 // Quantizer
 input wire 	    qua_buf_sel,
 input wire [5:0]   qua_rdaddr,
 output wire [11:0] qua_data,
 // FDCT
 output wire 	    fdct_buf_sel,
 output wire [5:0]  fdct_rd_addr,
 input wire [11:0]  fdct_data,
 output wire 	    fdct_rden
 );   
   
   wire [11:0] 	 dbuf_data;
   wire [11:0] 	 dbuf_q;
   wire 	 dbuf_we;
   wire [6:0] 	 dbuf_waddr;
   wire [6:0] 	 dbuf_raddr;
    
   wire [11:0] 	 zigzag_di;
   wire 	 zigzag_divalid;
   wire [11:0] 	 zigzag_dout;
   wire 	 zigzag_dovalid;
    
   reg [5:0] 	 wr_cnt = 0;
   reg [5:0] 	 rd_cnt = 0;    
   reg [5:0] 	 rd_en_d;
   reg 		 rd_en;
    
   reg 		 fdct_buf_sel_s;
   wire [5:0] 	 zz_rd_addr;
   wire 	 fifo_empty;
   reg 		 fifo_rden;
    
   //-----------------------------------------------------------------------------
   // Architecture: begin
   //-----------------------------------------------------------------------------
   
   assign fdct_rd_addr = (zz_rd_addr);
   assign qua_data = dbuf_q;
   assign fdct_buf_sel = fdct_buf_sel_s;
   assign fdct_rden = rd_en;
    
   //-----------------------------------------------------------------
   // ZigZag Core
   //-----------------------------------------------------------------
   ZIGZAG 
     #(.RAMADDR_W(16), .RAMDATA_W(12))
   U_ZIGZAG
     (.rst        (RST),
      .clk        (CLK),
      .di         (zigzag_di),
      .divalid    (zigzag_divalid),
      .rd_addr    (rd_cnt),
      .fifo_rden  (fifo_rden),
      .fifo_empty (fifo_empty),
      .dout       (zigzag_dout),
      .dovalid    (zigzag_dovalid),
      .zz_rd_addr (zz_rd_addr)
      );
      
   assign zigzag_di = fdct_data;
   assign zigzag_divalid = rd_en_d[1];
    
   //-----------------------------------------------------------------
   // DBUF
   //-----------------------------------------------------------------
   RAMZ 
     #(.RAMADDR_W(7),
       .RAMDATA_W(12) )
   U_RAMZ
     (.d(dbuf_data),
      .waddr(dbuf_waddr),
      .raddr(dbuf_raddr),
      .we(dbuf_we),
      .clk(CLK),
      .q(dbuf_q)
      );
      
   assign dbuf_data = zigzag_dout;
   assign dbuf_waddr = {( ~qua_buf_sel),(wr_cnt)};
   assign dbuf_we = zigzag_dovalid;
   assign dbuf_raddr = {qua_buf_sel,qua_rdaddr};
   
   //-----------------------------------------------------------------
   // FIFO Ctrl
   //-----------------------------------------------------------------
   always @(posedge CLK or posedge RST) begin
      if(RST == 1'b1) begin
	 fifo_rden <= 1'b0;
      end 
      else begin
	 if(fifo_empty == 1'b0) begin
            fifo_rden <= 1'b1;
	 end
	 else begin
            fifo_rden <= 1'b0;
	 end
      end
   end
   
   //-----------------------------------------------------------------
   // Counter1
   //-----------------------------------------------------------------
   always @(posedge CLK or posedge RST) begin
      if(RST == 1'b1) begin
	 rd_en <= 1'b0;
	 rd_en_d <= {6{1'b0}};
	 rd_cnt <= {6{1'b0}};
      end 
      else begin
	 rd_en_d <= {rd_en_d[5 - 2:0],rd_en};
	 if (start_pb == 1'b1) begin
            rd_cnt <= {6{1'b0}};
            rd_en <= 1'b1;
         end
	 
         if(rd_en == 1'b 1) begin
             if(rd_cnt == (64 - 1)) begin
                rd_cnt <= {6{1'b0}};
                rd_en <= 1'b0;
             end
             else begin
		rd_cnt <= rd_cnt + 1;
             end
	 end	 
      end
   end
   
   //-----------------------------------------------------------------
   // wr_cnt
   //-----------------------------------------------------------------
   always @(posedge CLK or posedge RST) begin
      if(RST == 1'b1) begin
	 wr_cnt <= {6{1'b0}};
         ready_pb <= 1'b0;
      end 
      else begin
	 ready_pb <= 1'b0;
	 if(start_pb == 1'b1) begin
            wr_cnt <= {6{1'b0}};
         end
	 if(zigzag_dovalid == 1'b1) begin
            if(wr_cnt == (64 - 1)) begin
               wr_cnt <= {6{1'b0}};
	     end
            else begin
               wr_cnt <= wr_cnt + 1;
            end
            // give ready ahead to save cycles!
            if(wr_cnt == (64 - 1 - 3)) begin
               ready_pb <= 1'b1;
            end
	 end
      end
   end
   
   //-----------------------------------------------------------------
   // fdct_buf_sel
   //-----------------------------------------------------------------
   always @(posedge CLK or posedge RST) begin
      if(RST == 1'b 1) begin
	 fdct_buf_sel_s <= 1'b 0;
      end 
      else begin
	 if(start_pb == 1'b 1) begin
            fdct_buf_sel_s <=  ~fdct_buf_sel_s;
	 end
      end
   end
   
   //-----------------------------------------------------------------------------
   // Architecture: end
   //-----------------------------------------------------------------------------
   
endmodule
