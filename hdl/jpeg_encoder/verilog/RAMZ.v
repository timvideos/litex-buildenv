

module RAMZ
#(
  parameter RAMADDR_W = 6,
  parameter RAMDATA_W = 12
)  
(
 input wire [RAMDATA_W-1:0]  d,
 input wire [RAMADDR_W-1:0]  waddr,
 input wire [RAMADDR_W-1:0]  raddr,
 input wire 		     we,
 input wire                  rd,     /// debug only
 input wire 		     clk,
 output wire [RAMDATA_W-1:0] q
 );
    
    reg [RAMADDR_W-1:0]     read_addr;
    localparam MEM_SIZE = 2**RAMADDR_W;
    reg [RAMDATA_W-1:0]  mem [0:MEM_SIZE-1];

    // @todo: debug
    integer write_count [0:MEM_SIZE-1];
    integer read_count  [0:MEM_SIZE-1];

    integer ii;
    initial begin
	for(ii=0; ii<MEM_SIZE; ii=ii+1) begin
	    write_count[ii] = 0;
	    read_count[ii]  = 0;
	end
    end
    
    assign q = mem[read_addr];

    always @(posedge clk) begin
	if (rd) begin
	    read_count[raddr] <= read_count[raddr] + 1;
	end
	if (we) begin
	    write_count[waddr] <= read_count[waddr] + 1;
	end
    end
    
    always @(posedge clk) begin: RAMZ_RTL
	read_addr <= raddr;
	if (we) begin
            mem[waddr] <= d;
	end
    end
    
endmodule
