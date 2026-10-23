`timescale 1ns/1ps
`include "rv32i_defs.vh"
module rv32i_alu(
    input [31:0] a, b,
    input [3:0] operation,
    output reg [31:0] result,
    output zero
);
    always @* begin
        case (operation)
            `ALU_ADD:  result = a + b;
            `ALU_SUB:  result = a - b;
            `ALU_AND:  result = a & b;
            `ALU_OR:   result = a | b;
            `ALU_XOR:  result = a ^ b;
            `ALU_SLL:  result = a << b[4:0];
            `ALU_SRL:  result = a >> b[4:0];
            `ALU_SRA:  result = $signed(a) >>> b[4:0];
            `ALU_SLT:  result = {31'b0, ($signed(a) < $signed(b))};
            `ALU_SLTU: result = {31'b0, (a < b)};
            default:   result = 32'b0;
        endcase
    end
    assign zero = (result == 32'b0);
endmodule
