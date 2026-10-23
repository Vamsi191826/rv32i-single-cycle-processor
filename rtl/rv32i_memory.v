`timescale 1ns/1ps
module rv32i_memory #(
    parameter IMEM_WORDS = 1024,
    parameter DMEM_BYTES = 4096,
    parameter IMEM_INIT_FILE = ""
)(
    input clk,
    input [31:0] imem_address,
    output reg [31:0] imem_data,
    output reg imem_fault,
    input dmem_request,
    input [31:0] dmem_address, dmem_write_data,
    input [3:0] dmem_write_strobe,
    input [1:0] dmem_size,
    output reg [31:0] dmem_data,
    output reg dmem_fault
);
    // Asynchronous read implies distributed memory/registers, not synchronous BRAM.
    (* ram_style = "distributed" *) reg [31:0] imem [0:IMEM_WORDS-1];
    (* ram_style = "distributed" *) reg [7:0] dmem [0:DMEM_BYTES-1];
    integer i;
    wire [31:0] word_base = {dmem_address[31:2], 2'b00};
    initial begin
        for (i = 0; i < IMEM_WORDS; i = i + 1) imem[i] = 32'h00000013;
        for (i = 0; i < DMEM_BYTES; i = i + 1) dmem[i] = 8'b0;
        if (IMEM_INIT_FILE != "") $readmemh(IMEM_INIT_FILE, imem);
    end
    always @* begin
        imem_data = 32'h00000013;
        imem_fault = (imem_address >= IMEM_WORDS * 4);
        if (!imem_fault) imem_data = imem[imem_address >> 2];
    end
    // Keep instruction and data read logic independent. A data request must
    // never retrigger instruction decoding through transient default values.
    always @* begin
        dmem_data = 32'b0; dmem_fault = 0;
        if (dmem_request) begin
            // mem_size encodes byte=0, halfword=1, word=2.
            dmem_fault = (dmem_address > DMEM_BYTES - (1 << dmem_size));
            if (!dmem_fault && word_base <= DMEM_BYTES - 4)
                dmem_data = {dmem[word_base+3], dmem[word_base+2], dmem[word_base+1], dmem[word_base]};
        end
    end
    always @(posedge clk) begin
        if (dmem_request && !dmem_fault) begin
            if (dmem_write_strobe[0]) dmem[word_base]   <= dmem_write_data[7:0];
            if (dmem_write_strobe[1]) dmem[word_base+1] <= dmem_write_data[15:8];
            if (dmem_write_strobe[2]) dmem[word_base+2] <= dmem_write_data[23:16];
            if (dmem_write_strobe[3]) dmem[word_base+3] <= dmem_write_data[31:24];
        end
    end
endmodule
