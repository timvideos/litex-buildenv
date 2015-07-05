// File ../design/CtrlSM_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name :  CtrlSM.vhd
//
// Project   : JPEG_ENC
//
// Module    : CtrlSM
//
// Content   : CtrlSM
//
// Description : CtrlSM core
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

module CtrlSM
//#(
//)  
(
 input wire 	    CLK,
 input wire 	    RST,

 //-- ouput IF
 input wire 	    outif_almost_full,

 //-- HOST IF
 input wire 	    sof,
 input wire [15:0]  img_size_x,
 input wire [15:0]  img_size_y,
 output reg 	    jpeg_ready,
 output reg 	    jpeg_busy,

 //-- FDCT
 output wire 	    fdct_start,
 input wire 	    fdct_ready,
 output wire [15:0] fdct_sm_settings_x_cnt,
 output wire [15:0] fdct_sm_settings_y_cnt,
 output wire [2:0]  fdct_sm_settings_cmp_idx,

 //-- ZIGZAG
 output wire 	    zig_start,
 input wire 	    zig_ready,
 output wire [15:0] zig_sm_settings_x_cnt,
 output wire [15:0] zig_sm_settings_y_cnt,
 output wire [2:0]  zig_sm_settings_cmp_idx,
 
 //-- Qauntizer
 output wire 	    qua_start,
 input wire 	    qua_ready,
 output wire [15:0] qua_sm_settings_x_cnt,
 output wire [15:0] qua_sm_settings_y_cnt,
 output wire [2:0]  qua_sm_settings_cmp_idx,
 
 //-- RLE
 output wire 	    rle_start,
 input wire 	    rle_ready,
 output wire [15:0] rle_sm_settings_x_cnt,
 output wire [15:0] rle_sm_settings_y_cnt,
 output wire [2:0]  rle_sm_settings_cmp_idx,
 
 //-- Huffman
 output wire 	    huf_start,
 input wire 	    huf_ready,
 output wire [15:0] huf_sm_settings_x_cnt,
 output wire [15:0] huf_sm_settings_y_cnt,
 output wire [2:0]  huf_sm_settings_cmp_idx,
 
 //-- ByteStuffer
 output wire 	    bs_start,
 input wire 	    bs_ready,
 output wire [15:0] bs_sm_settings_x_cnt,
 output wire [15:0] bs_sm_settings_y_cnt,
 output wire [2:0]  bs_sm_settings_cmp_idx,
 
 //-- JFIF GEN
 output reg 	    jfif_start, 
 input wire 	    jfif_ready,
 output reg 	    jfif_eoi,

 //-- OUT MUX
 output reg 	    out_mux_ctrl
 
);
    
    localparam NUM_STAGES = 6; // Processing block stages
    localparam CMP_MAX    = 4; // Component max
	
    /// @todo: verify correct encoding for states
    localparam
      IDLES = 1,
      JFIF  = 2,
      HORIZ = 3,
      COMP  = 4,
      VERT  = 5,
      EOI   = 6;
    
    reg [15:0] Reg_x_cnt   [0:NUM_STAGES+1];
    reg [15:0] Reg_y_cnt   [0:NUM_STAGES+1];
    reg [2:0]  Reg_cmp_idx [0:NUM_STAGES+1];
       
    reg  [2:0] 	   main_state;
    
    wire [NUM_STAGES + 1:1] start;
    wire [NUM_STAGES + 1:1] idle;
    reg 		    start1_d;    
    
    wire [NUM_STAGES:1]     start_PB;
    wire [NUM_STAGES:1]     ready_PB;
    wire [1:0] 		    fsm[NUM_STAGES:1];

    reg [15:0] 		    RSM_x_cnt;
    reg [15:0] 		    RSM_y_cnt;
    reg [2:0] 		    RSM_cmp_idx;
    
    reg 		    out_mux_ctrl_s;
    reg 		    out_mux_ctrl_s2;  
    
    // settings from the host interface
    assign fdct_sm_setting_x_cnt   = Reg_x_cnt[1];
    assign fdct_sm_setting_y_cnt   = Reg_y_cnt[1];
    assign fdct_sm_setting_cmp_idx = Reg_cmp_idx[1];

    assign zig_sm_setting_x_cnt    = Reg_x_cnt[2];
    assign zig_sm_setting_y_cnt    = Reg_y_cnt[2];
    assign zig_sm_setting_cmp_idx  = Reg_cmp_idx[2];

    assign qua_sm_setting_x_cnt    = Reg_x_cnt[3];
    assign qua_sm_setting_y_cnt    = Reg_y_cnt[3];
    assign qua_sm_setting_cmp_idx  = Reg_cmp_idx[3];

    assign rle_sm_setting_x_cnt    = Reg_x_cnt[4];
    assign rle_sm_setting_y_cnt    = Reg_y_cnt[4];
    assign rle_sm_setting_cmp_idx  = Reg_cmp_idx[4];

    assign huf_sm_setting_x_cnt    = Reg_x_cnt[5];
    assign huf_sm_setting_y_cnt    = Reg_y_cnt[5];
    assign huf_sm_setting_cmp_idx  = Reg_cmp_idx[5];
    
    assign bs_sm_setting_x_cnt     = Reg_x_cnt[6];
    assign bs_sm_setting_y_cnt     = Reg_y_cnt[6];
    assign bs_sm_setting_cmp_idx   = Reg_cmp_idx[6];

    //
    assign fdct_start  = start_PB[1];
    assign ready_PB[1] = fdct_ready;
    assign zig_start   = start_PB[2];
    assign ready_PB[2] = zig_ready;
    assign qua_start   = start_PB[3];
    assign ready_PB[3] = qua_ready;
    assign rle_start   = start_PB[4];
    assign ready_PB[4] = rle_ready;
    assign huf_start   = start_PB[5];
    assign ready_PB[5] = huf_ready;
    assign bs_start    = start_PB[6];
    assign ready_PB[6] = bs_ready;
    
    
    //---------------------------------------------------------------------------
    // CTRLSM 1..NUM_STAGES
    //---------------------------------------------------------------------------
    genvar gi;
    generate
	for(gi=1; gi < NUM_STAGES+1; gi=gi+1) begin : G_CTRL_SM
	    SingleSM
	       U_S_CTRL_SM
	       (.CLK          (CLK           ),
		.RST          (RST           ),		
		//-- from/to SM(m)   
		.start_i      (start[gi]     ),      
		.idle_o       (idle[gi]      ),		
		//-- from/to SM(m+1) 
		.idle_i       (idle[gi+1]    ),      
		.start_o      (start[gi+1]   ),		
		//-- from/to processing block
		.pb_rdy_i     (ready_PB[gi]  ),     
		.pb_start_o   (start_PB[gi]  ),		
		//-- state out
		.fsm_o        (fsm[gi]       )
		);	    
	end
    endgenerate
        
    assign idle[NUM_STAGES + 1] =  ~outif_almost_full;
    
    //-----------------------------------------------------------------
    // Regs
    //-----------------------------------------------------------------
    
    genvar  gj;
    generate for (gj=1; gj <= NUM_STAGES; gj = gj + 1) begin: G_REG_SM
    	always @(posedge CLK or posedge RST) begin
    	    if(RST == 1'b1) begin
		Reg_x_cnt[gj] <= 0;
		Reg_y_cnt[gj] <= 0;
		Reg_cmp_idx[gj] <= 0;
    	    end 
	    else begin
    		if(start[gj] == 1'b1) begin
    		    if (gj == 1) begin
    			Reg_x_cnt[gj]    <= RSM_x_cnt;
    			Reg_y_cnt[gj]    <= RSM_y_cnt;
    			Reg_cmp_idx[gj]  <= RSM_cmp_idx;
		    end
    		    else begin
    			//  @og: Reg(i) <= Reg(i-1);
			Reg_x_cnt[gj]   <= Reg_x_cnt[gj-1];
			Reg_y_cnt[gj]   <= Reg_y_cnt[gj-1];
			Reg_cmp_idx[gj] <= Reg_cmp_idx[gj-1];			
    		    end                  
    		end
    	    end
    	end	
    end
    endgenerate
    
    //-----------------------------------------------------------------
    // Main_SM
    //-----------------------------------------------------------------
    reg    start_sm;
    assign start[1] = start_sm;
    always @(posedge CLK or posedge RST) begin
	if(RST == 1'b1) begin
	    main_state      <= IDLES;
	    start_sm        <= 1'b0;  // was start(1)
	    start1_d        <= 1'b0;
	    jpeg_ready      <= 1'b0;

	    RSM_x_cnt       <= 0; 
	    RSM_y_cnt       <= 0; 
	    RSM_cmp_idx     <= 0; 
	    
	    jpeg_busy       <= 1'b0;
	    out_mux_ctrl_s  <= 1'b0;
	    out_mux_ctrl_s2 <= 1'b0;
	    jfif_eoi        <= 1'b0;
	    out_mux_ctrl    <= 1'b0;
	    jfif_start      <= 1'b0;
	end 
	else begin
	    start_sm <= 1'b0;      // default value
	    start1_d <= start_sm;
	    
	    jpeg_ready <= 1'b 0;
	    jfif_start <= 1'b 0;
	    out_mux_ctrl_s2 <= out_mux_ctrl_s;
	    out_mux_ctrl <= out_mux_ctrl_s2;
	    
	    case(main_state)
	      
              //-----------------------------
	      // IDLE
	      //-----------------------------	      
	      IDLES : begin		  
		  if(sof == 1'b1) begin
		      RSM_x_cnt      <= {16{1'b0}};
		      RSM_y_cnt      <= {16{1'b0}};
		      jfif_start     <= 1'b1;
		      out_mux_ctrl_s <= 1'b0;
		      jfif_eoi       <= 1'b0;
		      main_state     <= JFIF;
                  end
	      end
	      
	      //-----------------------------
	      // JFIF
	      //-----------------------------	      
	      JFIF : begin
		  if(jfif_ready == 1'b1) begin
		      out_mux_ctrl_s <= 1'b 1;
		      main_state     <= HORIZ;
		  end
	      end

	      //-----------------------------
	      // HORIZ
	      //-----------------------------	      
	      HORIZ : begin
		  if(RSM_x_cnt < img_size_x) begin
		      main_state <= COMP;
		  end
		  else begin
		      RSM_x_cnt  <= {16{1'b0}};
		      main_state <= VERT;
                  end
	      end

	      //-----------------------------
	      // COMP
	      //-----------------------------	     
	      COMP : begin
		  if(idle[1] == 1'b1 && start_sm == 1'b0) begin
		      if(RSM_cmp_idx < CMP_MAX) begin
		      	  start_sm <= 1'b1;
		      end
		      else begin
		      	  RSM_cmp_idx <= 0;
		          RSM_x_cnt  <= RSM_x_cnt + 16;		      
		          main_state <= HORIZ;		      
		      end
		  end
		  
	      end
	      
	      //-----------------------------
	      // VERT
	      //-----------------------------	      
	      VERT : begin
		  if(RSM_y_cnt < (img_size_y - 8)) begin
		      RSM_x_cnt  <= {16{1'b0}};
		      RSM_y_cnt  <= RSM_y_cnt + 8;
		      main_state <= HORIZ;
                  end
		  else begin
		      if (idle[NUM_STAGES+1:1] == {(NUM_STAGES+1){1'b1}}) begin
		        main_state     <= EOI;
		        jfif_eoi       <= 1'b1;
		        out_mux_ctrl_s <= 1'b0;
		        jfif_start     <= 1'b1;
		      end
		  end
	      end

	      //-----------------------------
	      // VERT
	      //-----------------------------	      
	      EOI : begin
		  if(jfif_ready == 1'b1) begin
		      jpeg_ready <= 1'b1;
		      main_state <= IDLES;
		  end
	      end

	      //-----------------------------
	      // others
	      //-----------------------------	      
	      default : begin
		  main_state <= IDLES;
	      end
	    endcase

	    if(start1_d == 1'b1) begin
	      	RSM_cmp_idx <= RSM_cmp_idx + 1;
	    end
	    
	    if(main_state == IDLES) begin
		jpeg_busy <= 1'b0;
	    end	    
	    else begin
		jpeg_busy <= 1'b1;
	    end
	    
	end
    end
    
endmodule
