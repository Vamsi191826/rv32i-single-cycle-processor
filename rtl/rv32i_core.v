`timescale 1ns/1ps
`include "rv32i_defs.vh"
// Single-cycle interface contract: instruction/data reads and fault responses
// are combinational. Stores are captured by memory on the rising clock edge.
// There is no ready/valid stall protocol and no instruction pipeline.
module rv32i_core #(parameter RESET_PC = 32'h00000000)(
    input clk, rst,
    output [31:0] imem_address,
    input [31:0] imem_read_data,
    input imem_fault,
    output dmem_request,
    output [31:0] dmem_address, dmem_write_data,
    output [3:0] dmem_write_strobe,
    output [1:0] dmem_size,
    input [31:0] dmem_read_data,
    input dmem_fault,
    input [4:0] debug_reg_address,
    output [31:0] debug_reg_data,
    output reg halted,
    output trap_valid,
    output reg [31:0] trap_cause, trap_pc, trap_value,
    output reg retire_valid,
    output reg [31:0] trace_pc, trace_instruction, trace_next_pc,
    output reg trace_rd_write,
    output reg [4:0] trace_rd,
    output reg [31:0] trace_rd_data,
    output reg trace_mem_read,
    output reg [31:0] trace_mem_address,
    output reg [3:0] trace_mem_strobe,
    output reg [31:0] trace_mem_data
);
    wire [31:0] pc;
    wire [31:0] instruction = imem_read_data;
    wire [4:0] rs1 = instruction[19:15], rs2 = instruction[24:20], rd = instruction[11:7];
    wire reg_write, alu_b_immediate, jump, jalr, mem_read, mem_write;
    wire load_unsigned, illegal, ecall, ebreak, fence;
    wire [1:0] alu_a_select, writeback_select, mem_size;
    wire [3:0] alu_operation;
    wire [2:0] immediate_format, branch_condition;
    wire [31:0] rs1_data, rs2_data, immediate;
    wire [31:0] alu_a, alu_b, alu_result;
    wire alu_zero, branch_taken;
    wire [31:0] pc_plus4 = pc + 32'd4;
    wire [31:0] pc_relative_target = pc + immediate;
    wire [31:0] jalr_target = alu_result & 32'hfffffffe;
    wire [31:0] next_pc = jalr ? jalr_target :
                          ((jump || branch_taken) ? pc_relative_target : pc_plus4);
    reg pending_trap;
    reg [31:0] pending_cause, pending_value;
    wire register_write_enable = reg_write && !rst && !halted && !pending_trap;
    reg [31:0] load_result;
    wire [31:0] shifted_load = dmem_read_data >> {alu_result[1:0], 3'b000};
    wire [31:0] writeback_data = (writeback_select == `WB_LOAD) ? load_result :
                                ((writeback_select == `WB_PC4) ? pc_plus4 : alu_result);
    reg [3:0] store_mask;

    rv32i_decoder u_decoder(
        .instruction(instruction), .reg_write(reg_write), .alu_a_select(alu_a_select),
        .alu_b_immediate(alu_b_immediate), .alu_operation(alu_operation),
        .immediate_format(immediate_format), .writeback_select(writeback_select),
        .branch_condition(branch_condition), .jump(jump), .jalr(jalr),
        .mem_read(mem_read), .mem_write(mem_write), .mem_size(mem_size),
        .load_unsigned(load_unsigned), .illegal(illegal), .ecall(ecall), .ebreak(ebreak), .fence(fence)
    );
    rv32i_immediate u_immediate(.instruction(instruction), .format(immediate_format), .immediate(immediate));
    rv32i_regfile u_regfile(
        .clk(clk), .rst(rst), .write_enable(register_write_enable),
        .rs1(rs1), .rs2(rs2), .rd(rd), .write_data(writeback_data),
        .rs1_data(rs1_data), .rs2_data(rs2_data),
        .debug_address(debug_reg_address), .debug_data(debug_reg_data)
    );
    assign alu_a = (alu_a_select == `A_PC) ? pc : ((alu_a_select == `A_ZERO) ? 32'b0 : rs1_data);
    assign alu_b = alu_b_immediate ? immediate : rs2_data;
    rv32i_alu u_alu(.a(alu_a), .b(alu_b), .operation(alu_operation), .result(alu_result), .zero(alu_zero));
    rv32i_branch u_branch(.rs1_data(rs1_data), .rs2_data(rs2_data), .condition(branch_condition), .taken(branch_taken));
    rv32i_pc #(.RESET_PC(RESET_PC)) u_pc(.clk(clk), .rst(rst), .enable(!halted && !pending_trap), .next_pc(next_pc), .pc(pc));

    always @* begin
        case (mem_size)
            0: load_result = load_unsigned ? {24'b0, shifted_load[7:0]} : {{24{shifted_load[7]}}, shifted_load[7:0]};
            1: load_result = load_unsigned ? {16'b0, shifted_load[15:0]} : {{16{shifted_load[15]}}, shifted_load[15:0]};
            default: load_result = shifted_load;
        endcase
        case (mem_size)
            0: store_mask = 4'b0001 << alu_result[1:0];
            1: store_mask = 4'b0011 << alu_result[1:0];
            default: store_mask = 4'b1111;
        endcase
    end
    // Fault priority is defined for this minimal execution environment.
    // A fault suppresses PC update, register write and every store byte lane.
    always @* begin
        pending_trap = 0; pending_cause = 0; pending_value = 0;
        if (pc[1:0] != 0) begin
            pending_trap = 1; pending_cause = 0; pending_value = pc;
        end else if (imem_fault) begin
            pending_trap = 1; pending_cause = 1; pending_value = pc;
        end else if (illegal) begin
            pending_trap = 1; pending_cause = 2; pending_value = instruction;
        end else if (ebreak) begin
            pending_trap = 1; pending_cause = 3;
        end else if (ecall) begin
            pending_trap = 1; pending_cause = 11;
        end else if ((jump || jalr || branch_taken) && next_pc[1:0] != 0) begin
            pending_trap = 1; pending_cause = 0; pending_value = next_pc;
        end else if ((mem_read || mem_write) &&
                     (((mem_size == 1) && alu_result[0]) || ((mem_size == 2) && alu_result[1:0] != 0))) begin
            pending_trap = 1; pending_cause = mem_write ? 6 : 4; pending_value = alu_result;
        end else if ((mem_read || mem_write) && dmem_fault) begin
            pending_trap = 1; pending_cause = mem_write ? 7 : 5; pending_value = alu_result;
        end
    end
    assign imem_address = pc;
    assign dmem_request = (mem_read || mem_write) && !rst && !halted;
    assign dmem_address = alu_result;
    assign dmem_size = mem_size;
    assign dmem_write_data = rs2_data << {alu_result[1:0], 3'b000};
    assign dmem_write_strobe = (mem_write && !rst && !halted && !pending_trap) ? store_mask : 4'b0;
    assign trap_valid = halted;

    always @(posedge clk) begin
        if (rst) begin
            halted <= 0; trap_cause <= 0; trap_pc <= 0; trap_value <= 0; retire_valid <= 0;
            trace_pc <= 0; trace_instruction <= 0; trace_next_pc <= 0;
            trace_rd_write <= 0; trace_rd <= 0; trace_rd_data <= 0;
            trace_mem_read <= 0; trace_mem_address <= 0; trace_mem_strobe <= 0; trace_mem_data <= 0;
        end else begin
            retire_valid <= 0;
            if (!halted) begin
                if (pending_trap) begin
                    halted <= 1; trap_cause <= pending_cause; trap_pc <= pc; trap_value <= pending_value;
                end else begin
                    retire_valid <= 1;
                    trace_pc <= pc; trace_instruction <= instruction; trace_next_pc <= next_pc;
                    trace_rd_write <= reg_write && rd != 0;
                    trace_rd <= (reg_write && rd != 0) ? rd : 5'b0;
                    trace_rd_data <= (reg_write && rd != 0) ? writeback_data : 32'b0;
                    trace_mem_read <= mem_read;
                    trace_mem_address <= (mem_read || mem_write) ? alu_result : 32'b0;
                    trace_mem_strobe <= mem_write ? store_mask : 4'b0;
                    trace_mem_data <= mem_write ? dmem_write_data : 32'b0;
                end
            end
        end
    end
endmodule
