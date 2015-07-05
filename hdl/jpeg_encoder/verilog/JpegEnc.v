// File ../design/JpegEnc_c.vhd translated with vhd2vl v2.4 VHDL to Verilog RTL translator
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
// File Name : JpegEnc.vhd
//
// Project   : JPEG_ENC
//
// Module    : JpegEnc
//
// Content   : JPEG Encoder Top Level
//
// Description : 
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


module JpegEnc
#(
  parameter C_PIXEL_BITS = 24
)  
(
 input wire 			 CLK,
 input wire 			 RST,

 input wire [31:0] 		 OPB_ABus,
 input wire [3:0] 		 OPB_BE,
 input wire [31:0] 		 OPB_DBus_in,
 input wire 			 OPB_RNW,
 input wire 			 OPB_select,
 output wire [31:0] 		 OPB_DBus_out,
 output wire 			 OPB_XferAck,
 output wire 			 OPB_retry,
 output wire 			 OPB_toutSup,
 output wire 			 OPB_errAck,

 input wire [C_PIXEL_BITS - 1:0] iram_wdata,
 input wire 			 iram_wren,
 output wire 			 iram_fifo_afull,
 output wire [7:0] 		 ram_byte,
 output wire 			 ram_wren,
 output wire [23:0] 		 ram_wraddr,
 input wire 			 outif_almost_full,
 output wire [23:0] 		 frame_size
);

    wire [7:0] 			 qdata;
    wire [6:0] 			 qaddr;
    wire 			 qwren;
    wire 			 jpeg_ready;
    wire 			 jpeg_busy;
    wire [9:0] 			 outram_base_addr;
    wire [23:0] 		 num_enc_bytes;
    wire [15:0] 		 img_size_x;
    wire [15:0] 		 img_size_y;
    wire 			 sof;
    wire 			 jpg_iram_rden;
    wire [31:0] 		 jpg_iram_rdaddr;
    wire [23:0] 		 jpg_iram_rdata;
    wire 			 fdct_start;
    wire 			 fdct_ready;
    wire 			 zig_start;
    wire 			 zig_ready;
    wire 			 qua_start;
    wire 			 qua_ready;
    wire 			 rle_start;
    wire 			 rle_ready;
    wire 			 huf_start;
    wire 			 huf_ready;
    wire 			 bs_start;
    wire 			 bs_ready;
    wire 			 zz_buf_sel;
    wire [5:0] 			 zz_rd_addr;
    wire [11:0] 		 zz_data;
    wire 			 rle_buf_sel;
    wire [5:0] 			 rle_rdaddr;
    wire [11:0] 		 rle_data;
    wire 			 qua_buf_sel;
    wire [5:0] 			 qua_rdaddr;
    wire [11:0] 		 qua_data;
    wire 			 huf_buf_sel;
    wire [5:0] 			 huf_rdaddr;
    wire 			 huf_rden;
    wire [3:0] 			 huf_runlength;
    wire [3:0] 			 huf_size;
    wire [11:0] 		 huf_amplitude;
    wire 			 huf_dval;
    wire 			 bs_buf_sel;
    wire 			 bs_fifo_empty;
    wire 			 bs_rd_req;
    wire [7:0] 			 bs_packed_byte;
    wire 			 huf_fifo_empty;    
    wire 			 zz_rden;  

    wire [15:0] 		 fdct_sm_settings_x_cnt;
    wire [15:0] 		 fdct_sm_settings_y_cnt;
    wire [2:0] 			 fdct_sm_settings_cmp_idx;

    wire [15:0] 		 zig_sm_settings_x_cnt;
    wire [15:0] 		 zig_sm_settings_y_cnt;
    wire [2:0] 			 zig_sm_settings_cmp_idx;

    wire [15:0] 		 qua_sm_settings_x_cnt;
    wire [15:0] 		 qua_sm_settings_y_cnt;
    wire [2:0] 			 qua_sm_settings_cmp_idx;

    wire [15:0] 		 rle_sm_settings_x_cnt;
    wire [15:0] 		 rle_sm_settings_y_cnt;
    wire [2:0] 			 rle_sm_settings_cmp_idx;

    wire [15:0] 		 huf_sm_settings_x_cnt;
    wire [15:0] 		 huf_sm_settings_y_cnt;
    wire [2:0] 			 huf_sm_settings_cmp_idx;

    wire [15:0] 		 bs_sm_settings_x_cnt;
    wire [15:0] 		 bs_sm_settings_y_cnt;
    wire [2:0] 			 bs_sm_settings_cmp_idx;
    				 
    
    wire [31:0] image_size_reg;
    wire [7:0] 	jfif_ram_byte;
    wire 	jfif_ram_wren;
    wire [23:0] jfif_ram_wraddr;
    wire 	out_mux_ctrl;
    wire 	img_size_wr;
    wire 	jfif_start;
    wire 	jfif_ready;
    wire [7:0] 	bs_ram_byte;
    wire 	bs_ram_wren;
    wire [23:0] bs_ram_wraddr;
    wire 	jfif_eoi;
    wire 	fdct_fifo_rd;
    wire [23:0] fdct_fifo_q;
    wire 	fdct_fifo_hf_full;  


  //-----------------------------------------------------------------
  // Host Interface
  //-----------------------------------------------------------------
    HostIF
      U_HostIF
	(.CLK                (CLK              ),
	 .RST                (RST              ),

	 .OPB_ABus           (OPB_ABus         ),
	 .OPB_BE             (OPB_BE           ),
	 .OPB_DBus_in        (OPB_DBus_in      ),
	 .OPB_RNW            (OPB_RNW	       ),
	 .OPB_select         (OPB_select       ),
	 .OPB_DBus_out       (OPB_DBus_out     ),
	 .OPB_XferAck        (OPB_XferAck      ),
	 .OPB_retry          (OPB_retry	       ),
	 .OPB_toutSup        (OPB_toutSup      ),
	 .OPB_errAck         (OPB_errAck       ),
         		     		       
	 //-- Quantizer RAM  		       
	 .qdata              (qdata	       ),
	 .qaddr              (qaddr	       ),
	 .qwren              (qwren	       ),
	 		     		       
	 //-- CTRL	     		       
	 .jpeg_ready         (jpeg_ready       ),
	 .jpeg_busy          (jpeg_busy	       ),
	 		     		       
	 //-- ByteStuffer    		       
	 .outram_base_addr   (outram_base_addr ),
	 .num_enc_bytes      (num_enc_bytes    ),
	 		     		       
	 //-- global	     		       
	 .img_size_x         (img_size_x       ),
	 .img_size_y         (img_size_y       ),
	 .img_size_wr        (img_size_w       ),
	 .sof                (sof              )
	 );

  //-----------------------------------------------------------------
  // BUF_FIFO
  //-----------------------------------------------------------------
    BUF_FIFO
      U_BUF_FIFO
	(.CLK (CLK ),
	 .RST (RST ),
	 
	 .img_size_x         (img_size_x           ),
	 .img_size_y         (img_size_y	   ),
	 .sof                (sof		   ),
  	 
	 //-- HOST DATA      			   
	 .iram_wren          (iram_wren	           ),
	 .iram_wdata         (iram_wdata	   ),
	 .fifo_almost_full   (iram_fifo_afull	   ),
	 
	 //-- FDCT	      			   
	 .fdct_fifo_rd       (fdct_fifo_rd	   ),
	 .fdct_fifo_q        (fdct_fifo_q	   ),
	 .fdct_fifo_hf_full  (fdct_fifo_hf_full    )
	 );
    
    
  //-----------------------------------------------------------------
  // Controller
  //-----------------------------------------------------------------
  CtrlSM
    U_CTRL_SM      
      (.CLK                (CLK                 ),
       .RST                (RST                 ),
       
       //-- output IF
       .outif_almost_full  (outif_almost_full   ),
       
       //-- HOST IF
       .sof                (sof            ),
       .img_size_x         (img_size_x	   ),
       .img_size_y         (img_size_y	   ),
       .jpeg_ready         (jpeg_ready	   ),
       .jpeg_busy          (jpeg_busy      ),
       
       //-- FDCT 
       .fdct_start               (fdct_start          ),
       .fdct_ready               (fdct_ready          ),
       .fdct_sm_settings_x_cnt   (fdct_sm_settings_x_cnt),
       .fdct_sm_settings_y_cnt   (fdct_sm_settings_y_cnt),
       .fdct_sm_settings_cmp_idx (fdct_sm_settings_cmp_idx),
       
       //-- ZIGZAG
       .zig_start               (zig_start           ),
       .zig_ready               (zig_ready           ),
       .zig_sm_settings_x_cnt   (zig_sm_settings_x_cnt),
       .zig_sm_settings_y_cnt   (zig_sm_settings_y_cnt),
       .zig_sm_settings_cmp_idx (zig_sm_settings_cmp_idx),
              
       //-- Quantizer
       .qua_start               (qua_start           ),
       .qua_ready               (qua_ready           ),
       .qua_sm_settings_x_cnt   (qua_sm_settings_x_cnt),
       .qua_sm_settings_y_cnt   (qua_sm_settings_y_cnt),
       .qua_sm_settings_cmp_idx (qua_sm_settings_cmp_idx),
       
       //-- RLE
       .rle_start               (rle_start           ),
       .rle_ready               (rle_ready           ),
       .rle_sm_settings_x_cnt   (rle_sm_settings_x_cnt),
       .rle_sm_settings_y_cnt   (rle_sm_settings_y_cnt),
       .rle_sm_settings_cmp_idx (rle_sm_settings_cmp_idx),
       
       //-- Huffman
       .huf_start          (huf_start           ),
       .huf_ready          (huf_ready           ),
       .huf_sm_settings_x_cnt   (huf_sm_settings_x_cnt),
       .huf_sm_settings_y_cnt   (huf_sm_settings_y_cnt),
       .huf_sm_settings_cmp_idx (huf_sm_settings_cmp_idx),
       
       //-- ByteStuffdr
       .bs_start           (bs_start            ),
       .bs_ready           (bs_ready            ),
       .bs_sm_settings_x_cnt   (bs_sm_settings_x_cnt),
       .bs_sm_settings_y_cnt   (bs_sm_settings_y_cnt),
       .bs_sm_settings_cmp_idx (bs_sm_settings_cmp_idx),
              
       //-- JFIF GEN
       .jfif_start         (jfif_start         ),
       .jfif_ready         (jfif_ready         ),
       .jfif_eoi           (jfif_eoi           ),
       
       //-- OUT MUX         
       .out_mux_ctrl       (out_mux_ctrl       )
       );

    
    //-----------------------------------------------------------------
    // FDCT
    //-----------------------------------------------------------------
    FDCT
      U_FDCT
	(
	 .CLK                (CLK                 ),      
	 .RST                (RST		   ),
	 //-- CTRL	      			   
	 .start_pb           (fdct_start	   ),
	 .ready_pb           (fdct_ready	   ),
	 
	 // @note fdct_sm_setting not used
	 //.fdct_sm_settings   (fdct_sm_settings	   ),
  	 
	 //-- BUF_FIFO	      			   
	 .bf_fifo_rd         (fdct_fifo_rd	   ),
	 .bf_fifo_q          (fdct_fifo_q  	   ),
	 .bf_fifo_hf_full    (fdct_fifo_hf_full   ),
  	 
	 //-- ZIG ZAG	      			   
	 .zz_buf_sel         (zz_buf_sel	   ),
	 .zz_rd_addr         (zz_rd_addr	   ),
	 .zz_data            (zz_data		   ),
	 .zz_rden            (zz_rden		   ),
  	 
	 //-- HOST	      			   
	 .img_size_x         (img_size_x	   ),
	 .img_size_y         (img_size_y	   ),
	 .sof                (sof                 )      
	 );

	
    //-----------------------------------------------------------------
    // ZigZag top level
    //-----------------------------------------------------------------
    ZZ_TOP
      U_ZZ_TOP
	(
	 .CLK                (CLK           ),
	 .RST                (RST	    ),
	 //-- CTRL	      			    
	 .start_pb           (zig_start	    ),
	 .ready_pb           (zig_ready	    ),
	 
	 // @note zig_sm_settings not used
	 //.zig_sm_settings    (zig_sm_settings  ),
  	 
	 //-- Quantizer      			    
	 .qua_buf_sel        (qua_buf_sel   ),
	 .qua_rdaddr         (qua_rdaddr    ),
	 .qua_data           (qua_data	    ),
  	 
	 //-- FDCT	      		     
	 .fdct_buf_sel       (zz_buf_sel    ),
	 .fdct_rd_addr       (zz_rd_addr    ),
	 .fdct_data          (zz_data	    ),
	 .fdct_rden          (zz_rden       )  
	 );
    
    
    //-----------------------------------------------------------------
    // Quantizer top level
    //-----------------------------------------------------------------
    QUANT_TOP
      U_QUANT_TOP
	(
	 .CLK                (CLK                 ),
	 .RST                (RST		   ),
	 //-- CTRL	      			   ),
	 .start_pb           (qua_start	   ),
	 .ready_pb           (qua_ready	   ),
	 
	 //.qua_sm_settings    (qua_sm_settings	   ),
	 .qua_sm_settings_x_cnt   (qua_sm_settings_x_cnt),
	 .qua_sm_settings_y_cnt   (qua_sm_settings_y_cnt),
	 .qua_sm_settings_cmp_idx (qua_sm_settings_cmp_idx),
  	
	 //-- RLE	      			   ),
	 .rle_buf_sel        (rle_buf_sel	   ),
	 .rle_rdaddr         (rle_rdaddr	   ),
	 .rle_data           (rle_data		   ),
	 
	 //-- ZIGZAG	      			   
	 .zig_buf_sel        (qua_buf_sel	   ),
	 .zig_rd_addr        (qua_rdaddr	   ),
	 .zig_data           (qua_data		   ),
  		      			   
	 //-- HOST	      			   
	 .qdata              (qdata		   ),
	 .qaddr              (qaddr 		   ),
	 .qwren              (qwren               )   

	 );

    
    //-----------------------------------------------------------------
    // RLE TOP
    //-----------------------------------------------------------------
    // run-length-encoding
    RLE_TOP
      U_RLE_TOP
	(
	 .CLK                (CLK               ),  
	 .RST                (RST 		),
	 //-- CTRL	      			  
	 .start_pb           (rle_start 	),
	 .ready_pb           (rle_ready 	),
	 // @todo: fix "settings"
	 //.rle_sm_settings    (rle_sm_settings,	  ),
  	 .rss_cmp_idx        (rle_sm_settings_cmp_idx),
	 
	 //-- HUFFMAN	      			  
	 .huf_buf_sel        (huf_buf_sel       ),
	 .huf_rden           (huf_rden 	        ),
	 .huf_runlength      (huf_runlength     ),
	 .huf_size           (huf_size 	        ),
	 .huf_amplitude      (huf_amplitude 	),
	 .huf_dval           (huf_dval 	        ),
	 .huf_fifo_empty     (huf_fifo_empty 	),
  	 
	 //-- Quantizer      			  
	 .qua_buf_sel        (rle_buf_sel 	),
	 .qua_rd_addr        (rle_rdaddr 	),
	 .qua_data           (rle_data 	        ),
  	
	 //-- HostIF	      			  
	 .sof                (sof               )
	 );
    
    
    //-----------------------------------------------------------------
    // Huffman Encoder
    //-----------------------------------------------------------------
    //U_Huffman : entity work.Huffman
    Huffman
      U_Huffman
	(
	 .CLK                (CLK              ),
	 .RST                (RST		 ),
	 //-- CTRL	       			 ),
	 .start_pb           (huf_start	 ),
	 .ready_pb           (huf_ready	 ),
	 //.huf_sm_settings    (huf_sm_settings	 ),
	 .huf_sm_cmp_idx     (huf_sm_settings_cmp_idx),
	 
	 //-- HOST IF	       			 ),
	 .sof                (sof		 ),
	 .img_size_x         (img_size_x	 ),
	 .img_size_y         (img_size_y	 ),
	 //-- RLE	       			 ),
	 .rle_buf_sel        (huf_buf_sel	 ),
	 .rd_en              (huf_rden	 ),
	 .runlength          (huf_runlength	 ),
	 .VLI_size           (huf_size	 ),
	 .VLI                (huf_amplitude	 ),
	 .d_val              (huf_dval	 ),
	 .rle_fifo_empty     (huf_fifo_empty	 ),
	 //-- Byte Stuffer   			 ),
	 .bs_buf_sel         (bs_buf_sel	 ),
	 .bs_fifo_empty      (bs_fifo_empty	 ),
	 .bs_rd_req          (bs_rd_req	 ),
	 .bs_packed_byte     (bs_packed_byte   )  
	 );
    
    //-----------------------------------------------------------------
    // Byte Stuffer
    //-----------------------------------------------------------------
    ByteStuffer
      U_ByteStuffer
	(
         .CLK                (CLK               ),
         .RST                (RST	       ),
         //-- CTRL	    		       
         .start_pb           (bs_start	       ),
         .ready_pb           (bs_ready	       ),
         //-- HOST IF	    		      
         .sof                (sof	       ),
         .num_enc_bytes      (num_enc_bytes     ),
         .outram_base_addr   (outram_base_addr  ),
         //-- Huffman	    		       
         .huf_buf_sel        (bs_buf_sel	       ),
         .huf_fifo_empty     (bs_fifo_empty     ),
         .huf_rd_req         (bs_rd_req	       ),
         .huf_packed_byte    (bs_packed_byte    ),
         //-- OUT RAM	    		       
         .ram_byte           (bs_ram_byte       ),
         .ram_wren           (bs_ram_wren       ),
         .ram_wraddr         (bs_ram_wraddr     )   
	 );
    
  //debug signal
  assign frame_size = num_enc_bytes;
    
  //-----------------------------------------------------------------
  // JFIF Generator
  //-----------------------------------------------------------------
    JFIFGen
      U_JFIFGen	
	(
         .CLK                (CLK             ),
         .RST                (RST	     ),
         //-- CTRL	    		     
         .start              (jfif_start	     ),
         .ready              (jfif_ready	     ),
         .eoi                (jfif_eoi        ),
         //-- ByteStuffer    		     
         .num_enc_bytes      (num_enc_bytes   ),
         //-- HOST IF	    		     
         .qwren              (qwren	     ),
         .qwaddr             (qaddr	     ),
         .qwdata             (qdata	     ),
         .image_size_reg     (image_size_reg  ),
         .image_size_reg_wr  (img_size_wr     ),	
         //-- OUT RAM	    		      
         .ram_byte           (jfif_ram_byte   ),
         .ram_wren           (jfif_ram_wren   ),
         .ram_wraddr         (jfif_ram_wraddr )  
	 );
    
    assign image_size_reg = {img_size_x,img_size_y};
    
    //-----------------------------------------------------------------
    // OutMux
    //-----------------------------------------------------------------
    OutMux
      U_OutMux
	(
         .CLK                (CLK               ),
         .RST                (RST	       ),
         //-- CTRL	    		       
         .out_mux_ctrl       (out_mux_ctrl      ),
         //-- ByteStuffer    		       
         .bs_ram_byte        (bs_ram_byte       ),
         .bs_ram_wren        (bs_ram_wren       ),
         .bs_ram_wraddr      (bs_ram_wraddr     ),
         //-- ByteStuffer    		       
         .jfif_ram_byte      (jfif_ram_byte     ),
         .jfif_ram_wren      (jfif_ram_wren     ),
         .jfif_ram_wraddr    (jfif_ram_wraddr   ),
         //-- OUT RAM	    		       
         .ram_byte           (ram_byte	       ),
         .ram_wren           (ram_wren	       ),
         .ram_wraddr         (ram_wraddr        )  
	 );
    
endmodule
