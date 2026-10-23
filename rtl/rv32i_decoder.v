`timescale 1ns/1ps
`include "rv32i_defs.vh"
module rv32i_decoder(
    input [31:0] instruction,
    output reg reg_write,
    output reg [1:0] alu_a_select,
    output reg alu_b_immediate,
    output reg [3:0] alu_operation,
    output reg [2:0] immediate_format,
    output reg [1:0] writeback_select,
    output reg [2:0] branch_condition,
    output reg jump, jalr, mem_read, mem_write,
    output reg [1:0] mem_size,
    output reg load_unsigned,
    output reg illegal, ecall, ebreak, fence
);
    wire [6:0] opcode = instruction[6:0];
    wire [2:0] funct3 = instruction[14:12];
    wire [6:0] funct7 = instruction[31:25];
    always @* begin
        reg_write = 0; alu_a_select = `A_RS1; alu_b_immediate = 0;
        alu_operation = `ALU_ADD; immediate_format = `IMM_NONE;
        writeback_select = `WB_ALU; branch_condition = `BR_NONE;
        jump = 0; jalr = 0; mem_read = 0; mem_write = 0;
        mem_size = 2; load_unsigned = 0;
        illegal = 1; ecall = 0; ebreak = 0; fence = 0;
        case (opcode)
            7'h33: begin // Register-register arithmetic.
                illegal = 0; reg_write = 1;
                case (funct3)
                    0: begin
                        if (funct7 == 0) alu_operation = `ALU_ADD;
                        else if (funct7 == 7'h20) alu_operation = `ALU_SUB;
                        else illegal = 1;
                    end
                    1: begin alu_operation = `ALU_SLL;  if (funct7 != 0) illegal = 1; end
                    2: begin alu_operation = `ALU_SLT;  if (funct7 != 0) illegal = 1; end
                    3: begin alu_operation = `ALU_SLTU; if (funct7 != 0) illegal = 1; end
                    4: begin alu_operation = `ALU_XOR;  if (funct7 != 0) illegal = 1; end
                    5: begin
                        if (funct7 == 0) alu_operation = `ALU_SRL;
                        else if (funct7 == 7'h20) alu_operation = `ALU_SRA;
                        else illegal = 1;
                    end
                    6: begin alu_operation = `ALU_OR;  if (funct7 != 0) illegal = 1; end
                    7: begin alu_operation = `ALU_AND; if (funct7 != 0) illegal = 1; end
                endcase
            end
            7'h13: begin // Immediate arithmetic. ADDI never decodes as SUB.
                illegal = 0; reg_write = 1; alu_b_immediate = 1; immediate_format = `IMM_I;
                case (funct3)
                    0: alu_operation = `ALU_ADD;
                    2: alu_operation = `ALU_SLT;
                    3: alu_operation = `ALU_SLTU;
                    4: alu_operation = `ALU_XOR;
                    6: alu_operation = `ALU_OR;
                    7: alu_operation = `ALU_AND;
                    1: begin alu_operation = `ALU_SLL; if (funct7 != 0) illegal = 1; end
                    5: begin
                        if (funct7 == 0) alu_operation = `ALU_SRL;
                        else if (funct7 == 7'h20) alu_operation = `ALU_SRA;
                        else illegal = 1;
                    end
                    default: illegal = 1;
                endcase
            end
            7'h03: begin // Loads.
                illegal = 0; reg_write = 1; mem_read = 1;
                alu_b_immediate = 1; immediate_format = `IMM_I; writeback_select = `WB_LOAD;
                case (funct3)
                    0: mem_size = 0;
                    1: mem_size = 1;
                    2: mem_size = 2;
                    4: begin mem_size = 0; load_unsigned = 1; end
                    5: begin mem_size = 1; load_unsigned = 1; end
                    default: illegal = 1;
                endcase
            end
            7'h23: begin // Stores.
                illegal = 0; mem_write = 1; alu_b_immediate = 1; immediate_format = `IMM_S;
                case (funct3)
                    0: mem_size = 0;
                    1: mem_size = 1;
                    2: mem_size = 2;
                    default: illegal = 1;
                endcase
            end
            7'h63: begin // All six conditional branches.
                illegal = 0; immediate_format = `IMM_B; alu_operation = `ALU_SUB;
                case (funct3)
                    0: branch_condition = `BR_EQ;
                    1: branch_condition = `BR_NE;
                    4: branch_condition = `BR_LT;
                    5: branch_condition = `BR_GE;
                    6: branch_condition = `BR_LTU;
                    7: branch_condition = `BR_GEU;
                    default: illegal = 1;
                endcase
            end
            7'h37: begin // LUI = 0 + U immediate.
                illegal = 0; reg_write = 1; alu_a_select = `A_ZERO;
                alu_b_immediate = 1; immediate_format = `IMM_U;
            end
            7'h17: begin // AUIPC = current PC + U immediate.
                illegal = 0; reg_write = 1; alu_a_select = `A_PC;
                alu_b_immediate = 1; immediate_format = `IMM_U;
            end
            7'h6f: begin
                illegal = 0; reg_write = 1; jump = 1;
                immediate_format = `IMM_J; writeback_select = `WB_PC4;
            end
            7'h67: begin
                if (funct3 == 0) begin
                    illegal = 0; reg_write = 1; jalr = 1;
                    alu_b_immediate = 1; immediate_format = `IMM_I; writeback_select = `WB_PC4;
                end
            end
            7'h0f: begin
                // Strongly ordered single-hart memory: FENCE needs no extra action.
                // Reserved rd/rs1/fm fields are ignored; FENCE.I is not implemented.
                if (funct3 == 0) begin illegal = 0; fence = 1; end
            end
            7'h73: begin
                if (instruction == 32'h00000073) begin illegal = 0; ecall = 1; end
                else if (instruction == 32'h00100073) begin illegal = 0; ebreak = 1; end
            end
        endcase
        if (illegal) begin
            reg_write = 0; mem_read = 0; mem_write = 0;
            jump = 0; jalr = 0; branch_condition = `BR_NONE;
        end
    end
endmodule
