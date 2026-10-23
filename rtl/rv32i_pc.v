`timescale 1ns/1ps
module rv32i_pc #(parameter RESET_PC = 32'h00000000)(
    input clk, rst, enable,
    input [31:0] next_pc,
    output reg [31:0] pc
);
    // Active-high synchronous reset, consistent with the register file.
    always @(posedge clk) begin
        if (rst) pc <= RESET_PC;
        else if (enable) pc <= next_pc;
    end
endmodule
