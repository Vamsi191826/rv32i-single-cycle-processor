`timescale 1ns/1ps
// Convenience wrapper for simulation. Vivado synthesis uses rv32i_core as top
// so a constant demonstration ROM cannot optimize the processor away.
module rv32i_system #(
    parameter IMEM_WORDS = 1024,
    parameter DMEM_BYTES = 4096,
    parameter IMEM_INIT_FILE = ""
)(
    input clk, rst,
    input [4:0] debug_reg_address,
    output [31:0] debug_reg_data,
    output halted, trap_valid,
    output [31:0] trap_cause, trap_pc, trap_value,
    output retire_valid,
    output [31:0] trace_pc, trace_instruction, trace_next_pc,
    output trace_rd_write,
    output [4:0] trace_rd,
    output [31:0] trace_rd_data,
    output trace_mem_read,
    output [31:0] trace_mem_address,
    output [3:0] trace_mem_strobe,
    output [31:0] trace_mem_data
);
    wire [31:0] imem_address, imem_data, dmem_address, dmem_write_data, dmem_data;
    wire imem_fault, dmem_fault, dmem_request;
    wire [3:0] dmem_write_strobe;
    wire [1:0] dmem_size;
    rv32i_core u_core(
        .clk(clk), .rst(rst), .imem_address(imem_address), .imem_read_data(imem_data), .imem_fault(imem_fault),
        .dmem_request(dmem_request), .dmem_address(dmem_address), .dmem_write_data(dmem_write_data),
        .dmem_write_strobe(dmem_write_strobe), .dmem_size(dmem_size), .dmem_read_data(dmem_data), .dmem_fault(dmem_fault),
        .debug_reg_address(debug_reg_address), .debug_reg_data(debug_reg_data), .halted(halted), .trap_valid(trap_valid),
        .trap_cause(trap_cause), .trap_pc(trap_pc), .trap_value(trap_value), .retire_valid(retire_valid),
        .trace_pc(trace_pc), .trace_instruction(trace_instruction), .trace_next_pc(trace_next_pc),
        .trace_rd_write(trace_rd_write), .trace_rd(trace_rd), .trace_rd_data(trace_rd_data),
        .trace_mem_read(trace_mem_read), .trace_mem_address(trace_mem_address),
        .trace_mem_strobe(trace_mem_strobe), .trace_mem_data(trace_mem_data)
    );
    rv32i_memory #(.IMEM_WORDS(IMEM_WORDS), .DMEM_BYTES(DMEM_BYTES), .IMEM_INIT_FILE(IMEM_INIT_FILE)) u_memory(
        .clk(clk), .imem_address(imem_address), .imem_data(imem_data), .imem_fault(imem_fault),
        .dmem_request(dmem_request), .dmem_address(dmem_address), .dmem_write_data(dmem_write_data),
        .dmem_write_strobe(dmem_write_strobe), .dmem_size(dmem_size), .dmem_data(dmem_data), .dmem_fault(dmem_fault)
    );
endmodule
