`timescale 1ns/1ps
module tb_regfile;
    `include "tb_common.svh"
    reg clk=0, rst=1, write_enable=0;
    reg [4:0] rs1=0,rs2=0,rd=0,debug_address=0;
    reg [31:0] write_data=0,expected[0:31];
    wire [31:0] rs1_data,rs2_data,debug_data;
    integer i,j,checks;
    always #5 clk=~clk;
    rv32i_regfile dut(.*);
    task automatic check_reads;
        begin
            #1;
            if(rs1_data !== expected[rs1] || rs2_data !== expected[rs2] || debug_data !== expected[debug_address])
                $fatal(1,"Register-file read mismatch rs1=%0d rs2=%0d debug=%0d",rs1,rs2,debug_address);
            checks=checks+1;
        end
    endtask
    initial begin
        configure_paths(); checks=0;
        for(i=0;i<32;i=i+1) expected[i]=0;
        repeat(2) @(posedge clk); @(negedge clk); rst=0;
        for(i=1;i<32;i=i+1) begin
            @(negedge clk); rd=i; rs1=i; rs2=31-i; debug_address=i; write_data=random_word(); write_enable=1;
            check_reads(); // Read old value before the write edge.
            @(posedge clk); expected[i]=write_data; check_reads();
        end
        @(negedge clk); rd=0; write_data=32'hdeadbeef; write_enable=1; rs1=0; rs2=0; debug_address=0;
        @(posedge clk); check_reads();
        @(negedge clk); rd=7; write_data=99; write_enable=0;
        @(posedge clk); rs1=7; check_reads();
        for(i=0;i<32;i=i+1) begin rs1=i; rs2=31-i; debug_address=i; check_reads(); end
        // Reset must wait for a rising edge, matching the documented contract.
        @(negedge clk); rst=1; rs1=7; check_reads();
        @(posedge clk); for(j=0;j<32;j=j+1) expected[j]=0; check_reads();
        $display("REGFILE_CHECKS=%0d",checks); mark_pass("tb_regfile"); $finish;
    end
endmodule
