`timescale 1ns/1ps
module tb_memory;
    `include "tb_common.svh"
    reg clk=0;
    reg [31:0] imem_address=0,dmem_address=0,dmem_write_data=0;
    reg dmem_request=1;
    reg [3:0] dmem_write_strobe=0;
    reg [1:0] dmem_size=2;
    wire [31:0] imem_data,dmem_data;
    wire imem_fault,dmem_fault;
    integer checks;
    always #5 clk=~clk;
    rv32i_memory #(.IMEM_WORDS(16),.DMEM_BYTES(64)) dut(.*);
    task automatic expect_word(input [31:0] value);
        begin #1; if(dmem_data !== value) $fatal(1,"Memory got=%h expected=%h",dmem_data,value); checks=checks+1; end
    endtask
    initial begin
        configure_paths(); checks=0; #1;
        dut.imem[0]=32'h00c58533; dut.imem[1]=32'h40f706b3;
        #1; if(imem_data!==32'h00c58533) $fatal(1,"Instruction read");
        imem_address=4; #1; if(imem_data!==32'h40f706b3) $fatal(1,"Instruction read must follow address without clock");
        imem_address=64; #1; if(!imem_fault) $fatal(1,"Instruction bounds");
        @(negedge clk); dmem_address=0; dmem_write_data=32'h11223344; dmem_write_strobe=15;
        expect_word(0); @(posedge clk); expect_word(32'h11223344);
        @(negedge clk); dmem_size=0; dmem_address=1; dmem_write_data=32'h0000aa00; dmem_write_strobe=2;
        @(posedge clk); expect_word(32'h1122aa44);
        @(negedge clk); dmem_size=1; dmem_address=2; dmem_write_data=32'hbeef0000; dmem_write_strobe=12;
        @(posedge clk); expect_word(32'hbeefaa44);
        @(negedge clk); dmem_write_strobe=0; dmem_size=2; dmem_address=4; expect_word(0);
        dmem_address=0; expect_word(32'hbeefaa44);
        dmem_address=63; dmem_size=0; #1; if(dmem_fault) $fatal(1,"Last byte must be accessible");
        dmem_size=1; #1; if(!dmem_fault) $fatal(1,"Halfword boundary must fault");
        dmem_address=64; dmem_size=0; #1; if(!dmem_fault) $fatal(1,"Byte outside RAM must fault");
        dmem_address=32'hfffffffc; dmem_size=2; #1; if(!dmem_fault) $fatal(1,"Negative/wrapped address must fault");
        $display("MEMORY_CHECKS=%0d",checks+7); mark_pass("tb_memory"); $finish;
    end
endmodule
