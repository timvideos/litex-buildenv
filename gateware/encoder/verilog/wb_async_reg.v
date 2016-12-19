/*
Copyright (c) 2015-2016 Alex Forencich
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

// Language: Verilog 2001

`timescale 1ns / 1ps

/*
 * Wishbone register
 */
module wb_async_reg #
(
    parameter DATA_WIDTH = 32,                  // width of data bus in bits (8, 16, 32, or 64)
    parameter ADDR_WIDTH = 32,                  // width of address bus in bits
    parameter SELECT_WIDTH = (DATA_WIDTH/8)     // width of word select bus (1, 2, 4, or 8)
)
(
    // master side
    input  wire                    wbm_clk,
    input  wire                    wbm_rst,
    input  wire [ADDR_WIDTH-1:0]   wbm_adr_i,   // ADR_I() address
    input  wire [DATA_WIDTH-1:0]   wbm_dat_i,   // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbm_dat_o,   // DAT_O() data out
    input  wire                    wbm_we_i,    // WE_I write enable input
    input  wire [SELECT_WIDTH-1:0] wbm_sel_i,   // SEL_I() select input
    input  wire                    wbm_stb_i,   // STB_I strobe input
    output wire                    wbm_ack_o,   // ACK_O acknowledge output
    output wire                    wbm_err_o,   // ERR_O error output
    output wire                    wbm_rty_o,   // RTY_O retry output
    input  wire                    wbm_cyc_i,   // CYC_I cycle input

    // slave side
    input  wire                    wbs_clk,
    input  wire                    wbs_rst,
    output wire [ADDR_WIDTH-1:0]   wbs_adr_o,   // ADR_O() address
    input  wire [DATA_WIDTH-1:0]   wbs_dat_i,   // DAT_I() data in
    output wire [DATA_WIDTH-1:0]   wbs_dat_o,   // DAT_O() data out
    output wire                    wbs_we_o,    // WE_O write enable output
    output wire [SELECT_WIDTH-1:0] wbs_sel_o,   // SEL_O() select output
    output wire                    wbs_stb_o,   // STB_O strobe output
    input  wire                    wbs_ack_i,   // ACK_I acknowledge input
    input  wire                    wbs_err_i,   // ERR_I error input
    input  wire                    wbs_rty_i,   // RTY_I retry input
    output wire                    wbs_cyc_o    // CYC_O cycle output
);

reg [ADDR_WIDTH-1:0] wbm_adr_i_reg = 0;
reg [DATA_WIDTH-1:0] wbm_dat_i_reg = 0;
reg [DATA_WIDTH-1:0] wbm_dat_o_reg = 0;
reg wbm_we_i_reg = 0;
reg [SELECT_WIDTH-1:0] wbm_sel_i_reg = 0;
reg wbm_stb_i_reg = 0;
reg wbm_ack_o_reg = 0;
reg wbm_err_o_reg = 0;
reg wbm_rty_o_reg = 0;
reg wbm_cyc_i_reg = 0;

reg wbm_done_sync1 = 0;
reg wbm_done_sync2 = 0;
reg wbm_done_sync3 = 0;

reg [ADDR_WIDTH-1:0] wbs_adr_o_reg = 0;
reg [DATA_WIDTH-1:0] wbs_dat_i_reg = 0;
reg [DATA_WIDTH-1:0] wbs_dat_o_reg = 0;
reg wbs_we_o_reg = 0;
reg [SELECT_WIDTH-1:0] wbs_sel_o_reg = 0;
reg wbs_stb_o_reg = 0;
reg wbs_ack_i_reg = 0;
reg wbs_err_i_reg = 0;
reg wbs_rty_i_reg = 0;
reg wbs_cyc_o_reg = 0;

reg wbs_cyc_o_sync1 = 0;
reg wbs_cyc_o_sync2 = 0;
reg wbs_cyc_o_sync3 = 0;

reg wbs_stb_o_sync1 = 0;
reg wbs_stb_o_sync2 = 0;
reg wbs_stb_o_sync3 = 0;

reg wbs_done_reg = 0;

assign wbm_dat_o = wbm_dat_o_reg;
assign wbm_ack_o = wbm_ack_o_reg;
assign wbm_err_o = wbm_err_o_reg;
assign wbm_rty_o = wbm_rty_o_reg;

assign wbs_adr_o = wbs_adr_o_reg;
assign wbs_dat_o = wbs_dat_o_reg;
assign wbs_we_o = wbs_we_o_reg;
assign wbs_sel_o = wbs_sel_o_reg;
assign wbs_stb_o = wbs_stb_o_reg;
assign wbs_cyc_o = wbs_cyc_o_reg;

