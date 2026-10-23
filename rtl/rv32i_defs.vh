`ifndef RV32I_DEFS_VH
`define RV32I_DEFS_VH
// One shared definition of every internal control encoding.
`define ALU_ADD  4'd0
`define ALU_SUB  4'd1
`define ALU_AND  4'd2
`define ALU_OR   4'd3
`define ALU_XOR  4'd4
`define ALU_SLL  4'd5
`define ALU_SRL  4'd6
`define ALU_SRA  4'd7
`define ALU_SLT  4'd8
`define ALU_SLTU 4'd9
`define IMM_NONE 3'd0
`define IMM_I    3'd1
`define IMM_S    3'd2
`define IMM_B    3'd3
`define IMM_U    3'd4
`define IMM_J    3'd5
`define A_RS1    2'd0
`define A_PC     2'd1
`define A_ZERO   2'd2
`define WB_ALU  2'd0
`define WB_LOAD 2'd1
`define WB_PC4  2'd2
`define BR_NONE 3'd0
`define BR_EQ   3'd1
`define BR_NE   3'd2
`define BR_LT   3'd3
`define BR_GE   3'd4
`define BR_LTU  3'd5
`define BR_GEU  3'd6
`endif
