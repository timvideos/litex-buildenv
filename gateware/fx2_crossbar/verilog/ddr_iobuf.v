module ddr_iobuf(input clk, input d, input oe, output q, inout io);
	wire clk;
	wire d;
	wire q;
	wire io;

	wire ioddr_d;
	wire ioddr_q;
	wire ioddr_t;

	IDDR2 id (
		.C0(clk),
		.C1(~clk),
		.CE(1'b1),
		.R(1'b0),
		.S(1'b0),
		.D(ioddr_d),
		.Q1(q)
	);
	ODDR2 od (
		.C0(clk),
		.C1(~clk),
		.CE(1'b1),
		.R(1'b0),
		.S(1'b0),
		.D0(d),
		.D1(d),
		.Q(ioddr_q)
	);
	ODDR2 ot (
		.C0(clk),
		.C1(~clk),
		.CE(1'b1),
		.R(1'b0),
		.S(1'b0),
		.D0(~oe),
		.D1(~oe),
		.Q(ioddr_t)
	);
	IOBUF iob (
		.I(ioddr_q),
		.O(ioddr_d),
		.T(ioddr_t),
		.IO(io)
	);
endmodule
