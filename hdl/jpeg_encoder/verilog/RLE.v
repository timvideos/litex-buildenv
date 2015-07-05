// File ../design/RLE_c.VHD translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
//                          COPYRIGHT (C) 2009                                --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// Title       : RLE                                                          --
// Design      : MDCT CORE                                                    --
// Author      : Michal Krepa                                                 --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
// File        : RLE.VHD                                                      --
// Created     : Wed Mar 04 2009                                              --
//                                                                            --
//------------------------------------------------------------------------------
//                                                                            --
//  Description : Run Length Encoder                                          --
//                Baseline Entropy Coding                                     --
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

module rle
(
 input wire 		     rst,
 input wire 		     clk,
 input wire [RAMDATA_W-1:0]  di,
 input wire 		     start_pb,
 input wire 		     sof,
 input wire [2:0] 	     rss_cmp_idx,
 output reg [3:0] 	     runlength,
 output wire [3:0] 	     size,
 output wire [RAMDATA_W-1:0] amplitude,
 output reg 		     dovalid,
 output wire [5:0] 	     rd_addr
);

   parameter [31:0] RAMADDR_W = 6;
   parameter [31:0] RAMDATA_W = 12;

   parameter SIZE_REG_C = 4;
   parameter ZEROS_32_C = 0;
   
   reg [RAMDATA_W - 1:0]       prev_dc_reg_0 = 0;
   reg [RAMDATA_W - 1:0]       prev_dc_reg_1 = 0;
   reg [RAMDATA_W - 1:0]       prev_dc_reg_2 = 0;
   reg [RAMDATA_W - 1:0]       prev_dc_reg_3 = 0;
    
   reg [RAMDATA_W:0] 	       acc_reg = 0;
   reg [SIZE_REG_C - 1:0]      size_reg = 0;
   reg [RAMDATA_W:0] 	       ampli_vli_reg = 0;
   reg [3:0] 		       runlength_reg = 0;
   reg 			       dovalid_reg = 1'b0;
   reg [5:0] 		       zero_cnt = 0;
    
   reg [5:0] 		       wr_cnt_d1 = 0;
   reg [5:0] 		       wr_cnt = 0;
   reg [5:0] 		       rd_cnt = 0;
   reg 			       rd_en = 1'b0;
    
   reg 			       divalid = 1'b0;
   reg 			       divalid_en = 1'b0;
    
   reg 			       zrl_proc = 1'b0;
   reg [RAMDATA_W - 1:0]       zrl_di = 0;
   
   assign size = (size_reg);
   assign amplitude = (ampli_vli_reg[11:0]);
   assign rd_addr = (rd_cnt);
   
    //-----------------------------------------
    // MAIN PROCESSING
    //-----------------------------------------
    always @(posedge clk or posedge rst) begin
	if(rst == 1'b1) begin
	    wr_cnt_d1 <= {6{1'b0}};
            prev_dc_reg_0 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
            prev_dc_reg_1 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
            prev_dc_reg_2 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
            prev_dc_reg_3 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
            dovalid_reg <= 1'b0;
            acc_reg <= {(((RAMDATA_W))-((0))+1){1'b0}};
            runlength_reg <= {4{1'b0}};
            runlength <= {4{1'b0}};
            dovalid <= 1'b0;
            zero_cnt <= {6{1'b0}};
            zrl_proc <= 1'b0;
            rd_en <= 1'b0;
            rd_cnt <= {6{1'b0}};
            divalid_en <= 1'b0;
        end 
	else begin
	    dovalid_reg <= 1'b0;
	    runlength_reg <= {4{1'b0}};
	    wr_cnt_d1 <= wr_cnt;
	    runlength <= (runlength_reg);
	    dovalid <= dovalid_reg;
	    divalid <= rd_en;
	 
	    if(start_pb == 1'b1) begin
		rd_cnt <= {6{1'b0}};
                rd_en <= 1'b1;
                divalid_en <= 1'b1;
            end	    
            if(divalid == 1'b1 && wr_cnt == 63) begin
	        divalid_en <= 1'b0;
	    end
	 
	    // input read enable
	    if(rd_en == 1'b1) begin
		if(rd_cnt == (64 - 1)) begin
		    rd_cnt <= {6{1'b0}};
		    rd_en <= 1'b 0;
                end
                else begin
                   rd_cnt <= rd_cnt + 1;
                end
	    end 
	 
	    // input data valid
	    if(divalid == 1'b1) begin
		wr_cnt <= wr_cnt + 1;
		// first DCT coefficient received, DC data
		if(wr_cnt == 0) begin
		    
		    // differental coding of DC data per component
		    case(rss_cmp_idx)
		      3'b000, 3'b001 : begin
			  // @todo verify?
			  //acc_reg <= RESIZE(SIGNED(di),RAMDATA_W+1) - RESIZE(prev_dc_reg_0,RAMDATA_W+1);
			  acc_reg <= $signed(di) - prev_dc_reg_0;	     
			  prev_dc_reg_0 <= (di);
		      end
		      3'b010 : begin
			  // @todo: verify?              
			  //acc_reg <= RESIZE(SIGNED(di),RAMDATA_W+1) - RESIZE(prev_dc_reg_1,RAMDATA_W+1);
			  acc_reg <= $signed(di) - prev_dc_reg_1;
			  prev_dc_reg_1 <= (di);
		      end
		      3'b011 : begin
			  // @todo: verify?            
			  //acc_reg <= RESIZE(SIGNED(di),RAMDATA_W+1) - RESIZE(prev_dc_reg_2,RAMDATA_W+1);
			  acc_reg <= $signed(di) - prev_dc_reg_2;	     
			  prev_dc_reg_2 <= (di);
		      end
		      default : begin
		      end
		    endcase
		    
		    runlength_reg <= {4{1'b0}};
		    dovalid_reg <= 1'b 1;
		    // AC coefficient
		end
		else begin
		    // zero AC
		    if(((di)) == 0) begin
			// EOB
			if(wr_cnt == 63) begin
			    acc_reg <= {(((RAMDATA_W))-((0))+1){1'b0}};
			runlength_reg <= {4{1'b0}};
			dovalid_reg <= 1'b1;
			// no EOB
		    end
			else begin
			    zero_cnt <= zero_cnt + 1;
			end
			// non-zero AC
		    end
		    else begin
			// normal RLE case
			if(zero_cnt <= 15) begin
			    // @todo: verify?  
			    //acc_reg        <= RESIZE(SIGNED(di),RAMDATA_W+1);  
			    acc_reg <= $signed(di);             
			    runlength_reg <= zero_cnt[3:0];
			    zero_cnt <= {6{1'b0}};
			    dovalid_reg <= 1'b1;
			    // zero_cnt > 15
			end
			else begin
			    // generate ZRL
			    acc_reg <= {(((RAMDATA_W))-((0))+1){1'b0}};
    		    	    runlength_reg <= 4'hF;
			    zero_cnt <= zero_cnt - 16;
			    dovalid_reg <= 1'b1;
          		    // stall input until ZRL is handled
    		   	    zrl_proc <= 1'b1;
			    zrl_di <= di;
			    divalid <= 1'b0;
			    rd_cnt <= rd_cnt;
		        end
		    end
		end
	    end
	  
	    // ZRL processing
	    if(zrl_proc == 1'b1) begin
		if(zero_cnt <= 15) begin
		    
		    // @todo: verify
		    //acc_reg        <= RESIZE(SIGNED(zrl_di),RAMDATA_W+1);
		    acc_reg = $signed(zrl_di);	    
		    runlength_reg <= zero_cnt[3:0];
		    
		    if(((zrl_di)) == 0) begin
			//zero_cnt     <= to_unsigned(1,zero_cnt'length);
			zero_cnt <= 1;
		    end
		    else begin
			zero_cnt <= {6{1'b0}};
		end
		    
		    dovalid_reg <= 1'b1;
		    divalid <= divalid_en;
		    // continue input handling
		    zrl_proc <= 1'b0;
		    // zero_cnt > 15
		end
		else begin
		    // generate ZRL
		    acc_reg <= {(((RAMDATA_W))-((0))+1){1'b0}};
                    runlength_reg <= 4'hF;
                    zero_cnt <= zero_cnt - 16;
                    dovalid_reg <= 1'b1;
                    divalid <= 1'b0;
                    rd_cnt <= rd_cnt;
                end
	    end
	  
	    // start of 8x8 block processing
	    if(start_pb == 1'b1) begin
		zero_cnt <= {6{1'b0}};
                wr_cnt <= {6{1'b0}};
            end
	    if(sof == 1'b1) begin
                prev_dc_reg_0 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
                prev_dc_reg_1 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
                 prev_dc_reg_2 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
                prev_dc_reg_3 <= {(((RAMDATA_W - 1))-((0))+1){1'b0}};
             end
	end
    end

    //-----------------------------------------------------------------
    // Entropy Coder
    //-----------------------------------------------------------------
    always @(posedge clk or posedge rst) begin
	if(rst == 1'b1) begin
	    ampli_vli_reg <= {(((RAMDATA_W))-((0))+1){1'b0}};
      	    size_reg <= {(((SIZE_REG_C - 1))-((0))+1){1'b0}};
        end 
	else begin
	    // perform VLI (variable length integer) encoding for Symbol-2 (Amplitude)
	    // positive input
	    if(acc_reg >= 0) begin
		ampli_vli_reg <= acc_reg;
	    end
	    else begin
		ampli_vli_reg <= acc_reg - 1;	 
	    end
       
	    // compute Symbol-1 Size	    
	    // clog2 implementation
	    if (acc_reg == -1) begin
		size_reg <= 1;
	    end
	    else if (acc_reg < -1 && acc_reg > -4) begin
		size_reg <= 2;
	    end
	    else if (acc_reg < -3 && acc_reg > -8) begin
		size_reg <= 3;
	    end
	    else if (acc_reg < -7 && acc_reg > -16) begin
		size_reg <= 4;
	    end
	    else if (acc_reg < -15 && acc_reg > -32) begin
		size_reg <= 5;
	    end
	    else if (acc_reg < -31 && acc_reg > -64) begin
		size_reg <= 6;
	    end
	    else if (acc_reg < -63 && acc_reg > -128) begin
		size_reg <= 7;
	    end
	    else if (acc_reg < -127 && acc_reg > -256) begin
		size_reg <= 8;
	    end
	    else if (acc_reg < -255 && acc_reg > -512) begin
		size_reg <= 9;
	    end
	    else if (acc_reg < -511 && acc_reg > -1024) begin
		size_reg <= 10;
	    end
	    else if (acc_reg < -1023 && acc_reg > -2048) begin
		size_reg <= 11;
	    end
       
	    // compute Symbol-1 Size
	    // positive input
	    // simple clog2
	    if (acc_reg == 1) begin
		size_reg <= 1;
	    end
	    else if (acc_reg > 1 && acc_reg < 4) begin
		size_reg <= 2;
	    end
	    else if (acc_reg > 3 && acc_reg < 8) begin
		size_reg <= 3;
	    end
	    else if (acc_reg > 7 && acc_reg < 16) begin
		size_reg <= 4;
	    end
	    else if (acc_reg > 15 && acc_reg < 32) begin
		size_reg <= 5;
	    end
	    else if (acc_reg > 31 && acc_reg < 64) begin
		size_reg <= 6;
	    end
	    else if (acc_reg > 63 && acc_reg < 128) begin
		size_reg <= 7;
	    end
	    else if (acc_reg > 127 && acc_reg < 256) begin
		size_reg <= 8;
	    end
	    else if (acc_reg > 255 && acc_reg < 512) begin
		size_reg <= 9;
	    end
	    else if (acc_reg > 511 && acc_reg < 1024) begin
		size_reg <= 10;
	    end
	    else if (acc_reg > 1023 && acc_reg < 2048) begin
		size_reg <= 11;
	    end
	    
	    // DC coefficient amplitude=0 case OR EOB
	    if(acc_reg == 0) begin
		size_reg <= (0);
	    end
	end
    end


endmodule
