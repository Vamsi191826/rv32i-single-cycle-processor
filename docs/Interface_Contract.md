# Interface and timing contract

## Core ports

| Port | Direction | Meaning |
| --- | --- | --- |
| `clk`, `rst` | input | Rising-edge clock; active-high synchronous reset |
| `imem_address[31:0]` | output | Current instruction byte address |
| `imem_read_data[31:0]`, `imem_fault` | input | Combinational instruction and access-fault response |
| `dmem_request` | output | Valid memory operation while running; may remain asserted for a faulting access |
| `dmem_address[31:0]` | output | Effective byte address, not an aligned word index |
| `dmem_size[1:0]` | output | 0=byte, 1=halfword, 2=word |
| `dmem_write_data[31:0]` | output | rs2 shifted left by 8*address[1:0] |
| `dmem_write_strobe[3:0]` | output | Little-endian byte lanes; nonzero only for a successful store |
| `dmem_read_data[31:0]` | input | Combinational aligned word at address & ~3 |
| `dmem_fault` | input | Combinational access-fault response based on request/address/size |
| `debug_reg_address[4:0]`, `debug_reg_data[31:0]` | in/out | Asynchronous observation of a GPR |
| `halted`, `trap_valid` | output | Sticky execution stop; trap_valid equals halted |
| `trap_cause`, `trap_pc`, `trap_value` | output | Registered metadata retained until CPU reset |
| `retire_valid`, `trace_*` | output | Registered successful instruction event; see below |

The external memory must respond combinationally. There is no ready, busy or retry signal. Access faults must not depend on store strobes: the core derives the strobes from fault checking, so such feedback would create a combinational loop. A successful store is sampled at the rising edge using the byte strobes. Do not commit a write merely because `dmem_request` is high.

Instruction and data memories are separate address spaces in `rv32i_system`. Each occupies byte addresses 0..4095 by default. An instruction address must be four-byte aligned; data accesses require alignment to their width.

The memory model supports other positive, word-aligned capacities (IMEM_WORDS >= 1; DMEM_BYTES >= 4 and a multiple of four). Verification uses the default sizes only.

## State update

Between clock edges: fetch -> decode/register read -> execute -> memory read/writeback selection -> next-PC decision. At the rising edge: update PC, write one GPR, perform a successful store, and register the retirement event.

A taken branch or jump uses its target. An untaken branch uses PC+4. JAL/JALR write PC+4 into rd but use a separate value as the next PC.

Reset clears GPRs, PC and halt/trace state. The data memory has no reset input; CPU reset does not erase it. The testbench explicitly reinitializes it between cases.

## Trap contract

| Cause | Event | trap_value |
| --- | --- | --- |
| 0 | Instruction address misaligned | Misaligned PC or taken target |
| 1 | Instruction access fault | Faulting fetch PC |
| 2 | Illegal instruction | Raw 32-bit instruction |
| 3 | EBREAK | 0 |
| 4 | Load address misaligned | Effective address |
| 5 | Load access fault | Effective address |
| 6 | Store address misaligned | Effective address |
| 7 | Store access fault | Effective address |
| 11 | ECALL | 0 |

`trap_pc` is the instruction PC. A misaligned taken branch/jump is attributed to the control-flow instruction; an inaccessible aligned jump target is detected during the next fetch. Untaken branches do not fault on their unused target.

Priority: current-PC alignment -> instruction access -> illegal encoding -> EBREAK/ECALL -> taken-target alignment -> data alignment -> data access. ECALL's numeric cause uses the machine-environment convention, but there is no implemented privilege state, CSR file, handler or MRET instruction.

On a fault, the instruction does not retire; PC, GPRs and memory do not update. The core latches metadata and halts until reset.

## Retirement record

Golden traces are 320-bit records, printed as ten 32-bit fields in this order:

1. Current PC.
2. Instruction word.
3. Next PC.
4. Actual GPR write flag (0 or 1).
5. rd index, or zero when no GPR is changed.
6. rd value, or zero when no GPR is changed.
7. Load flag (0 or 1).
8. Effective memory address, or zero for non-memory instructions.
9. Store byte strobes, zero extended to 32 bits.
10. Shifted store bus data, or zero for non-stores.

`trace_*` signals describe the completed instruction after the edge and remain stable until the next event. Always qualify them with `retire_valid`. A load to x0 has a load trace but no GPR write; it can still fault.

This is a project trace format, not the complete RVFI interface.

