`timescale 1ns/1ps
`include "rv32i_defs.vh"
module tb_decoder;
    `include "tb_common.svh"
    reg [31:0] instruction;
    wire reg_write,alu_b_immediate,jump,jalr,mem_read,mem_write,load_unsigned,illegal,ecall,ebreak,fence;
    wire [1:0] alu_a_select,writeback_select,mem_size;
    wire [3:0] alu_operation;
    wire [2:0] immediate_format,branch_condition;
    integer f3,f7,i,checks;
    reg legal_expected;
    reg [3:0] op_expected;
    rv32i_decoder dut(.*);
    task automatic check_legality(input bit legal_value);
        begin
            #1;
            if(illegal !== !legal_value) $fatal(1,"Decoder legality mismatch instruction=%h",instruction);
            if(!legal_value && (reg_write || mem_read || mem_write || jump || jalr || branch_condition!=0))
                $fatal(1,"Illegal instruction enabled a side effect: %h",instruction);
            checks=checks+1;
        end
    endtask
    initial begin
        configure_paths(); checks=0;
        for(f3=0;f3<8;f3=f3+1) for(f7=0;f7<128;f7=f7+1) begin
            instruction=(f7<<25)|(2<<20)|(1<<15)|(f3<<12)|(3<<7)|32'h33;
            legal_expected=(f7==0)||((f7==32)&&(f3==0||f3==5));
            check_legality(legal_expected);
            if(legal_expected) begin
                case(f3)
                    0: op_expected=(f7==32)?`ALU_SUB:`ALU_ADD;
                    1: op_expected=`ALU_SLL;
                    2: op_expected=`ALU_SLT;
                    3: op_expected=`ALU_SLTU;
                    4: op_expected=`ALU_XOR;
                    5: op_expected=(f7==32)?`ALU_SRA:`ALU_SRL;
                    6: op_expected=`ALU_OR;
                    7: op_expected=`ALU_AND;
                endcase
                if(!reg_write || alu_b_immediate || alu_operation !== op_expected) $fatal(1,"R-type controls mismatch");
            end
        end
        for(f3=0;f3<8;f3=f3+1) for(f7=0;f7<128;f7=f7+1) begin
            instruction=(f7<<25)|(17<<20)|(1<<15)|(f3<<12)|(3<<7)|32'h13;
            legal_expected=(f3!=1&&f3!=5)||(f7==0)||((f3==5)&&(f7==32));
            check_legality(legal_expected);
            if(legal_expected && (!reg_write || !alu_b_immediate || immediate_format!=`IMM_I)) $fatal(1,"I-type controls mismatch");
            if(f3==0 && alu_operation!=`ALU_ADD) $fatal(1,"ADDI with immediate bit 30 set incorrectly selected SUB");
        end
        for(f3=0;f3<8;f3=f3+1) begin
            instruction=(f3<<12)|32'h03; check_legality(f3==0||f3==1||f3==2||f3==4||f3==5);
            instruction=(f3<<12)|32'h23; check_legality(f3<3);
            instruction=(f3<<12)|32'h63; check_legality(f3==0||f3==1||f3>=4);
            instruction=(f3<<12)|32'h67; check_legality(f3==0);
            instruction=(f3<<12)|32'h0f; check_legality(f3==0);
        end
        instruction=32'h00000073; check_legality(1); if(!ecall||reg_write) $fatal(1,"ECALL controls");
        instruction=32'h00100073; check_legality(1); if(!ebreak||reg_write) $fatal(1,"EBREAK controls");
        instruction=32'h300010f3; check_legality(0);
        instruction=32'hfffff037; check_legality(1); if(alu_a_select!=`A_ZERO) $fatal(1,"LUI operand A must be zero");
        instruction=32'h12345017; check_legality(1); if(alu_a_select!=`A_PC) $fatal(1,"AUIPC operand A must be current PC");
        $display("DECODER_CHECKS=%0d",checks); mark_pass("tb_decoder"); $finish;
    end
endmodule