// master side logic
always @(posedge wbm_clk) begin
    if (wbm_rst) begin
        wbm_adr_i_reg <= 0;
        wbm_dat_i_reg <= 0;
        wbm_dat_o_reg <= 0;
        wbm_we_i_reg <= 0;
        wbm_sel_i_reg <= 0;
        wbm_stb_i_reg <= 0;
        wbm_ack_o_reg <= 0;
        wbm_err_o_reg <= 0;
        wbm_rty_o_reg <= 0;
        wbm_cyc_i_reg <= 0;
    end else begin
        if (wbm_cyc_i_reg & wbm_stb_i_reg) begin
            // cycle - hold master
            if (wbm_done_sync2 & ~wbm_done_sync3) begin
                // end of cycle - store slave
                wbm_dat_o_reg <= wbs_dat_i_reg;
                wbm_ack_o_reg <= wbs_ack_i_reg;
                wbm_err_o_reg <= wbs_err_i_reg;
                wbm_rty_o_reg <= wbs_rty_i_reg;
                wbm_we_i_reg <= 0;
                wbm_stb_i_reg <= 0;
            end
        end else begin
            // idle - store master
            wbm_adr_i_reg <= wbm_adr_i;
            wbm_dat_i_reg <= wbm_dat_i;
            wbm_dat_o_reg <= 0;
            wbm_we_i_reg <= wbm_we_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            wbm_sel_i_reg <= wbm_sel_i;
            wbm_stb_i_reg <= wbm_stb_i & ~(wbm_ack_o | wbm_err_o | wbm_rty_o);
            wbm_ack_o_reg <= 0;
            wbm_err_o_reg <= 0;
            wbm_rty_o_reg <= 0;
            wbm_cyc_i_reg <= wbm_cyc_i;
        end
    end

    // synchronize signals
    wbm_done_sync1 <= wbs_done_reg;
    wbm_done_sync2 <= wbm_done_sync1;
    wbm_done_sync3 <= wbm_done_sync2;
end

// slave side logic
always @(posedge wbs_clk) begin
    if (wbs_rst) begin
        wbs_adr_o_reg <= 0;
        wbs_dat_i_reg <= 0;
        wbs_dat_o_reg <= 0;
        wbs_we_o_reg <= 0;
        wbs_sel_o_reg <= 0;
        wbs_stb_o_reg <= 0;
        wbs_ack_i_reg <= 0;
        wbs_err_i_reg <= 0;
        wbs_rty_i_reg <= 0;
        wbs_cyc_o_reg <= 0;
        wbs_done_reg <= 0;
    end else begin
        if (wbs_ack_i | wbs_err_i | wbs_rty_i) begin
            // end of cycle - store slave
            wbs_dat_i_reg <= wbs_dat_i;
            wbs_ack_i_reg <= wbs_ack_i;
            wbs_err_i_reg <= wbs_err_i;
            wbs_rty_i_reg <= wbs_rty_i;
            wbs_we_o_reg <= 0;
            wbs_stb_o_reg <= 0;
            wbs_done_reg <= 1;
        end else if (wbs_stb_o_sync2 & ~wbs_stb_o_sync3) begin
            // beginning of cycle - store master
            wbs_adr_o_reg <= wbm_adr_i_reg;
            wbs_dat_i_reg <= 0;
            wbs_dat_o_reg <= wbm_dat_i_reg;
            wbs_we_o_reg <= wbm_we_i_reg;
            wbs_sel_o_reg <= wbm_sel_i_reg;
            wbs_stb_o_reg <= wbm_stb_i_reg;
            wbs_ack_i_reg <= 0;
            wbs_err_i_reg <= 0;
            wbs_rty_i_reg <= 0;
            wbs_cyc_o_reg <= wbm_cyc_i_reg;
            wbs_done_reg <= 0;
        end else if (~wbs_cyc_o_sync2 & wbs_cyc_o_sync3) begin
            // cyc deassert
            wbs_adr_o_reg <= 0;
            wbs_dat_i_reg <= 0;
            wbs_dat_o_reg <= 0;
            wbs_we_o_reg <= 0;
            wbs_sel_o_reg <= 0;
            wbs_stb_o_reg <= 0;
            wbs_ack_i_reg <= 0;
            wbs_err_i_reg <= 0;
            wbs_rty_i_reg <= 0;
            wbs_cyc_o_reg <= 0;
            wbs_done_reg <= 0;
        end
    end

    // synchronize signals
    wbs_cyc_o_sync1 <= wbm_cyc_i_reg;
    wbs_cyc_o_sync2 <= wbs_cyc_o_sync1;
    wbs_cyc_o_sync3 <= wbs_cyc_o_sync2;

    wbs_stb_o_sync1 <= wbm_stb_i_reg;
    wbs_stb_o_sync2 <= wbs_stb_o_sync1;
    wbs_stb_o_sync3 <= wbs_stb_o_sync2;
end

endmodule