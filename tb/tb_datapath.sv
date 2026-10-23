`timescale 1ns/1ps
`include "rv32i_defs.vh"
module tb_datapath;
    `include "tb_common.svh"
    reg [31:0] a, b;
    reg [3:0] operation;
    wire [31:0] result;
    wire zero;
    reg [2:0] condition;
    wire taken;
    reg [31:0] expected, corners [0:8];
    reg expected_taken;
    integer op, i, j, checks;
    rv32i_alu dut(.a(a), .b(b), .operation(operation), .result(result), .zero(zero));
    rv32i_branch branch_dut(.rs1_data(a), .rs2_data(b), .condition(condition), .taken(taken));
    task automatic check_alu;
        begin
            case(operation)
                `ALU_ADD: expected=a+b;
                `ALU_SUB: expected=a-b;
                `ALU_AND: expected=a&b;
                `ALU_OR: expected=a|b;
                `ALU_XOR: expected=a^b;
                `ALU_SLL: expected=a<<b[4:0];
                `ALU_SRL: expected=a>>b[4:0];
                `ALU_SRA: expected=$signed(a)>>>b[4:0];
                `ALU_SLT: expected=($signed(a)<$signed(b)) ? 1 : 0;
                `ALU_SLTU: expected=(a<b) ? 1 : 0;
                default: expected=0;
            endcase
            #1;
            if (result !== expected || zero !== (expected == 0))
                $fatal(1,"ALU mismatch op=%0d a=%h b=%h got=%h expected=%h zero=%b",operation,a,b,result,expected,zero);
            checks=checks+1;
        end
    endtask
    task automatic check_branch;
        begin
            case(condition)
                `BR_EQ: expected_taken=(a==b);
                `BR_NE: expected_taken=(a!=b);
                `BR_LT: expected_taken=($signed(a)<$signed(b));
                `BR_GE: expected_taken=($signed(a)>=$signed(b));
                `BR_LTU: expected_taken=(a<b);
                `BR_GEU: expected_taken=(a>=b);
                default: expected_taken=0;
            endcase
            #1;
            if(taken !== expected_taken) $fatal(1,"Branch mismatch cond=%0d a=%h b=%h",condition,a,b);
            checks=checks+1;
        end
    endtask
    initial begin
        configure_paths(); checks=0; a=0; b=0; operation=0; condition=0;
        corners[0]=0; corners[1]=1; corners[2]=32'hffffffff; corners[3]=32'h80000000;
        corners[4]=32'h7fffffff; corners[5]=31; corners[6]=32;
        corners[7]=32'haaaaaaaa; corners[8]=32'h55555555;
        for(op=0;op<10;op=op+1) begin
            operation=op;
            for(i=0;i<9;i=i+1) for(j=0;j<9;j=j+1) begin a=corners[i]; b=corners[j]; check_alu(); end
            for(i=0;i<1024;i=i+1) begin a=random_word(); b=random_word(); check_alu(); end
        end
        for(op=10;op<16;op=op+1) begin operation=op; a=random_word(); b=random_word(); check_alu(); end
        for(op=0;op<8;op=op+1) begin
            condition=op;
            for(i=0;i<9;i=i+1) for(j=0;j<9;j=j+1) begin a=corners[i]; b=corners[j]; check_branch(); end
            for(i=0;i<256;i=i+1) begin a=random_word(); b=random_word(); check_branch(); end
        end
        $display("DATAPATH_CHECKS=%0d",checks); mark_pass("tb_datapath"); $finish;
    end
endmodule
