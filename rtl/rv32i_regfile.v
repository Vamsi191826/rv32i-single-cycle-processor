`timescale 1ns/1ps
module rv32i_regfile(
    input clk, rst, write_enable,
    input [4:0] rs1, rs2, rd, debug_address,
    input [31:0] write_data,
    output [31:0] rs1_data, rs2_data, debug_data
);
    reg [31:0] registers [0:31];
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 32; i = i + 1) registers[i] <= 32'b0;
        end else if (write_enable && rd != 0) begin
            registers[rd] <= write_data;
        end
    end
    // Explicitly force x0 on every read, including before reset.
    assign rs1_data = (rs1 == 0) ? 32'b0 : registers[rs1];
    assign rs2_data = (rs2 == 0) ? 32'b0 : registers[rs2];
    assign debug_data = (debug_address == 0) ? 32'b0 : registers[debug_address];
endmodule
