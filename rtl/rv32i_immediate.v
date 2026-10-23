`timescale 1ns/1ps
`include "rv32i_defs.vh"
module rv32i_immediate(
    input [31:0] instruction,
    input [2:0] format,
    output reg [31:0] immediate
);
    always @* begin
        case (format)
            `IMM_I: immediate = {{20{instruction[31]}}, instruction[31:20]};
            `IMM_S: immediate = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
            `IMM_B: immediate = {{19{instruction[31]}}, instruction[31], instruction[7],
                                  instruction[30:25], instruction[11:8], 1'b0};
            `IMM_U: immediate = {instruction[31:12], 12'b0};
            `IMM_J: immediate = {{11{instruction[31]}}, instruction[31], instruction[19:12],
                                  instruction[20], instruction[30:21], 1'b0};
            default: immediate = 32'b0;
        endcase
    end
endmodule
