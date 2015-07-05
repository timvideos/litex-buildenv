// File ../design/FDCT_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  FDCT.vhd
//
// Project   : JPEG_ENC
//
// Module    : FDCT
//
// Content   : FDCT
//
// Description : 2D Discrete Cosine Transform
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

module FDCT
(
 input wire 	    CLK,
 input wire 	    RST,
 //-- CTRL
 input wire 	    start_pb,
 output reg 	    ready_pb,

 //-- BUF_FIFO
 output wire 	    bf_fifo_rd,
 input wire [23:0]  bf_fifo_q,
 input wire 	    bf_fifo_hf_full,

 //-- ZIG ZAG
 input wire 	    zz_buf_sel,
 input wire [5:0]   zz_rd_addr,
 output wire [11:0] zz_data,
 input wire 	    zz_rden,

 //-- HOST
 input wire [15:0]  img_size_x,
 input wire [15:0]  img_size_y,
 input wire 	    sof
);
        
    localparam C_Y_1   = 4899  ;   
    localparam C_Y_2   = 9617  ;
    localparam C_Y_3   = 1868  ;
    localparam C_Cb_1  = -2764 ;
    localparam C_Cb_2  = -5428 ;
    localparam C_Cb_3  = 8192  ;
    localparam C_Cr_1  = 8192  ;
    localparam C_Cr_2  = -6860 ;
    localparam C_Cr_3  = -1332 ; 


    reg [7:0] 	    mdct_data_in;
    wire 	    mdct_idval;
    wire 	    mdct_odval;
    wire [11:0]     mdct_data_out;
    
    wire 	    odv1;
    wire [11:0]     dcto1;
    reg [15:0] 	    x_pixel_cnt;
    reg [15:0] 	    y_line_cnt;
    wire [31:0]     rd_addr;
    reg [6:0] 	    input_rd_cnt;
    
    reg 	    rd_en;
    reg 	    rd_en_d1;
    wire [31:0]     rdaddr;
    
    reg 	    bf_dval;
    reg 	    bf_dval_m1;
    reg 	    bf_dval_m2;
    reg 	    bf_dval_m3;    
    
    wire [11:0]     dbuf_data;
    wire [11:0]     dbuf_q;
    wire 	    dbuf_we;
    wire [6:0] 	    dbuf_waddr;
    wire [6:0] 	    dbuf_raddr;

    reg [5:0] 	    wr_cnt;    
    reg [2:0] 	    xw_cnt;
    reg [2:0] 	    yw_cnt;
    wire [11:0]     dbuf_q_z1;
    
    parameter C_SIMA_ASZ = 9;
    wire [C_SIMA_ASZ - 1:0] sim_rd_addr;
    
    reg [23:0] 	    Y_Reg_1;
    reg [23:0] 	    Y_Reg_2;
    reg [23:0] 	    Y_Reg_3;
    
    reg [23:0] 	    Cb_Reg_1;
    reg [23:0] 	    Cb_Reg_2;
    reg [23:0] 	    Cb_Reg_3;
    reg [23:0] 	    Cr_Reg_1;
    reg [23:0] 	    Cr_Reg_2;
    reg [23:0] 	    Cr_Reg_3;
    
    reg [23:0] 	    Y_Reg;
    reg [23:0] 	    Cb_Reg;
    reg [23:0] 	    Cr_Reg;
    
    wire [8:0] 	    R_s;
    wire [8:0] 	    G_s;
    wire [8:0] 	    B_s;
    
    wire [7:0] 	    Y_8bit;
    wire [7:0] 	    Cb_8bit;
    wire [7:0] 	    Cr_8bit;
    reg [2:0] 	    cmp_idx;
    
    reg [2:0] 	    cur_cmp_idx;
    reg [2:0] 	    cur_cmp_idx_d1;
    reg [2:0] 	    cur_cmp_idx_d2;
    reg [2:0] 	    cur_cmp_idx_d3;
    reg [2:0] 	    cur_cmp_idx_d4;
    reg [2:0] 	    cur_cmp_idx_d5;
    reg [2:0] 	    cur_cmp_idx_d6;
    reg [2:0] 	    cur_cmp_idx_d7;
    reg [2:0] 	    cur_cmp_idx_d8;
    reg [2:0] 	    cur_cmp_idx_d9;
    
    reg 	    fifo1_rd;
    wire 	    fifo1_wr;
    wire [11:0]     fifo1_q;
    wire 	    fifo1_full;
    wire 	    fifo1_empty;
    wire [9:0] 	    fifo1_count;
    reg [5:0] 	    fifo1_rd_cnt;
    reg 	    fifo1_q_dval;
    wire [11:0]     fifo_data_in;    
    reg 	    fifo_rd_arm;
    
    reg 	    eoi_fdct;
    reg 	    bf_fifo_rd_s;
    reg 	    start_int;
    reg [4:0] 	    start_int_d;
    
    wire [23:0]     fram1_data;
    wire [23:0]     fram1_q;
    wire 	    fram1_we;
    reg [6:0] 	    fram1_waddr;
    reg [6:0] 	    fram1_raddr;
    reg [8:0] 	    fram1_rd_d;
    reg 	    fram1_rd;
    
    reg 	    rd_started;    
    reg 	    writing_en;
    
    wire 	    fram1_q_vld;
    reg [2:0] 	    fram1_line_cnt;
    wire [2:0] 	    fram1_line_cnt_p1;
    reg [2:0] 	    fram1_pix_cnt;  
    
    assign zz_data    = dbuf_q;
    assign bf_fifo_rd = bf_fifo_rd_s;
    
    //-----------------------------------------------------------------
    // FRAM1 (Frame RAM, hold 16x8)
    //-----------------------------------------------------------------
    RAMZ
      #(.RAMADDR_W(7), .RAMDATA_W(24))
    U_FRAM1
      (.d     (fram1_data),
       .waddr (fram1_waddr),
       .raddr (fram1_raddr),
       .we    (fram1_we),
       .rd    (fram1_rd),
       .clk   (CLK),
       .q     (fram1_q)
       );
       
    assign fram1_we = bf_dval;           // moving a new block
    assign fram1_data = bf_fifo_q;       // data from BUF_FIFO
    assign fram1_q_vld = fram1_rd_d[5];  // onto the next ...
    
    //-----------------------------------------------------------------
    // FRAM1 address process
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b 1) begin
	    fram1_waddr <= {7{1'b0}};
        end 
	else begin
	    if(fram1_we == 1'b1) begin
		fram1_waddr <= fram1_waddr + 1;
	    end
	end
    end
    
    //-----------------------------------------------------------------
    // Intermidiate (I)RAM read process 
    //-----------------------------------------------------------------

    // @todo: TEMP DEBUG remove
    m_fdct_read_proc_sm_monitor U_MON
      (.clock           (CLK),
       .reset           (RST),
       .sof             (sof),
       .start_int       (start_int),
       .x_pixel_cnt     (x_pixel_cnt),
       .y_line_cnt      (y_line_cnt),
       .img_size_x      (img_size_x),
       .img_size_y      (img_size_y),
       .cmp_idx         (cmp_idx),
       .cur_cmp_idx     (cur_cmp_idx),
       .rd_started      (rd_started),
       .bf_fifo_hf_full (bf_fifo_hf_full),
       .fram1_rd        (fram1_rd),
       .fram1_raddr     (fram1_raddr),
       .fram1_ln_cnt    (fram1_line_cnt),
       .fram1_px_cnt    (fram1_pix_cnt),
       .fram1_we        (fram1_we),
       .fram1_waddr     (fram1_waddr),
       .midv            (mdct_idval),
       .modv            (mdct_odval),
       .zz_rd           (zz_rden),
       .zz_raddr        (zz_rd_addr)
       );
       
    assign fram1_line_cnt_p1 = fram1_line_cnt + 1;
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    rd_en        <= 1'b0;
	    rd_en_d1     <= 1'b0;
	    x_pixel_cnt  <= {16{1'b0}};
	    y_line_cnt   <= {16{1'b0}};
	    input_rd_cnt <= {7{1'b0}};
	    cmp_idx      <= {3{1'b0}};
	    
	    cur_cmp_idx <= {3{1'b0}};
	    cur_cmp_idx_d1 <= {3{1'b0}};
	    cur_cmp_idx_d2 <= {3{1'b0}};
	    cur_cmp_idx_d3 <= {3{1'b0}};
	    cur_cmp_idx_d4 <= {3{1'b0}};
	    cur_cmp_idx_d5 <= {3{1'b0}};
	    cur_cmp_idx_d6 <= {3{1'b0}};
	    cur_cmp_idx_d7 <= {3{1'b0}};
	    cur_cmp_idx_d8 <= {3{1'b0}};
	    cur_cmp_idx_d9 <= {3{1'b0}};
	    
	    eoi_fdct <= 1'b0;
	    start_int <= 1'b0;
	    bf_fifo_rd_s <= 1'b0;
	    bf_dval <= 1'b0;
	    bf_dval_m1 <= 1'b0;
	    bf_dval_m2 <= 1'b0;
	    
	    fram1_rd <= 1'b 0;
	    fram1_rd_d <= {9{1'b0}};
	    start_int_d <= {5{1'b0}};
	    fram1_raddr <= {7{1'b0}};
	    fram1_line_cnt <= {3{1'b0}};
	    fram1_pix_cnt <= {3{1'b0}};
	end 
	else begin
	    rd_en_d1 <= rd_en;
	    
	    cur_cmp_idx_d1 <= cur_cmp_idx;
	    cur_cmp_idx_d2 <= cur_cmp_idx_d1;
	    cur_cmp_idx_d3 <= cur_cmp_idx_d2;
	    cur_cmp_idx_d4 <= cur_cmp_idx_d3;
	    cur_cmp_idx_d5 <= cur_cmp_idx_d4;
	    cur_cmp_idx_d6 <= cur_cmp_idx_d5;
	    cur_cmp_idx_d7 <= cur_cmp_idx_d6;
	    cur_cmp_idx_d8 <= cur_cmp_idx_d7;
	    cur_cmp_idx_d9 <= cur_cmp_idx_d8;
	    
	    start_int  <= 1'b0;
	    bf_dval_m3 <= bf_fifo_rd_s;
	    bf_dval_m2 <= bf_dval_m3;
	    bf_dval_m1 <= bf_dval_m2;
	    bf_dval    <= bf_dval_m1;
	    
	    fram1_rd_d <= {fram1_rd_d[9-2:0], fram1_rd};
	    start_int_d <= {start_int_d[5-2:0], start_int};

	    //--------------------------------------------------------
	    // SOF or internal self-start
	    if((sof == 1'b1 || start_int == 1'b1)) begin
		input_rd_cnt <= {7{1'b0}};
                // enable BUF_FIFO/FRAM1 reading
                rd_started <= 1'b1;
            
	        // component index
                if(cmp_idx == (4 - 1)) begin
		    cmp_idx <= {3{1'b0}};
            
	            // horizontal block counter
                    if(x_pixel_cnt == (((img_size_x)) - 16)) begin
		        x_pixel_cnt <= {16{1'b0}};
            
	               // vertical block counter
                       if(y_line_cnt == (((img_size_y)) - 8)) begin
		           y_line_cnt <= {16{1'b0}};
            
  	                  // set end of image flag
                          eoi_fdct <= 1'b1;
                       end
                       else begin
		           y_line_cnt <= y_line_cnt + 8;
                       end
                    end
                    else begin
		        x_pixel_cnt <= x_pixel_cnt + 16;
                    end
                end
                else begin
		    cmp_idx <= cmp_idx + 1;
                end
	    
                cur_cmp_idx <= cmp_idx;
	    end // end sof == 1 or start_int == 1
	    
	    //--------------------------------------------------------	    
	    // wait until FIFO becomes half full but only for component 0
	    // as we read buf FIFO only during component 0
	    if(rd_started == 1'b1 && (bf_fifo_hf_full == 1'b1 || cur_cmp_idx > 1)) begin
		rd_en      <= 1'b1;
		rd_started <= 1'b0;
	    end

	    // default values, assigned below
	    bf_fifo_rd_s <= 1'b0;
	    fram1_rd     <= 1'b0;

	    //--------------------------------------------------------
	    // stall reading from input FIFO and writing to output FIFO 
	    // when output FIFO is almost full
	    if(rd_en == 1'b1 && (fifo1_count < (512 - 64)) && 
	       (bf_fifo_hf_full == 1'b1 || cur_cmp_idx > 1)) begin
		// read request goes to BUF_FIFO only for component 0. 
		if(cur_cmp_idx < 2) begin
		    bf_fifo_rd_s <= 1'b1;
		end
		// count number of samples read from input in one run
		if(input_rd_cnt == (64 - 1)) begin
		    rd_en <= 1'b0;
		    // internal restart
		    start_int <= 1'b1 &  ~eoi_fdct;
		    eoi_fdct <= 1'b0;
		end
		else begin
		    input_rd_cnt <= input_rd_cnt + 1;
		end
		// FRAM read enable
		fram1_rd <= 1'b1;
	    end
	    //--------------------------------------------------------


	    //--------------------------------------------------------
	    // increment FRAM1 read address according to subsampling
	    // idea is to extract 8x8 from 16x8 block
	    // there are two luminance blocks left and right
	    // there is 2:1 subsampled Cb block
	    // there is 2:1 subsampled Cr block
	    // subsampling done as simple decimation by 2 wo/ averaging
	    if(sof == 1'b1) begin 
		fram1_raddr    <= {7{1'b0}};
                fram1_line_cnt <= {3{1'b0}};
                fram1_pix_cnt  <= {3{1'b0}};
	    end
	    else if(start_int_d[4] == 1'b1) begin
		fram1_line_cnt <= {3{1'b0}};
		fram1_pix_cnt  <= {3{1'b0}};
		 
		case(cur_cmp_idx_d4)
                   // Y1, Cr, Cb
		   3'b000, 3'b010, 3'b011 : begin
		       fram1_raddr <= {7{1'b0}};
		   end
		  // Y2		  
		   3'b001 : begin
		       fram1_raddr <= 64;
		   end
		   default : begin
		   end
	        endcase
	     end
	    
	    else if(fram1_rd_d[4] == 1'b1) begin
		if(fram1_pix_cnt == (8 - 1)) begin
		    fram1_pix_cnt <= {3{1'b0}};
		    if(fram1_line_cnt == (8 - 1)) begin
		        fram1_line_cnt <= {3{1'b0}};
                    end
		    else begin
		        fram1_line_cnt <= fram1_line_cnt + 1;
		    end
                end
	        else begin
	            fram1_pix_cnt <= fram1_pix_cnt + 1;
	        end

		
		case(cur_cmp_idx_d6)
		  3'b000, 3'b001 : begin
	              fram1_raddr <= (((fram1_raddr)) + 1);
		  end
		  3'b010, 3'b011 : begin
	              if(fram1_pix_cnt == (4 - 1)) begin
	    		  fram1_raddr <= {1'b1,fram1_line_cnt,3'b000};
	              end
	              else if(fram1_pix_cnt == (8 - 1)) begin
	    		  if(fram1_line_cnt == (8 - 1)) begin
	    		      fram1_raddr <= {1'b0,3'b000,3'b000};
	    		  end
	    		  else begin
	    		      fram1_raddr <= {1'b0, fram1_line_cnt_p1, 3'b000};
	    		  end
	              end
	              else begin
	    		  fram1_raddr <= fram1_raddr + 2;
	              end
		  end
		  default : begin
		  end
		endcase
	    end // if(sof == 1'b1) 
	    //--------------------------------------------------------
	    
	end
    end
    
    //-----------------------------------------------------------------
    // FDCT with input level shift
    //-----------------------------------------------------------------
    MDCT U_MDCT
      (.clk     (CLK),
       .rst     (RST),
       .dcti    (mdct_data_in),
       .idv     (mdct_idval),
       .odv     (mdct_odval),
       .dcto    (mdct_data_out),
       .odv1    (odv1),
       .dcto1   (dcto1)
       );
    
    assign mdct_idval = fram1_rd_d[8];
    
    assign R_s = {1'b0, fram1_q[7:0]};
    assign G_s = {1'b0, fram1_q[15:8]};
    assign B_s = {1'b0, fram1_q[23:16]};
    
    //-----------------------------------------------------------------
    // Mux1
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    mdct_data_in <= {8{1'b0}};
        end 
	else begin
	    case(cur_cmp_idx_d9)
	      3'b000, 3'b001 : begin
		  mdct_data_in <= (Y_8bit);
	      end
	      3'b010 : begin
		  mdct_data_in <= (Cb_8bit);
	      end
	      3'b011 : begin
		  mdct_data_in <= (Cr_8bit);
	      end
	      default : begin
	      end
	    endcase
	end
    end

    //-----------------------------------------------------------------
    // FIFO1
    //-----------------------------------------------------------------
    FIFO
      #(.DATA_WIDTH(12), .ADDR_WIDTH(9))
    U_FIFO1      
      (.rst      (RST           ),
       .clk      (CLK	        ),
       .rinc     (fifo1_rd      ),
       .winc     (fifo1_wr      ),
       .datai    (fifo_data_in  ),   
       .datao    (fifo1_q       ),
       .fullo    (fifo1_full    ),
       .emptyo   (fifo1_empty   ),
       .count    (fifo1_count   )
       );
    
    assign fifo1_wr = mdct_odval;
    assign fifo_data_in = mdct_data_out;
    
    //-----------------------------------------------------------------
    // FIFO1 rd controller
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    fifo1_rd     <= 1'b0;
	    fifo_rd_arm  <= 1'b0;
	    fifo1_rd_cnt <= {6{1'b0}};
	    fifo1_q_dval <= 1'b0;
	end 
	else begin
	    fifo1_rd <= 1'b0;
	    fifo1_q_dval <= fifo1_rd;
	    
	    if(start_pb == 1'b1) begin
		fifo_rd_arm <= 1'b1;
		fifo1_rd_cnt <= {6{1'b0}};
	    end
	    
	    if(fifo_rd_arm == 1'b1) begin
		if(fifo1_rd_cnt == (64 - 1)) begin
		    fifo_rd_arm <= 1'b0;
		    fifo1_rd    <= 1'b1;
		end
		else if(fifo1_empty == 1'b0) begin
		    fifo1_rd     <= 1'b1;
		    fifo1_rd_cnt <= fifo1_rd_cnt + 1;
		end
	    end
	end
    end

    //-----------------------------------------------------------------
    // write counter
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    wr_cnt     <= {6{1'b0}};
            ready_pb   <= 1'b0;
            xw_cnt     <= {3{1'b0}};
       	    yw_cnt     <= {3{1'b0}};
            writing_en <= 1'b0;
        end 
        else begin
	    ready_pb <= 1'b0;
	    
	    if(start_pb == 1'b1) begin
                wr_cnt     <= {6{1'b0}};
                xw_cnt     <= {3{1'b0}};
                yw_cnt     <= {3{1'b0}};
                writing_en <= 1'b1;
            end
	    
	    if(writing_en == 1'b1) begin
                if(fifo1_q_dval == 1'b1) begin		    
	    	    if(wr_cnt == (64 - 1)) begin
	    	        wr_cnt <= {6{1'b0}};
	    	        ready_pb <= 1'b1;
                        writing_en <= 1'b0;
                    end
                    else begin
	    	        wr_cnt <= wr_cnt + 1;
	    	    end
		    
	    	    if(yw_cnt == (8 - 1)) begin
	    	        yw_cnt <= {3{1'b0}};
	    	        xw_cnt <= xw_cnt + 1;
                        end
	    	    else begin
	    	        yw_cnt <= yw_cnt + 1;
	    	    end
		    
                end
	    end
	end
    end

    //-----------------------------------------------------------------
    // RGB to YCbCr conversion
    //-----------------------------------------------------------------
    always @(posedge CLK or posedge RST) begin	
	if(RST == 1'b1) begin	    
	    Y_Reg_1 <= {1{1'b0}};
	    Y_Reg_2 <= {1{1'b0}};
	    Y_Reg_3 <= {1{1'b0}};
            Cb_Reg_1 <= {1{1'b0}};
            Cb_Reg_2 <= {1{1'b0}};
            Cb_Reg_3 <= {1{1'b0}};
            Cr_Reg_1 <= {1{1'b0}};
            Cr_Reg_2 <= {1{1'b0}};
            Cr_Reg_3 <= {1{1'b0}};
            Y_Reg <= {1{1'b0}};
            Cb_Reg <= {1{1'b0}};
            Cr_Reg <= {1{1'b0}};
        end 
	else begin
            Y_Reg_1 <= R_s * C_Y_1;
            Y_Reg_2 <= G_s * C_Y_2;
            Y_Reg_3 <= B_s * C_Y_3;
            Cb_Reg_1 <= R_s * C_Cb_1;
            Cb_Reg_2 <= G_s * C_Cb_2;
            Cb_Reg_3 <= B_s * C_Cb_3;
            Cr_Reg_1 <= R_s * C_Cr_1;
            Cr_Reg_2 <= G_s * C_Cr_2;
            Cr_Reg_3 <= B_s * C_Cr_3;
	    
            Y_Reg <= Y_Reg_1 + Y_Reg_2 + Y_Reg_3;            	
            Cb_Reg <= Cb_Reg_1 + Cb_Reg_2 + Cb_Reg_3 + (128*16384);
            Cr_Reg <= Cr_Reg_1 + Cr_Reg_2 + Cr_Reg_3 + (128*16384);
	end
    end
    
    assign Y_8bit  = (Y_Reg[21:14]);
    assign Cb_8bit = (Cb_Reg[21:14]);
    assign Cr_8bit = (Cr_Reg[21:14]);
    
    //-----------------------------------------------------------------
    // DBUF
    //-----------------------------------------------------------------
    RAMZ
      #(.RAMADDR_W(7), .RAMDATA_W(12))
    U_RAMZ
      (.d      (dbuf_data  ),
       .waddr  (dbuf_waddr ),
       .raddr  (dbuf_raddr ),
       .we     (dbuf_we	   ),
       .clk    (CLK        ),         
       .q      (dbuf_q     ) 
       );
    
  assign dbuf_data  = fifo1_q;
  assign dbuf_we    = fifo1_q_dval;
  assign dbuf_waddr = {( ~zz_buf_sel),{yw_cnt, xw_cnt}};
  assign dbuf_raddr = {zz_buf_sel, zz_rd_addr};
    

endmodule
