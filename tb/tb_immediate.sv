`timescale 1ns/1ps
`include "rv32i_defs.vh"
module tb_immediate;
    `include "tb_common.svh"
    reg [31:0] instruction, raw, expected;
    reg [2:0] format;
    wire [31:0] immediate;
    integer f,i,checks;
    rv32i_immediate dut(.instruction(instruction),.format(format),.immediate(immediate));
    initial begin
        configure_paths(); checks=0;
        for(f=0;f<8;f=f+1) begin
            format=f;
            for(i=0;i<1024;i=i+1) begin
                raw=random_word(); instruction=raw;
                case(format)
                    `IMM_I: begin instruction=raw<<20; expected=$signed(raw[11:0]); end
                    `IMM_S: begin instruction=((raw>>5)&127)<<25 | (raw&31)<<7; expected=$signed(raw[11:0]); end
                    `IMM_B: begin
                        raw=raw&32'h00001ffe;
                        instruction=((raw>>12)&1)<<31 | ((raw>>11)&1)<<7 | ((raw>>5)&63)<<25 | ((raw>>1)&15)<<8;
                        expected=$signed(raw[12:0]);
                    end
                    `IMM_U: begin instruction=raw&32'hfffff000; expected=instruction; end
                    `IMM_J: begin
                        raw=raw&32'h001ffffe;
                        instruction=((raw>>20)&1)<<31 | ((raw>>12)&255)<<12 | ((raw>>11)&1)<<20 | ((raw>>1)&1023)<<21;
                        expected=$signed(raw[20:0]);
                    end
                    default: expected=0;
                endcase
                #1;
                if(immediate !== expected) $fatal(1,"Immediate mismatch format=%0d ins=%h got=%h expected=%h",format,instruction,immediate,expected);
                checks=checks+1;
            end
        end
        $display("IMMEDIATE_CHECKS=%0d",checks); mark_pass("tb_immediate"); $finish;
    end
endmodule
