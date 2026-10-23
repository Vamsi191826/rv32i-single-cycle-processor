`timescale 1ns/1ps
module tb_system;
    `include "tb_common.svh"
    localparam MAX_TRACE=20000;
    reg clk=0,rst=1;
    reg [4:0] debug_reg_address=0;
    wire [31:0] debug_reg_data;
    wire halted,trap_valid,retire_valid,trace_rd_write,trace_mem_read;
    wire [31:0] trap_cause,trap_pc,trap_value,trace_pc,trace_instruction,trace_next_pc,trace_rd_data,trace_mem_address,trace_mem_data;
    wire [4:0] trace_rd;
    wire [3:0] trace_mem_strobe;
    reg [319:0] expected_trace[0:MAX_TRACE-1];
    reg [31:0] expected_regs[0:31];
    reg [7:0] expected_memory[0:4095];
    wire [319:0] observed_trace={trace_pc,trace_instruction,trace_next_pc,
        {31'b0,trace_rd_write},{27'b0,trace_rd},trace_rd_data,{31'b0,trace_mem_read},
        trace_mem_address,{28'b0,trace_mem_strobe},trace_mem_data};
    integer total_cases=0,total_retired=0,trace_file;
    integer i;
    always #5 clk=~clk;
    rv32i_system dut(.*);

    // Protocol assertions are checked at the actual state-update edge.
    always @(posedge clk) begin
        if(!rst) begin
            if(dut.u_core.pending_trap && (dut.dmem_write_strobe!=0 || dut.u_core.register_write_enable))
                $fatal(1,"Faulting instruction attempted a side effect");
            if(halted && (dut.dmem_write_strobe!=0 || dut.u_core.register_write_enable))
                $fatal(1,"Halted core attempted a side effect");
        end
    end
    task automatic run_case(input string name,input integer words,input integer expected_count,
                            input [31:0] expected_cause,input [31:0] expected_pc,input [31:0] expected_value);
        string base;
        integer index,cycles,k;
        reg [31:0] held_pc;
        begin
            base={project_root,"/programs/generated/",name};
            require_file({base,".hex"}); require_file({base,"_regs.hex"}); require_file({base,"_memory.hex"});
            if(expected_count>0) require_file({base,"_trace.hex"});
            @(negedge clk); rst=1;
            for(k=0;k<1024;k=k+1) dut.u_memory.imem[k]=32'h00000013;
            for(k=0;k<4096;k=k+1) dut.u_memory.dmem[k]=0;
            $readmemh({base,".hex"},dut.u_memory.imem,0,words-1);
            if(expected_count>0) $readmemh({base,"_trace.hex"},expected_trace,0,expected_count-1);
            $readmemh({base,"_regs.hex"},expected_regs);
            $readmemh({base,"_memory.hex"},expected_memory);
            repeat(2) @(posedge clk);
            @(negedge clk); rst=0; index=0; cycles=0;
            while(!halted && cycles<expected_count+10) begin
                @(negedge clk); cycles=cycles+1;
                if(retire_valid) begin
                    if(index>=expected_count) $fatal(1,"Unexpected extra retire event in %s",name);
                    if(observed_trace !== expected_trace[index]) begin
                        $display("CASE=%s STEP=%0d ACTUAL=%h EXPECTED=%h",name,index,observed_trace,expected_trace[index]);
                        $fatal(1,"Architectural trace mismatch");
                    end
                    $fdisplay(trace_file,"%s,%0d,%08h,%08h,%08h,%0d,%0d,%08h,%0d,%08h,%01h,%08h",
                        name,index,trace_pc,trace_instruction,trace_next_pc,trace_rd_write,trace_rd,
                        trace_rd_data,trace_mem_read,trace_mem_address,trace_mem_strobe,trace_mem_data);
                    index=index+1;
                end
            end
            if(!halted || !trap_valid) $fatal(1,"Watchdog expired in %s",name);
            if(index!=expected_count) $fatal(1,"Retire count mismatch in %s: got=%0d expected=%0d",name,index,expected_count);
            if(trap_cause !== expected_cause || trap_pc !== expected_pc || trap_value !== expected_value)
                $fatal(1,"Trap mismatch %s cause=%h pc=%h value=%h",name,trap_cause,trap_pc,trap_value);
            for(k=0;k<32;k=k+1) begin
                debug_reg_address=k; #1;
                if(debug_reg_data !== expected_regs[k]) $fatal(1,"Final register mismatch %s x%0d got=%h expected=%h",name,k,debug_reg_data,expected_regs[k]);
            end
            for(k=0;k<4096;k=k+1)
                if(dut.u_memory.dmem[k] !== expected_memory[k]) $fatal(1,"Final memory mismatch %s byte=%0d",name,k);
            held_pc=dut.imem_address;
            repeat(3) begin
                @(negedge clk);
                if(retire_valid || dut.imem_address !== held_pc) $fatal(1,"Halt stability failure in %s",name);
            end
            total_cases=total_cases+1; total_retired=total_retired+index;
            $display("CASE_PASS %s retires=%0d cause=%0d",name,index,trap_cause);
        end
    endtask
    initial begin
        configure_paths();
        trace_file=$fopen({output_directory,"/retire_trace.csv"},"w");
        if(trace_file==0) $fatal(1,"Cannot create trace output");
        $fdisplay(trace_file,"case,step,pc,instruction,next_pc,rd_write,rd,rd_data,mem_read,mem_address,mem_strobe,mem_data");
        if($test$plusargs("WAVES")) begin
            $dumpfile({output_directory,"/system.vcd"});
            $dumpvars(0,tb_system.dut.u_core);
        end
        `include "case_list.svh"
        // Reset must release a sticky trap and clear all architectural registers.
        @(negedge clk); rst=1; @(posedge clk); #1;
        if(halted || trap_valid || dut.imem_address!=0) $fatal(1,"Reset did not release halted core");
        for(i=0;i<32;i=i+1) begin debug_reg_address=i; #1; if(debug_reg_data!=0) $fatal(1,"Reset register x%0d",i); end
        $fclose(trace_file);
        $display("SYSTEM_SUMMARY cases=%0d retired=%0d",total_cases,total_retired);
        mark_pass("tb_system"); $finish;
    end
endmodule
